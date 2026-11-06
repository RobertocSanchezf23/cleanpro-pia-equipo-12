"""Repositorios SQLAlchemy (patrón Repository + Data Mapper) y Unidad de Trabajo.

Los repositorios traducen entre las filas de la base y los objetos del dominio. El dominio nunca
ve una fila de SQLAlchemy: así puede probarse sin base de datos.
"""
from __future__ import annotations

from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from src.application.puertos import Notificacion
from src.domain.comun import Dinero, Rol
from src.domain.cotizacion import Cotizacion, EstadoCotizacion
from src.domain.entidades import Cliente, Cuadrilla
from src.domain.factura import ConceptoFacturado, EstadoPago, Factura, OrigenConcepto
from src.domain.servicio import (
    CargoAdicional,
    EstadoServicio,
    Incidencia,
    OrigenCargo,
    Servicio,
    TipoIncidencia,
)
from src.domain.valores import (
    DatosDelInmueble,
    EstimacionOperativa,
    ExtraDelCatalogo,
    ExtraSolicitado,
    Frecuencia,
    Programacion,
    TipoInmueble,
)
from src.domain.vigencia import Vigencia

from .db import (
    CargoRow,
    ClienteRow,
    ConceptoRow,
    CotizacionRow,
    CuadrillaRow,
    ExtraRow,
    FacturaRow,
    IncidenciaRow,
    NotificacionRow,
    ServicioRow,
)

ACTIVOS = (EstadoServicio.PROGRAMADO.value, EstadoServicio.EN_EJECUCION.value)


def _dinero(centavos: int | None) -> Dinero | None:
    return None if centavos is None else Dinero.desde_centavos(centavos)


def _dec(texto: str | None) -> Decimal | None:
    return None if texto is None else Decimal(texto)


class SqlClientes:
    def __init__(self, session: Session):
        self.session = session

    def obtener(self, id: str) -> Cliente | None:
        row = self.session.get(ClienteRow, id)
        return Cliente(row.id, row.nombre, row.activo, row.ciudad) if row else None


class SqlCuadrillas:
    def __init__(self, session: Session):
        self.session = session

    def obtener(self, id: str) -> Cuadrilla | None:
        row = self.session.get(CuadrillaRow, id)
        return Cuadrilla(row.id, row.nombre, row.integrantes, row.activa) if row else None


class SqlCatalogoDeExtras:
    def __init__(self, session: Session):
        self.session = session

    def buscar(self, codigo: str) -> ExtraDelCatalogo | None:
        row = self.session.get(ExtraRow, codigo)
        if row is None:
            return None
        return ExtraDelCatalogo(row.codigo, row.descripcion, Dinero.desde_centavos(row.precio_centavos))


class SqlCotizaciones:
    def __init__(self, session: Session):
        self.session = session

    def obtener(self, id: str) -> Cotizacion | None:
        row = self.session.get(CotizacionRow, id)
        if row is None:
            return None
        estimacion = (EstimacionOperativa(Decimal(row.duracion_horas), row.personal)
                      if row.duracion_horas is not None else None)
        return Cotizacion(
            id=row.id, cliente_id=row.cliente_id,
            inmueble=DatosDelInmueble(row.ubicacion, Decimal(row.superficie_m2), TipoInmueble(row.tipo_inmueble)),
            frecuencia=Frecuencia(row.frecuencia),
            extras=tuple(ExtraSolicitado(e["codigo"], e["descripcion"], Dinero.desde_centavos(e["precio_centavos"]))
                         for e in row.extras),
            solicitada_en=row.solicitada_en, estado=EstadoCotizacion(row.estado), estimacion=estimacion,
            precio=_dinero(row.precio_centavos), vigencia=Vigencia(row.enviada_en) if row.enviada_en else None,
            respondida_en=row.respondida_en, renovada_de=row.renovada_de,
        )

    def guardar(self, c: Cotizacion) -> None:
        row = self.session.get(CotizacionRow, c.id) or CotizacionRow(id=c.id)
        row.cliente_id = c.cliente_id
        row.ubicacion = c.inmueble.ubicacion
        row.superficie_m2 = str(c.inmueble.superficie_m2)
        row.tipo_inmueble = c.inmueble.tipo.value
        row.frecuencia = c.frecuencia.value
        row.extras = [{"codigo": e.codigo, "descripcion": e.descripcion, "precio_centavos": e.precio.centavos}
                      for e in c.extras]
        row.estado = c.estado.value
        row.duracion_horas = str(c.estimacion.duracion_horas) if c.estimacion else None
        row.personal = c.estimacion.personal if c.estimacion else None
        row.precio_centavos = c.precio.centavos if c.precio else None
        row.solicitada_en = c.solicitada_en
        row.enviada_en = c.vigencia.enviada_en if c.vigencia else None
        row.respondida_en = c.respondida_en
        row.renovada_de = c.renovada_de
        self.session.add(row)


