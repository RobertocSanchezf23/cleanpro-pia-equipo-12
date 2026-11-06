"""Integración de la API REST: cada endpoint con su base de datos real (SQLite en memoria o PostgreSQL)."""
from tests.conftest import rol

COT = {"cliente_id": "CLN-C001", "ubicacion": "Av. Universidad 500, San Nicolás", "superficie_m2": 100,
       "tipo_inmueble": "RESIDENCIAL", "frecuencia": "UNICA", "extras": ["VENTANAS"]}
PROG = {"cotizacion_id": "COT-DEMO-01", "cuadrilla_id": "CUA-01", "supervisor": "Ana López",
        "inicio": "2026-11-05T09:00:00"}


def cotizacion_enviada(api, **cambios):
    cid = api.post("/cotizaciones", json={**COT, **cambios}, headers=rol("CLIENTE")).json()["id"]
    api.post(f"/cotizaciones/{cid}/estimacion", json={"duracion_horas": 3, "personal": 2}, headers=rol("COORDINADOR"))
    api.post(f"/cotizaciones/{cid}/envio", headers=rol("COORDINADOR"))
    return cid


def servicio(api, **cambios):
    r = api.post("/servicios", json={**PROG, **cambios}, headers=rol("COORDINADOR"))
    assert r.status_code == 201, r.json()
    return r.json()["id"]


# ----- General --------------------------------------------------------------------------
def test_salud_y_documentacion(cliente_api):
    assert cliente_api.get("/salud").json()["estado"] == "ok"
    assert cliente_api.get("/", follow_redirects=False).headers["location"] == "/docs"
    esquema = cliente_api.get("/openapi.json").json()
    assert esquema["info"]["title"] == "CleanPro API"
    assert "/servicios/{servicio_id}/incidencias" in esquema["paths"]


def test_sin_encabezado_de_rol_la_api_responde_422(cliente_api):
    r = cliente_api.post("/cotizaciones", json=COT)
    assert r.status_code == 422 and r.json()["detail"][0]["loc"] == ["header", "X-Rol"]


def test_recurso_inexistente_responde_404(cliente_api):
    for url in ("/cotizaciones/NO-EXISTE", "/servicios/NO-EXISTE", "/facturas/NO-EXISTE"):
        r = cliente_api.get(url)
        assert r.status_code == 404 and r.json()["error"] == "no_encontrado"


# ----- Cotizaciones ---------------------------------------------------------------------
def test_us01_us06_us07_solicitar_estimar_y_enviar(cliente_api):
    r = cliente_api.post("/cotizaciones", json=COT, headers=rol("CLIENTE"))
    assert r.status_code == 201 and r.json()["estado"] == "SOLICITADA"
    cid = r.json()["id"]
    r = cliente_api.post(f"/cotizaciones/{cid}/estimacion", json={"duracion_horas": 3, "personal": 2},
                         headers=rol("COORDINADOR"))
    assert r.json()["precio"] == "1450.00"
    r = cliente_api.post(f"/cotizaciones/{cid}/envio", headers=rol("COORDINADOR"))
    assert r.json()["estado"] == "PENDIENTE" and r.json()["vence_en"] == "2026-11-11T23:59:59"


def test_us01_e2_extra_inexistente_responde_422_con_la_regla(cliente_api):
    r = cliente_api.post("/cotizaciones", json={**COT, "extras": ["PISCINA"]}, headers=rol("CLIENTE"))
    assert r.status_code == 422 and r.json()["regla"] == "SUP-06"


def test_us01_e3_cliente_inactivo_responde_422(cliente_api):
    r = cliente_api.post("/cotizaciones", json={**COT, "cliente_id": "CLN-C007"}, headers=rol("CLIENTE"))
    assert r.status_code == 422 and "inactivo" in r.json()["detalle"]


def test_validacion_de_datos_superficie_negativa(cliente_api):
    assert cliente_api.post("/cotizaciones", json={**COT, "superficie_m2": -1},
                            headers=rol("CLIENTE")).status_code == 422


