"""Esquemas de entrada y salida de la API (Pydantic). Swagger los muestra con sus ejemplos."""
from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from src.domain.cotizacion import Cotizacion
from src.domain.factura import Factura
from src.domain.servicio import Servicio
from src.domain.valores import Frecuencia, TipoInmueble


def _m(dinero) -> Decimal | None:
    return None if dinero is None else dinero.monto


# ----- Entradas -------------------------------------------------------------
class CotizacionEntrada(BaseModel):
    model_config = ConfigDict(json_schema_extra={"example": {
        "cliente_id": "CLN-C001", "ubicacion": "Av. Universidad 500, San Nicolás", "superficie_m2": 100,
        "tipo_inmueble": "RESIDENCIAL", "frecuencia": "UNICA", "extras": ["VENTANAS"]}})
    cliente_id: str
    ubicacion: str = Field(min_length=1)
    superficie_m2: Decimal = Field(gt=0)
    tipo_inmueble: TipoInmueble
    frecuencia: Frecuencia
    extras: list[str] = Field(default_factory=list, description="Códigos del catálogo (GET /catalogo/extras)")


class EstimacionEntrada(BaseModel):
    model_config = ConfigDict(json_schema_extra={"example": {"duracion_horas": 3, "personal": 2}})
    duracion_horas: Decimal = Field(gt=0)
    personal: int = Field(ge=1)


class ProgramacionEntrada(BaseModel):
    model_config = ConfigDict(json_schema_extra={"example": {
        "cotizacion_id": "COT-DEMO-01", "cuadrilla_id": "CUA-01", "supervisor": "Ana López",
        "inicio": "2026-12-15T09:00:00"}})
    cotizacion_id: str
    cuadrilla_id: str
    supervisor: str = Field(min_length=1)
    inicio: datetime = Field(description="Fecha y hora local de Monterrey")


class ReprogramacionEntrada(BaseModel):
    model_config = ConfigDict(json_schema_extra={"example": {"nuevo_inicio": "2026-12-16T10:00:00", "cargo": None}})
    nuevo_inicio: datetime
    cargo: Decimal | None = Field(default=None, ge=0, description="Solo con menos de 2 h de anticipación (H-07)")


class AusenciaEntrada(BaseModel):
    model_config = ConfigDict(json_schema_extra={"example": {
        "integrante": "Luis Pérez", "reasignado": False, "nuevo_inicio": "2026-12-17T09:00:00"}})
    integrante: str = Field(min_length=1)
    reasignado: bool
    nuevo_inicio: datetime | None = None


class AccesoDenegadoEntrada(BaseModel):
    model_config = ConfigDict(json_schema_extra={"example": {"minutos_espera": 15}})
    minutos_espera: int = Field(ge=0)


class IncidenciaEntrada(BaseModel):
    model_config = ConfigDict(json_schema_extra={"example": {
        "tipo": "SERVICIO_ADICIONAL", "descripcion": "El cliente pidió limpiar el horno", "extra": "HORNO"}})
    tipo: Literal["CAMBIO", "SERVICIO_ADICIONAL", "INMUEBLE_MAYOR", "MATERIAL_ESPECIAL"]
    descripcion: str = Field(min_length=1)
    extra: str | None = Field(default=None, description="Para SERVICIO_ADICIONAL (RB-12)")
    monto: Decimal | None = Field(default=None, gt=0, description="Para MATERIAL_ESPECIAL (RB-14)")
    superficie_real: Decimal | None = Field(default=None, gt=0, description="Para INMUEBLE_MAYOR (RB-13)")


class FacturaEntrada(BaseModel):
    servicio_id: str


# ----- Salidas --------------------------------------------------------------
class ExtraSalida(BaseModel):
    codigo: str
    descripcion: str
    precio: Decimal


