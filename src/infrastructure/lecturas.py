"""Implementación SQL del lado de lectura (CQRS): consultas directas que devuelven datos planos."""
from __future__ import annotations

from contextlib import contextmanager

from sqlalchemy import func, select
from sqlalchemy.orm import Session, sessionmaker

from src.domain.comun import Dinero
from src.domain.vigencia import Vigencia

from .db import (
    ClienteRow,
    CotizacionRow,
    CuadrillaRow,
    ExtraRow,
    FacturaRow,
    IncidenciaRow,
    NotificacionRow,
    ServicioRow,
)


def _monto(centavos: int | None) -> str | None:
    return None if centavos is None else str(Dinero.desde_centavos(centavos).monto)


class LectorSql:
    def __init__(self, session: Session):
        self.session = session

    # REP-01
    def cotizaciones(self, estado: str | None = None) -> list[dict]:
        consulta = select(CotizacionRow).order_by(CotizacionRow.solicitada_en.desc())
        if estado:
            consulta = consulta.where(CotizacionRow.estado == estado.upper())
        return [{
            "id": c.id, "cliente_id": c.cliente_id, "estado": c.estado, "tipo_inmueble": c.tipo_inmueble,
            "superficie_m2": c.superficie_m2, "frecuencia": c.frecuencia, "precio": _monto(c.precio_centavos),
            "enviada_en": c.enviada_en,
            "vence_en": Vigencia(c.enviada_en).vence_en if c.enviada_en else None,
        } for c in self.session.scalars(consulta)]

    # REP-02
    def servicios(self, estado: str | None = None) -> list[dict]:
        consulta = select(ServicioRow).order_by(ServicioRow.inicio)
        if estado:
            consulta = consulta.where(ServicioRow.estado == estado.upper())
        return [self._fila_servicio(s) for s in self.session.scalars(consulta)]

    # US-17
    def servicios_de_cuadrilla(self, cuadrilla_id: str) -> list[dict]:
        consulta = (select(ServicioRow).where(ServicioRow.cuadrilla_id == cuadrilla_id)
                    .order_by(ServicioRow.inicio))
        return [self._fila_servicio(s) for s in self.session.scalars(consulta)]

    # REP-05
    def carga_por_cuadrilla(self) -> list[dict]:
        conteos = dict(self.session.execute(
            select(ServicioRow.cuadrilla_id, func.count(ServicioRow.id)).group_by(ServicioRow.cuadrilla_id)).all())
        return [{"cuadrilla_id": c.id, "nombre": c.nombre, "activa": c.activa, "servicios": conteos.get(c.id, 0)}
                for c in self.session.scalars(select(CuadrillaRow).order_by(CuadrillaRow.id))]

    # REP-03
    def incidencias(self, servicio_id: str | None = None) -> list[dict]:
        consulta = select(IncidenciaRow).order_by(IncidenciaRow.registrada_en, IncidenciaRow.id)
        if servicio_id:
            consulta = consulta.where(IncidenciaRow.servicio_id == servicio_id)
        return [{"id": i.id, "servicio_id": i.servicio_id, "tipo": i.tipo, "descripcion": i.descripcion,
                 "registrada_en": i.registrada_en, "registrada_por": i.registrada_por, "cargo_id": i.cargo_id}
                for i in self.session.scalars(consulta)]

    # REP-04
    def facturacion(self) -> list[dict]:
        consulta = select(FacturaRow).order_by(FacturaRow.emitida_en)
        return [{"id": f.id, "servicio_id": f.servicio_id, "cliente_id": f.cliente_id, "emitida_en": f.emitida_en,
                 "total": _monto(f.total_centavos), "estado_pago": f.estado_pago, "pagada_en": f.pagada_en}
                for f in self.session.scalars(consulta)]

    # US-19, US-03, US-05
    def notificaciones(self, destinatario: str | None = None, cliente_id: str | None = None) -> list[dict]:
        consulta = select(NotificacionRow).order_by(NotificacionRow.id.desc())
        if destinatario:
            consulta = consulta.where(NotificacionRow.destinatario == destinatario.upper())
        if cliente_id:
            consulta = consulta.where(NotificacionRow.cliente_id == cliente_id)
        return [{"id": n.id, "destinatario": n.destinatario, "cliente_id": n.cliente_id, "evento": n.evento,
                 "referencia": n.referencia, "mensaje": n.mensaje, "creada_en": n.creada_en}
                for n in self.session.scalars(consulta)]

    def clientes(self) -> list[dict]:
        return [{"id": c.id, "nombre": c.nombre, "activo": c.activo, "ciudad": c.ciudad}
                for c in self.session.scalars(select(ClienteRow).order_by(ClienteRow.id))]

    def cuadrillas(self) -> list[dict]:
        return [{"id": c.id, "nombre": c.nombre, "integrantes": c.integrantes, "activa": c.activa}
                for c in self.session.scalars(select(CuadrillaRow).order_by(CuadrillaRow.id))]

    def catalogo(self) -> list[dict]:
        return [{"codigo": e.codigo, "descripcion": e.descripcion, "precio": _monto(e.precio_centavos)}
                for e in self.session.scalars(select(ExtraRow).order_by(ExtraRow.codigo))]

    @staticmethod
    def _fila_servicio(s: ServicioRow) -> dict:
        return {"id": s.id, "cotizacion_id": s.cotizacion_id, "cliente_id": s.cliente_id,
                "cuadrilla_id": s.cuadrilla_id, "supervisor": s.supervisor, "inicio": s.inicio, "fin": s.fin,
                "ubicacion": s.ubicacion, "estado": s.estado, "precio_acordado": _monto(s.precio_acordado_centavos)}


def fabrica_de_lectores(fabrica: sessionmaker):
    @contextmanager
    def abrir():
        session = fabrica()
        try:
            yield LectorSql(session)
        finally:
            session.close()
    return abrir