def test_us06_e4_estimar_con_otro_rol_responde_403(cliente_api):
    cid = cliente_api.post("/cotizaciones", json=COT, headers=rol("CLIENTE")).json()["id"]
    r = cliente_api.post(f"/cotizaciones/{cid}/estimacion", json={"duracion_horas": 3, "personal": 2},
                         headers=rol("CLIENTE"))
    assert r.status_code == 403 and r.json()["regla"] == "RB-15"


def test_us07_e2_enviar_sin_estimar_responde_422(cliente_api):
    cid = cliente_api.post("/cotizaciones", json=COT, headers=rol("CLIENTE")).json()["id"]
    assert cliente_api.post(f"/cotizaciones/{cid}/envio", headers=rol("COORDINADOR")).json()["regla"] == "RB-01"


def test_us02_aceptar_y_rechazar(cliente_api):
    a, b = cotizacion_enviada(cliente_api), cotizacion_enviada(cliente_api)
    assert cliente_api.post(f"/cotizaciones/{a}/aceptacion", headers=rol("CLIENTE")).json()["estado"] == "ACEPTADA"
    assert cliente_api.post(f"/cotizaciones/{b}/rechazo", headers=rol("CLIENTE")).json()["estado"] == "RECHAZADA"
    r = cliente_api.post(f"/cotizaciones/{b}/aceptacion", headers=rol("CLIENTE"))
    assert r.status_code == 409 and r.json()["error"] == "transicion_invalida"


def test_us22_aceptar_despues_de_5_dias_habiles_la_deja_vencida(cliente_api, reloj):
    cid = cotizacion_enviada(cliente_api)
    reloj.avanzar(days=8)  # jueves 12 de noviembre
    r = cliente_api.post(f"/cotizaciones/{cid}/aceptacion", headers=rol("CLIENTE"))
    assert r.status_code == 409 and r.json()["regla"] == "RB-08"
    assert cliente_api.get(f"/cotizaciones/{cid}").json()["estado"] == "VENCIDA"  # el cambio sí se guardó


def test_us22_e1_consultar_marca_vencida_y_renovar_crea_una_nueva(cliente_api):
    assert cliente_api.get("/cotizaciones/COT-DEMO-02").json()["estado"] == "VENCIDA"
    r = cliente_api.post("/cotizaciones/COT-DEMO-02/renovacion", headers=rol("COORDINADOR"))
    assert r.status_code == 201 and r.json()["estado"] == "SOLICITADA" and r.json()["renovada_de"] == "COT-DEMO-02"
    vencidas = cliente_api.get("/cotizaciones", params={"estado": "VENCIDA"}).json()
    assert [c["id"] for c in vencidas] == ["COT-DEMO-02"]


# ----- Servicios ------------------------------------------------------------------------
def test_us08_us09_us03_programar_y_avisar_al_cliente(cliente_api):
    r = cliente_api.post("/servicios", json=PROG, headers=rol("COORDINADOR"))
    assert r.status_code == 201
    s = r.json()
    assert s["estado"] == "PROGRAMADO" and s["cuadrilla_id"] == "CUA-01" and s["fin"] == "2026-11-05T12:00:00"
    avisos = cliente_api.get("/notificaciones", params={"cliente_id": "CLN-C001"}).json()
    assert avisos[0]["evento"] == "ServicioProgramado" and "2026-11-05 09:00" in avisos[0]["mensaje"]


def test_us08_e2_programar_cotizacion_no_aceptada_responde_422(cliente_api):
    cid = cotizacion_enviada(cliente_api)
    r = cliente_api.post("/servicios", json={**PROG, "cotizacion_id": cid}, headers=rol("COORDINADOR"))
    assert r.status_code == 422 and r.json()["regla"] == "RB-02"


def test_us08_e3_segunda_programacion_de_la_misma_cotizacion(cliente_api):
    servicio(cliente_api)
    r = cliente_api.post("/servicios", json={**PROG, "cuadrilla_id": "CUA-02"}, headers=rol("COORDINADOR"))
    assert r.status_code == 422 and r.json()["regla"] == "H-06"


