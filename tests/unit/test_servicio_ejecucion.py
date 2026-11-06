"""CU-04: ejecución del servicio, incidencias y cargos (RB-05, RB-06, RB-11, RB-12, RB-13, RB-14, RB-15)."""
from decimal import Decimal

import pytest

from src.domain.comun import Dinero, PermisoDenegado, ReglaDeNegocioError, Rol, TransicionInvalida
from src.domain.precio import CalculadoraDePrecio
from src.domain.servicio import EstadoServicio, OrigenCargo, TipoIncidencia
from src.domain.valores import Frecuencia
from tests.conftest import HORNO, MANANA_9, servicio_en_ejecucion, servicio_programado

T = MANANA_9


# ----- Inicio y terminación (US-13, US-14, US-18) ---------------------------------------
def test_us13_e1_registrar_inicio_cambia_a_en_ejecucion():
    s = servicio_programado()
    s.registrar_inicio(T, Rol.SUPERVISOR)
    assert s.estado == EstadoServicio.EN_EJECUCION and s.iniciado_en == T


def test_us13_e2_no_se_inicia_un_servicio_que_no_esta_programado():
    s = servicio_en_ejecucion()
    with pytest.raises(TransicionInvalida, match="iniciar"):
        s.registrar_inicio(T, Rol.SUPERVISOR)


def test_rb05_solo_el_supervisor_registra_inicio_y_terminacion():
    with pytest.raises(PermisoDenegado, match="RB-05"):
        servicio_programado().registrar_inicio(T, Rol.CUADRILLA)
    with pytest.raises(PermisoDenegado, match="RB-05"):
        servicio_en_ejecucion().registrar_terminacion(T, Rol.COORDINADOR)


def test_us14_e1_y_us18_e1_terminar_habilita_la_facturacion():
    s = servicio_en_ejecucion()
    s.registrar_terminacion(T, Rol.SUPERVISOR)
    assert s.estado == EstadoServicio.TERMINADO
    assert s.eventos[-1].nombre == "ServicioTerminado"


def test_us14_e2_no_se_termina_un_servicio_que_no_ha_iniciado():
    with pytest.raises(TransicionInvalida, match="terminar"):
        servicio_programado().registrar_terminacion(T, Rol.SUPERVISOR)


# ----- Acceso denegado (US-16, RB-11) ---------------------------------------------------
def test_us16_e1_tras_15_minutos_el_servicio_queda_no_realizado():
    s = servicio_programado()
    s.registrar_acceso_denegado(15, T, Rol.SUPERVISOR)
    assert s.estado == EstadoServicio.NO_REALIZADO
    assert s.incidencias[-1].tipo == TipoIncidencia.ACCESO_DENEGADO
    assert [e.nombre for e in s.eventos][-2:] == ["IncidenciaRegistrada", "ServicioNoRealizado"]


def test_us16_e2_con_14_minutos_todavia_no_se_puede_cancelar():
    s = servicio_programado()
    with pytest.raises(ReglaDeNegocioError, match="RB-11"):
        s.registrar_acceso_denegado(14, T, Rol.SUPERVISOR)
    assert s.estado == EstadoServicio.PROGRAMADO and s.incidencias == []


def test_rb11_acceso_denegado_solo_antes_de_iniciar():
    with pytest.raises(TransicionInvalida):
        servicio_en_ejecucion().registrar_acceso_denegado(20, T, Rol.SUPERVISOR)


# ----- Incidencias (US-15, US-19) ---------------------------------------------------------
def test_us15_e1_la_incidencia_queda_asociada_y_genera_evento_para_administracion():
    s = servicio_en_ejecucion()
    inc = s.registrar_incidencia(TipoIncidencia.CAMBIO, "El cliente pidió cambiar el orden", T, Rol.SUPERVISOR)
    assert inc.id == "SRV-1-I1" and inc.registrada_por == Rol.SUPERVISOR and inc in s.incidencias
    assert s.eventos[-1].nombre == "IncidenciaRegistrada"  # US-19: la política lo envía a administración


def test_rb06_solo_durante_la_ejecucion():
    with pytest.raises(TransicionInvalida):
        servicio_programado().registrar_incidencia(TipoIncidencia.CAMBIO, "x", T, Rol.SUPERVISOR)


