"""Casos de uso CU-03 (programar y asignar cuadrilla) y CU-04 (ejecución con incidencias)."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

from src.domain.comun import Dinero, ReglaDeNegocioError, Rol
from src.domain.precio import CalculadoraDePrecio
from src.domain.servicio import Servicio, SolicitudDeProgramacion, TipoIncidencia
from src.domain.valores import Programacion

from .base import CasoDeUso, obtener_o_fallar


@dataclass
class DatosDeProgramacion:
    cotizacion_id: str
    cuadrilla_id: str
    supervisor: str
    inicio: datetime


@dataclass
class DatosDeIncidencia:
    tipo: TipoIncidencia
    descripcion: str
    extra: str | None = None
    monto: Decimal | None = None
    superficie_real: Decimal | None = None


class ProgramacionDeServicios(CasoDeUso):
    # US-08, US-09, US-03
    def programar(self, datos: DatosDeProgramacion, rol: Rol) -> Servicio:
        with self.uow_factory() as uow:
            cotizacion = obtener_o_fallar(uow.cotizaciones.obtener(datos.cotizacion_id), "Cotización",
                                          datos.cotizacion_id)
            cuadrilla = obtener_o_fallar(uow.cuadrillas.obtener(datos.cuadrilla_id), "Cuadrilla",
                                         datos.cuadrilla_id)
            ahora = self.reloj.ahora()
            duracion = cotizacion.estimacion.duracion_horas if cotizacion.estimacion else Decimal("1")
            solicitud = SolicitudDeProgramacion(
                cotizacion=cotizacion, cuadrilla=cuadrilla, programacion=Programacion(datos.inicio, duracion),
                ocupaciones=uow.servicios.ocupaciones_de_cuadrilla(cuadrilla.id),
                ya_tiene_servicio=uow.servicios.existe_para_cotizacion(cotizacion.id), ahora=ahora,
            )
            servicio = Servicio.programar(self.ids.nuevo("SRV"), solicitud, datos.supervisor, rol)
            uow.servicios.guardar(servicio)
            self._confirmar(uow, servicio)
            return servicio

    # US-04
    def reprogramar(self, servicio_id: str, nuevo_inicio: datetime, rol: Rol,
                    cargo: Decimal | None = None) -> Servicio:
        with self.uow_factory() as uow:
            servicio = _obtener(uow, servicio_id)
            ocupaciones = uow.servicios.ocupaciones_de_cuadrilla(servicio.cuadrilla_id, excluir_id=servicio.id)
            servicio.reprogramar(nuevo_inicio, self.reloj.ahora(), rol, ocupaciones,
                                 Dinero(cargo) if cargo is not None else None)
            uow.servicios.guardar(servicio)
            self._confirmar(uow, servicio)
            return servicio

    # US-10
    def registrar_ausencia(self, servicio_id: str, integrante: str, reasignado: bool, rol: Rol,
                           nuevo_inicio: datetime | None = None) -> Servicio:
        with self.uow_factory() as uow:
            servicio = _obtener(uow, servicio_id)
            ocupaciones = uow.servicios.ocupaciones_de_cuadrilla(servicio.cuadrilla_id, excluir_id=servicio.id)
            servicio.registrar_ausencia(self.reloj.ahora(), rol, integrante, reasignado, nuevo_inicio, ocupaciones)
            uow.servicios.guardar(servicio)
            self._confirmar(uow, servicio)
            return servicio


class EjecucionDeServicios(CasoDeUso):
    def __init__(self, uow_factory, reloj, ids, calculadora: CalculadoraDePrecio | None = None):
        super().__init__(uow_factory, reloj, ids)
        self.calculadora = calculadora or CalculadoraDePrecio()

    def obtener(self, servicio_id: str) -> Servicio:
        with self.uow_factory() as uow:
            return _obtener(uow, servicio_id)

    # US-13
    def registrar_inicio(self, servicio_id: str, rol: Rol) -> Servicio:
        return self._operar(servicio_id, lambda s: s.registrar_inicio(self.reloj.ahora(), rol))

    # US-14, US-18
    def registrar_terminacion(self, servicio_id: str, rol: Rol) -> Servicio:
        return self._operar(servicio_id, lambda s: s.registrar_terminacion(self.reloj.ahora(), rol))

    # US-16
    def registrar_acceso_denegado(self, servicio_id: str, minutos_espera: int, rol: Rol) -> Servicio:
        return self._operar(servicio_id,
                            lambda s: s.registrar_acceso_denegado(minutos_espera, self.reloj.ahora(), rol))

    # US-15, US-11 (servicio adicional), US-12 (inmueble mayor), RB-14 (material especial)
    def registrar_incidencia(self, servicio_id: str, datos: DatosDeIncidencia, rol: Rol) -> Servicio:
        with self.uow_factory() as uow:
            servicio = _obtener(uow, servicio_id)
            extra = None
            if datos.extra:
                extra = uow.catalogo.buscar(datos.extra.strip().upper())
                if extra is None:
                    raise ReglaDeNegocioError("SUP-06", f"el extra '{datos.extra}' no está en el catálogo de extras")
            servicio.registrar_incidencia(
                datos.tipo, datos.descripcion, self.reloj.ahora(), rol, extra=extra,
                monto=Dinero(datos.monto) if datos.monto is not None else None,
                superficie_real=datos.superficie_real,
            )
            uow.servicios.guardar(servicio)
            self._confirmar(uow, servicio)
            return servicio

    # US-11, RB-14, RB-15
    def autorizar_cargo(self, servicio_id: str, cargo_id: str, rol: Rol) -> Servicio:
        return self._operar(servicio_id, lambda s: s.autorizar_cargo(cargo_id, rol))

    # US-12
    def recalcular_precio(self, servicio_id: str, rol: Rol) -> Servicio:
        return self._operar(servicio_id, lambda s: s.recalcular_precio(self.calculadora, rol))

    def _operar(self, servicio_id: str, operacion) -> Servicio:
        with self.uow_factory() as uow:
            servicio = _obtener(uow, servicio_id)
            operacion(servicio)
            uow.servicios.guardar(servicio)
            self._confirmar(uow, servicio)
            return servicio


def _obtener(uow, servicio_id: str) -> Servicio:
    return obtener_o_fallar(uow.servicios.obtener(servicio_id), "Servicio", servicio_id)
