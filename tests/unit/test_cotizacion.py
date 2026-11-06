"""Aggregate Cotizacion: máquina de estados, vigencia (RB-08, H-12) y roles (RB-15)."""
from datetime import date, datetime

import pytest

from src.domain.comun import Dinero, PermisoDenegado, ReglaDeNegocioError, Rol, TransicionInvalida
from src.domain.cotizacion import EstadoCotizacion
from src.domain.precio import CalculadoraDePrecio
from src.domain.valores import EstimacionOperativa
from src.domain.vigencia import Vigencia, sumar_dias_habiles
from tests.conftest import AHORA, nueva_cotizacion

calc = CalculadoraDePrecio()


def enviada(momento=AHORA):
    c = nueva_cotizacion()
    c.estimar(EstimacionOperativa(3, 2), calc, Rol.COORDINADOR)
    c.enviar(momento, Rol.COORDINADOR)
    return c


def test_us01_e1_la_solicitud_queda_registrada_para_estimar():
    c = nueva_cotizacion()
    assert c.estado == EstadoCotizacion.SOLICITADA and c.precio is None
    assert [e.nombre for e in c.eventos] == ["CotizacionSolicitada"]


def test_us01_e3_cliente_inactivo_no_puede_solicitar():
    with pytest.raises(ReglaDeNegocioError, match="inactivo"):
        nueva_cotizacion(activo=False)


def test_us01_cuadrilla_no_puede_solicitar_cotizaciones():
    from src.domain.cotizacion import Cotizacion
    from src.domain.entidades import Cliente
    from src.domain.valores import DatosDelInmueble, Frecuencia, TipoInmueble
    with pytest.raises(PermisoDenegado):
        Cotizacion.solicitar("C", Cliente("X", "X"), DatosDelInmueble("A", 10, TipoInmueble.RESIDENCIAL),
                             Frecuencia.UNICA, (), AHORA, Rol.CUADRILLA)


def test_us06_e1_estimar_guarda_duracion_personal_y_precio():
    c = nueva_cotizacion()
    precio = c.estimar(EstimacionOperativa(3, 2), calc, Rol.COORDINADOR)
    assert precio == Dinero(1450) and c.estimacion.personal == 2 and c.estado == EstadoCotizacion.SOLICITADA


def test_us06_e4_solo_el_coordinador_estima():
    with pytest.raises(PermisoDenegado, match="RB-15"):
        nueva_cotizacion().estimar(EstimacionOperativa(3, 2), calc, Rol.SUPERVISOR)


def test_us07_e1_al_enviar_queda_pendiente_con_vigencia():
    c = enviada()
    assert c.estado == EstadoCotizacion.PENDIENTE
    assert c.vigencia.vence_en == datetime(2026, 11, 11, 23, 59, 59)  # miércoles + 5 días hábiles
    assert c.eventos[-1].nombre == "CotizacionEnviada"


def test_us07_e2_no_se_envia_sin_estimar():
    with pytest.raises(ReglaDeNegocioError, match="RB-01"):
        nueva_cotizacion().enviar(AHORA, Rol.COORDINADOR)


def test_maquina_de_estados_no_se_estima_ni_envia_dos_veces():
    c = enviada()
    with pytest.raises(TransicionInvalida):
        c.estimar(EstimacionOperativa(1, 1), calc, Rol.COORDINADOR)
    with pytest.raises(TransicionInvalida):
        c.enviar(AHORA, Rol.COORDINADOR)


def test_us02_e1_el_cliente_acepta_dentro_de_la_vigencia():
    c = enviada()
    c.aceptar(AHORA, Rol.CLIENTE)
    assert c.estado == EstadoCotizacion.ACEPTADA and c.respondida_en == AHORA


def test_us02_e1_el_cliente_rechaza():
    c = enviada()
    c.rechazar(AHORA, Rol.CLIENTE)
    assert c.estado == EstadoCotizacion.RECHAZADA


@pytest.mark.parametrize("accion", ["aceptar", "rechazar"])
def test_us02_e2_no_se_responde_una_cotizacion_que_no_esta_pendiente(accion):
    c = enviada()
    c.aceptar(AHORA, Rol.CLIENTE)
    with pytest.raises(TransicionInvalida, match="US-02"):
        getattr(c, accion)(AHORA, Rol.CLIENTE)
    assert c.estado == EstadoCotizacion.ACEPTADA


def test_us02_e2_no_se_acepta_antes_de_enviarse():
    with pytest.raises(TransicionInvalida, match="pendiente"):
        nueva_cotizacion().aceptar(AHORA, Rol.CLIENTE)


def test_rb15_el_coordinador_no_acepta_en_nombre_del_cliente():
    with pytest.raises(PermisoDenegado):
        enviada().aceptar(AHORA, Rol.COORDINADOR)


def test_us22_e1_pendiente_despues_de_5_dias_habiles_queda_vencida():
    c = enviada()
    assert not c.actualizar_vencimiento(datetime(2026, 11, 11, 23, 59, 59))  # último segundo de vigencia
    assert c.actualizar_vencimiento(datetime(2026, 11, 12, 0, 0))
    assert c.estado == EstadoCotizacion.VENCIDA
    assert c.eventos[-1].nombre == "CotizacionVencida"


def test_rb08_aceptar_fuera_de_vigencia_se_rechaza():
    c = enviada()
    with pytest.raises(TransicionInvalida, match="RB-08"):
        c.aceptar(datetime(2026, 11, 12, 8, 0), Rol.CLIENTE)


def test_us22_e2_enviada_en_viernes_sigue_vigente_el_jueves_siguiente():
    viernes = datetime(2026, 11, 6, 17, 0)
    c = enviada(viernes)
    c.aceptar(datetime(2026, 11, 12, 18, 0), Rol.CLIENTE)  # jueves: 4 días hábiles
    assert c.estado == EstadoCotizacion.ACEPTADA


def test_h12_los_fines_de_semana_no_cuentan_como_dias_habiles():
    assert sumar_dias_habiles(date(2026, 11, 6), 5) == date(2026, 11, 13)  # viernes → viernes siguiente
    assert sumar_dias_habiles(date(2026, 11, 7), 1) == date(2026, 11, 9)  # sábado → lunes
    assert Vigencia(datetime(2026, 11, 7, 10, 0)).vence_en.date() == date(2026, 11, 13)


def test_us22_solo_una_cotizacion_vencida_se_renueva_y_conserva_sus_datos():
    c = enviada()
    with pytest.raises(TransicionInvalida):
        c.renovar("COT-2", AHORA, Rol.COORDINADOR)
    c.actualizar_vencimiento(datetime(2026, 11, 20, 9, 0))
    nueva = c.renovar("COT-2", datetime(2026, 11, 20, 9, 0), Rol.COORDINADOR)
    assert nueva.estado == EstadoCotizacion.SOLICITADA and nueva.renovada_de == c.id
    assert nueva.inmueble == c.inmueble and nueva.extras == c.extras and nueva.precio is None


def test_us22_actualizar_vencimiento_no_afecta_cotizaciones_aceptadas():
    c = enviada()
    c.aceptar(AHORA, Rol.CLIENTE)
    assert not c.actualizar_vencimiento(datetime(2027, 1, 1))
    assert c.estado == EstadoCotizacion.ACEPTADA
