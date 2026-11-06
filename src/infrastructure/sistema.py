"""Reloj, generador de ids y armado de todas las piezas (composition root)."""
from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime
from zoneinfo import ZoneInfo

from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker

from src.application.consultas import ServicioDeConsultas
from src.application.cotizaciones import ServicioDeCotizaciones
from src.application.facturacion import FacturacionDeServicios
from src.application.servicios import EjecucionDeServicios, ProgramacionDeServicios

from .config import Configuracion
from .db import crear_engine, crear_fabrica_de_sesiones, crear_tablas
from .lecturas import fabrica_de_lectores
from .repositorios import UnidadDeTrabajoSql


class RelojDelSistema:
    """Hora local del negocio (Monterrey), sin zona horaria, en segundos enteros."""

    def __init__(self, zona: str = "America/Monterrey"):
        self.zona = ZoneInfo(zona)

    def ahora(self) -> datetime:
        return datetime.now(self.zona).replace(tzinfo=None, microsecond=0)


class GeneradorDeIdsAleatorio:
    def nuevo(self, prefijo: str) -> str:
        return f"{prefijo}-{uuid.uuid4().hex[:8].upper()}"


@dataclass
class Sistema:
    engine: Engine
    fabrica: sessionmaker
    reloj: object
    cotizaciones: ServicioDeCotizaciones
    programacion: ProgramacionDeServicios
    ejecucion: EjecucionDeServicios
    facturacion: FacturacionDeServicios
    consultas: ServicioDeConsultas

    def unidad_de_trabajo(self) -> UnidadDeTrabajoSql:
        return UnidadDeTrabajoSql(self.fabrica)


def construir_sistema(config: Configuracion, reloj=None, ids=None, engine: Engine | None = None) -> Sistema:
    engine = engine or crear_engine(config.database_url)
    crear_tablas(engine)
    fabrica = crear_fabrica_de_sesiones(engine)
    reloj = reloj or RelojDelSistema(config.zona_horaria)
    ids = ids or GeneradorDeIdsAleatorio()

    def uow():
        return UnidadDeTrabajoSql(fabrica)

    sistema = Sistema(
        engine=engine, fabrica=fabrica, reloj=reloj,
        cotizaciones=ServicioDeCotizaciones(uow, reloj, ids),
        programacion=ProgramacionDeServicios(uow, reloj, ids),
        ejecucion=EjecucionDeServicios(uow, reloj, ids),
        facturacion=FacturacionDeServicios(uow, reloj, ids),
        consultas=ServicioDeConsultas(fabrica_de_lectores(fabrica)),
    )
    if config.cargar_datos_demo:
        from .datos_demo import cargar_datos_demo
        cargar_datos_demo(fabrica, reloj)
    return sistema