def test_us09_e2_cuadrilla_ocupada_y_rb04_cuadrilla_inactiva(cliente_api):
    servicio(cliente_api)
    otra = cotizacion_enviada(cliente_api)
    cliente_api.post(f"/cotizaciones/{otra}/aceptacion", headers=rol("CLIENTE"))
    r = cliente_api.post("/servicios", json={**PROG, "cotizacion_id": otra, "inicio": "2026-11-05T10:00:00"},
                         headers=rol("COORDINADOR"))
    assert r.json()["regla"] == "RES-01"
    r = cliente_api.post("/servicios", json={**PROG, "cotizacion_id": otra, "cuadrilla_id": "CUA-04"},
                         headers=rol("COORDINADOR"))
    assert r.json()["regla"] == "RB-04"
    assert servicio(cliente_api, cotizacion_id=otra, cuadrilla_id="CUA-02")  # otra cuadrilla sí está libre


def test_programar_acepta_fecha_con_zona_horaria(cliente_api):
    sid = servicio(cliente_api, inicio="2026-11-05T15:00:00Z")  # 15:00 UTC = 09:00 en Monterrey
    assert cliente_api.get(f"/servicios/{sid}").json()["inicio"] == "2026-11-05T09:00:00"


def test_us04_reprogramar_sin_costo_y_de_ultima_hora(cliente_api, reloj):
    sid = servicio(cliente_api)
    r = cliente_api.post(f"/servicios/{sid}/reprogramacion", json={"nuevo_inicio": "2026-11-06T09:00:00"},
                         headers=rol("CLIENTE"))
    assert r.status_code == 200 and r.json()["inicio"] == "2026-11-06T09:00:00" and r.json()["cargos"] == []
    reloj.avanzar(days=1, hours=22, minutes=30)  # viernes 6, 08:30: faltan 30 min
    r = cliente_api.post(f"/servicios/{sid}/reprogramacion", json={"nuevo_inicio": "2026-11-09T09:00:00"},
                         headers=rol("CLIENTE"))
    assert r.status_code == 403  # US-04 E3
    r = cliente_api.post(f"/servicios/{sid}/reprogramacion",
                         json={"nuevo_inicio": "2026-11-09T09:00:00", "cargo": 150}, headers=rol("COORDINADOR"))
    assert r.json()["cargos"][0]["monto"] == "150.00"


def test_us10_ausencia_sin_reemplazo_con_aviso_tardio(cliente_api, reloj):
    sid = servicio(cliente_api)
    reloj.avanzar(hours=22, minutes=30)  # jueves 5, 08:30
    r = cliente_api.post(f"/servicios/{sid}/ausencia", json={
        "integrante": "Luis Pérez", "reasignado": False, "nuevo_inicio": "2026-11-06T09:00:00"},
        headers=rol("COORDINADOR"))
    assert [i["tipo"] for i in r.json()["incidencias"]] == ["EMPLEADO_AUSENTE", "AVISO_TARDIO"]


def test_us13_us15_us11_us14_ejecucion_con_cargo_autorizado(cliente_api):
    sid = servicio(cliente_api)
    assert cliente_api.post(f"/servicios/{sid}/inicio", headers=rol("SUPERVISOR")).json()["estado"] == "EN_EJECUCION"
    r = cliente_api.post(f"/servicios/{sid}/incidencias", json={
        "tipo": "SERVICIO_ADICIONAL", "descripcion": "Limpiar el horno", "extra": "horno"}, headers=rol("SUPERVISOR"))
    assert r.status_code == 201
    cargo = r.json()["cargos"][0]
    assert cargo["monto"] == "200.00" and not cargo["autorizado"]
    r = cliente_api.post(f"/servicios/{sid}/cargos/{cargo['id']}/autorizacion", headers=rol("SUPERVISOR"))
    assert r.status_code == 403  # US-11 E2
    r = cliente_api.post(f"/servicios/{sid}/cargos/{cargo['id']}/autorizacion", headers=rol("COORDINADOR"))
    assert r.json()["cargos"][0]["autorizado"]
    assert cliente_api.post(f"/servicios/{sid}/terminacion", headers=rol("SUPERVISOR")).json()["estado"] == "TERMINADO"


