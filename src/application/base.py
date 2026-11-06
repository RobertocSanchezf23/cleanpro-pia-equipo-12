"""Piezas comunes de los casos de uso."""
from __future__ import annotations

from collections.abc import Callable

from src.domain.comun import RaizDeAggregate

from .notificaciones import notificaciones_para
from .puertos import GeneradorDeIds, Reloj, UnidadDeTrabajo


class NoEncontrado(Exception):
    def __init__(self, recurso: str, id: str):
        self.recurso = recurso
        self.id = id
        super().__init__(f"{recurso} {id} no existe")


def obtener_o_fallar(valor, recurso: str, id: str):
    if valor is None:
        raise NoEncontrado(recurso, id)
    return valor


class CasoDeUso:
    def __init__(self, uow_factory: Callable[[], UnidadDeTrabajo], reloj: Reloj, ids: GeneradorDeIds):
        self.uow_factory = uow_factory
        self.reloj = reloj
        self.ids = ids

    def _confirmar(self, uow: UnidadDeTrabajo, *aggregates: RaizDeAggregate) -> None:
        """Publica los eventos como notificaciones y confirma todo en una sola transacción."""
        ahora = self.reloj.ahora()
        for aggregate in aggregates:
            for evento in aggregate.extraer_eventos():
                for notificacion in notificaciones_para(evento, ahora):
                    uow.notificaciones.agregar(notificacion)
        uow.commit()
