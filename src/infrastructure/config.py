"""Configuración por variables de entorno (12-Factor App, factor III).

Ningún valor sensible está escrito en el código: todo se lee del entorno. Los valores por defecto
sirven para trabajar en local sin configurar nada (SQLite en un archivo).
"""
from __future__ import annotations

import os
from dataclasses import dataclass


def _booleano(valor: str | None, por_defecto: bool) -> bool:
    if valor is None or valor.strip() == "":
        return por_defecto
    return valor.strip().lower() in {"1", "true", "si", "sí", "yes", "on"}


def normalizar_url(url: str) -> str:
    """Render y otros servicios entregan postgres:// o postgresql://; SQLAlchemy necesita el driver."""
    if url.startswith("postgres://"):
        url = "postgresql://" + url[len("postgres://"):]
    if url.startswith("postgresql://"):
        url = "postgresql+psycopg://" + url[len("postgresql://"):]
    return url


@dataclass(frozen=True)
class Configuracion:
    database_url: str
    entorno: str
    cargar_datos_demo: bool
    zona_horaria: str

    @classmethod
    def desde_entorno(cls) -> "Configuracion":
        return cls(
            database_url=normalizar_url(os.getenv("DATABASE_URL", "sqlite:///./cleanpro.db")),
            entorno=os.getenv("APP_ENV", "desarrollo"),
            cargar_datos_demo=_booleano(os.getenv("CARGAR_DATOS_DEMO"), True),
            zona_horaria=os.getenv("ZONA_HORARIA", "America/Monterrey"),
        )