class SqlServicios:
    def __init__(self, session: Session):
        self.session = session

    def obtener(self, id: str) -> Servicio | None:
        row = self.session.get(ServicioRow, id)
        if row is None:
            return None
        return Servicio(
            id=row.id, cotizacion_id=row.cotizacion_id, cliente_id=row.cliente_id, cuadrilla_id=row.cuadrilla_id,
            supervisor=row.supervisor, programacion=Programacion(row.inicio, Decimal(row.duracion_horas)),
            ubicacion=row.ubicacion, tipo_inmueble=TipoInmueble(row.tipo_inmueble),
            frecuencia=Frecuencia(row.frecuencia), superficie_cotizada=Decimal(row.superficie_cotizada),
            precio_extras=Dinero.desde_centavos(row.precio_extras_centavos),
            precio_acordado=Dinero.desde_centavos(row.precio_acordado_centavos),
            estado=EstadoServicio(row.estado),
            incidencias=[Incidencia(i.id, TipoIncidencia(i.tipo), i.descripcion, i.registrada_en,
                                    Rol(i.registrada_por), i.cargo_id) for i in row.incidencias],
            cargos=[CargoAdicional(c.id, OrigenCargo(c.origen), c.descripcion,
                                   Dinero.desde_centavos(c.monto_centavos), c.autorizado) for c in row.cargos],
            superficie_real=_dec(row.superficie_real), recalculo_pendiente=row.recalculo_pendiente,
            iniciado_en=row.iniciado_en, terminado_en=row.terminado_en,
        )

    def guardar(self, s: Servicio) -> None:
        row = self.session.get(ServicioRow, s.id) or ServicioRow(id=s.id)
        row.cotizacion_id = s.cotizacion_id
        row.cliente_id = s.cliente_id
        row.cuadrilla_id = s.cuadrilla_id
        row.supervisor = s.supervisor
        row.inicio = s.programacion.inicio
        row.fin = s.programacion.fin
        row.duracion_horas = str(s.programacion.duracion_horas)
        row.ubicacion = s.ubicacion
        row.tipo_inmueble = s.tipo_inmueble.value
        row.frecuencia = s.frecuencia.value
        row.superficie_cotizada = str(s.superficie_cotizada)
        row.superficie_real = str(s.superficie_real) if s.superficie_real is not None else None
        row.precio_extras_centavos = s.precio_extras.centavos
        row.precio_acordado_centavos = s.precio_acordado.centavos
        row.estado = s.estado.value
        row.recalculo_pendiente = s.recalculo_pendiente
        row.iniciado_en = s.iniciado_en
        row.terminado_en = s.terminado_en

        existentes = {i.id: i for i in row.incidencias}
        for orden, inc in enumerate(s.incidencias, start=1):
            if inc.id not in existentes:  # las incidencias no se modifican: solo se agregan (evidencia, BN-08)
                row.incidencias.append(IncidenciaRow(
                    id=inc.id, orden=orden, tipo=inc.tipo.value, descripcion=inc.descripcion,
                    registrada_en=inc.registrada_en, registrada_por=inc.registrada_por.value, cargo_id=inc.cargo_id))
        cargos = {c.id: c for c in row.cargos}
        for orden, cargo in enumerate(s.cargos, start=1):
            existente = cargos.get(cargo.id)
            if existente is None:
                row.cargos.append(CargoRow(id=cargo.id, orden=orden, origen=cargo.origen.value,
                                           descripcion=cargo.descripcion, monto_centavos=cargo.monto.centavos,
                                           autorizado=cargo.autorizado))
            else:
                existente.autorizado = cargo.autorizado
        self.session.add(row)

    def existe_para_cotizacion(self, cotizacion_id: str) -> bool:
        return self.session.scalar(
            select(ServicioRow.id).where(ServicioRow.cotizacion_id == cotizacion_id)) is not None

    def ocupaciones_de_cuadrilla(self, cuadrilla_id: str, excluir_id: str | None = None) -> list[Programacion]:
        consulta = select(ServicioRow).where(ServicioRow.cuadrilla_id == cuadrilla_id,
                                             ServicioRow.estado.in_(ACTIVOS))
        if excluir_id:
            consulta = consulta.where(ServicioRow.id != excluir_id)
        return [Programacion(r.inicio, Decimal(r.duracion_horas)) for r in self.session.scalars(consulta)]


