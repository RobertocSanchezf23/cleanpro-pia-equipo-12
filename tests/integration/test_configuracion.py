"""Configuración por variables de entorno (12-Factor) y arranque de la aplicación."""
from fastapi.testclient import TestClient

from src.api.main import crear_app
from src.infrastructure.config import Configuracion, _booleano, normalizar_url
from src.infrastructure.datos_demo import cargar_datos_demo
from src.infrastructure.sistema import GeneradorDeIdsAleatorio, RelojDelSistema


def test_normalizar_url_de_postgres_para_sqlalchemy():
    assert normalizar_url("postgres://u:p@h:5432/db") == "postgresql+psycopg://u:p@h:5432/db"
    assert normalizar_url("postgresql://u:p@h/db") == "postgresql+psycopg://u:p@h/db"
    assert normalizar_url("sqlite:///./x.db") == "sqlite:///./x.db"


def test_configuracion_desde_el_entorno(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgres://u:p@db:5432/cleanpro")
    monkeypatch.setenv("CARGAR_DATOS_DEMO", "false")
    monkeypatch.setenv("APP_ENV", "produccion")
    config = Configuracion.desde_entorno()
    assert config.database_url.startswith("postgresql+psycopg://") and not config.cargar_datos_demo
    assert config.entorno == "produccion" and config.zona_horaria == "America/Monterrey"


def test_valores_por_defecto(monkeypatch):
    for variable in ("DATABASE_URL", "CARGAR_DATOS_DEMO", "APP_ENV", "ZONA_HORARIA"):
        monkeypatch.delenv(variable, raising=False)
    config = Configuracion.desde_entorno()
    assert config.database_url == "sqlite:///./cleanpro.db" and config.cargar_datos_demo
    assert _booleano("Sí", False) and not _booleano("no", True) and _booleano("", True)


def test_la_app_arma_su_sistema_al_arrancar(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "sqlite://")
    monkeypatch.setenv("CARGAR_DATOS_DEMO", "true")
    with TestClient(crear_app()) as api:
        assert api.get("/salud").json() == {"estado": "ok", "base_de_datos": "sqlite"}
        assert len(api.get("/clientes").json()) == 40


def test_los_datos_demo_no_se_duplican(sistema):
    assert cargar_datos_demo(sistema.fabrica, sistema.reloj) is False  # ya estaban cargados


def test_reloj_e_ids_del_sistema():
    ahora = RelojDelSistema().ahora()
    assert ahora.tzinfo is None and ahora.microsecond == 0
    ids = GeneradorDeIdsAleatorio()
    a, b = ids.nuevo("COT"), ids.nuevo("COT")
    assert a.startswith("COT-") and len(a) == 12 and a != b
