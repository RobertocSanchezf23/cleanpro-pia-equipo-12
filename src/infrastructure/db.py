"""Motor de base de datos y tablas (SQLAlchemy 2). Funciona con PostgreSQL y con SQLite.

Los importes se guardan en centavos (enteros) y las cantidades decimales como texto, para que
PostgreSQL y SQLite guarden exactamente el mismo valor (PA-02: sin errores de redondeo).
"""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    create_engine,
)
from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship, sessionmaker
from sqlalchemy.pool import StaticPool


class Base(DeclarativeBase):
    pass


class ClienteRow(Base):
    __tablename__ = "clientes"
    id: Mapped[str] = mapped_column(String(20), primary_key=True)
    nombre: Mapped[str] = mapped_column(String(120))
    activo: Mapped[bool] = mapped_column(Boolean, default=True)
    ciudad: Mapped[str] = mapped_column(String(80), default="")


class CuadrillaRow(Base):
    __tablename__ = "cuadrillas"
    id: Mapped[str] = mapped_column(String(20), primary_key=True)
    nombre: Mapped[str] = mapped_column(String(80))
    integrantes: Mapped[int] = mapped_column(Integer)
    activa: Mapped[bool] = mapped_column(Boolean, default=True)


class ExtraRow(Base):
    __tablename__ = "extras_catalogo"
    codigo: Mapped[str] = mapped_column(String(30), primary_key=True)
    descripcion: Mapped[str] = mapped_column(String(120))
    precio_centavos: Mapped[int] = mapped_column(Integer)


class CotizacionRow(Base):
    __tablename__ = "cotizaciones"
    id: Mapped[str] = mapped_column(String(20), primary_key=True)
    cliente_id: Mapped[str] = mapped_column(ForeignKey("clientes.id"))
    ubicacion: Mapped[str] = mapped_column(String(200))
    superficie_m2: Mapped[str] = mapped_column(String(20))
    tipo_inmueble: Mapped[str] = mapped_column(String(20))
    frecuencia: Mapped[str] = mapped_column(String(20))
    extras: Mapped[list] = mapped_column(JSON, default=list)
    estado: Mapped[str] = mapped_column(String(20), index=True)
    duracion_horas: Mapped[str | None] = mapped_column(String(20), nullable=True)
    personal: Mapped[int | None] = mapped_column(Integer, nullable=True)
    precio_centavos: Mapped[int | None] = mapped_column(Integer, nullable=True)
    solicitada_en: Mapped[datetime] = mapped_column(DateTime)
    enviada_en: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    respondida_en: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    renovada_de: Mapped[str | None] = mapped_column(String(20), nullable=True)


class ServicioRow(Base):
    __tablename__ = "servicios"
    id: Mapped[str] = mapped_column(String(20), primary_key=True)
    # unique=True: una cotización genera un solo servicio (H-06), protegido también en la base
    cotizacion_id: Mapped[str] = mapped_column(ForeignKey("cotizaciones.id"), unique=True)
    cliente_id: Mapped[str] = mapped_column(ForeignKey("clientes.id"))
    cuadrilla_id: Mapped[str] = mapped_column(ForeignKey("cuadrillas.id"), index=True)
    supervisor: Mapped[str] = mapped_column(String(120))
    inicio: Mapped[datetime] = mapped_column(DateTime)
    fin: Mapped[datetime] = mapped_column(DateTime)
    duracion_horas: Mapped[str] = mapped_column(String(20))
    ubicacion: Mapped[str] = mapped_column(String(200))
    tipo_inmueble: Mapped[str] = mapped_column(String(20))
    frecuencia: Mapped[str] = mapped_column(String(20))
    superficie_cotizada: Mapped[str] = mapped_column(String(20))
    superficie_real: Mapped[str | None] = mapped_column(String(20), nullable=True)
    precio_extras_centavos: Mapped[int] = mapped_column(Integer)
    precio_acordado_centavos: Mapped[int] = mapped_column(Integer)
    estado: Mapped[str] = mapped_column(String(20), index=True)
    recalculo_pendiente: Mapped[bool] = mapped_column(Boolean, default=False)
    iniciado_en: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    terminado_en: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    incidencias: Mapped[list["IncidenciaRow"]] = relationship(
        back_populates="servicio", cascade="all, delete-orphan", order_by="IncidenciaRow.orden")
    cargos: Mapped[list["CargoRow"]] = relationship(
        back_populates="servicio", cascade="all, delete-orphan", order_by="CargoRow.orden")


