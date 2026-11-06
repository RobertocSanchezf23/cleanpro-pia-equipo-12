"""Dependencias compartidas de los endpoints."""
from __future__ import annotations

from datetime import datetime
from typing import Annotated
from zoneinfo import ZoneInfo

from fastapi import Header, Request

from src.domain.comun import Rol
from src.infrastructure.sistema import Sistema

RolHeader = Annotated[Rol, Header(
    alias="X-Rol",
    description="Rol de quien realiza la operación (RB-15): CLIENTE, COORDINADOR, SUPERVISOR, CUADRILLA "
                "o ADMINISTRACION",
)]


def sistema(request: Request) -> Sistema:
    return request.app.state.sistema


def hora_local(momento: datetime, zona: str = "America/Monterrey") -> datetime:
    """El dominio trabaja en hora local sin zona; si llega con zona horaria, se convierte."""
    if momento.tzinfo is not None:
        momento = momento.astimezone(ZoneInfo(zona)).replace(tzinfo=None)
    return momento.replace(microsecond=0)
