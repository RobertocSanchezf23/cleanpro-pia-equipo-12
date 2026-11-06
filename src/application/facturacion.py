"""Caso de uso CU-05: facturar servicio (US-20, US-05) y registrar su pago."""
from __future__ import annotations

from src.domain.comun import Rol
from src.domain.factura import Factura, GeneradorDeFactura

from .base import CasoDeUso, obtener_o_fallar


class FacturacionDeServicios(CasoDeUso):
    def __init__(self, uow_factory, reloj, ids, generador: GeneradorDeFactura | None = None):
        super().__init__(uow_factory, reloj, ids)
        self.generador = generador or GeneradorDeFactura()

    def facturar(self, servicio_id: str, rol: Rol) -> Factura:
        with self.uow_factory() as uow:
            servicio = obtener_o_fallar(uow.servicios.obtener(servicio_id), "Servicio", servicio_id)
            factura = self.generador.generar(self.ids.nuevo("FAC"), servicio,
                                             uow.facturas.existe_para_servicio(servicio.id),
                                             self.reloj.ahora(), rol)
            uow.facturas.guardar(factura)
            self._confirmar(uow, factura)
            return factura

    def registrar_pago(self, factura_id: str, rol: Rol) -> Factura:
        with self.uow_factory() as uow:
            factura = self.obtener_en(uow, factura_id)
            factura.registrar_pago(self.reloj.ahora(), rol)
            uow.facturas.guardar(factura)
            self._confirmar(uow, factura)
            return factura

    def obtener(self, factura_id: str) -> Factura:
        with self.uow_factory() as uow:
            return self.obtener_en(uow, factura_id)

    @staticmethod
    def obtener_en(uow, factura_id: str) -> Factura:
        return obtener_o_fallar(uow.facturas.obtener(factura_id), "Factura", factura_id)
