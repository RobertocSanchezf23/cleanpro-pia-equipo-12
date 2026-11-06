"""Aggregate Servicio (CU-03, CU-04): programación, ejecución, incidencias y cargos.

Máquina de estados (H-02):

    PROGRAMADO --registrar_inicio--> EN_EJECUCION --registrar_terminacion--> TERMINADO
    PROGRAMADO --acceso denegado tras 15 min--> NO_REALIZADO
    PROGRAMADO --reprogramar / ausencia sin reemplazo--> PROGRAMADO (nueva fecha)
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import Decimal
from enum import Enum

from .comun import (
    Dinero,
    RaizDeAggregate,
    ReglaDeNegocioError,
    Rol,
    TransicionInvalida,
    exigir_rol,
    formato_fecha,
)
from .cotizacion import Cotizacion
from .entidades import Cuadrilla
from .especificaciones import Especificacion, exigir
from .precio import CalculadoraDePrecio
from .valores import DatosDelInmueble, ExtraDelCatalogo, Frecuencia, Programacion, TipoInmueble

ANTICIPACION_SIN_CARGO = timedelta(hours=2)  # RB-09
ANTICIPACION_AVISO_AUSENCIA = timedelta(hours=1)  # RB-10
MINUTOS_DE_ESPERA_POR_ACCESO = 15  # RB-11, RES-06
TOLERANCIA_SUPERFICIE = Decimal("0.15")  # RB-13


class EstadoServicio(str, Enum):
    PROGRAMADO = "PROGRAMADO"
    EN_EJECUCION = "EN_EJECUCION"
    TERMINADO = "TERMINADO"
    NO_REALIZADO = "NO_REALIZADO"


class TipoIncidencia(str, Enum):
    CAMBIO = "CAMBIO"  # cambio o incidencia general (RB-06)
    SERVICIO_ADICIONAL = "SERVICIO_ADICIONAL"  # RB-12
    INMUEBLE_MAYOR = "INMUEBLE_MAYOR"  # RB-13
    MATERIAL_ESPECIAL = "MATERIAL_ESPECIAL"  # RB-14
    EMPLEADO_AUSENTE = "EMPLEADO_AUSENTE"  # RB-10
    ACCESO_DENEGADO = "ACCESO_DENEGADO"  # RB-11
    AVISO_TARDIO = "AVISO_TARDIO"  # RB-10, H-08


TIPOS_EN_SITIO = {
    TipoIncidencia.CAMBIO,
    TipoIncidencia.SERVICIO_ADICIONAL,
    TipoIncidencia.INMUEBLE_MAYOR,
    TipoIncidencia.MATERIAL_ESPECIAL,
}


class OrigenCargo(str, Enum):
    SERVICIO_ADICIONAL = "SERVICIO_ADICIONAL"  # RB-12
    MATERIAL_ESPECIAL = "MATERIAL_ESPECIAL"  # RB-14
    REPROGRAMACION = "REPROGRAMACION"  # RB-09, H-07


@dataclass
class CargoAdicional:
    """Nace pendiente; solo el coordinador lo autoriza (RB-12, RB-14, RB-15)."""

    id: str
    origen: OrigenCargo
    descripcion: str
    monto: Dinero
    autorizado: bool = False

    def __post_init__(self):
        if self.monto.monto <= 0:
            raise ReglaDeNegocioError("RB-14", "el cargo adicional debe ser mayor que cero")


@dataclass
class Incidencia:
    """Entity dentro del aggregate Servicio (SUP-03)."""

    id: str
    tipo: TipoIncidencia
    descripcion: str
    registrada_en: datetime
    registrada_por: Rol
    cargo_id: str | None = None


# --- Specifications de la programación (CU-03) ------------------------------
@dataclass
class SolicitudDeProgramacion:
    cotizacion: Cotizacion
    cuadrilla: Cuadrilla
    programacion: Programacion
    ocupaciones: list[Programacion]
    ya_tiene_servicio: bool
    ahora: datetime


class CotizacionAceptada(Especificacion[SolicitudDeProgramacion]):
    regla, motivo = "RB-02", "el servicio solo se programa si el cliente aceptó la cotización"

    def se_cumple(self, s: SolicitudDeProgramacion) -> bool:
        return s.cotizacion.esta_aceptada


class CotizacionSinServicio(Especificacion[SolicitudDeProgramacion]):
    regla, motivo = "H-06", "la cotización ya tiene un servicio programado"

    def se_cumple(self, s: SolicitudDeProgramacion) -> bool:
        return not s.ya_tiene_servicio


class CuadrillaActiva(Especificacion[SolicitudDeProgramacion]):
    regla, motivo = "RB-04", "la cuadrilla no está activa"

    def se_cumple(self, s: SolicitudDeProgramacion) -> bool:
        return s.cuadrilla.activa


class CuadrillaDisponible(Especificacion[SolicitudDeProgramacion]):
    regla, motivo = "RES-01", "la cuadrilla ya tiene otro servicio en ese horario"

    def se_cumple(self, s: SolicitudDeProgramacion) -> bool:
        return not any(s.programacion.se_traslapa_con(o) for o in s.ocupaciones)


class FechaFutura(Especificacion[SolicitudDeProgramacion]):
    regla, motivo = "US-08", "la fecha del servicio debe ser posterior al momento actual"

    def se_cumple(self, s: SolicitudDeProgramacion) -> bool:
        return s.programacion.inicio > s.ahora


PUEDE_PROGRAMARSE = (
    CotizacionAceptada() & CotizacionSinServicio() & FechaFutura() & CuadrillaActiva() & CuadrillaDisponible()
)


# --- Aggregate -----------------------------------------------------------------
class Servicio(RaizDeAggregate):
    def __init__(self, id: str, cotizacion_id: str, cliente_id: str, cuadrilla_id: str, supervisor: str,
                 programacion: Programacion, ubicacion: str, tipo_inmueble: TipoInmueble,
                 frecuencia: Frecuencia, superficie_cotizada: Decimal, precio_extras: Dinero,
                 precio_acordado: Dinero, estado: EstadoServicio = EstadoServicio.PROGRAMADO,
                 incidencias: list[Incidencia] | None = None, cargos: list[CargoAdicional] | None = None,
                 superficie_real: Decimal | None = None, recalculo_pendiente: bool = False,
                 iniciado_en: datetime | None = None, terminado_en: datetime | None = None):
        super().__init__()
        self.id = id
        self.cotizacion_id = cotizacion_id
        self.cliente_id = cliente_id
        self.cuadrilla_id = cuadrilla_id
        self.supervisor = supervisor
        self.programacion = programacion
        self.ubicacion = ubicacion
        self.tipo_inmueble = tipo_inmueble
        self.frecuencia = frecuencia
        self.superficie_cotizada = Decimal(str(superficie_cotizada))
        self.precio_extras = precio_extras
        self.precio_acordado = precio_acordado
        self.estado = estado
        self.incidencias = incidencias or []
        self.cargos = cargos or []
        self.superficie_real = superficie_real
        self.recalculo_pendiente = recalculo_pendiente
        self.iniciado_en = iniciado_en
        self.terminado_en = terminado_en

    # ----- CU-03: programar y asignar cuadrilla (US-08, US-09, US-03) ------------
    @classmethod
    def programar(cls, id: str, solicitud: SolicitudDeProgramacion, supervisor: str, rol: Rol) -> "Servicio":
        exigir_rol(rol, Rol.COORDINADOR, accion="programar un servicio")
        if not supervisor or not supervisor.strip():
            raise ReglaDeNegocioError("SUP-02", "el servicio necesita un supervisor responsable")
        exigir(PUEDE_PROGRAMARSE, solicitud)
        cot = solicitud.cotizacion
        servicio = cls(
            id=id, cotizacion_id=cot.id, cliente_id=cot.cliente_id, cuadrilla_id=solicitud.cuadrilla.id,
            supervisor=supervisor.strip(), programacion=solicitud.programacion, ubicacion=cot.inmueble.ubicacion,
            tipo_inmueble=cot.inmueble.tipo, frecuencia=cot.frecuencia,
            superficie_cotizada=cot.inmueble.superficie_m2,
            precio_extras=sum((e.precio for e in cot.extras), Dinero.cero()),
            precio_acordado=cot.precio,
        )
        servicio._registrar_evento(
            "ServicioProgramado", cliente_id=cot.cliente_id, cuadrilla_id=solicitud.cuadrilla.id,
            fecha=formato_fecha(solicitud.programacion.inicio), supervisor=servicio.supervisor,
        )
        return servicio

    # ----- US-04: reprogramación (RB-09, RB-15, H-07) ----------------------------
    def reprogramar(self, nuevo_inicio: datetime, ahora: datetime, rol: Rol, ocupaciones: list[Programacion],
                    cargo: Dinero | None = None) -> bool:
        """Devuelve True si fue una reprogramación de última hora (menos de 2 h)."""
        self._exigir_estado(EstadoServicio.PROGRAMADO, "reprogramar")
        ultima_hora = self.programacion.inicio - ahora < ANTICIPACION_SIN_CARGO
        if ultima_hora:
            exigir_rol(rol, Rol.COORDINADOR, accion="autorizar una reprogramación de última hora",
                       regla="RB-09/RB-15")
        else:
            exigir_rol(rol, Rol.CLIENTE, Rol.COORDINADOR, accion="solicitar una reprogramación")
            if cargo is not None and cargo.monto > 0:
                raise ReglaDeNegocioError("RB-09", "con 2 horas o más de anticipación la reprogramación no tiene costo")
        self._mover_a(nuevo_inicio, ahora, ocupaciones)
        if ultima_hora and cargo is not None and cargo.monto > 0:
            nuevo = CargoAdicional(self._nuevo_id_cargo(), OrigenCargo.REPROGRAMACION,
                                   "Reprogramación de última hora", cargo, autorizado=True)
            self.cargos.append(nuevo)
        self._registrar_evento("ServicioReprogramado", cliente_id=self.cliente_id,
                               fecha=formato_fecha(self.programacion.inicio), ultima_hora=ultima_hora,
                               motivo="solicitud del cliente")
        return ultima_hora

    # ----- US-10: empleado ausente (RB-10, H-08) ----------------------------------
    def registrar_ausencia(self, ahora: datetime, rol: Rol, integrante: str, reasignado: bool,
                           nuevo_inicio: datetime | None = None,
                           ocupaciones: list[Programacion] | None = None) -> None:
        exigir_rol(rol, Rol.COORDINADOR, accion="reasignar personal o reprogramar por ausencia")
        self._exigir_estado(EstadoServicio.PROGRAMADO, "registrar una ausencia en")
        if reasignado:
            self._agregar_incidencia(TipoIncidencia.EMPLEADO_AUSENTE,
                                     f"Ausencia de {integrante}; se reasignó personal disponible", ahora, rol)
            return
        if nuevo_inicio is None:
            raise ReglaDeNegocioError("RB-10", "si no se completa la cuadrilla, el servicio debe reprogramarse")
        anticipacion = self.programacion.inicio - ahora
        self._agregar_incidencia(TipoIncidencia.EMPLEADO_AUSENTE,
                                 f"Ausencia de {integrante}; no se completó la cuadrilla", ahora, rol)
        self._mover_a(nuevo_inicio, ahora, ocupaciones or [])
        if anticipacion < ANTICIPACION_AVISO_AUSENCIA:
            minutos = max(int(anticipacion.total_seconds() // 60), 0)
            self._agregar_incidencia(TipoIncidencia.AVISO_TARDIO,
                                     f"Se avisó al cliente con {minutos} min de anticipación (mínimo 60)", ahora, rol)
        self._registrar_evento("ServicioReprogramado", cliente_id=self.cliente_id,
                               fecha=formato_fecha(self.programacion.inicio), ultima_hora=False,
                               motivo="falta de personal en la cuadrilla")

    # ----- US-16: cliente no permite el acceso (RB-11, RES-06) -------------------
    def registrar_acceso_denegado(self, minutos_espera: int, ahora: datetime, rol: Rol) -> None:
        exigir_rol(rol, Rol.SUPERVISOR, accion="registrar el acceso denegado")
        self._exigir_estado(EstadoServicio.PROGRAMADO, "registrar acceso denegado en")
        if minutos_espera < MINUTOS_DE_ESPERA_POR_ACCESO:
            raise ReglaDeNegocioError(
                "RB-11", f"se debe esperar al menos {MINUTOS_DE_ESPERA_POR_ACCESO} minutos "
                         f"(se esperaron {minutos_espera})")
        self._agregar_incidencia(TipoIncidencia.ACCESO_DENEGADO,
                                 f"El cliente no permitió el acceso; espera de {minutos_espera} min", ahora, rol)
        self.estado = EstadoServicio.NO_REALIZADO
        self._registrar_evento("ServicioNoRealizado", cliente_id=self.cliente_id)

    # ----- US-13 / US-14: inicio y terminación (RB-05, RES-03, RB-13) ------------
    def registrar_inicio(self, ahora: datetime, rol: Rol) -> None:
        exigir_rol(rol, Rol.SUPERVISOR, accion="registrar el inicio del servicio", regla="RB-05")
        self._exigir_estado(EstadoServicio.PROGRAMADO, "iniciar")
        self.estado = EstadoServicio.EN_EJECUCION
        self.iniciado_en = ahora
        self._registrar_evento("ServicioIniciado")

    def registrar_terminacion(self, ahora: datetime, rol: Rol) -> None:
        exigir_rol(rol, Rol.SUPERVISOR, accion="registrar la terminación del servicio", regla="RB-05")
        self._exigir_estado(EstadoServicio.EN_EJECUCION, "terminar")
        if self.recalculo_pendiente:
            raise ReglaDeNegocioError("RB-13", "el coordinador debe recalcular el precio antes de terminar el servicio")
        self.estado = EstadoServicio.TERMINADO
        self.terminado_en = ahora
        self._registrar_evento("ServicioTerminado", cliente_id=self.cliente_id)

    # ----- US-15, US-11, US-12: incidencias en sitio (RB-06, RB-12, RB-13, RB-14) -
    def registrar_incidencia(self, tipo: TipoIncidencia, descripcion: str, ahora: datetime, rol: Rol, *,
                             extra: ExtraDelCatalogo | None = None, monto: Dinero | None = None,
                             superficie_real: Decimal | None = None) -> Incidencia:
        exigir_rol(rol, Rol.SUPERVISOR, accion="registrar incidencias", regla="RB-06")
        self._exigir_estado(EstadoServicio.EN_EJECUCION, "registrar incidencias en")
        if tipo not in TIPOS_EN_SITIO:
            raise ReglaDeNegocioError("RB-06", f"el tipo {tipo.value} se registra con su propia operación")
        if not descripcion or not descripcion.strip():
            raise ReglaDeNegocioError("RB-06", "la incidencia debe tener una descripción")

        cargo = None
        if tipo == TipoIncidencia.SERVICIO_ADICIONAL:
            if extra is None:
                raise ReglaDeNegocioError("RB-12", "el servicio adicional se cotiza con el catálogo de extras")
            cargo = CargoAdicional(self._nuevo_id_cargo(), OrigenCargo.SERVICIO_ADICIONAL,
                                   f"Servicio adicional: {extra.descripcion}", extra.precio)
        elif tipo == TipoIncidencia.MATERIAL_ESPECIAL:
            if monto is None:
                raise ReglaDeNegocioError("RB-14", "el material especial requiere el monto del cargo")
            cargo = CargoAdicional(self._nuevo_id_cargo(), OrigenCargo.MATERIAL_ESPECIAL,
                                   f"Material especial: {descripcion.strip()}", monto)
        elif tipo == TipoIncidencia.INMUEBLE_MAYOR:
            if superficie_real is None or Decimal(str(superficie_real)) <= 0:
                raise ReglaDeNegocioError("RB-13", "se debe indicar la superficie real del inmueble")
            self.superficie_real = Decimal(str(superficie_real))
            self.recalculo_pendiente = self.excede_superficie(self.superficie_real)

        if cargo is not None:
            self.cargos.append(cargo)
        return self._agregar_incidencia(tipo, descripcion.strip(), ahora, rol, cargo)

    def excede_superficie(self, superficie_real: Decimal) -> bool:
        """RB-13 / H-09: solo una diferencia de MÁS de 15 % obliga a recalcular."""
        return superficie_real > self.superficie_cotizada * (Decimal("1") + TOLERANCIA_SUPERFICIE)

    # ----- US-11: autorizar cargos (RB-12, RB-14, RB-15) --------------------------
    def autorizar_cargo(self, cargo_id: str, rol: Rol) -> CargoAdicional:
        exigir_rol(rol, Rol.COORDINADOR, accion="autorizar cargos adicionales")
        if self.estado not in (EstadoServicio.EN_EJECUCION, EstadoServicio.TERMINADO):
            raise TransicionInvalida("Máquina de estados",
                                     f"no se autorizan cargos en un servicio {self.estado.value}")
        cargo = next((c for c in self.cargos if c.id == cargo_id), None)
        if cargo is None:
            raise ReglaDeNegocioError("RB-14", f"el cargo {cargo_id} no pertenece a este servicio")
        if cargo.autorizado:
            raise TransicionInvalida("RB-14", "el cargo ya estaba autorizado")
        cargo.autorizado = True
        self._registrar_evento("CargoAdicionalAutorizado", cargo_id=cargo.id, monto=str(cargo.monto.monto))
        return cargo

    # ----- US-12: recalcular precio (RB-13, RB-03) -------------------------------
    def recalcular_precio(self, calculadora: CalculadoraDePrecio, rol: Rol) -> Dinero:
        exigir_rol(rol, Rol.COORDINADOR, accion="recalcular el precio")
        if not self.recalculo_pendiente:
            raise TransicionInvalida("RB-13", "el servicio no tiene un recálculo de precio pendiente")
        anterior = self.precio_acordado
        inmueble = DatosDelInmueble(self.ubicacion, self.superficie_real, self.tipo_inmueble)
        self.precio_acordado = calculadora.precio_base(inmueble, self.frecuencia) + self.precio_extras
        self.recalculo_pendiente = False
        self._registrar_evento("PrecioRecalculado", anterior=str(anterior.monto),
                               nuevo=str(self.precio_acordado.monto))
        return self.precio_acordado

    # ----- consultas del aggregate ----------------------------------------------
    @property
    def cargos_pendientes(self) -> list[CargoAdicional]:
        return [c for c in self.cargos if not c.autorizado]

    @property
    def cargos_autorizados(self) -> list[CargoAdicional]:
        return [c for c in self.cargos if c.autorizado]

    # ----- auxiliares ---------------------------------------------------------------
    def _mover_a(self, nuevo_inicio: datetime, ahora: datetime, ocupaciones: list[Programacion]) -> None:
        nueva = self.programacion.con_nuevo_inicio(nuevo_inicio)
        if nueva.inicio <= ahora:
            raise ReglaDeNegocioError("US-04", "la nueva fecha debe ser posterior al momento actual")
        if any(nueva.se_traslapa_con(o) for o in ocupaciones):
            raise ReglaDeNegocioError("RES-01", "la cuadrilla ya tiene otro servicio en el nuevo horario")
        self.programacion = nueva

    def _agregar_incidencia(self, tipo: TipoIncidencia, descripcion: str, ahora: datetime, rol: Rol,
                            cargo: CargoAdicional | None = None) -> Incidencia:
        incidencia = Incidencia(f"{self.id}-I{len(self.incidencias) + 1}", tipo, descripcion, ahora, rol,
                                cargo.id if cargo else None)
        self.incidencias.append(incidencia)
        self._registrar_evento("IncidenciaRegistrada", incidencia_id=incidencia.id, tipo=tipo.value,
                               descripcion=descripcion, cargo=str(cargo.monto.monto) if cargo else None)
        return incidencia

    def _nuevo_id_cargo(self) -> str:
        return f"{self.id}-C{len(self.cargos) + 1}"

    def _exigir_estado(self, esperado: EstadoServicio, accion: str) -> None:
        if self.estado != esperado:
            raise TransicionInvalida(
                "Máquina de estados", f"no se puede {accion} un servicio en estado {self.estado.value}")
