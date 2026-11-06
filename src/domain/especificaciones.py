"""Patrón Specification: reglas de negocio como objetos que se combinan con AND, OR y NOT.

Cada especificación sabe qué regla del BRD representa (``regla``) y cómo explicar su
incumplimiento (``motivo``). Así, cuando una combinación falla, el error dice exactamente
qué regla se violó.
"""
from __future__ import annotations

from typing import Generic, TypeVar

from .comun import ReglaDeNegocioError

T = TypeVar("T")


class Especificacion(Generic[T]):
    regla: str = ""
    motivo: str = ""

    def se_cumple(self, candidato: T) -> bool:  # pragma: no cover - método abstracto
        raise NotImplementedError

    def incumplidas(self, candidato: T) -> list["Especificacion[T]"]:
        """Especificaciones que fallan para el candidato (vacía si se cumple)."""
        return [] if self.se_cumple(candidato) else [self]

    def __and__(self, otra: "Especificacion[T]") -> "Especificacion[T]":
        return Conjuncion(self, otra)

    def __or__(self, otra: "Especificacion[T]") -> "Especificacion[T]":
        return Disyuncion(self, otra)

    def __invert__(self) -> "Especificacion[T]":
        return Negacion(self)


class Conjuncion(Especificacion[T]):
    """AND: se cumple si se cumplen todas las partes."""

    def __init__(self, *partes: Especificacion[T]):
        self.partes = list(partes)

    def se_cumple(self, candidato: T) -> bool:
        return all(p.se_cumple(candidato) for p in self.partes)

    def incumplidas(self, candidato: T) -> list[Especificacion[T]]:
        fallas: list[Especificacion[T]] = []
        for parte in self.partes:
            fallas.extend(parte.incumplidas(candidato))
        return fallas

    def __and__(self, otra: Especificacion[T]) -> Especificacion[T]:
        return Conjuncion(*self.partes, otra)


class Disyuncion(Especificacion[T]):
    """OR: se cumple si se cumple al menos una parte."""

    def __init__(self, *partes: Especificacion[T], regla: str = "", motivo: str = ""):
        self.partes = list(partes)
        self.regla = regla
        self.motivo = motivo

    def se_cumple(self, candidato: T) -> bool:
        return any(p.se_cumple(candidato) for p in self.partes)

    def incumplidas(self, candidato: T) -> list[Especificacion[T]]:
        if self.se_cumple(candidato):
            return []
        if self.motivo:
            return [self]
        fallas: list[Especificacion[T]] = []
        for parte in self.partes:
            fallas.extend(parte.incumplidas(candidato))
        return fallas

    def con_motivo(self, regla: str, motivo: str) -> "Disyuncion[T]":
        return Disyuncion(*self.partes, regla=regla, motivo=motivo)


class Negacion(Especificacion[T]):
    """NOT: se cumple si la interna NO se cumple."""

    def __init__(self, interna: Especificacion[T], regla: str = "", motivo: str = ""):
        self.interna = interna
        self.regla = regla or interna.regla
        self.motivo = motivo or interna.motivo  # la interna describe la situación que NO debe darse

    def se_cumple(self, candidato: T) -> bool:
        return not self.interna.se_cumple(candidato)


def exigir(
    especificacion: Especificacion[T],
    candidato: T,
    error: type[ReglaDeNegocioError] = ReglaDeNegocioError,
) -> None:
    """Lanza el error de la primera regla incumplida."""
    fallas = especificacion.incumplidas(candidato)
    if fallas:
        primera = fallas[0]
        raise error(primera.regla, primera.motivo)