def test_us15_extra_en_sitio_fuera_del_catalogo(cliente_api):
    sid = servicio(cliente_api)
    cliente_api.post(f"/servicios/{sid}/inicio", headers=rol("SUPERVISOR"))
    r = cliente_api.post(f"/servicios/{sid}/incidencias", json={
        "tipo": "SERVICIO_ADICIONAL", "descripcion": "x", "extra": "PISCINA"}, headers=rol("SUPERVISOR"))
    assert r.json()["regla"] == "SUP-06"


def test_us12_inmueble_mayor_bloquea_terminacion_hasta_recalcular(cliente_api):
    sid = servicio(cliente_api)  # COT-DEMO-01: 120 m² + ventanas = $1,690
    cliente_api.post(f"/servicios/{sid}/inicio", headers=rol("SUPERVISOR"))
    cliente_api.post(f"/servicios/{sid}/incidencias", json={
        "tipo": "INMUEBLE_MAYOR", "descripcion": "Cuarto extra", "superficie_real": 150}, headers=rol("SUPERVISOR"))
    r = cliente_api.post(f"/servicios/{sid}/terminacion", headers=rol("SUPERVISOR"))
    assert r.status_code == 422 and r.json()["regla"] == "RB-13"
    r = cliente_api.post(f"/servicios/{sid}/recalculo", headers=rol("COORDINADOR"))
    assert r.json()["precio_acordado"] == "2050.00" and not r.json()["recalculo_pendiente"]  # 150×12 + 250


def test_us16_acceso_denegado(cliente_api):
    sid = servicio(cliente_api)
    r = cliente_api.post(f"/servicios/{sid}/acceso-denegado", json={"minutos_espera": 14}, headers=rol("SUPERVISOR"))
    assert r.status_code == 422 and r.json()["regla"] == "RB-11"
    r = cliente_api.post(f"/servicios/{sid}/acceso-denegado", json={"minutos_espera": 15}, headers=rol("SUPERVISOR"))
    assert r.json()["estado"] == "NO_REALIZADO"


def test_transicion_invalida_responde_409(cliente_api):
    sid = servicio(cliente_api)
    r = cliente_api.post(f"/servicios/{sid}/terminacion", headers=rol("SUPERVISOR"))
    assert r.status_code == 409 and r.json()["regla"] == "Máquina de estados"


# ----- Facturación -----------------------------------------------------------------------
def test_us20_us05_facturar_y_pagar(cliente_api):
    sid = servicio(cliente_api)
    r = cliente_api.post("/facturas", json={"servicio_id": sid}, headers=rol("ADMINISTRACION"))
    assert r.status_code == 422 and r.json()["regla"] == "RB-07"  # US-20 E2
    cliente_api.post(f"/servicios/{sid}/inicio", headers=rol("SUPERVISOR"))
    cliente_api.post(f"/servicios/{sid}/terminacion", headers=rol("SUPERVISOR"))
    r = cliente_api.post("/facturas", json={"servicio_id": sid}, headers=rol("ADMINISTRACION"))
    assert r.status_code == 201 and r.json()["total"] == "1690.00" and r.json()["estado_pago"] == "PENDIENTE"
    fid = r.json()["id"]
    assert cliente_api.post("/facturas", json={"servicio_id": sid},
                            headers=rol("ADMINISTRACION")).json()["regla"] == "SUP-04"  # US-20 E4
    assert cliente_api.post(f"/facturas/{fid}/pago", headers=rol("ADMINISTRACION")).json()["estado_pago"] == "PAGADA"
    assert cliente_api.get(f"/facturas/{fid}").json()["pagada_en"] is not None
    aviso = cliente_api.get("/notificaciones", params={"destinatario": "CLIENTE"}).json()[0]
    assert aviso["evento"] == "FacturaEmitida" and "$1,690.00" in aviso["mensaje"]  # US-05


