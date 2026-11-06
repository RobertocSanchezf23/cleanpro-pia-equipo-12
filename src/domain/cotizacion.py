"""Aggregate Cotizacion (CU-01, CU-02).

Máquina de estados (H-03):

    SOLICITADA --estimar--> SOLICITADA (con precio) --enviar--> PENDIENTE
    PENDIENTE --aceptar--> ACEPTADA
    PENDIENTE --rechazar--> RECHAZADA
    PENDIENTE --5 días hábiles sin respuesta--> VENCIDA --renovar--> (nueva cotización SOLICITADA)
"""
from __future__ import annotations

from datetime import datetime
from enum import Enum

from .comun import Dinero, RaizDeAggregate, Rol, TransicionInvalida, exigir_rol
from .entidades import Cliente
from .especificaciones import Especificacion, exigir
from .precio import CalculadoraDePrecio
from .valores import DatosDelInmueble, EstimacionOperativa, ExtraSolicitado, Frecuencia
from .vigencia import Vigencia


class EstadoCotizacion(str, Enum):
    SOLICITADA = "SOLICITADA"
    PENDIENTE = "PENDIENTE"
    ACEPTADA = "ACEPTADA"
    RECHAZADA = "RECHAZADA"
    VENCIDA = "VENCIDA"


# --- Specifications ---------------------------------------------------------
class ClienteActivo(Especificacion[Cliente]):
    regla, motivo = "Paquete PIA", "el cliente está inactivo y no puede solicitar cotizaciones"

    def se_cumple(self, cliente: Cliente) -> bool:
        return cliente.activo


class EstaPendiente(Especificacion["Cotizacion"]):
    regla, motivo = "US-02", "solo se responde una cotización pendiente"

    def se_cumple(self, cotizacion: "Cotizacion") -> bool:
        return cotizacion.estado == EstadoCotizacion.PENDIENTE


class EstaVigente(Especificacion["Cotizacion"]):
    regla, motivo = "RB-08", "la cotización venció: pasaron más de 5 días hábiles desde su envío"

    def __init__(self, ahora: datetime):
        self.ahora = ahora

    def se_cumple(self, cotizacion: "Cotizacion") -> bool:
        return cotizacion.vigencia is not None and cotizacion.vigencia.esta_vigente(self.ahora)


class TienePrecio(Especificacion["Cotizacion"]):
    regla, motivo = "RB-01", "la cotización debe estimarse (con precio calculado) antes de enviarse"

    def se_cumple(self, cotizacion: "Cotizacion") -> bool:
        return cotizacion.precio is not None


def puede_aceptarse(ahora: datetime) -> Especificacion["Cotizacion"]:
    return EstaPendiente() & EstaVigente(ahora)


