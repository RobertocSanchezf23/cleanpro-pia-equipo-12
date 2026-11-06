"""Elementos compartidos del dominio: Dinero, roles, errores de negocio y eventos.

El dominio no importa FastAPI, SQLAlchemy ni nada de infraestructura: solo Python estándar.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from decimal import ROUND_HALF_UP, Decimal
from enum import Enum
from typing import Any

CENTAVOS = Decimal("0.01")


# ---------------------------------------------------------------------------
# Value Object: Dinero (PA-02: un solo lugar para sumar y redondear montos)
# ---------------------------------------------------------------------------
@dataclass(frozen=True, order=True)
class Dinero:
    """Monto en MXN con dos decimales. Inmutable: cada operación devuelve un Dinero nuevo."""

    monto: Decimal

    def __post_init__(self):
        valor = Decimal(str(self.monto)).quantize(CENTAVOS, ROUND_HALF_UP)
        if valor < 0:
            raise ValueError("Un monto de dinero no puede ser negativo")
        object.__setattr__(self, "monto", valor)

    @classmethod
    def cero(cls) -> "Dinero":
        return cls(Decimal("0"))

    def __add__(self, otro: "Dinero") -> "Dinero":
        return Dinero(self.monto + otro.monto)

    def por(self, factor: Decimal | int | str) -> "Dinero":
        return Dinero(self.monto * Decimal(str(factor)))

    @property
    def centavos(self) -> int:
        return int(self.monto * 100)

    @classmethod
    def desde_centavos(cls, centavos: int) -> "Dinero":
        return cls(Decimal(centavos) / 100)

    def __str__(self) -> str:
        return f"${self.monto:,.2f}"


def sumar(montos) -> Dinero:
    total = Dinero.cero()
    for m in montos:
        total = total + m
    return total


# ---------------------------------------------------------------------------
# Roles (RB-15)
# ---------------------------------------------------------------------------
class Rol(str, Enum):
    CLIENTE = "CLIENTE"
    COORDINADOR = "COORDINADOR"
    SUPERVISOR = "SUPERVISOR"
    CUADRILLA = "CUADRILLA"
    ADMINISTRACION = "ADMINISTRACION"


# ---------------------------------------------------------------------------
# Errores de negocio. Cada uno lleva la regla del BRD que se violó.
# ---------------------------------------------------------------------------
class ReglaDeNegocioError(Exception):
    """Una operación viola una regla del BRD."""

    def __init__(self, regla: str, mensaje: str):
        self.regla = regla
        self.mensaje = mensaje
        super().__init__(f"{regla}: {mensaje}")


class TransicionInvalida(ReglaDeNegocioError):
    """La máquina de estados no permite la operación en el estado actual."""


class PermisoDenegado(ReglaDeNegocioError):
    """El rol no tiene permiso para la operación (RB-15)."""


def exigir_rol(rol: Rol, *permitidos: Rol, accion: str, regla: str = "RB-15") -> None:
    if rol not in permitidos:
        nombres = ", ".join(p.value for p in permitidos)
        raise PermisoDenegado(regla, f"solo {nombres} puede {accion} (rol: {rol.value})")


# ---------------------------------------------------------------------------
# Eventos de dominio y raíz de aggregate
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class EventoDominio:
    nombre: str
    aggregate_id: str
    datos: dict[str, Any] = field(default_factory=dict)


class RaizDeAggregate:
    """Guarda los eventos que produce el aggregate hasta que la Unidad de Trabajo los publica."""

    def __init__(self):
        self._eventos: list[EventoDominio] = []

    def _registrar_evento(self, nombre: str, **datos) -> None:
        self._eventos.append(EventoDominio(nombre, self.id, datos))

    @property
    def eventos(self) -> list[EventoDominio]:
        return list(self._eventos)

    def extraer_eventos(self) -> list[EventoDominio]:
        eventos, self._eventos = self._eventos, []
        return eventos


def formato_fecha(momento: datetime) -> str:
    return momento.strftime("%Y-%m-%d %H:%M")
