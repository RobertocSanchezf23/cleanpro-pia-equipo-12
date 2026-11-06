"""Puertos (interfaces) que la capa de aplicación necesita. La infraestructura los implementa.

Principio de inversión de dependencias (DIP): los casos de uso dependen de estas abstracciones,
no de SQLAlchemy ni de FastAPI.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Protocol

from src.domain.cotizacion import Cotizacion
from src.domain.entidades import Cliente, Cuadrilla
from src.domain.factura import Factura
from src.domain.servicio import Servicio
from src.domain.valores import CatalogoDeExtras, Programacion


@dataclass(frozen=True)
class Notificacion:
    """Mensaje registrado para un destinatario cuando ocurre un evento del dominio (FAL-07)."""

    destinatario: str  # CLIENTE, COORDINADOR o ADMINISTRACION
    evento: str
    referencia: str  # id del aggregate que produjo el evento
    mensaje: str
    cliente_id: str | None = None
    creada_en: datetime | None = None


class RepositorioCotizaciones(Protocol):
    def obtener(self, id: str) -> Cotizacion | None: ...
    def guardar(self, cotizacion: Cotizacion) -> None: ...


class RepositorioServicios(Protocol):
    def obtener(self, id: str) -> Servicio | None: ...
    def guardar(self, servicio: Servicio) -> None: ...
    def existe_para_cotizacion(self, cotizacion_id: str) -> bool: ...
    def ocupaciones_de_cuadrilla(self, cuadrilla_id: str, excluir_id: str | None = None) -> list[Programacion]: ...


class RepositorioFacturas(Protocol):
    def obtener(self, id: str) -> Factura | None: ...
    def guardar(self, factura: Factura) -> None: ...
    def existe_para_servicio(self, servicio_id: str) -> bool: ...


class RepositorioClientes(Protocol):
    def obtener(self, id: str) -> Cliente | None: ...


class RepositorioCuadrillas(Protocol):
    def obtener(self, id: str) -> Cuadrilla | None: ...


class BandejaDeNotificaciones(Protocol):
    def agregar(self, notificacion: Notificacion) -> None: ...


class UnidadDeTrabajo(Protocol):
    """Agrupa los repositorios de una transacción: todo se confirma o todo se deshace."""

    cotizaciones: RepositorioCotizaciones
    servicios: RepositorioServicios
    facturas: RepositorioFacturas
    clientes: RepositorioClientes
    cuadrillas: RepositorioCuadrillas
    catalogo: CatalogoDeExtras
    notificaciones: BandejaDeNotificaciones

    def __enter__(self) -> "UnidadDeTrabajo": ...
    def __exit__(self, *args) -> None: ...
    def commit(self) -> None: ...
    def rollback(self) -> None: ...


class Reloj(Protocol):
    def ahora(self) -> datetime: ...


class GeneradorDeIds(Protocol):
    def nuevo(self, prefijo: str) -> str: ...
