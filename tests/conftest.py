"""Fixtures compartidas.

Las pruebas de integración usan SQLite en memoria por defecto. Si existe la variable
TEST_DATABASE_URL (por ejemplo dentro de Docker Compose), usan esa base PostgreSQL real.
"""
from __future__ import annotations

import os
from datetime import datetime, timedelta
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient

from src.api.main import crear_app
from src.domain.comun import Dinero, Rol
from src.domain.cotizacion import Cotizacion
from src.domain.entidades import Cliente, Cuadrilla
from src.domain.precio import CalculadoraDePrecio
from src.domain.servicio import Servicio, SolicitudDeProgramacion
from src.domain.valores import (
    DatosDelInmueble,
    EstimacionOperativa,
    ExtraDelCatalogo,
    ExtraSolicitado,
    Frecuencia,
    Programacion,
    TipoInmueble,
)
from src.infrastructure.config import Configuracion, normalizar_url
from src.infrastructure.db import Base, crear_engine
from src.infrastructure.sistema import construir_sistema

# Miércoles 4 de noviembre de 2026, 10:00 (hora local). Todas las pruebas usan esta hora fija.
AHORA = datetime(2026, 11, 4, 10, 0)
MANANA_9 = datetime(2026, 11, 5, 9, 0)
VENTANAS = ExtraDelCatalogo("VENTANAS", "Limpieza de ventanas", Dinero(Decimal("250")))
HORNO = ExtraDelCatalogo("HORNO", "Limpieza de horno", Dinero(Decimal("200")))


class RelojFijo:
    def __init__(self, ahora: datetime = AHORA):
        self.momento = ahora

    def ahora(self) -> datetime:
        return self.momento

    def avanzar(self, **delta) -> None:
        self.momento += timedelta(**delta)


class IdsSecuenciales:
    def __init__(self):
        self.contador = 0

    def nuevo(self, prefijo: str) -> str:
        self.contador += 1
        return f"{prefijo}-{self.contador:04d}"


# ----- Fábricas de objetos del dominio --------------------------------------------
def nueva_cotizacion(superficie=100, tipo=TipoInmueble.RESIDENCIAL, frecuencia=Frecuencia.UNICA,
                     extras=(VENTANAS,), activo=True, id="COT-1") -> Cotizacion:
    cliente = Cliente("CLN-C001", "Contratante 01", activo=activo)
    solicitados = tuple(ExtraSolicitado(e.codigo, e.descripcion, e.precio) for e in extras)
    return Cotizacion.solicitar(id, cliente, DatosDelInmueble("Av. Universidad 500", superficie, tipo),
                                frecuencia, solicitados, AHORA, Rol.CLIENTE)


def cotizacion_aceptada(**kwargs) -> Cotizacion:
    c = nueva_cotizacion(**kwargs)
    c.estimar(EstimacionOperativa(3, 2), CalculadoraDePrecio(), Rol.COORDINADOR)
    c.enviar(AHORA, Rol.COORDINADOR)
    c.aceptar(AHORA, Rol.CLIENTE)
    c.extraer_eventos()
    return c


def solicitud(cotizacion=None, cuadrilla=None, inicio=MANANA_9, ocupaciones=(), ya_tiene_servicio=False,
              ahora=AHORA) -> SolicitudDeProgramacion:
    cotizacion = cotizacion or cotizacion_aceptada()
    return SolicitudDeProgramacion(
        cotizacion=cotizacion, cuadrilla=cuadrilla or Cuadrilla("CUA-01", "Cuadrilla Norte", 4),
        programacion=Programacion(inicio, cotizacion.estimacion.duracion_horas if cotizacion.estimacion else 3),
        ocupaciones=list(ocupaciones), ya_tiene_servicio=ya_tiene_servicio, ahora=ahora)


def servicio_programado(inicio=MANANA_9, **kwargs) -> Servicio:
    s = Servicio.programar("SRV-1", solicitud(cotizacion_aceptada(**kwargs), inicio=inicio), "Ana López",
                           Rol.COORDINADOR)
    s.extraer_eventos()
    return s


def servicio_en_ejecucion(**kwargs) -> Servicio:
    s = servicio_programado(**kwargs)
    s.registrar_inicio(MANANA_9, Rol.SUPERVISOR)
    s.extraer_eventos()
    return s


# ----- Base de datos y API ------------------------------------------------------------
def url_de_pruebas() -> str:
    return normalizar_url(os.getenv("TEST_DATABASE_URL", "sqlite://"))


@pytest.fixture
def engine():
    engine = crear_engine(url_de_pruebas())
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    yield engine
    Base.metadata.drop_all(engine)
    engine.dispose()


@pytest.fixture
def reloj():
    return RelojFijo()


@pytest.fixture
def sistema(engine, reloj):
    config = Configuracion(database_url=url_de_pruebas(), entorno="pruebas", cargar_datos_demo=True,
                           zona_horaria="America/Monterrey")
    return construir_sistema(config, reloj=reloj, ids=IdsSecuenciales(), engine=engine)


@pytest.fixture
def cliente_api(sistema):
    with TestClient(crear_app(sistema=sistema)) as cliente:
        yield cliente


def rol(nombre: str) -> dict[str, str]:
    return {"X-Rol": nombre}