class CotizacionSalida(BaseModel):
    id: str
    cliente_id: str
    estado: str
    ubicacion: str
    superficie_m2: Decimal
    tipo_inmueble: str
    frecuencia: str
    extras: list[ExtraSalida]
    duracion_horas: Decimal | None
    personal: int | None
    precio: Decimal | None
    solicitada_en: datetime
    enviada_en: datetime | None
    vence_en: datetime | None
    renovada_de: str | None

    @classmethod
    def de(cls, c: Cotizacion) -> "CotizacionSalida":
        return cls(
            id=c.id, cliente_id=c.cliente_id, estado=c.estado.value, ubicacion=c.inmueble.ubicacion,
            superficie_m2=c.inmueble.superficie_m2, tipo_inmueble=c.inmueble.tipo.value, frecuencia=c.frecuencia.value,
            extras=[ExtraSalida(codigo=e.codigo, descripcion=e.descripcion, precio=e.precio.monto) for e in c.extras],
            duracion_horas=c.estimacion.duracion_horas if c.estimacion else None,
            personal=c.estimacion.personal if c.estimacion else None, precio=_m(c.precio),
            solicitada_en=c.solicitada_en, enviada_en=c.vigencia.enviada_en if c.vigencia else None,
            vence_en=c.vigencia.vence_en if c.vigencia else None, renovada_de=c.renovada_de,
        )


class IncidenciaSalida(BaseModel):
    id: str
    tipo: str
    descripcion: str
    registrada_en: datetime
    registrada_por: str
    cargo_id: str | None


class CargoSalida(BaseModel):
    id: str
    origen: str
    descripcion: str
    monto: Decimal
    autorizado: bool


class ServicioSalida(BaseModel):
    id: str
    cotizacion_id: str
    cliente_id: str
    cuadrilla_id: str
    supervisor: str
    inicio: datetime
    fin: datetime
    ubicacion: str
    estado: str
    precio_acordado: Decimal
    superficie_cotizada: Decimal
    superficie_real: Decimal | None
    recalculo_pendiente: bool
    incidencias: list[IncidenciaSalida]
    cargos: list[CargoSalida]

    @classmethod
    def de(cls, s: Servicio) -> "ServicioSalida":
        return cls(
            id=s.id, cotizacion_id=s.cotizacion_id, cliente_id=s.cliente_id, cuadrilla_id=s.cuadrilla_id,
            supervisor=s.supervisor, inicio=s.programacion.inicio, fin=s.programacion.fin, ubicacion=s.ubicacion,
            estado=s.estado.value, precio_acordado=s.precio_acordado.monto, superficie_cotizada=s.superficie_cotizada,
            superficie_real=s.superficie_real, recalculo_pendiente=s.recalculo_pendiente,
            incidencias=[IncidenciaSalida(id=i.id, tipo=i.tipo.value, descripcion=i.descripcion,
                                          registrada_en=i.registrada_en, registrada_por=i.registrada_por.value,
                                          cargo_id=i.cargo_id) for i in s.incidencias],
            cargos=[CargoSalida(id=c.id, origen=c.origen.value, descripcion=c.descripcion, monto=c.monto.monto,
                                autorizado=c.autorizado) for c in s.cargos],
        )


class ConceptoSalida(BaseModel):
    descripcion: str
    origen: str
    monto: Decimal
    referencia: str | None


class FacturaSalida(BaseModel):
    id: str
    servicio_id: str
    cliente_id: str
    emitida_en: datetime
    estado_pago: str
    pagada_en: datetime | None
    total: Decimal
    conceptos: list[ConceptoSalida]

    @classmethod
    def de(cls, f: Factura) -> "FacturaSalida":
        return cls(
            id=f.id, servicio_id=f.servicio_id, cliente_id=f.cliente_id, emitida_en=f.emitida_en,
            estado_pago=f.estado_pago.value, pagada_en=f.pagada_en, total=f.total.monto,
            conceptos=[ConceptoSalida(descripcion=c.descripcion, origen=c.origen.value, monto=c.monto.monto,
                                      referencia=c.referencia) for c in f.conceptos],
        )


class ErrorSalida(BaseModel):
    error: str
    regla: str | None = None
    detalle: str