def test_res03_despues_de_terminar_ya_no_se_registran_incidencias():
    s = servicio_en_ejecucion()
    s.registrar_terminacion(T, Rol.SUPERVISOR)
    with pytest.raises(TransicionInvalida):
        s.registrar_incidencia(TipoIncidencia.CAMBIO, "tarde", T, Rol.SUPERVISOR)


def test_rb06_requiere_descripcion_y_tipo_valido():
    s = servicio_en_ejecucion()
    with pytest.raises(ReglaDeNegocioError, match="descripción"):
        s.registrar_incidencia(TipoIncidencia.CAMBIO, "  ", T, Rol.SUPERVISOR)
    with pytest.raises(ReglaDeNegocioError, match="propia operación"):
        s.registrar_incidencia(TipoIncidencia.ACCESO_DENEGADO, "x", T, Rol.SUPERVISOR)


def test_rb06_solo_el_supervisor_registra_incidencias():
    with pytest.raises(PermisoDenegado, match="RB-06"):
        servicio_en_ejecucion().registrar_incidencia(TipoIncidencia.CAMBIO, "x", T, Rol.ADMINISTRACION)


# ----- Servicio adicional y material especial (US-11, RB-12, RB-14) ------------------------
def test_us11_e1_servicio_adicional_se_cotiza_con_el_catalogo_y_queda_pendiente():
    s = servicio_en_ejecucion()
    inc = s.registrar_incidencia(TipoIncidencia.SERVICIO_ADICIONAL, "Limpiar el horno", T, Rol.SUPERVISOR,
                                 extra=HORNO)
    (cargo,) = s.cargos
    assert cargo.monto == Dinero(200) and cargo.origen == OrigenCargo.SERVICIO_ADICIONAL and not cargo.autorizado
    assert inc.cargo_id == cargo.id


def test_rb12_servicio_adicional_sin_extra_del_catalogo_se_rechaza():
    with pytest.raises(ReglaDeNegocioError, match="RB-12"):
        servicio_en_ejecucion().registrar_incidencia(TipoIncidencia.SERVICIO_ADICIONAL, "x", T, Rol.SUPERVISOR)


def test_rb14_material_especial_genera_cargo_con_el_monto_capturado():
    s = servicio_en_ejecucion()
    s.registrar_incidencia(TipoIncidencia.MATERIAL_ESPECIAL, "Removedor de sarro", T, Rol.SUPERVISOR,
                           monto=Dinero(Decimal("180.50")))
    assert s.cargos[0].monto == Dinero(Decimal("180.50")) and s.cargos[0].origen == OrigenCargo.MATERIAL_ESPECIAL


def test_rb14_material_especial_requiere_monto_mayor_a_cero():
    s = servicio_en_ejecucion()
    with pytest.raises(ReglaDeNegocioError, match="RB-14"):
        s.registrar_incidencia(TipoIncidencia.MATERIAL_ESPECIAL, "x", T, Rol.SUPERVISOR)
    with pytest.raises(ReglaDeNegocioError, match="mayor que cero"):
        s.registrar_incidencia(TipoIncidencia.MATERIAL_ESPECIAL, "x", T, Rol.SUPERVISOR, monto=Dinero(0))


def test_us11_e1_el_coordinador_autoriza_el_cargo():
    s = servicio_en_ejecucion()
    s.registrar_incidencia(TipoIncidencia.SERVICIO_ADICIONAL, "Horno", T, Rol.SUPERVISOR, extra=HORNO)
    s.autorizar_cargo("SRV-1-C1", Rol.COORDINADOR)
    assert s.cargos[0].autorizado and s.cargos_pendientes == []
    assert s.eventos[-1].nombre == "CargoAdicionalAutorizado"


@pytest.mark.parametrize("rol", [Rol.SUPERVISOR, Rol.ADMINISTRACION, Rol.CLIENTE])
def test_us11_e2_solo_el_coordinador_autoriza_cargos(rol):
    s = servicio_en_ejecucion()
    s.registrar_incidencia(TipoIncidencia.SERVICIO_ADICIONAL, "Horno", T, Rol.SUPERVISOR, extra=HORNO)
    with pytest.raises(PermisoDenegado, match="RB-15"):
        s.autorizar_cargo("SRV-1-C1", rol)
    assert not s.cargos[0].autorizado


