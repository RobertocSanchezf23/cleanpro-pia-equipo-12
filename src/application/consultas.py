"""Lado de lectura (CQRS básico, ADR-004): reportes REP-01 a REP-05 y consultas US-17, US-21.

Las consultas no pasan por los aggregates: solo leen y devuelven datos planos (DTO).
No protegen invariantes, por eso no necesitan el modelo de dominio.
"""
from __future__ import annotations

from typing import Any, Protocol

Fila = dict[str, Any]


class LectorDeConsultas(Protocol):
    def cotizaciones(self, estado: str | None = None) -> list[Fila]: ...
    def servicios(self, estado: str | None = None) -> list[Fila]: ...
    def servicios_de_cuadrilla(self, cuadrilla_id: str) -> list[Fila]: ...
    def carga_por_cuadrilla(self) -> list[Fila]: ...
    def incidencias(self, servicio_id: str | None = None) -> list[Fila]: ...
    def facturacion(self) -> list[Fila]: ...
    def notificaciones(self, destinatario: str | None = None, cliente_id: str | None = None) -> list[Fila]: ...
    def clientes(self) -> list[Fila]: ...
    def cuadrillas(self) -> list[Fila]: ...
    def catalogo(self) -> list[Fila]: ...


class ServicioDeConsultas:
    def __init__(self, lector_factory):
        self.lector_factory = lector_factory

    def __getattr__(self, nombre: str):
        """Delega cada consulta en el lector, abriendo y cerrando su propia sesión de solo lectura."""
        def consulta(*args, **kwargs):
            with self.lector_factory() as lector:
                return getattr(lector, nombre)(*args, **kwargs)
        return consulta

    def resumen(self) -> Fila:
        """US-21: estado general de servicios, incidencias y facturación."""
        with self.lector_factory() as lector:
            servicios = lector.servicios()
            facturas = lector.facturacion()
            por_estado: dict[str, int] = {}
            for s in servicios:
                por_estado[s["estado"]] = por_estado.get(s["estado"], 0) + 1
            return {
                "servicios_por_estado": por_estado,
                "incidencias_registradas": len(lector.incidencias()),
                "facturas_emitidas": len(facturas),
                "facturas_pendientes_de_pago": sum(1 for f in facturas if f["estado_pago"] == "PENDIENTE"),
                "total_facturado": f"{sum(float(f['total']) for f in facturas):.2f}",
            }
