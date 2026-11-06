# CleanPro — Sistema de cotización, programación, ejecución y facturación

![CI/CD](https://github.com/RobertocSanchezf23/cleanpro-pia-equipo-12/actions/workflows/ci.yml/badge.svg)

**Materia:** Componentes de Lógica de Negocio · FIME UANL · **PIA** (Producto Integrador de Aprendizaje)
**Profesor:** Miguel Ángel Gómez Marroquín

| Integrante | Matrícula |
|---|---|
| Roberto Carlos Sánchez Flores | 2151262 |
| Donovan Adrian Serrato Lores | 2154304 |
| Laura Sofía Vargas Ramírez | 2152053 |

| | Enlace |
|---|---|
| **Sistema desplegado (Swagger)** | https://cleanpro-pia-equipo-12.onrender.com/docs |
| **Repositorio** | https://github.com/RobertocSanchezf23/cleanpro-pia-equipo-12 |

CleanPro presta servicios de limpieza residencial y empresarial. Este sistema implementa su proceso principal con las reglas del BRD del equipo:

**cotización → respuesta del cliente → programación y cuadrilla → ejecución con incidencias → facturación y pago**

Resuelve los problemas del BRD: los cambios que no llegaban a administración (PA-01), los errores de facturación (PA-02), las asignaciones manuales (PA-03) y la falta de evidencia de incidencias y extras (PA-04).

## Documentación

| Documento | Contenido |
|---|---|
| [docs/BRD.md](docs/BRD.md) | BRD completo, con el refinamiento del PIA (sección 18) |
| [docs/analisis/user-stories.md](docs/analisis/user-stories.md) | 22 User Stories con criterios Gherkin |
| [docs/analisis/bpmn.md](docs/analisis/bpmn.md) | BPMN del proceso y su relación con la API |
| [docs/analisis/glosario.md](docs/analisis/glosario.md) | Glosario de dominio (con los nombres usados en el código) |
| [docs/architecture/decisiones-tecnicas.md](docs/architecture/decisiones-tecnicas.md) | Capas, patrones, SOLID y riesgos |
| [docs/architecture/diagramas.md](docs/architecture/diagramas.md) | Diagramas DDD, UML de clases, estados, secuencias y despliegue |
| [docs/architecture/adr/](docs/architecture/adr) | ADR-001 a ADR-010 |
| [docs/api/](docs/api) | Especificación OpenAPI y tabla de endpoints |
| [docs/trazabilidad.md](docs/trazabilidad.md) | Regla → User Story → endpoint → código → prueba |

## Arquitectura en una imagen

```
src/
├── domain/          Modelo de dominio: Cotizacion, Servicio, Factura, Value Objects,
│                    Specifications (AND/OR/NOT), máquinas de estados y eventos. Sin dependencias.
├── application/     Casos de uso CU-01 a CU-05, puertos (interfaces), notificaciones y consultas (CQRS)
├── infrastructure/  SQLAlchemy (PostgreSQL/SQLite), repositorios, Unidad de Trabajo, configuración
└── api/             FastAPI: endpoints REST, esquemas y manejo de errores
tests/
├── unit/            123 pruebas del dominio (sin base de datos)
├── integration/     Repositorios, API completa y flujo del BPMN (SQLite o PostgreSQL)
└── test_trazabilidad.py   Verifica que cada escenario Gherkin tenga prueba
```

## Ejecutar en local (sin Docker)

Requiere Python 3.11 o superior. Sin configurar nada, usa SQLite en el archivo `cleanpro.db`.

```bash
python -m venv .venv
# Windows PowerShell:
.venv\Scripts\Activate.ps1
# macOS / Linux:
source .venv/bin/activate

python -m pip install -r requirements-dev.txt
python -m uvicorn src.api.main:app --reload
```

Abrir **http://localhost:8000/docs**. Al arrancar por primera vez se cargan datos de demostración: 40 clientes del paquete del PIA, 4 cuadrillas (CUA-04 inactiva), 5 extras en el catálogo, una cotización aceptada (`COT-DEMO-01`) y una sin respuesta desde hace dos semanas (`COT-DEMO-02`).

## Ejecutar con Docker Compose (DB + App + Tests)

```bash
docker compose up --build        # PostgreSQL + API en http://localhost:8000/docs + pruebas
docker compose run --rm tests    # solo las pruebas, contra PostgreSQL
docker compose down -v           # apagar y borrar los datos
```

Opcional: copiar `.env.example` como `.env` para cambiar el usuario y la contraseña de PostgreSQL.

## Pruebas y calidad

| Qué | Comando |
|---|---|
| Todas las pruebas | `python -m pytest -v` |
| Solo dominio | `python -m pytest tests/unit -v` |
| Cobertura (mínimo 80 %) | `python -m pytest --cov=src --cov-report=term-missing --cov-report=html --cov-fail-under=80` |
| Estilo | `python -m ruff check src tests` |
| Pruebas de integración contra PostgreSQL | definir `TEST_DATABASE_URL=postgresql+psycopg://usuario:contraseña@localhost:5432/base` y correr `pytest tests/integration` |
| Regenerar `docs/api/openapi.json` | `python -m herramientas.exportar_openapi` |

## Pipeline CI/CD (`.github/workflows/ci.yml`)

En cada push o pull request:

1. **pruebas:** Ruff + pytest con cobertura mínima de 80 % (publica el reporte HTML como artefacto).
2. **pruebas-postgres:** pruebas de integración contra un PostgreSQL real.
3. **docker:** construye las imágenes, corre las pruebas dentro de Docker Compose y levanta la API para verificar `/salud` y `/docs`.
4. **despliegue:** solo en `main` y solo si todo lo anterior pasó, avisa a Render que despliegue (secreto `RENDER_DEPLOY_HOOK`).

## Variables de entorno

| Variable | Para qué | Valor por defecto |
|---|---|---|
| `DATABASE_URL` | Base de datos (`postgresql+psycopg://…` o `sqlite:///…`; también acepta `postgres://` de Render) | `sqlite:///./cleanpro.db` |
| `APP_ENV` | Nombre del entorno | `desarrollo` |
| `CARGAR_DATOS_DEMO` | Cargar los datos de demostración si la base está vacía | `true` |
| `ZONA_HORARIA` | Zona horaria del negocio | `America/Monterrey` |
| `TEST_DATABASE_URL` | Base para las pruebas de integración (opcional) | SQLite en memoria |
| `PORT` | Puerto (lo define Render) | `8000` |

Ningún secreto está en el repositorio: `.env` está en `.gitignore` y `.env.example` solo tiene valores de ejemplo.

## Guion de demostración (Swagger)

Cada operación pide el encabezado **`X-Rol`**. En Swagger aparece como un campo en cada endpoint.

| # | Endpoint | X-Rol | Datos | Qué se demuestra |
|---|---|---|---|---|
| 1 | `POST /cotizaciones` | CLIENTE | el ejemplo que trae Swagger | US-01: queda `SOLICITADA` |
| 2 | `POST /cotizaciones/{id}/estimacion` | COORDINADOR | `{"duracion_horas": 3, "personal": 2}` | RB-03: 100 m² × $12 + ventanas $250 = **$1,450.00** |
| 3 | `POST /cotizaciones/{id}/estimacion` | SUPERVISOR | igual | RB-15: **403** solo el coordinador estima |
| 4 | `POST /cotizaciones/{id}/envio` | COORDINADOR | — | Queda `PENDIENTE` con fecha de vencimiento (5 días hábiles) |
| 5 | `POST /servicios` | COORDINADOR | con esa cotización | RB-02: **422**, todavía no la acepta el cliente |
| 6 | `POST /cotizaciones/{id}/aceptacion` | CLIENTE | — | `ACEPTADA` |
| 7 | `POST /servicios` | COORDINADOR | cuadrilla `CUA-01`, una fecha futura | `PROGRAMADO`; el cliente recibe aviso (US-03) |
| 8 | `POST /servicios` | COORDINADOR | otra cotización (`COT-DEMO-01`), misma cuadrilla y hora | RES-01: **422**, cuadrilla ocupada |
| 9 | `POST /servicios/{id}/inicio` | SUPERVISOR | — | `EN_EJECUCION` |
| 10 | `POST /servicios/{id}/incidencias` | SUPERVISOR | el ejemplo (extra `HORNO`) | RB-12: cargo de $200 **pendiente** |
| 11 | `POST /facturas` | ADMINISTRACION | `{"servicio_id": "…"}` | RB-07: **422**, no ha terminado |
| 12 | `POST /servicios/{id}/terminacion` → `POST /facturas` | SUPERVISOR → ADMINISTRACION | — | RB-14: **422**, hay un cargo sin autorizar |
| 13 | `POST /servicios/{id}/cargos/{cargo_id}/autorizacion` | COORDINADOR | — | Se autoriza el cargo |
| 14 | `POST /facturas` | ADMINISTRACION | — | Factura de **$1,650.00** (servicio + cargo) |
| 15 | `GET /notificaciones` y `GET /reportes/resumen` | — | — | PA-01 y US-21: avisos y estado general |
| 16 | `GET /cotizaciones/COT-DEMO-02` | — | — | US-22: queda `VENCIDA` |

Otras reglas para mostrar: `POST /servicios/{id}/acceso-denegado` con 14 y luego 15 minutos (RB-11, factura del 50 %), e `INMUEBLE_MAYOR` con `superficie_real` de 115 y de 130 (RB-13).
