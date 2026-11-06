"""CU-03: programar y asignar cuadrilla (RB-02, RB-04, RES-01, H-06, SUP-02), reprogramación (RB-09)
y empleado ausente (RB-10)."""
from datetime import datetime, timedelta

import pytest

from src.domain.comun import Dinero, PermisoDenegado, ReglaDeNegocioError, Rol, TransicionInvalida
from src.domain.entidades import Cuadrilla
from src.domain.servicio import EstadoServicio, OrigenCargo, Servicio, TipoIncidencia
from src.domain.valores import Programacion
from tests.conftest import AHORA, MANANA_9, nueva_cotizacion, servicio_programado, solicitud


def programar(sol, rol=Rol.COORDINADOR, supervisor="Ana López"):
    return Servicio.programar("SRV-1", sol, supervisor, rol)


# ----- Programar ----------------------------------------------------------------------
def test_us08_e1_cotizacion_aceptada_queda_programada_con_fecha_y_cuadrilla():
    s = programar(solicitud())
    assert s.estado == EstadoServicio.PROGRAMADO
    assert s.programacion.inicio == MANANA_9 and s.cuadrilla_id == "CUA-01"
    assert s.precio_acordado == Dinero(1450)  # se copia de la cotización aceptada


def test_us03_e1_al_programar_se_genera_el_evento_para_avisar_al_cliente():
    evento = programar(solicitud()).eventos[-1]
    assert evento.nombre == "ServicioProgramado"
    assert evento.datos["fecha"] == "2026-11-05 09:00" and evento.datos["cuadrilla_id"] == "CUA-01"


def test_us08_e2_cotizacion_no_aceptada_no_se_programa():
    with pytest.raises(ReglaDeNegocioError, match="RB-02"):
        programar(solicitud(cotizacion=nueva_cotizacion()))


def test_us08_e3_una_cotizacion_solo_genera_un_servicio():
    with pytest.raises(ReglaDeNegocioError, match="H-06"):
        programar(solicitud(ya_tiene_servicio=True))


def test_us08_no_se_programa_en_el_pasado():
    with pytest.raises(ReglaDeNegocioError, match="US-08"):
        programar(solicitud(inicio=AHORA - timedelta(hours=1)))


def test_rb04_cuadrilla_inactiva_no_se_asigna():
    with pytest.raises(ReglaDeNegocioError, match="RB-04"):
        programar(solicitud(cuadrilla=Cuadrilla("CUA-04", "Apodaca", 3, activa=False)))


def test_us09_e2_cuadrilla_ocupada_en_ese_horario_se_rechaza():
    ocupado = Programacion(MANANA_9 + timedelta(hours=2), 2)  # 11:00–13:00 se cruza con 09:00–12:00
    with pytest.raises(ReglaDeNegocioError, match="RES-01"):
        programar(solicitud(ocupaciones=[ocupado]))


def test_us09_e1_cuadrilla_con_servicio_que_termina_justo_antes_si_esta_disponible():
    anterior = Programacion(MANANA_9 - timedelta(hours=2), 2)  # 07:00–09:00
    assert programar(solicitud(ocupaciones=[anterior])).estado == EstadoServicio.PROGRAMADO


def test_rb15_solo_el_coordinador_programa():
    with pytest.raises(PermisoDenegado):
        programar(solicitud(), rol=Rol.CLIENTE)


def test_sup02_el_servicio_necesita_supervisor():
    with pytest.raises(ReglaDeNegocioError, match="SUP-02"):
        programar(solicitud(), supervisor=" ")


def test_specification_reporta_la_primera_regla_cuando_fallan_varias():
    with pytest.raises(ReglaDeNegocioError) as error:
        programar(solicitud(cotizacion=nueva_cotizacion(), cuadrilla=Cuadrilla("X", "X", 1, activa=False)))
    assert error.value.regla == "RB-02"


# ----- Reprogramación (US-04, RB-09, H-07) -----------------------------------------------
def test_us04_e1_con_2_horas_o_mas_el_cliente_reprograma_sin_costo():
    s = servicio_programado()
    hace_mas_de_2h = MANANA_9 - timedelta(hours=3)
    ultima_hora = s.reprogramar(datetime(2026, 11, 6, 9, 0), hace_mas_de_2h, Rol.CLIENTE, [])
    assert not ultima_hora and s.programacion.inicio == datetime(2026, 11, 6, 9, 0) and s.cargos == []
    assert s.eventos[-1].nombre == "ServicioReprogramado"


def test_us04_e1_exactamente_2_horas_antes_sigue_siendo_sin_costo():
    s = servicio_programado()
    assert not s.reprogramar(datetime(2026, 11, 6, 9, 0), MANANA_9 - timedelta(hours=2), Rol.CLIENTE, [])


