"""RB-03 (cálculo del precio), H-05, Dinero y Value Objects."""
from decimal import Decimal

import pytest

from src.domain.comun import Dinero, ReglaDeNegocioError
from src.domain.precio import CalculadoraDePrecio
from src.domain.valores import (
    DatosDelInmueble,
    EstimacionOperativa,
    ExtraSolicitado,
    Frecuencia,
    Programacion,
    TipoInmueble,
    resolver_extras,
)
from tests.conftest import MANANA_9, VENTANAS

calc = CalculadoraDePrecio()
ALFOMBRA = ExtraSolicitado("ALFOMBRA", "Lavado de alfombra", Dinero(Decimal("300")))


def inmueble(m2, tipo=TipoInmueble.RESIDENCIAL):
    return DatosDelInmueble("Av. Universidad 500", m2, tipo)


def test_us06_e2_residencial_100m2_unica_con_ventanas_cuesta_1450():
    extras = (ExtraSolicitado(VENTANAS.codigo, VENTANAS.descripcion, VENTANAS.precio),)
    assert calc.calcular(inmueble(100), Frecuencia.UNICA, extras) == Dinero(Decimal("1450.00"))


def test_us06_e3_empresarial_200m2_semanal_con_alfombra_cuesta_3000():
    assert calc.calcular(inmueble(200, TipoInmueble.EMPRESARIAL), Frecuencia.SEMANAL, (ALFOMBRA,)) == Dinero(3000)


def test_h05_el_descuento_recurrente_no_se_aplica_a_los_extras():
    # 100 × 12 × 0.90 = 1080 + 300 completos (sin descuento) = 1380
    assert calc.calcular(inmueble(100), Frecuencia.MENSUAL, (ALFOMBRA,)) == Dinero(1380)


@pytest.mark.parametrize("frecuencia", [Frecuencia.SEMANAL, Frecuencia.QUINCENAL, Frecuencia.MENSUAL])
def test_rb03_las_tres_frecuencias_recurrentes_tienen_10_por_ciento(frecuencia):
    assert calc.precio_base(inmueble(50), frecuencia) == Dinero(540)  # 50 × 12 × 0.90


def test_rb03_superficie_con_decimales_redondea_a_centavos():
    assert calc.precio_base(inmueble(Decimal("33.333"), TipoInmueble.EMPRESARIAL), Frecuencia.UNICA) == Dinero(
        Decimal("500.00"))  # 499.995 → 500.00 (redondeo comercial)


def test_dinero_suma_y_no_admite_negativos():
    assert Dinero(Decimal("0.1")) + Dinero(Decimal("0.2")) == Dinero(Decimal("0.30"))
    assert Dinero.desde_centavos(12345).monto == Decimal("123.45")
    assert str(Dinero(1450)) == "$1,450.00"
    with pytest.raises(ValueError):
        Dinero(-1)


@pytest.mark.parametrize("m2", [0, -5])
def test_us01_superficie_debe_ser_positiva(m2):
    with pytest.raises(ReglaDeNegocioError, match="superficie"):
        inmueble(m2)


def test_us01_ubicacion_obligatoria():
    with pytest.raises(ReglaDeNegocioError, match="ubicación"):
        DatosDelInmueble("  ", 100, TipoInmueble.RESIDENCIAL)


def test_us06_estimacion_requiere_duracion_y_personal_positivos():
    with pytest.raises(ReglaDeNegocioError, match="duración"):
        EstimacionOperativa(0, 2)
    with pytest.raises(ReglaDeNegocioError, match="personal"):
        EstimacionOperativa(2, 0)


class CatalogoEnMemoria:
    def buscar(self, codigo):
        return VENTANAS if codigo == "VENTANAS" else None


def test_us01_e2_extra_fuera_del_catalogo_se_rechaza():
    with pytest.raises(ReglaDeNegocioError, match="SUP-06.*PISCINA"):
        resolver_extras(["PISCINA"], CatalogoEnMemoria())


def test_sup06_el_extra_se_busca_sin_importar_mayusculas_ni_espacios():
    (extra,) = resolver_extras([" ventanas "], CatalogoEnMemoria())
    assert extra.codigo == "VENTANAS" and extra.precio == Dinero(250)


def test_h15_programaciones_que_se_cruzan_y_que_solo_se_tocan():
    a = Programacion(MANANA_9, 3)  # 09:00–12:00
    assert a.fin.hour == 12
    assert a.se_traslapa_con(Programacion(MANANA_9.replace(hour=11), 2))
    assert not a.se_traslapa_con(Programacion(MANANA_9.replace(hour=12), 2))  # empieza justo al terminar


def test_programacion_no_acepta_hora_con_zona_horaria():
    from datetime import timezone
    with pytest.raises(ValueError):
        Programacion(MANANA_9.replace(tzinfo=timezone.utc), 1)
