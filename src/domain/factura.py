"""Aggregate Factura y Domain Service GeneradorDeFactura (CU-05).

Estado de pago (H-14): PENDIENTE --registrar_pago--> PAGADA
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from enum import Enum

from .comun import Dinero, RaizDeAggregate, Rol, TransicionInvalida, exigir_rol, sumar
from .especificaciones import Disyuncion, Especificacion, exigir
from .servicio import EstadoServicio, Servicio, TipoIncidencia

PORCENTAJE_CANCELACION = Decimal("0.50")  # RB-11


class EstadoPago(str, Enum):
    PENDIENTE = "PENDIENTE"
    PAGADA = "PAGADA"


class OrigenConcepto(str, Enum):
    SERVICIO = "SERVICIO"
    CARGO_ADICIONAL = "CARGO_ADICIONAL"
    CANCELACION = "CANCELACION"


@dataclass(frozen=True)
class ConceptoFacturado:
    descripcion: str
    origen: OrigenConcepto
    monto: Dinero
    referencia: str | None = None  # id del cargo o de la incidencia que lo originó (RES-04)


class Factura(RaizDeAggregate):
    def __init__(self, id: str, servicio_id: str, cliente_id: str, conceptos: list[ConceptoFacturado],
                 emitida_en: datetime, estado_pago: EstadoPago = EstadoPago.PENDIENTE,
                 pagada_en: datetime | None = None):
        super().__init__()
        self.id = id
        self.servicio_id = servicio_id
        self.cliente_id = cliente_id
        self.conceptos = list(conceptos)
        self.emitida_en = emitida_en
        self.estado_pago = estado_pago
        self.pagada_en = pagada_en

    @property
    def total(self) -> Dinero:
        """RES-04: el total siempre es la suma de los conceptos."""
        return sumar(c.monto for c in self.conceptos)

    # US-20 E5
    def registrar_pago(self, ahora: datetime, rol: Rol) -> None:
        exigir_rol(rol, Rol.ADMINISTRACION, accion="registrar pagos")
        if self.estado_pago != EstadoPago.PENDIENTE:
            raise TransicionInvalida("H-14", "la factura ya está pagada")
        self.estado_pago = EstadoPago.PAGADA
        self.pagada_en = ahora
        self._registrar_evento("FacturaPagada", servicio_id=self.servicio_id)


# --- Specifications de la facturación -----------------------------------------
@dataclass
class CandidatoAFactura:
    servicio: Servicio
    ya_facturado: bool


class EstaTerminado(Especificacion[CandidatoAFactura]):
    regla, motivo = "RB-07", "el servicio no está terminado"

    def se_cumple(self, c: CandidatoAFactura) -> bool:
        return c.servicio.estado == EstadoServicio.TERMINADO


class EstaNoRealizado(Especificacion[CandidatoAFactura]):
    regla, motivo = "RB-11", "el servicio no está como no realizado"

    def se_cumple(self, c: CandidatoAFactura) -> bool:
        return c.servicio.estado == EstadoServicio.NO_REALIZADO


class TieneCargosPendientes(Especificacion[CandidatoAFactura]):
    regla, motivo = "RB-14", "hay cargos adicionales sin autorizar"

    def se_cumple(self, c: CandidatoAFactura) -> bool:
        return bool(c.servicio.cargos_pendientes)


class YaFacturado(Especificacion[CandidatoAFactura]):
    regla, motivo = "SUP-04", "el servicio ya tiene factura"

    def se_cumple(self, c: CandidatoAFactura) -> bool:
        return c.ya_facturado


# (Terminado OR No realizado) AND NOT cargos pendientes AND NOT ya facturado   — H-01, RB-07, RB-14, SUP-04
SERVICIO_FACTURABLE = (
    Disyuncion(EstaTerminado(), EstaNoRealizado()).con_motivo(
        "RB-07", "solo se factura un servicio terminado o no realizado")
    & ~TieneCargosPendientes()
    & ~YaFacturado()
)


class GeneradorDeFactura:
    """Domain Service: arma la Factura a partir del Servicio (involucra dos aggregates)."""

    def generar(self, factura_id: str, servicio: Servicio, ya_facturado: bool, ahora: datetime,
                rol: Rol) -> Factura:
        exigir_rol(rol, Rol.ADMINISTRACION, accion="registrar la facturación")
        exigir(SERVICIO_FACTURABLE, CandidatoAFactura(servicio, ya_facturado))

        if servicio.estado == EstadoServicio.NO_REALIZADO:
            conceptos = [ConceptoFacturado(
                "Cargo de cancelación (50 %): el cliente no permitió el acceso", OrigenConcepto.CANCELACION,
                servicio.precio_acordado.por(PORCENTAJE_CANCELACION),
                next((i.id for i in servicio.incidencias if i.tipo == TipoIncidencia.ACCESO_DENEGADO), None),
            )]
        else:
            conceptos = [ConceptoFacturado("Servicio de limpieza", OrigenConcepto.SERVICIO,
                                           servicio.precio_acordado, servicio.cotizacion_id)]
            conceptos += [ConceptoFacturado(c.descripcion, OrigenConcepto.CARGO_ADICIONAL, c.monto, c.id)
                          for c in servicio.cargos_autorizados]

        factura = Factura(factura_id, servicio.id, servicio.cliente_id, conceptos, ahora)
        factura._registrar_evento("FacturaEmitida", cliente_id=servicio.cliente_id, servicio_id=servicio.id,
                                  total=str(factura.total.monto))
        return factura