def test_rb09_con_2_horas_o_mas_no_se_puede_cobrar_cargo():
    with pytest.raises(ReglaDeNegocioError, match="RB-09"):
        servicio_programado().reprogramar(datetime(2026, 11, 6, 9, 0), AHORA, Rol.COORDINADOR, [], Dinero(100))


def test_us04_e2_con_menos_de_2_horas_el_coordinador_aplica_cargo():
    s = servicio_programado()
    una_hora_antes = MANANA_9 - timedelta(hours=1)
    assert s.reprogramar(datetime(2026, 11, 6, 9, 0), una_hora_antes, Rol.COORDINADOR, [], Dinero(150))
    (cargo,) = s.cargos
    assert cargo.origen == OrigenCargo.REPROGRAMACION and cargo.monto == Dinero(150) and cargo.autorizado


def test_us04_e2_el_coordinador_puede_no_cobrar_cargo():
    s = servicio_programado()
    s.reprogramar(datetime(2026, 11, 6, 9, 0), MANANA_9 - timedelta(minutes=30), Rol.COORDINADOR, [], Dinero(0))
    assert s.cargos == []


def test_us04_e3_con_menos_de_2_horas_el_cliente_no_puede_reprogramar_solo():
    with pytest.raises(PermisoDenegado, match="RB-09/RB-15"):
        servicio_programado().reprogramar(datetime(2026, 11, 6, 9, 0), MANANA_9 - timedelta(minutes=119),
                                          Rol.CLIENTE, [])


def test_us04_e4_nueva_fecha_sin_cuadrilla_disponible_se_rechaza():
    s = servicio_programado()
    ocupado = [Programacion(datetime(2026, 11, 6, 10, 0), 2)]
    with pytest.raises(ReglaDeNegocioError, match="RES-01"):
        s.reprogramar(datetime(2026, 11, 6, 9, 0), AHORA, Rol.CLIENTE, ocupado)
    assert s.programacion.inicio == MANANA_9  # no cambió


def test_us04_la_nueva_fecha_debe_ser_futura():
    with pytest.raises(ReglaDeNegocioError, match="US-04"):
        servicio_programado().reprogramar(AHORA - timedelta(days=1), AHORA, Rol.CLIENTE, [])


def test_us04_solo_se_reprograma_un_servicio_programado():
    s = servicio_programado()
    s.registrar_inicio(MANANA_9, Rol.SUPERVISOR)
    with pytest.raises(TransicionInvalida):
        s.reprogramar(datetime(2026, 11, 6, 9, 0), AHORA, Rol.CLIENTE, [])


# ----- Empleado ausente (US-10, RB-10, H-08) -----------------------------------------------
def test_us10_e1_se_reasigna_personal_y_el_servicio_sigue_igual():
    s = servicio_programado()
    s.registrar_ausencia(AHORA, Rol.COORDINADOR, "Luis Pérez", reasignado=True)
    assert s.estado == EstadoServicio.PROGRAMADO and s.programacion.inicio == MANANA_9
    assert [i.tipo for i in s.incidencias] == [TipoIncidencia.EMPLEADO_AUSENTE]


def test_us10_e2_sin_reemplazo_se_reprograma_y_se_avisa_al_cliente():
    s = servicio_programado()
    s.registrar_ausencia(AHORA, Rol.COORDINADOR, "Luis Pérez", reasignado=False,
                         nuevo_inicio=datetime(2026, 11, 6, 9, 0))
    assert s.programacion.inicio == datetime(2026, 11, 6, 9, 0)
    assert [i.tipo for i in s.incidencias] == [TipoIncidencia.EMPLEADO_AUSENTE]
    assert s.eventos[-1].nombre == "ServicioReprogramado"


def test_us10_e2_con_exactamente_1_hora_no_hay_aviso_tardio():
    s = servicio_programado()
    s.registrar_ausencia(MANANA_9 - timedelta(hours=1), Rol.COORDINADOR, "Luis", False, datetime(2026, 11, 6, 9, 0))
    assert TipoIncidencia.AVISO_TARDIO not in [i.tipo for i in s.incidencias]


def test_us10_e3_con_menos_de_1_hora_queda_incidencia_de_aviso_tardio():
    s = servicio_programado()
    s.registrar_ausencia(MANANA_9 - timedelta(minutes=40), Rol.COORDINADOR, "Luis", False,
                         datetime(2026, 11, 6, 9, 0))
    assert s.incidencias[-1].tipo == TipoIncidencia.AVISO_TARDIO
    assert "40 min" in s.incidencias[-1].descripcion


def test_rb10_sin_reemplazo_hay_que_dar_nueva_fecha():
    with pytest.raises(ReglaDeNegocioError, match="RB-10"):
        servicio_programado().registrar_ausencia(AHORA, Rol.COORDINADOR, "Luis", reasignado=False)


def test_rb10_solo_el_coordinador_reasigna_personal():
    with pytest.raises(PermisoDenegado):
        servicio_programado().registrar_ausencia(AHORA, Rol.SUPERVISOR, "Luis", reasignado=True)