def test_us20_e3_factura_con_cargo_pendiente(cliente_api):
    sid = servicio(cliente_api)
    cliente_api.post(f"/servicios/{sid}/inicio", headers=rol("SUPERVISOR"))
    cliente_api.post(f"/servicios/{sid}/incidencias", json={
        "tipo": "MATERIAL_ESPECIAL", "descripcion": "Sellador", "monto": 80}, headers=rol("SUPERVISOR"))
    cliente_api.post(f"/servicios/{sid}/terminacion", headers=rol("SUPERVISOR"))
    r = cliente_api.post("/facturas", json={"servicio_id": sid}, headers=rol("ADMINISTRACION"))
    assert r.status_code == 422 and r.json()["regla"] == "RB-14"


def test_us16_factura_del_servicio_no_realizado_es_el_50_por_ciento(cliente_api):
    sid = servicio(cliente_api)
    cliente_api.post(f"/servicios/{sid}/acceso-denegado", json={"minutos_espera": 20}, headers=rol("SUPERVISOR"))
    r = cliente_api.post("/facturas", json={"servicio_id": sid}, headers=rol("ADMINISTRACION"))
    assert r.json()["total"] == "845.00" and r.json()["conceptos"][0]["origen"] == "CANCELACION"


# ----- Consultas y reportes -----------------------------------------------------------------
def test_catalogos_de_consulta(cliente_api):
    assert len(cliente_api.get("/clientes").json()) == 40
    assert [c["id"] for c in cliente_api.get("/cuadrillas").json()] == ["CUA-01", "CUA-02", "CUA-03", "CUA-04"]
    assert {e["codigo"] for e in cliente_api.get("/catalogo/extras").json()} >= {"VENTANAS", "HORNO"}


def test_us17_us19_us21_reportes(cliente_api):
    sid = servicio(cliente_api)
    cliente_api.post(f"/servicios/{sid}/inicio", headers=rol("SUPERVISOR"))
    cliente_api.post(f"/servicios/{sid}/incidencias", json={"tipo": "CAMBIO", "descripcion": "Mueble movido"},
                     headers=rol("SUPERVISOR"))
    cliente_api.post(f"/servicios/{sid}/terminacion", headers=rol("SUPERVISOR"))
    cliente_api.post("/facturas", json={"servicio_id": sid}, headers=rol("ADMINISTRACION"))

    (asignado,) = cliente_api.get("/cuadrillas/CUA-01/servicios").json()  # US-17
    assert asignado["ubicacion"].startswith("Av. Constitución") and asignado["inicio"] == "2026-11-05T09:00:00"
    admin = cliente_api.get("/notificaciones", params={"destinatario": "ADMINISTRACION"}).json()  # US-19
    assert any(n["evento"] == "IncidenciaRegistrada" and "Mueble movido" in n["mensaje"] for n in admin)
    assert cliente_api.get("/reportes/incidencias", params={"servicio_id": sid}).json()[0]["tipo"] == "CAMBIO"
    assert cliente_api.get("/reportes/facturacion").json()[0]["total"] == "1690.00"
    carga = {c["cuadrilla_id"]: c["servicios"] for c in cliente_api.get("/reportes/carga-cuadrillas").json()}
    assert carga["CUA-01"] == 1 and carga["CUA-02"] == 0
    resumen = cliente_api.get("/reportes/resumen").json()  # US-21
    assert resumen == {"servicios_por_estado": {"TERMINADO": 1}, "incidencias_registradas": 1,
                       "facturas_emitidas": 1, "facturas_pendientes_de_pago": 1, "total_facturado": "1690.00"}
    assert cliente_api.get("/servicios", params={"estado": "TERMINADO"}).json()[0]["id"] == sid
    assert cliente_api.get("/cotizaciones", params={"estado": "ACEPTADA"}).json()[0]["id"] == "COT-DEMO-01"