# --- Aggregate ---------------------------------------------------------------
class Cotizacion(RaizDeAggregate):
    def __init__(self, id: str, cliente_id: str, inmueble: DatosDelInmueble, frecuencia: Frecuencia,
                 extras: tuple[ExtraSolicitado, ...], solicitada_en: datetime,
                 estado: EstadoCotizacion = EstadoCotizacion.SOLICITADA,
                 estimacion: EstimacionOperativa | None = None, precio: Dinero | None = None,
                 vigencia: Vigencia | None = None, respondida_en: datetime | None = None,
                 renovada_de: str | None = None):
        super().__init__()
        self.id = id
        self.cliente_id = cliente_id
        self.inmueble = inmueble
        self.frecuencia = frecuencia
        self.extras = tuple(extras)
        self.solicitada_en = solicitada_en
        self.estado = estado
        self.estimacion = estimacion
        self.precio = precio
        self.vigencia = vigencia
        self.respondida_en = respondida_en
        self.renovada_de = renovada_de

    # US-01
    @classmethod
    def solicitar(cls, id: str, cliente: Cliente, inmueble: DatosDelInmueble, frecuencia: Frecuencia,
                  extras: tuple[ExtraSolicitado, ...], ahora: datetime, rol: Rol) -> "Cotizacion":
        exigir_rol(rol, Rol.CLIENTE, Rol.COORDINADOR, accion="solicitar una cotización")
        exigir(ClienteActivo(), cliente)
        cotizacion = cls(id, cliente.id, inmueble, frecuencia, extras, ahora)
        cotizacion._registrar_evento("CotizacionSolicitada", cliente_id=cliente.id)
        return cotizacion

    # US-06 (RB-03, RB-15)
    def estimar(self, estimacion: EstimacionOperativa, calculadora: CalculadoraDePrecio, rol: Rol) -> Dinero:
        exigir_rol(rol, Rol.COORDINADOR, accion="estimar una cotización")
        self._exigir_estado(EstadoCotizacion.SOLICITADA, "estimar")
        self.estimacion = estimacion
        self.precio = calculadora.calcular(self.inmueble, self.frecuencia, self.extras)
        self._registrar_evento("CotizacionEstimada", precio=str(self.precio.monto))
        return self.precio

    # US-07 (RB-01, RB-08)
    def enviar(self, ahora: datetime, rol: Rol) -> None:
        exigir_rol(rol, Rol.COORDINADOR, accion="enviar una cotización")
        self._exigir_estado(EstadoCotizacion.SOLICITADA, "enviar")
        exigir(TienePrecio(), self)
        self.estado = EstadoCotizacion.PENDIENTE
        self.vigencia = Vigencia(ahora)
        self._registrar_evento("CotizacionEnviada", cliente_id=self.cliente_id,
                               precio=str(self.precio.monto), vence_en=self.vigencia.vence_en.isoformat())

    # US-22 (RB-08, RES-05)
    def actualizar_vencimiento(self, ahora: datetime) -> bool:
        """Marca la cotización como vencida si sigue pendiente fuera de su vigencia."""
        if self.estado == EstadoCotizacion.PENDIENTE and not self.vigencia.esta_vigente(ahora):
            self.estado = EstadoCotizacion.VENCIDA
            self._registrar_evento("CotizacionVencida", cliente_id=self.cliente_id)
            return True
        return False

    # US-02 (RB-02, RB-08)
    def aceptar(self, ahora: datetime, rol: Rol) -> None:
        exigir_rol(rol, Rol.CLIENTE, accion="aceptar la cotización")
        exigir(puede_aceptarse(ahora), self, TransicionInvalida)
        self.estado = EstadoCotizacion.ACEPTADA
        self.respondida_en = ahora
        self._registrar_evento("CotizacionAceptada", cliente_id=self.cliente_id)

    def rechazar(self, ahora: datetime, rol: Rol) -> None:
        exigir_rol(rol, Rol.CLIENTE, accion="rechazar la cotización")
        exigir(EstaPendiente(), self, TransicionInvalida)
        self.estado = EstadoCotizacion.RECHAZADA
        self.respondida_en = ahora
        self._registrar_evento("CotizacionRechazada", cliente_id=self.cliente_id)

    # US-22: "permitir generar una nueva"
    def renovar(self, nuevo_id: str, ahora: datetime, rol: Rol) -> "Cotizacion":
        exigir_rol(rol, Rol.COORDINADOR, accion="generar una nueva cotización")
        self._exigir_estado(EstadoCotizacion.VENCIDA, "renovar")
        nueva = Cotizacion(nuevo_id, self.cliente_id, self.inmueble, self.frecuencia, self.extras, ahora,
                           renovada_de=self.id)
        nueva._registrar_evento("CotizacionSolicitada", cliente_id=self.cliente_id, renovada_de=self.id)
        return nueva

    @property
    def esta_aceptada(self) -> bool:
        return self.estado == EstadoCotizacion.ACEPTADA

    def _exigir_estado(self, esperado: EstadoCotizacion, accion: str) -> None:
        if self.estado != esperado:
            raise TransicionInvalida(
                "Máquina de estados",
                f"no se puede {accion} una cotización en estado {self.estado.value}",
            )

