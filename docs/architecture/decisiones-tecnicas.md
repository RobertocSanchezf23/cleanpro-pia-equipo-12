# Documento de decisiones técnicas — CleanPro (PIA)

Este documento explica **cómo está construido** el sistema y **por qué**. Cada decisión importante tiene su ADR en [`adr/`](adr) con contexto, alternativas y consecuencias. Los diagramas están en [diagramas.md](diagramas.md).

## 1. Vista general

| Capa | Carpeta | Responsabilidad | Depende de |
|---|---|---|---|
| Presentación | `src/api` | Endpoints REST, esquemas Pydantic y traducción de errores a códigos HTTP | application, infrastructure (solo para armar el sistema) |
| Aplicación | `src/application` | Casos de uso CU-01 a CU-05, puertos (interfaces), política de notificaciones y consultas | domain |
| Dominio | `src/domain` | Aggregates, Value Objects, Specifications, máquinas de estados, servicios y eventos de dominio | nada (solo Python estándar) |
| Infraestructura | `src/infrastructure` | Tablas SQLAlchemy, repositorios, Unidad de Trabajo, consultas SQL, configuración y armado (composition root) | application, domain |

**Regla de dependencias:** el dominio no importa FastAPI, Pydantic ni SQLAlchemy. Por eso sus 123 pruebas unitarias corren sin base de datos y en menos de un segundo.

## 2. Tecnologías

| Necesidad | Elección | Motivo | ADR |
|---|---|---|---|
| Lenguaje y API | Python 3.12, FastAPI, Pydantic v2 | Swagger/OpenAPI automático; stack de las Unidades 4 y 5 | ADR-005 |
| Persistencia | SQLAlchemy 2; PostgreSQL 16 (Docker y Render) o SQLite (local) | La misma capa de datos en los dos motores | ADR-002, ADR-006 |
| Montos | `Decimal` en el dominio, centavos enteros en la base | Sin errores de redondeo (PA-02) | ADR-006 |
| Pruebas y calidad | pytest, pytest-cov (≥ 80 %), Ruff | Las herramientas de la Unidad 5 | — |
| Contenedores | Dockerfile multi-etapa + Docker Compose (db, app, tests) | Entorno reproducible | ADR-007 |
| CI/CD y despliegue | GitHub Actions + Render | Gratis; solo se despliega lo que pasa las pruebas | ADR-008 |

## 3. Modelo de dominio

| Elemento DDD | Implementación | Reglas que protege |
|---|---|---|
| Aggregate **Cotizacion** | `src/domain/cotizacion.py` | RB-01, RB-02, RB-08, RES-05, US-22 |
| Aggregate **Servicio** (con `Incidencia` y `CargoAdicional`) | `src/domain/servicio.py` | RB-04, RB-05, RB-06, RB-09 a RB-14, RES-01, RES-03 |
| Aggregate **Factura** | `src/domain/factura.py` | RB-07, RB-11, RB-14, RES-04, SUP-04 |
| Value Objects | `Dinero`, `DatosDelInmueble`, `Frecuencia`, `ExtraSolicitado`, `EstimacionOperativa`, `Vigencia`, `Programacion`, `ConceptoFacturado` | Validaciones de datos y cálculos inmutables |
| Domain Services | `CalculadoraDePrecio` (RB-03, RB-13), `GeneradorDeFactura` (CU-05) | Reglas que usan más de un objeto |
| Domain Events | `CotizacionEnviada`, `ServicioProgramado`, `IncidenciaRegistrada`, `FacturaEmitida`… | PA-01: avisos automáticos (ADR-010) |
| Entidades de referencia | `Cliente`, `Cuadrilla`, `ExtraDelCatalogo` | Se consultan por id; no tienen reglas propias |

## 4. Patrones de diseño y su justificación

