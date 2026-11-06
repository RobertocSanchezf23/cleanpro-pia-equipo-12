"""Flujo completo del BPMN a través de la API (escenario de extremo a extremo sin interfaz gráfica).

Recorre el carril de cada rol: cliente → coordinador → supervisor → coordinador → administración.
"""
from tests.conftest import rol


def test_bpmn_servicio_completado_y_facturado(cliente_api, reloj):
    api = cliente_api
    # Cliente: solicitar cotización (empresarial, 200 m², semanal, con alfombra)
    cot = api.post("/cotizaciones", headers=rol("CLIENTE"), json={
        "cliente_id": "CLN-C010", "ubicacion": "Parque Industrial, Apodaca", "superficie_m2": 200,
        "tipo_inmueble": "EMPRESARIAL", "frecuencia": "SEMANAL", "extras": ["ALFOMBRA"]}).json()
    # Coordinador: estimar y enviar
    cot = api.post(f"/cotizaciones/{cot['id']}/estimacion", json={"duracion_horas": 4, "personal": 3},
                   headers=rol("COORDINADOR")).json()
    assert cot["precio"] == "3000.00"  # 200 × 15 × 0.90 + 300
    api.post(f"/cotizaciones/{cot['id']}/envio", headers=rol("COORDINADOR"))
    # Cliente: acepta al día siguiente
    reloj.avanzar(days=1)
    api.post(f"/cotizaciones/{cot['id']}/aceptacion", headers=rol("CLIENTE"))
    # Coordinador: programar y asignar cuadrilla
    srv = api.post("/servicios", headers=rol("COORDINADOR"), json={
        "cotizacion_id": cot["id"], "cuadrilla_id": "CUA-03", "supervisor": "Mario Ruiz",
        "inicio": "2026-11-09T08:00:00"}).json()
    # Supervisor: inicio, inmueble mayor y material especial
    reloj.avanzar(days=4, hours=-2)  # lunes 9, 08:00
    api.post(f"/servicios/{srv['id']}/inicio", headers=rol("SUPERVISOR"))
    api.post(f"/servicios/{srv['id']}/incidencias", headers=rol("SUPERVISOR"), json={
        "tipo": "INMUEBLE_MAYOR", "descripcion": "Bodega no reportada", "superficie_real": 250})
    srv = api.post(f"/servicios/{srv['id']}/incidencias", headers=rol("SUPERVISOR"), json={
        "tipo": "MATERIAL_ESPECIAL", "descripcion": "Desengrasante industrial", "monto": 420}).json()
    # Coordinador: recalcula el precio y autoriza el cargo
    api.post(f"/servicios/{srv['id']}/recalculo", headers=rol("COORDINADOR"))
    api.post(f"/servicios/{srv['id']}/cargos/{srv['cargos'][0]['id']}/autorizacion", headers=rol("COORDINADOR"))
    # Supervisor: terminación
    assert api.post(f"/servicios/{srv['id']}/terminacion", headers=rol("SUPERVISOR")).json()["estado"] == "TERMINADO"
    # Administración: factura y pago
    factura = api.post("/facturas", json={"servicio_id": srv["id"]}, headers=rol("ADMINISTRACION")).json()
    assert [c["monto"] for c in factura["conceptos"]] == ["3675.00", "420.00"]  # 250×15×0.9 + 300 ; material
    assert factura["total"] == "4095.00"
    api.post(f"/facturas/{factura['id']}/pago", headers=rol("ADMINISTRACION"))

    eventos = [n["evento"] for n in api.get("/notificaciones").json()]
    for esperado in ("CotizacionEnviada", "CotizacionAceptada", "ServicioProgramado", "IncidenciaRegistrada",
                     "PrecioRecalculado", "CargoAdicionalAutorizado", "ServicioTerminado", "FacturaEmitida"):
        assert esperado in eventos


def test_bpmn_cotizacion_rechazada_no_genera_servicio(cliente_api):
    api = cliente_api
    cid = api.post("/cotizaciones", headers=rol("CLIENTE"), json={
        "cliente_id": "CLN-C002", "ubicacion": "Centro, Monterrey", "superficie_m2": 60,
        "tipo_inmueble": "RESIDENCIAL", "frecuencia": "UNICA"}).json()["id"]
    api.post(f"/cotizaciones/{cid}/estimacion", json={"duracion_horas": 2, "personal": 1}, headers=rol("COORDINADOR"))
    api.post(f"/cotizaciones/{cid}/envio", headers=rol("COORDINADOR"))
    assert api.post(f"/cotizaciones/{cid}/rechazo", headers=rol("CLIENTE")).json()["estado"] == "RECHAZADA"
    r = api.post("/servicios", headers=rol("COORDINADOR"), json={
        "cotizacion_id": cid, "cuadrilla_id": "CUA-01", "supervisor": "Ana", "inicio": "2026-11-09T09:00:00"})
    assert r.json()["regla"] == "RB-02"
