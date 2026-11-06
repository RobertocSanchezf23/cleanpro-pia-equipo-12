# API REST de CleanPro

- **Especificación OpenAPI 3.1:** [`openapi.json`](openapi.json) (generada desde el código con `python -m herramientas.exportar_openapi`).
- **Swagger UI:** `/docs` en el servidor (local: http://localhost:8000/docs; producción: ver el README principal).
- **ReDoc:** `/redoc`.

## Convenciones

- **Rol:** cada operación que cambia estado pide el encabezado `X-Rol` con `CLIENTE`, `COORDINADOR`, `SUPERVISOR`, `CUADRILLA` o `ADMINISTRACION` (RB-15, ADR-009).
- **Fechas:** hora local de Monterrey en formato ISO, por ejemplo `2026-12-15T09:00:00`. Si se manda con zona horaria (`...Z`), se convierte.
- **Montos:** texto con dos decimales (`"1450.00"`) para no perder exactitud.
- **Errores de negocio:** `{"error": "...", "regla": "RB-02", "detalle": "..."}`.

| Código | Cuándo |
|---|---|
| 200 / 201 | Operación correcta / recurso creado |
| 403 `permiso_denegado` | El rol no puede hacer la operación (RB-15) |
| 404 `no_encontrado` | El id no existe |
| 409 `transicion_invalida` | La máquina de estados no lo permite (por ejemplo, terminar un servicio que no inició) |
| 422 `regla_de_negocio` | Se viola una regla del BRD (el campo `regla` dice cuál) |
| 422 (validación) | Datos con formato inválido o falta el encabezado `X-Rol` |

## Endpoints

| Método y ruta | Rol | Historia | Regla principal |
|---|---|---|---|
| `GET /salud` | — | — | Estado de la app y de la base |
| `POST /cotizaciones` | CLIENTE, COORDINADOR | US-01 | SUP-06, cliente activo |
| `GET /cotizaciones?estado=` | — | REP-01 | — |
| `GET /cotizaciones/{id}` | — | US-22 | RB-08 (marca vencida) |
| `POST /cotizaciones/{id}/estimacion` | COORDINADOR | US-06 | RB-03 |
| `POST /cotizaciones/{id}/envio` | COORDINADOR | US-07 | RB-01, RB-08 |
| `POST /cotizaciones/{id}/aceptacion` | CLIENTE | US-02 | RB-02, RB-08 |
| `POST /cotizaciones/{id}/rechazo` | CLIENTE | US-02 | — |
| `POST /cotizaciones/{id}/renovacion` | COORDINADOR | US-22 | RB-08 |
| `POST /servicios` | COORDINADOR | US-08, US-09, US-03 | RB-02, RB-04, RES-01, H-06 |
| `GET /servicios?estado=` | — | REP-02 | — |
| `GET /servicios/{id}` | — | CE-05 | — |
| `POST /servicios/{id}/reprogramacion` | CLIENTE (≥ 2 h) o COORDINADOR | US-04 | RB-09, RES-01 |
| `POST /servicios/{id}/ausencia` | COORDINADOR | US-10 | RB-10 |
| `POST /servicios/{id}/acceso-denegado` | SUPERVISOR | US-16 | RB-11 |
| `POST /servicios/{id}/inicio` | SUPERVISOR | US-13 | RB-05 |
| `POST /servicios/{id}/incidencias` | SUPERVISOR | US-15, US-11, US-12 | RB-06, RB-12, RB-13, RB-14 |
| `POST /servicios/{id}/cargos/{cargo_id}/autorizacion` | COORDINADOR | US-11 | RB-12, RB-14, RB-15 |
| `POST /servicios/{id}/recalculo` | COORDINADOR | US-12 | RB-13 |
| `POST /servicios/{id}/terminacion` | SUPERVISOR | US-14, US-18 | RB-05, RES-03, RB-13 |
| `POST /facturas` | ADMINISTRACION | US-20 | RB-07, RB-11, RB-14, SUP-04 |
| `GET /facturas/{id}` | — | US-05 | RES-04 |
| `POST /facturas/{id}/pago` | ADMINISTRACION | US-20 E5 | H-14 |
| `GET /clientes`, `/cuadrillas`, `/catalogo/extras` | — | — | Datos de referencia (SUP-06) |
| `GET /cuadrillas/{id}/servicios` | — | US-17 | — |
| `GET /notificaciones?destinatario=&cliente_id=` | — | US-03, US-05, US-19 | RB-06 |
| `GET /reportes/resumen` | — | US-21 | — |
| `GET /reportes/incidencias`, `/facturacion`, `/carga-cuadrillas` | — | REP-03, REP-04, REP-05 | — |

Las consultas (`GET`) no piden rol porque no cambian datos.