class SqlFacturas:
    def __init__(self, session: Session):
        self.session = session

    def obtener(self, id: str) -> Factura | None:
        row = self.session.get(FacturaRow, id)
        if row is None:
            return None
        return Factura(
            row.id, row.servicio_id, row.cliente_id,
            [ConceptoFacturado(c.descripcion, OrigenConcepto(c.origen), Dinero.desde_centavos(c.monto_centavos),
                               c.referencia) for c in row.conceptos],
            row.emitida_en, EstadoPago(row.estado_pago), row.pagada_en,
        )

    def guardar(self, f: Factura) -> None:
        row = self.session.get(FacturaRow, f.id)
        if row is None:
            row = FacturaRow(id=f.id, servicio_id=f.servicio_id, cliente_id=f.cliente_id, emitida_en=f.emitida_en,
                             total_centavos=f.total.centavos)
            row.conceptos = [ConceptoRow(orden=i, descripcion=c.descripcion, origen=c.origen.value,
                                         monto_centavos=c.monto.centavos, referencia=c.referencia)
                             for i, c in enumerate(f.conceptos, start=1)]
        row.estado_pago = f.estado_pago.value
        row.pagada_en = f.pagada_en
        self.session.add(row)

    def existe_para_servicio(self, servicio_id: str) -> bool:
        return self.session.scalar(select(FacturaRow.id).where(FacturaRow.servicio_id == servicio_id)) is not None


class SqlBandejaDeNotificaciones:
    def __init__(self, session: Session):
        self.session = session

    def agregar(self, n: Notificacion) -> None:
        self.session.add(NotificacionRow(destinatario=n.destinatario, evento=n.evento, referencia=n.referencia,
                                         mensaje=n.mensaje, cliente_id=n.cliente_id, creada_en=n.creada_en))


class UnidadDeTrabajoSql:
    """Una sesión = una transacción. Si no se llama a commit(), todo se deshace al salir."""

    def __init__(self, fabrica: sessionmaker):
        self.fabrica = fabrica

    def __enter__(self) -> "UnidadDeTrabajoSql":
        self.session: Session = self.fabrica()
        self.cotizaciones = SqlCotizaciones(self.session)
        self.servicios = SqlServicios(self.session)
        self.facturas = SqlFacturas(self.session)
        self.clientes = SqlClientes(self.session)
        self.cuadrillas = SqlCuadrillas(self.session)
        self.catalogo = SqlCatalogoDeExtras(self.session)
        self.notificaciones = SqlBandejaDeNotificaciones(self.session)
        return self

    def __exit__(self, *args) -> None:
        self.rollback()  # si ya hubo commit, no hay nada pendiente que deshacer
        self.session.close()

    def commit(self) -> None:
        self.session.commit()

    def rollback(self) -> None:
        self.session.rollback()
