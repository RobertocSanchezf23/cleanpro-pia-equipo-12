"""Patrón Specification: composición AND / OR / NOT y el mensaje de la regla incumplida."""
import pytest

from src.domain.comun import ReglaDeNegocioError
from src.domain.especificaciones import Disyuncion, Especificacion, exigir


class EsPar(Especificacion[int]):
    regla, motivo = "R-PAR", "el número no es par"

    def se_cumple(self, n):
        return n % 2 == 0


class EsPositivo(Especificacion[int]):
    regla, motivo = "R-POS", "el número no es positivo"

    def se_cumple(self, n):
        return n > 0


def test_and_reporta_todas_las_reglas_incumplidas_en_orden():
    spec = EsPar() & EsPositivo()
    assert spec.se_cumple(4)
    assert [s.regla for s in spec.incumplidas(-3)] == ["R-PAR", "R-POS"]


def test_or_sin_motivo_propio_reporta_las_partes():
    spec = EsPar() | EsPositivo()
    assert spec.se_cumple(-2) and spec.se_cumple(3)
    assert [s.regla for s in spec.incumplidas(-3)] == ["R-PAR", "R-POS"]


def test_or_con_motivo_propio_reporta_un_solo_error():
    spec = Disyuncion(EsPar(), EsPositivo()).con_motivo("R-OR", "debe ser par o positivo")
    assert [s.motivo for s in spec.incumplidas(-3)] == ["debe ser par o positivo"]


def test_not_invierte_y_conserva_la_regla():
    spec = ~EsPar()
    assert spec.se_cumple(3)
    assert not spec.se_cumple(2)
    assert spec.incumplidas(2)[0].regla == "R-PAR"


def test_exigir_lanza_el_error_de_la_primera_regla():
    with pytest.raises(ReglaDeNegocioError) as error:
        exigir(EsPar() & EsPositivo(), -3)
    assert error.value.regla == "R-PAR"
    exigir(EsPar() & EsPositivo(), 2)  # se cumple: no lanza nada
