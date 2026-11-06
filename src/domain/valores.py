"""Value Objects del dominio de CleanPro: inmueble, frecuencia, extras, estimación y programación."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import Decimal
from enum import Enum
from typing import Protocol

from .comun import Dinero, ReglaDeNegocioError


class TipoInmueble(str, Enum):
    RESIDENCIAL = "RESIDENCIAL"
    EMPRESARIAL = "EMPRESARIAL"


class Frecuencia(str, Enum):
    """RB-03: la frecuencia recurrente recibe 10 % de descuento sobre el precio base."""

    UNICA = "UNICA"
    SEMANAL = "SEMANAL"
    QUINCENAL = "QUINCENAL"
    MENSUAL = "MENSUAL"

    @property
    def es_recurrente(self) -> bool:
        return self is not Frecuencia.UNICA


@dataclass(frozen=True)
class DatosDelInmueble:
    ubicacion: str
    superficie_m2: Decimal
    tipo: TipoInmueble

    def __post_init__(self):
        object.__setattr__(self, "superficie_m2", Decimal(str(self.superficie_m2)))
        if not self.ubicacion or not self.ubicacion.strip():
            raise ReglaDeNegocioError("US-01", "la ubicación del inmueble es obligatoria")
        if self.superficie_m2 <= 0:
            raise ReglaDeNegocioError("US-01", "la superficie debe ser mayor que cero")


@dataclass(frozen=True)
class ExtraDelCatalogo:
    """Renglón del catálogo de extras (SUP-06): datos de referencia, no es un aggregate."""

    codigo: str
    descripcion: str
    precio: Dinero


@dataclass(frozen=True)
class ExtraSolicitado:
    """Extra del catálogo con el precio que tenía al momento de cotizar."""

    codigo: str
    descripcion: str
    precio: Dinero


class CatalogoDeExtras(Protocol):
    def buscar(self, codigo: str) -> ExtraDelCatalogo | None: ...


def resolver_extras(codigos: list[str], catalogo: CatalogoDeExtras) -> tuple[ExtraSolicitado, ...]:
    """CU-01 rechazo: un extra que no existe en el catálogo no se puede cotizar (SUP-06)."""
    extras = []
    for codigo in codigos:
        encontrado = catalogo.buscar(codigo.strip().upper())
        if encontrado is None:
            raise ReglaDeNegocioError("SUP-06", f"el extra '{codigo}' no está en el catálogo de extras")
        extras.append(ExtraSolicitado(encontrado.codigo, encontrado.descripcion, encontrado.precio))
    return tuple(extras)


@dataclass(frozen=True)
class EstimacionOperativa:
    """H-04: la duración y el personal los captura el coordinador."""

    duracion_horas: Decimal
    personal: int

    def __post_init__(self):
        object.__setattr__(self, "duracion_horas", Decimal(str(self.duracion_horas)))
        if self.duracion_horas <= 0:
            raise ReglaDeNegocioError("US-06", "la duración estimada debe ser mayor que cero")
        if self.personal <= 0:
            raise ReglaDeNegocioError("US-06", "el personal necesario debe ser al menos 1")


@dataclass(frozen=True)
class Programacion:
    """Fecha, hora y duración del servicio. La duración define cuándo está ocupada la cuadrilla (H-15)."""

    inicio: datetime
    duracion_horas: Decimal

    def __post_init__(self):
        object.__setattr__(self, "duracion_horas", Decimal(str(self.duracion_horas)))
        if self.inicio.tzinfo is not None:
            raise ValueError("Programacion usa hora local sin zona horaria")

    @property
    def fin(self) -> datetime:
        return self.inicio + timedelta(minutes=int(self.duracion_horas * 60))

    def se_traslapa_con(self, otra: "Programacion") -> bool:
        return self.inicio < otra.fin and otra.inicio < self.fin

    def con_nuevo_inicio(self, inicio: datetime) -> "Programacion":
        return Programacion(inicio, self.duracion_horas)