| Patrón | Dónde | Problema del caso que resuelve |
|---|---|---|
| **Domain Model** | `src/domain/` | 15 reglas que dependen del estado de cada cotización y servicio (ADR-001). |
| **Aggregate** | `Cotizacion`, `Servicio`, `Factura` | Cada uno protege sus invariantes en una transacción; `Servicio` contiene sus incidencias porque RB-14 y RES-03 las revisan juntas (ADR-003). |
| **Value Object** | `src/domain/valores.py`, `comun.Dinero`, `vigencia.Vigencia` | Montos, superficies, fechas de vigencia y horarios se validan una vez y no cambian (`frozen=True`). `Dinero` evita los redondeos distintos que causan PA-02. |
| **Specification** (AND, OR, NOT) | `src/domain/especificaciones.py`; `PUEDE_PROGRAMARSE` (`servicio.py`), `SERVICIO_FACTURABLE` (`factura.py`), `puede_aceptarse` (`cotizacion.py`) | Las precondiciones de programar y facturar combinan varias reglas. Cada especificación lleva el código de su regla, así el error dice "RB-02" o "RB-14" exactamente. `SERVICIO_FACTURABLE = (TERMINADO OR NO_REALIZADO) AND NOT cargos pendientes AND NOT ya facturado` expresa H-01, RB-07, RB-14 y SUP-04 en una línea. |
| **State Machine** | `EstadoCotizacion`, `EstadoServicio`, `EstadoPago` + `_exigir_estado()` | Cada operación solo es válida en ciertos estados (no terminar sin iniciar, no responder una cotización vencida). Una transición inválida lanza `TransicionInvalida` (HTTP 409). |
| **Domain Service** | `CalculadoraDePrecio`, `GeneradorDeFactura` | El precio se usa al cotizar y al recalcular (RB-03, RB-13); la factura involucra dos aggregates. |
| **Factory Method** | `Cotizacion.solicitar()`, `Servicio.programar()`, `Cotizacion.renovar()` | Un aggregate nace solo si se cumplen sus precondiciones (cliente activo, cotización aceptada). |
| **Repository + Data Mapper** | `src/infrastructure/repositorios.py` | El dominio no conoce SQL; los repositorios traducen filas ↔ objetos (ADR-002). |
| **Unit of Work** | `UnidadDeTrabajoSql` | Cada caso de uso es una transacción: todo o nada. |
| **Domain Events + Outbox simple** | `RaizDeAggregate._registrar_evento()`, `CasoDeUso._confirmar()`, `notificaciones.py` | El aviso se guarda junto con el cambio (PA-01, ADR-010). |
| **CQRS básico** | `src/application/consultas.py` + `src/infrastructure/lecturas.py` | Los reportes REP-01 a REP-05 no cargan aggregates ni pueden romper invariantes (ADR-004). |
| **Composition Root / Inyección de dependencias** | `construir_sistema()` en `src/infrastructure/sistema.py` | Un solo lugar arma repositorios, reloj y casos de uso. Las pruebas inyectan un reloj fijo y una base en memoria. |
| **Ports & Adapters** | `src/application/puertos.py` (`Protocol`) | La aplicación define lo que necesita; la infraestructura lo implementa. |

## 5. Aplicación de los principios SOLID

| Principio | Dónde se demuestra | Explicación |
|---|---|---|
| **S** — Responsabilidad única | `ProgramacionDeServicios` (coordinador), `EjecucionDeServicios` (supervisor), `FacturacionDeServicios` (administración) | Los casos de uso se separan por actor (hallazgo S-1 de la U3). Un cambio en la facturación no toca la clase que usa el supervisor; RB-15 separa esas responsabilidades. `rutas.py` solo traduce HTTP; no decide reglas. |
| **O** — Abierto/cerrado | `CalculadoraDePrecio(tarifas, descuento_recurrente)`; `Especificacion` | Las tarifas y el descuento se inyectan (S-2 de la U3): agregar un tipo de inmueble o cambiar la tarifa no modifica el cálculo. Una regla nueva de programación es una clase `Especificacion` más que se combina con `&`, sin editar las existentes. |
| **L** — Sustitución de Liskov | `Conjuncion`, `Disyuncion`, `Negacion` y cada especificación concreta; SQLite y PostgreSQL detrás de la misma `UnidadDeTrabajoSql` | Cualquier especificación se usa donde se espera una `Especificacion`. La suite de integración pasa igual con SQLite y con PostgreSQL: los dos motores son intercambiables para el código. |
| **I** — Segregación de interfaces | `RepositorioServicios`, `RepositorioFacturas`, `LectorDeConsultas` en `puertos.py` y `consultas.py` | Cada repositorio tiene solo los métodos que su aggregate necesita (`existe_para_servicio`, `ocupaciones_de_cuadrilla`). Los reportes viven en `LectorDeConsultas` (S-5 de la U3). |
| **D** — Inversión de dependencias | `CasoDeUso` recibe `uow_factory`, `Reloj` y `GeneradorDeIds` | Los casos de uso dependen de `Protocol`, no de SQLAlchemy. Por eso las pruebas usan `RelojFijo` e `IdsSecuenciales` para que las fechas y los ids sean predecibles. |

