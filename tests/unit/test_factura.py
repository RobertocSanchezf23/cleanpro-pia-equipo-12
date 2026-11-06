"""CU-05: GeneradorDeFactura y Factura (RB-07, RB-11, RB-14, RES-04, SUP-04, H-01, H-14)."""
from decimal import Decimal

import pytest

from src.domain.comun import Dinero, PermisoDenegado, ReglaDeNegocioError, Rol, TransicionInvalida
from src.domain.factura import EstadoPago, GeneradorDeFactura, OrigenConcepto
from src.domain.servicio import TipoIncidencia
from tests.conftest import HORNO, MANANA_9, servicio_en_ejecucion, servicio_programado

T = MANANA_9
generador = GeneradorDeFactura()


def terminado(con_cargo=False, autorizar=True):
    s = servicio_en_ejecucion()
    if con_cargo:
        s.registrar_incidencia(TipoIncidencia.SERVICIO_ADICIONAL, "Horno", T, Rol.SUPERVISOR, extra=HORNO)
        s.registrar_incidencia(TipoIncidencia.MATERIAL_ESPECIAL, "Sellador", T, Rol.SUPERVISOR,
                               monto=Dinero(Decimal("99.99")))
        if autorizar:
            s.autorizar_cargo("SRV-1-C1", Rol.COORDINADOR)
            s.autorizar_cargo("SRV-1-C2", Rol.COORDINADOR)
    s.registrar_terminacion(T, Rol.SUPERVISOR)
    return s


def facturar(servicio, ya=False, rol=Rol.ADMINISTRACION):
    return generador.generar("FAC-1", servicio, ya, T, rol)


def test_us20_e1_factura_de_servicio_terminado_queda_vinculada_y_pendiente_de_pago():
    f = facturar(terminado())
    assert f.servicio_id == "SRV-1" and f.estado_pago == EstadoPago.PENDIENTE
    assert [(c.origen, c.monto) for c in f.conceptos] == [(OrigenConcepto.SERVICIO, Dinero(1450))]


def test_us05_e1_el_monto_incluye_los_cargos_de_las_incidencias():
    f = facturar(terminado(con_cargo=True))
    assert f.total == Dinero(Decimal("1749.99"))  # 1450 + 200 + 99.99
    assert [c.referencia for c in f.conceptos[1:]] == ["SRV-1-C1", "SRV-1-C2"]  # RES-04: trazable al cargo
    assert f.eventos[-1].nombre == "FacturaEmitida"


def test_us16_e1_y_h01_servicio_no_realizado_factura_solo_el_50_por_ciento():
    s = servicio_programado()
    s.registrar_acceso_denegado(15, T, Rol.SUPERVISOR)
    f = facturar(s)
    (concepto,) = f.conceptos
    assert concepto.origen == OrigenConcepto.CANCELACION and concepto.monto == Dinero(725)
    assert concepto.referencia == "SRV-1-I1"


@pytest.mark.parametrize("preparar", ["programado", "en_ejecucion"])
def test_us20_e2_servicio_no_terminado_no_se_factura(preparar):
    s = servicio_programado() if preparar == "programado" else servicio_en_ejecucion()
    with pytest.raises(ReglaDeNegocioError, match="RB-07"):
        facturar(s)


def test_us20_e3_cargos_sin_autorizar_bloquean_la_factura():
    with pytest.raises(ReglaDeNegocioError, match="RB-14"):
        facturar(terminado(con_cargo=True, autorizar=False))


def test_us20_e3_basta_un_centavo_sin_autorizar_para_bloquear():
    s = servicio_en_ejecucion()
    s.registrar_incidencia(TipoIncidencia.MATERIAL_ESPECIAL, "Bolsa", T, Rol.SUPERVISOR, monto=Dinero("0.01"))
    s.registrar_terminacion(T, Rol.SUPERVISOR)
    with pytest.raises(ReglaDeNegocioError, match="RB-14"):
        facturar(s)


def test_us20_e4_una_sola_factura_por_servicio():
    with pytest.raises(ReglaDeNegocioError, match="SUP-04"):
        facturar(terminado(), ya=True)


def test_rb15_solo_administracion_factura():
    with pytest.raises(PermisoDenegado):
        facturar(terminado(), rol=Rol.COORDINADOR)


def test_reprogramacion_de_ultima_hora_se_factura_como_cargo():
    from datetime import datetime, timedelta
    s = servicio_programado()
    s.reprogramar(datetime(2026, 11, 6, 9, 0), MANANA_9 - timedelta(hours=1), Rol.COORDINADOR, [], Dinero(150))
    s.registrar_inicio(T, Rol.SUPERVISOR)
    s.registrar_terminacion(T, Rol.SUPERVISOR)
    assert facturar(s).total == Dinero(1600)


def test_us20_e5_registrar_pago():
    f = facturar(terminado())
    f.registrar_pago(T, Rol.ADMINISTRACION)
    assert f.estado_pago == EstadoPago.PAGADA and f.pagada_en == T
    with pytest.raises(TransicionInvalida, match="H-14"):
        f.registrar_pago(T, Rol.ADMINISTRACION)


def test_h14_solo_administracion_registra_pagos():
    with pytest.raises(PermisoDenegado):
        facturar(terminado()).registrar_pago(T, Rol.CLIENTE)
