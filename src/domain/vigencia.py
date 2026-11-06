"""Value Object Vigencia (RB-08, RES-05, H-12): 5 días hábiles desde el envío."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, time, timedelta

DIAS_HABILES_DE_VIGENCIA = 5


def es_dia_habil(dia: date) -> bool:
    """H-12: lunes a viernes, sin considerar días festivos."""
    return dia.weekday() < 5


def sumar_dias_habiles(desde: date, dias: int) -> date:
    actual = desde
    contados = 0
    while contados < dias:
        actual += timedelta(days=1)
        if es_dia_habil(actual):
            contados += 1
    return actual


@dataclass(frozen=True)
class Vigencia:
    enviada_en: datetime

    @property
    def vence_en(self) -> datetime:
        """Fin del 5.º día hábil posterior al envío."""
        ultimo_dia = sumar_dias_habiles(self.enviada_en.date(), DIAS_HABILES_DE_VIGENCIA)
        return datetime.combine(ultimo_dia, time(23, 59, 59))

    def esta_vigente(self, ahora: datetime) -> bool:
        return ahora <= self.vence_en