## 6. Cambios respecto a la Unidad 3

| En la Unidad 3 (C#) | En el PIA (Python) | Motivo |
|---|---|---|
| Código base en C# con repositorios en memoria | Python/FastAPI con SQLAlchemy y PostgreSQL | El PIA exige una aplicación funcional, desplegada y con base de datos (ADR-005, ADR-006). |
| Excepciones con nombre propio (`CotizacionNoAceptada`, `CuadrillaNoDisponible`…) | `ReglaDeNegocioError` con el **código de la regla** (`RB-02`, `RES-01`…) y tres subtipos para HTTP | El código de la regla en la respuesta hace visible la trazabilidad en Swagger. |
| `DisponibilidadDeCuadrilla` (Domain Service) | Especificación `CuadrillaDisponible` + `Programacion.se_traslapa_con()` | Las ocupaciones las trae el repositorio; la regla queda como una especificación más dentro de `PUEDE_PROGRAMARSE` (H-15). |
| `IPublicadorDeEventos` después de confirmar | Avisos guardados en la misma transacción (`notificaciones`) | Evita perder avisos o avisar cambios que no ocurrieron (ADR-010). |
| `CargoAdicional` como Value Object de la incidencia | Entity con id dentro de `Servicio` | El coordinador autoriza un cargo concreto desde la API; además hay cargos por reprogramación (H-07). |
| Fuera del diseño detallado: US-04, US-10, US-12, US-17, US-21 | Implementadas | El PIA pide los casos de uso principales completos; ahora las 22 historias tienen código y prueba. |

## 7. Riesgos conocidos y trabajo posterior

| Riesgo | Mitigación actual | Trabajo posterior |
|---|---|---|
| Dos coordinadores asignan la misma cuadrilla al mismo tiempo (RES-01) | La especificación revisa el traslape antes de guardar | Bloqueo de la cuadrilla (`SELECT … FOR UPDATE`) |
| Cualquiera puede declarar un rol en `X-Rol` | Documentado como FAL-06 / ADR-009 | Autenticación OAuth2/JWT en `dependencias.py` |
| Los avisos no se envían por correo | Se consultan en `GET /notificaciones` | Proceso de envío que lea la tabla (ADR-010) |
| Servicios recurrentes (H-06) | Cada programación crea un servicio | Generar automáticamente los servicios de una frecuencia recurrente |
| El plan gratuito de Render duerme el servicio | Abrir `/salud` un minuto antes de la demostración | Plan de pago o mantener activo con un monitor |

## 8. Índice de ADRs

| ADR | Decisión |
|---|---|
| [ADR-001](adr/ADR-001-domain-model.md) | Domain Model como patrón de lógica de negocio |
| [ADR-002](adr/ADR-002-repository-unit-of-work.md) | Repository por aggregate y Unidad de Trabajo con SQLAlchemy |
| [ADR-003](adr/ADR-003-incidencia-dentro-de-servicio.md) | Incidencias y cargos dentro del aggregate Servicio |
| [ADR-004](adr/ADR-004-cqrs-basico.md) | CQRS básico: comandos por el dominio, consultas directas |
| [ADR-005](adr/ADR-005-python-fastapi.md) | Python con FastAPI en lugar de C# |
| [ADR-006](adr/ADR-006-postgresql-y-montos.md) | PostgreSQL/SQLite y montos exactos en centavos |
| [ADR-007](adr/ADR-007-docker-y-configuracion.md) | Docker Compose (DB + App + Tests) y variables de entorno |
| [ADR-008](adr/ADR-008-despliegue-render-ci-cd.md) | Despliegue en Render y pipeline CI/CD |
| [ADR-009](adr/ADR-009-roles-por-encabezado.md) | Rol en el encabezado `X-Rol` (sin autenticación) |
| [ADR-010](adr/ADR-010-notificaciones-en-la-transaccion.md) | Notificaciones en la misma transacción |
