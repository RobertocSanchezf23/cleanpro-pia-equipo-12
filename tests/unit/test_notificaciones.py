"""Política de notificaciones (US-03, US-05, US-19, PA-01): cada evento avisa a quien le interesa."""
import pytest

from src.application.notificaciones import notificaciones_para
from src.domain.comun import EventoDominio
from tests.conftest import AHORA


def destinatarios(nombre, **datos):
    return [n.destinatario for n in notificaciones_para(EventoDominio(nombre, "X-1", datos), AHORA)]


def test_us19_e1_incidencia_avisa_a_administracion():
    avisos = notificaciones_para(EventoDominio("IncidenciaRegistrada", "SRV-1",
                                               {"tipo": "CAMBIO", "descripcion": "x", "cargo": None}), AHORA)
    assert [a.destinatario for a in avisos] == ["ADMINISTRACION"]
    assert "SRV-1" in avisos[0].mensaje and avisos[0].creada_en == AHORA


def test_incidencia_con_cargo_avisa_tambien_al_coordinador():
    assert destinatarios("IncidenciaRegistrada", tipo="SERVICIO_ADICIONAL", descripcion="x",
                         cargo="200.00") == ["ADMINISTRACION", "COORDINADOR"]


def test_us03_e1_servicio_programado_avisa_al_cliente_con_fecha_y_cuadrilla():
    (aviso,) = notificaciones_para(EventoDominio("ServicioProgramado", "SRV-1", {
        "cliente_id": "CLN-C001", "fecha": "2026-11-05 09:00", "cuadrilla_id": "CUA-01", "supervisor": "Ana"}),
        AHORA)
    assert aviso.destinatario == "CLIENTE" and aviso.cliente_id == "CLN-C001"
    assert "2026-11-05 09:00" in aviso.mensaje and "CUA-01" in aviso.mensaje


@pytest.mark.parametrize("evento, datos, esperados", [
    ("CotizacionEnviada", {"cliente_id": "C", "precio": "1450.00", "vence_en": "2026-11-11T23:59:59"}, ["CLIENTE"]),
    ("CotizacionAceptada", {"cliente_id": "C"}, ["COORDINADOR"]),
    ("CotizacionRechazada", {"cliente_id": "C"}, ["COORDINADOR"]),
    ("CotizacionVencida", {"cliente_id": "C"}, ["COORDINADOR"]),
    ("ServicioReprogramado", {"cliente_id": "C", "fecha": "f", "motivo": "m"}, ["CLIENTE", "ADMINISTRACION"]),
    ("CargoAdicionalAutorizado", {"cargo_id": "C1", "monto": "10.00"}, ["ADMINISTRACION"]),
    ("PrecioRecalculado", {"anterior": "1.00", "nuevo": "2.00"}, ["ADMINISTRACION"]),
    ("ServicioNoRealizado", {"cliente_id": "C"}, ["ADMINISTRACION"]),
    ("ServicioTerminado", {"cliente_id": "C"}, ["ADMINISTRACION"]),
    ("FacturaEmitida", {"cliente_id": "C", "total": "1450.00"}, ["CLIENTE"]),  # US-05
    ("ServicioIniciado", {}, []),
])
def test_cada_evento_tiene_sus_destinatarios(evento, datos, esperados):
    assert destinatarios(evento, **datos) == esperados
