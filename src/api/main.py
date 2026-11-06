"""Aplicación FastAPI de CleanPro. Ejecutar con:  uvicorn src.api.main:app --reload"""
from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError

from src.application.base import NoEncontrado
from src.domain.comun import PermisoDenegado, ReglaDeNegocioError, TransicionInvalida
from src.infrastructure.config import Configuracion
from src.infrastructure.sistema import Sistema, construir_sistema

from . import rutas

DESCRIPCION = """
Sistema de CleanPro (Equipo 12, PIA de Componentes de Lógica de Negocio, FIME UANL).

**Proceso:** cotización → respuesta del cliente → programación y cuadrilla → ejecución con incidencias → facturación.

**Cómo probar:** cada operación pide el encabezado `X-Rol` (RB-15). Por ejemplo, el coordinador estima y envía
la cotización, el cliente la acepta, el supervisor registra el inicio y administración factura.

**Errores de negocio:** la respuesta indica la regla del BRD que se violó, por ejemplo
`{"error": "regla_de_negocio", "regla": "RB-02", "detalle": "..."}`.

| Código | Significado |
|---|---|
| 403 | El rol no tiene permiso (RB-15) |
| 404 | El recurso no existe |
| 409 | La máquina de estados no permite la operación |
| 422 | Se viola una regla de negocio o los datos son inválidos |
"""


def _error(codigo: int, tipo: str, detalle: str, regla: str | None = None) -> JSONResponse:
    return JSONResponse(status_code=codigo, content={"error": tipo, "regla": regla, "detalle": detalle})


def crear_app(config: Configuracion | None = None, sistema: Sistema | None = None) -> FastAPI:
    @asynccontextmanager
    async def ciclo_de_vida(app: FastAPI):
        # El sistema (base de datos, repositorios, casos de uso) se arma al arrancar, no al importar el módulo.
        creado_aqui = app.state.sistema is None
        if creado_aqui:
            app.state.sistema = construir_sistema(config or Configuracion.desde_entorno())
        yield
        if creado_aqui:
            app.state.sistema.engine.dispose()

    app = FastAPI(title="CleanPro API", version="1.0.0", description=DESCRIPCION, lifespan=ciclo_de_vida)
    app.state.sistema = sistema

    @app.exception_handler(PermisoDenegado)
    def _permiso(_: Request, e: PermisoDenegado):
        return _error(403, "permiso_denegado", e.mensaje, e.regla)

    @app.exception_handler(TransicionInvalida)
    def _transicion(_: Request, e: TransicionInvalida):
        return _error(409, "transicion_invalida", e.mensaje, e.regla)

    @app.exception_handler(ReglaDeNegocioError)
    def _regla(_: Request, e: ReglaDeNegocioError):
        return _error(422, "regla_de_negocio", e.mensaje, e.regla)

    @app.exception_handler(NoEncontrado)
    def _no_encontrado(_: Request, e: NoEncontrado):
        return _error(404, "no_encontrado", str(e))

    @app.exception_handler(IntegrityError)
    def _integridad(_: Request, e: IntegrityError):
        return _error(409, "conflicto", "la base de datos rechazó un registro duplicado (H-06 / SUP-04)")

    @app.exception_handler(ValueError)
    def _valor(_: Request, e: ValueError):
        return _error(422, "dato_invalido", str(e))

    for router in (rutas.general, rutas.cotizaciones, rutas.servicios, rutas.facturas, rutas.consultas):
        app.include_router(router)
    return app


app = crear_app()
