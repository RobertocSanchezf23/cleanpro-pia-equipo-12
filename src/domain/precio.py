"""Domain Service CalculadoraDePrecio (RB-03, RB-13).

Es un servicio de dominio porque el mismo cálculo se usa al cotizar (CU-01) y al recalcular
por inmueble mayor a lo reportado (RB-13). Las tarifas viven en un solo lugar.
"""
from __future__ import annotations

from decimal import Decimal

from .comun import Dinero, sumar
from .valores import DatosDelInmueble, ExtraSolicitado, Frecuencia, TipoInmueble

TARIFA_POR_M2 = {
    TipoInmueble.RESIDENCIAL: Decimal("12"),
    TipoInmueble.EMPRESARIAL: Decimal("15"),
}
DESCUENTO_RECURRENTE = Decimal("0.10")


class CalculadoraDePrecio:
    def __init__(self, tarifas: dict[TipoInmueble, Decimal] | None = None,
                 descuento_recurrente: Decimal = DESCUENTO_RECURRENTE):
        self.tarifas = tarifas or TARIFA_POR_M2
        self.descuento_recurrente = descuento_recurrente

    def precio_base(self, inmueble: DatosDelInmueble, frecuencia: Frecuencia) -> Dinero:
        """Superficie × tarifa, con 10 % de descuento si es recurrente (H-05: sin incluir extras)."""
        base = inmueble.superficie_m2 * self.tarifas[inmueble.tipo]
        if frecuencia.es_recurrente:
            base = base * (Decimal("1") - self.descuento_recurrente)
        return Dinero(base)

    def calcular(self, inmueble: DatosDelInmueble, frecuencia: Frecuencia,
                 extras: tuple[ExtraSolicitado, ...] | list[ExtraSolicitado]) -> Dinero:
        return self.precio_base(inmueble, frecuencia) + sumar(e.precio for e in extras)
