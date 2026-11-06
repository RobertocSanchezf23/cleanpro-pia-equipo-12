"""Entidades de referencia: se identifican por id, pero no protegen reglas complejas."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Cliente:
    id: str
    nombre: str
    activo: bool = True
    ciudad: str = ""


@dataclass
class Cuadrilla:
    id: str
    nombre: str
    integrantes: int
    activa: bool = True