class IncidenciaRow(Base):
    __tablename__ = "incidencias"
    id: Mapped[str] = mapped_column(String(30), primary_key=True)
    servicio_id: Mapped[str] = mapped_column(ForeignKey("servicios.id"), index=True)
    orden: Mapped[int] = mapped_column(Integer)
    tipo: Mapped[str] = mapped_column(String(30))
    descripcion: Mapped[str] = mapped_column(Text)
    registrada_en: Mapped[datetime] = mapped_column(DateTime)
    registrada_por: Mapped[str] = mapped_column(String(20))
    cargo_id: Mapped[str | None] = mapped_column(String(30), nullable=True)
    servicio: Mapped[ServicioRow] = relationship(back_populates="incidencias")


class CargoRow(Base):
    __tablename__ = "cargos_adicionales"
    id: Mapped[str] = mapped_column(String(30), primary_key=True)
    servicio_id: Mapped[str] = mapped_column(ForeignKey("servicios.id"), index=True)
    orden: Mapped[int] = mapped_column(Integer)
    origen: Mapped[str] = mapped_column(String(30))
    descripcion: Mapped[str] = mapped_column(String(200))
    monto_centavos: Mapped[int] = mapped_column(Integer)
    autorizado: Mapped[bool] = mapped_column(Boolean, default=False)
    servicio: Mapped[ServicioRow] = relationship(back_populates="cargos")


class FacturaRow(Base):
    __tablename__ = "facturas"
    id: Mapped[str] = mapped_column(String(20), primary_key=True)
    # unique=True: una sola factura por servicio (SUP-04), protegido también en la base
    servicio_id: Mapped[str] = mapped_column(ForeignKey("servicios.id"), unique=True)
    cliente_id: Mapped[str] = mapped_column(ForeignKey("clientes.id"))
    emitida_en: Mapped[datetime] = mapped_column(DateTime)
    estado_pago: Mapped[str] = mapped_column(String(20))
    pagada_en: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    total_centavos: Mapped[int] = mapped_column(Integer)
    conceptos: Mapped[list["ConceptoRow"]] = relationship(
        back_populates="factura", cascade="all, delete-orphan", order_by="ConceptoRow.orden")


class ConceptoRow(Base):
    __tablename__ = "conceptos_factura"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    factura_id: Mapped[str] = mapped_column(ForeignKey("facturas.id"), index=True)
    orden: Mapped[int] = mapped_column(Integer)
    descripcion: Mapped[str] = mapped_column(String(200))
    origen: Mapped[str] = mapped_column(String(30))
    monto_centavos: Mapped[int] = mapped_column(Integer)
    referencia: Mapped[str | None] = mapped_column(String(30), nullable=True)
    factura: Mapped[FacturaRow] = relationship(back_populates="conceptos")


class NotificacionRow(Base):
    __tablename__ = "notificaciones"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    destinatario: Mapped[str] = mapped_column(String(20), index=True)
    evento: Mapped[str] = mapped_column(String(40))
    referencia: Mapped[str] = mapped_column(String(30))
    mensaje: Mapped[str] = mapped_column(Text)
    cliente_id: Mapped[str | None] = mapped_column(String(20), nullable=True, index=True)
    creada_en: Mapped[datetime] = mapped_column(DateTime)


def crear_engine(url: str) -> Engine:
    if url.startswith("sqlite"):
        opciones: dict = {"connect_args": {"check_same_thread": False}}
        if ":memory:" in url or url in ("sqlite://", "sqlite+pysqlite://"):
            opciones["poolclass"] = StaticPool  # una sola conexión compartida para la base en memoria
        return create_engine(url, **opciones)
    return create_engine(url, pool_pre_ping=True)


def crear_tablas(engine: Engine) -> None:
    Base.metadata.create_all(engine)


def crear_fabrica_de_sesiones(engine: Engine) -> sessionmaker:
    return sessionmaker(bind=engine, expire_on_commit=False)
