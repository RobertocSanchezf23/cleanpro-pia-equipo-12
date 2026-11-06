"""Casos de uso CU-01 (generar y enviar cotización) y CU-02 (responder cotización)."""
from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal

from src.domain.comun import Rol, TransicionInvalida
from src.domain.cotizacion import Cotizacion
from src.domain.precio import CalculadoraDePrecio
from src.domain.valores import DatosDelInmueble, EstimacionOperativa, Frecuencia, TipoInmueble, resolver_extras

from .base import CasoDeUso, obtener_o_fallar


@dataclass
class SolicitudDeCotizacion:
    cliente_id: str
    ubicacion: str
    superficie_m2: Decimal
    tipo_inmueble: TipoInmueble
    frecuencia: Frecuencia
    extras: list[str] = field(default_factory=list)


class ServicioDeCotizaciones(CasoDeUso):
    def __init__(self, uow_factory, reloj, ids, calculadora: CalculadoraDePrecio | None = None):
        super().__init__(uow_factory, reloj, ids)
        self.calculadora = calculadora or CalculadoraDePrecio()

    # US-01
    def solicitar(self, datos: SolicitudDeCotizacion, rol: Rol) -> Cotizacion:
        with self.uow_factory() as uow:
            cliente = obtener_o_fallar(uow.clientes.obtener(datos.cliente_id), "Cliente", datos.cliente_id)
            extras = resolver_extras(datos.extras, uow.catalogo)
            inmueble = DatosDelInmueble(datos.ubicacion, datos.superficie_m2, datos.tipo_inmueble)
            cotizacion = Cotizacion.solicitar(self.ids.nuevo("COT"), cliente, inmueble, datos.frecuencia,
                                              extras, self.reloj.ahora(), rol)
            uow.cotizaciones.guardar(cotizacion)
            self._confirmar(uow, cotizacion)
            return cotizacion

    # US-06
    def estimar(self, cotizacion_id: str, duracion_horas: Decimal, personal: int, rol: Rol) -> Cotizacion:
        with self.uow_factory() as uow:
            cotizacion = self._obtener(uow, cotizacion_id)
            cotizacion.estimar(EstimacionOperativa(duracion_horas, personal), self.calculadora, rol)
            uow.cotizaciones.guardar(cotizacion)
            self._confirmar(uow, cotizacion)
            return cotizacion

    # US-07
    def enviar(self, cotizacion_id: str, rol: Rol) -> Cotizacion:
        with self.uow_factory() as uow:
            cotizacion = self._obtener(uow, cotizacion_id)
            cotizacion.enviar(self.reloj.ahora(), rol)
            uow.cotizaciones.guardar(cotizacion)
            self._confirmar(uow, cotizacion)
            return cotizacion

    # US-02 (+ RB-08: si ya venció, queda registrada como vencida y se rechaza la respuesta)
    def aceptar(self, cotizacion_id: str, rol: Rol) -> Cotizacion:
        return self._responder(cotizacion_id, rol, aceptar=True)

    def rechazar(self, cotizacion_id: str, rol: Rol) -> Cotizacion:
        return self._responder(cotizacion_id, rol, aceptar=False)

    # US-22: al consultar, una cotización pendiente fuera de vigencia se marca como vencida
    def consultar(self, cotizacion_id: str) -> Cotizacion:
        with self.uow_factory() as uow:
            cotizacion = self._obtener(uow, cotizacion_id)
            if cotizacion.actualizar_vencimiento(self.reloj.ahora()):
                uow.cotizaciones.guardar(cotizacion)
                self._confirmar(uow, cotizacion)
            return cotizacion

    # US-22: generar una nueva cotización a partir de una vencida
    def renovar(self, cotizacion_id: str, rol: Rol) -> Cotizacion:
        with self.uow_factory() as uow:
            vencida = self._obtener(uow, cotizacion_id)
            vencida.actualizar_vencimiento(self.reloj.ahora())
            nueva = vencida.renovar(self.ids.nuevo("COT"), self.reloj.ahora(), rol)
            uow.cotizaciones.guardar(vencida)
            uow.cotizaciones.guardar(nueva)
            self._confirmar(uow, vencida, nueva)
            return nueva

    def _responder(self, cotizacion_id: str, rol: Rol, aceptar: bool) -> Cotizacion:
        with self.uow_factory() as uow:
            cotizacion = self._obtener(uow, cotizacion_id)
            ahora = self.reloj.ahora()
            if cotizacion.actualizar_vencimiento(ahora):
                uow.cotizaciones.guardar(cotizacion)
                self._confirmar(uow, cotizacion)
                raise TransicionInvalida("RB-08", "la cotización venció: pasaron más de 5 días hábiles desde "
                                                  "su envío; el coordinador debe generar una nueva")
            if aceptar:
                cotizacion.aceptar(ahora, rol)
            else:
                cotizacion.rechazar(ahora, rol)
            uow.cotizaciones.guardar(cotizacion)
            self._confirmar(uow, cotizacion)
            return cotizacion

    @staticmethod
    def _obtener(uow, cotizacion_id: str) -> Cotizacion:
        return obtener_o_fallar(uow.cotizaciones.obtener(cotizacion_id), "Cotización", cotizacion_id)