def test_rb14_no_se_autoriza_un_cargo_ajeno_ni_dos_veces():
    s = servicio_en_ejecucion()
    s.registrar_incidencia(TipoIncidencia.SERVICIO_ADICIONAL, "Horno", T, Rol.SUPERVISOR, extra=HORNO)
    with pytest.raises(ReglaDeNegocioError, match="no pertenece"):
        s.autorizar_cargo("SRV-99-C1", Rol.COORDINADOR)
    s.autorizar_cargo("SRV-1-C1", Rol.COORDINADOR)
    with pytest.raises(TransicionInvalida, match="ya estaba autorizado"):
        s.autorizar_cargo("SRV-1-C1", Rol.COORDINADOR)


def test_rb14_no_se_autorizan_cargos_en_un_servicio_no_realizado():
    s = servicio_programado()
    s.registrar_acceso_denegado(15, T, Rol.SUPERVISOR)
    with pytest.raises(TransicionInvalida):
        s.autorizar_cargo("SRV-1-C1", Rol.COORDINADOR)


# ----- Inmueble mayor a lo reportado (US-12, RB-13, H-09) -----------------------------------
def test_us12_e1_mas_de_15_por_ciento_exige_recalcular_antes_de_terminar():
    s = servicio_en_ejecucion()  # cotizado con 100 m²
    s.registrar_incidencia(TipoIncidencia.INMUEBLE_MAYOR, "Hay un cuarto extra", T, Rol.SUPERVISOR,
                           superficie_real=Decimal("115.01"))
    assert s.recalculo_pendiente


def test_us12_e2_exactamente_15_por_ciento_no_exige_recalcular():
    s = servicio_en_ejecucion()
    s.registrar_incidencia(TipoIncidencia.INMUEBLE_MAYOR, "Un poco mayor", T, Rol.SUPERVISOR, superficie_real=115)
    assert not s.recalculo_pendiente
    s.registrar_terminacion(T, Rol.SUPERVISOR)
    assert s.estado == EstadoServicio.TERMINADO


def test_us12_e3_no_se_termina_con_recalculo_pendiente():
    s = servicio_en_ejecucion()
    s.registrar_incidencia(TipoIncidencia.INMUEBLE_MAYOR, "Mayor", T, Rol.SUPERVISOR, superficie_real=130)
    with pytest.raises(ReglaDeNegocioError, match="RB-13"):
        s.registrar_terminacion(T, Rol.SUPERVISOR)


def test_us12_e1_el_coordinador_recalcula_con_la_formula_de_rb03():
    s = servicio_en_ejecucion()  # 100 m² residencial, única, ventanas $250 → $1,450
    s.registrar_incidencia(TipoIncidencia.INMUEBLE_MAYOR, "Mayor", T, Rol.SUPERVISOR, superficie_real=130)
    nuevo = s.recalcular_precio(CalculadoraDePrecio(), Rol.COORDINADOR)
    assert nuevo == Dinero(1810)  # 130 × 12 + 250
    assert not s.recalculo_pendiente
    s.registrar_terminacion(T, Rol.SUPERVISOR)
    assert s.estado == EstadoServicio.TERMINADO


def test_rb13_recalcular_sin_pendiente_o_sin_ser_coordinador_se_rechaza():
    s = servicio_en_ejecucion()
    with pytest.raises(TransicionInvalida, match="RB-13"):
        s.recalcular_precio(CalculadoraDePrecio(), Rol.COORDINADOR)
    s.registrar_incidencia(TipoIncidencia.INMUEBLE_MAYOR, "Mayor", T, Rol.SUPERVISOR, superficie_real=130)
    with pytest.raises(PermisoDenegado):
        s.recalcular_precio(CalculadoraDePrecio(), Rol.SUPERVISOR)


def test_rb13_inmueble_mayor_requiere_superficie_real():
    with pytest.raises(ReglaDeNegocioError, match="superficie real"):
        servicio_en_ejecucion().registrar_incidencia(TipoIncidencia.INMUEBLE_MAYOR, "x", T, Rol.SUPERVISOR)


def test_recurrente_recalcula_con_descuento():
    s = servicio_en_ejecucion(frecuencia=Frecuencia.SEMANAL)
    s.registrar_incidencia(TipoIncidencia.INMUEBLE_MAYOR, "Mayor", T, Rol.SUPERVISOR, superficie_real=200)
    assert s.recalcular_precio(CalculadoraDePrecio(), Rol.COORDINADOR) == Dinero(2410)  # 200×12×0.9 + 250
