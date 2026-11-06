# Diagramas de arquitectura — CleanPro (PIA)

Los diagramas están en Mermaid: GitHub los dibuja directamente en esta página y el código queda versionado junto al software. Las imágenes PNG de cada uno están en [`img/`](img) para el reporte. Todos los nombres son los del código en `src/`.

Los diagramas de la Unidad 3 (draw.io, diseño en C#) se conservan en [`u3/`](u3) como antecedente. Las diferencias se explican en [decisiones-tecnicas.md](decisiones-tecnicas.md#6-cambios-respecto-a-la-unidad-3).

## 1. Arquitectura por capas

Las dependencias apuntan hacia el dominio. El dominio no importa nada de las otras capas (DIP).

```mermaid
flowchart TB
    subgraph api["src/api — Presentación (FastAPI)"]
        direction LR
        rutas["rutas.py · endpoints REST"] ~~~ esquemas["esquemas.py · Pydantic"] ~~~ main["main.py · errores → 403/404/409/422"]
    end
    subgraph app["src/application — Casos de uso"]
        direction LR
        cot["ServicioDeCotizaciones<br/>CU-01, CU-02"] ~~~ prog["ProgramacionDeServicios<br/>CU-03"] ~~~ ejec["EjecucionDeServicios<br/>CU-04"] ~~~ fact["FacturacionDeServicios<br/>CU-05"] ~~~ cons["ServicioDeConsultas<br/>REP-01..05 (CQRS)"]
        puertos["puertos.py · UnidadDeTrabajo, repositorios, Reloj"] ~~~ notif["notificaciones.py · evento → aviso"]
    end
    subgraph dom["src/domain — Modelo de dominio (sin dependencias externas)"]
        direction LR
        agg["Aggregates<br/>Cotizacion · Servicio · Factura"] ~~~ vo["Value Objects<br/>Dinero · Vigencia · Programacion"] ~~~ spec["Specifications<br/>PUEDE_PROGRAMARSE<br/>SERVICIO_FACTURABLE"] ~~~ ds["Domain Services<br/>CalculadoraDePrecio<br/>GeneradorDeFactura"]
    end
    subgraph infra["src/infrastructure — Infraestructura"]
        direction LR
        repos["repositorios.py<br/>Repository + Data Mapper + UoW"] ~~~ lect["lecturas.py<br/>consultas SQL"] ~~~ db["db.py<br/>tablas SQLAlchemy"] ~~~ cfg["config.py<br/>variables de entorno"] ~~~ sis["sistema.py<br/>composition root"]
    end
    pg[("PostgreSQL (SQLite en local)")]

    api -- "llama a" --> app
    app -- "usa" --> dom
    infra -. "implementa los puertos" .-> app
    infra -- "traduce filas ↔ objetos" --> dom
    infra --> pg
```

## 2. Mapa de dominio (DDD)

```mermaid
flowchart LR
    subgraph AC["Aggregate Cotización"]
        C["«Aggregate Root»<br/>Cotizacion"]
        C --- DI["«VO» DatosDelInmueble"]
        C --- FR["«VO» Frecuencia"]
        C --- EX["«VO» ExtraSolicitado *"]
        C --- EO["«VO» EstimacionOperativa"]
        C --- VG["«VO» Vigencia"]
        C --- D1["«VO» Dinero (precio)"]
    end
    subgraph AS["Aggregate Servicio"]
        S["«Aggregate Root»<br/>Servicio"]
        S --- PR["«VO» Programacion"]
        S --- IN["«Entity» Incidencia *"]
        S --- CA["«Entity» CargoAdicional *"]
    end
    subgraph AF["Aggregate Factura"]
        F["«Aggregate Root»<br/>Factura"]
        F --- CF["«VO» ConceptoFacturado 1..*"]
    end
    REF["Referencia: Cliente · Cuadrilla · Catálogo de extras"]
    CALC{{"«Domain Service»<br/>CalculadoraDePrecio"}}
    GEN{{"«Domain Service»<br/>GeneradorDeFactura"}}

    C -- "cotizacion_id" --> S
    S -- "servicio_id" --> F
    CALC -. "RB-03" .-> C
    CALC -. "RB-13" .-> S
    GEN -. "RB-07, RB-11, RB-14" .-> F
    REF -. "por id" .-> C & S
```

| Evento de dominio | Lo produce | Aviso a | Regla |
|---|---|---|---|
| CotizacionEnviada | Cotizacion | Cliente | US-07 |
| CotizacionAceptada / Rechazada / Vencida | Cotizacion | Coordinador | US-02, US-22 |
| ServicioProgramado / ServicioReprogramado | Servicio | Cliente (y administración al reprogramar) | US-03, US-04, US-10 |
| IncidenciaRegistrada | Servicio | Administración (y coordinador si trae cargo) | RB-06, US-19 |
| CargoAdicionalAutorizado, PrecioRecalculado | Servicio | Administración | RB-12, RB-13, RB-14 |
| ServicioNoRealizado, ServicioTerminado | Servicio | Administración | RB-11, US-14 |
| FacturaEmitida | Factura | Cliente | US-05 |

## 3. Diagrama de clases (UML)

```mermaid
classDiagram
    direction LR
    class RaizDeAggregate {
        -_eventos: list~EventoDominio~
        +extraer_eventos() list
    }
    class Cotizacion {
        +id: str
        +cliente_id: str
        +inmueble: DatosDelInmueble
        +frecuencia: Frecuencia
        +extras: tuple~ExtraSolicitado~
        +estado: EstadoCotizacion
        +estimacion: EstimacionOperativa
        +precio: Dinero
        +vigencia: Vigencia
        +solicitar(...)$ Cotizacion
        +estimar(estimacion, calculadora, rol) Dinero
        +enviar(ahora, rol)
        +aceptar(ahora, rol)
        +rechazar(ahora, rol)
        +actualizar_vencimiento(ahora) bool
        +renovar(nuevo_id, ahora, rol) Cotizacion
    }
    class Servicio {
        +id: str
        +cotizacion_id: str
        +cuadrilla_id: str
        +supervisor: str
        +programacion: Programacion
        +precio_acordado: Dinero
        +estado: EstadoServicio
        +incidencias: list~Incidencia~
        +cargos: list~CargoAdicional~
        +recalculo_pendiente: bool
        +programar(id, solicitud, supervisor, rol)$ Servicio
        +reprogramar(nuevo_inicio, ahora, rol, ocupaciones, cargo) bool
        +registrar_ausencia(ahora, rol, integrante, reasignado, nuevo_inicio)
        +registrar_acceso_denegado(minutos, ahora, rol)
        +registrar_inicio(ahora, rol)
        +registrar_incidencia(tipo, descripcion, ahora, rol) Incidencia
        +autorizar_cargo(cargo_id, rol) CargoAdicional
        +recalcular_precio(calculadora, rol) Dinero
        +registrar_terminacion(ahora, rol)
    }
    class Factura {
        +id: str
        +servicio_id: str
        +conceptos: list~ConceptoFacturado~
        +estado_pago: EstadoPago
        +total() Dinero
        +registrar_pago(ahora, rol)
    }
    class Incidencia {
        +id: str
        +tipo: TipoIncidencia
        +descripcion: str
        +registrada_por: Rol
        +cargo_id: str
    }
    class CargoAdicional {
        +id: str
        +origen: OrigenCargo
        +monto: Dinero
        +autorizado: bool
    }
    class Dinero {
        <<ValueObject>>
        +monto: Decimal
        +por(factor) Dinero
    }
    class Vigencia {
        <<ValueObject>>
        +enviada_en: datetime
        +vence_en() datetime
        +esta_vigente(ahora) bool
    }
    class Programacion {
        <<ValueObject>>
        +inicio: datetime
        +duracion_horas: Decimal
        +fin() datetime
        +se_traslapa_con(otra) bool
    }
    class CalculadoraDePrecio {
        <<DomainService>>
        +precio_base(inmueble, frecuencia) Dinero
        +calcular(inmueble, frecuencia, extras) Dinero
    }
    class GeneradorDeFactura {
        <<DomainService>>
        +generar(id, servicio, ya_facturado, ahora, rol) Factura
    }
    class Especificacion~T~ {
        <<abstract>>
        +regla: str
        +motivo: str
        +se_cumple(candidato) bool
        +incumplidas(candidato) list
        +__and__() Conjuncion
        +__or__() Disyuncion
        +__invert__() Negacion
    }
    RaizDeAggregate <|-- Cotizacion
    RaizDeAggregate <|-- Servicio
    RaizDeAggregate <|-- Factura
    Servicio *-- "0..*" Incidencia
    Servicio *-- "0..*" CargoAdicional
    Servicio *-- Programacion
    Cotizacion *-- Vigencia
    Cotizacion ..> CalculadoraDePrecio
    Servicio ..> CalculadoraDePrecio
    GeneradorDeFactura ..> Servicio
    GeneradorDeFactura ..> Factura
    Especificacion <|-- Conjuncion
    Especificacion <|-- Disyuncion
    Especificacion <|-- Negacion
```

## 4. Máquinas de estados

### Cotización (H-03)
```mermaid
stateDiagram-v2
    [*] --> SOLICITADA: solicitar (US-01)
    SOLICITADA --> SOLICITADA: estimar (US-06, RB-03)
    SOLICITADA --> PENDIENTE: enviar (US-07, RB-01)
    PENDIENTE --> ACEPTADA: aceptar dentro de vigencia (US-02, RB-08)
    PENDIENTE --> RECHAZADA: rechazar (US-02)
    PENDIENTE --> VENCIDA: 5 días hábiles sin respuesta (US-22)
    VENCIDA --> [*]: renovar → nueva cotización SOLICITADA
    ACEPTADA --> [*]: se programa un servicio (RB-02)
    RECHAZADA --> [*]
```

### Servicio (H-02)
```mermaid
stateDiagram-v2
    [*] --> PROGRAMADO: programar (US-08, US-09)
    PROGRAMADO --> PROGRAMADO: reprogramar (RB-09) / ausencia sin reemplazo (RB-10)
    PROGRAMADO --> EN_EJECUCION: registrar inicio (US-13)
    PROGRAMADO --> NO_REALIZADO: acceso denegado ≥ 15 min (RB-11)
    EN_EJECUCION --> EN_EJECUCION: incidencia / autorizar cargo / recalcular (RB-12, RB-13, RB-14)
    EN_EJECUCION --> TERMINADO: registrar terminación sin recálculo pendiente (US-14, RB-13)
    TERMINADO --> [*]: factura: precio + cargos autorizados
    NO_REALIZADO --> [*]: factura: 50 % de cancelación
```

### Factura (H-14)
```mermaid
stateDiagram-v2
    [*] --> PENDIENTE: generar (US-20, RB-07, RB-14, SUP-04)
    PENDIENTE --> PAGADA: registrar pago (administración)
    PAGADA --> [*]
```

## 5. Secuencia CU-03: programar servicio y asignar cuadrilla

```mermaid
sequenceDiagram
    actor Coord as Coordinador
    participant API as POST /servicios
    participant UC as ProgramacionDeServicios
    participant UoW as UnidadDeTrabajoSql
    participant S as Servicio
    participant Spec as PUEDE_PROGRAMARSE
    participant DB as PostgreSQL

    Coord->>API: cotizacion_id, cuadrilla_id, supervisor, inicio (X-Rol: COORDINADOR)
    API->>UC: programar(datos, rol)
    UC->>UoW: cotizaciones.obtener / cuadrillas.obtener
    UC->>UoW: servicios.ocupaciones_de_cuadrilla(cuadrilla)
    UC->>UoW: servicios.existe_para_cotizacion(cotizacion)
    UC->>S: Servicio.programar(id, SolicitudDeProgramacion, supervisor, rol)
    S->>Spec: incumplidas(solicitud)
    Note over Spec: CotizacionAceptada (RB-02) AND CotizacionSinServicio (H-06)<br/>AND FechaFutura AND CuadrillaActiva (RB-04) AND CuadrillaDisponible (RES-01)
    alt alguna regla falla
        Spec-->>S: [primera regla incumplida]
        S-->>API: ReglaDeNegocioError(regla) → 422
    else todas se cumplen
        S-->>UC: Servicio PROGRAMADO + evento ServicioProgramado
        UC->>UoW: servicios.guardar(servicio)
        UC->>UoW: notificaciones.agregar(aviso al cliente, US-03)
        UC->>UoW: commit()
        UoW->>DB: INSERT servicio + notificación (una transacción)
        API-->>Coord: 201 ServicioSalida
    end
```

## 6. Secuencia CU-05: facturar servicio

```mermaid
sequenceDiagram
    actor Admin as Administración
    participant API as POST /facturas
    participant UC as FacturacionDeServicios
    participant UoW as UnidadDeTrabajoSql
    participant G as GeneradorDeFactura
    participant Spec as SERVICIO_FACTURABLE
    participant DB as PostgreSQL

    Admin->>API: servicio_id (X-Rol: ADMINISTRACION)
    API->>UC: facturar(servicio_id, rol)
    UC->>UoW: servicios.obtener(id)
    UC->>UoW: facturas.existe_para_servicio(id)
    UC->>G: generar(id, servicio, ya_facturado, ahora, rol)
    G->>Spec: (TERMINADO OR NO_REALIZADO) AND NOT cargos pendientes AND NOT ya facturado
    alt no es facturable
        Spec-->>API: RB-07 / RB-14 / SUP-04 → 422
    else NO_REALIZADO
        G-->>UC: Factura con concepto CANCELACION = 50 % (RB-11)
    else TERMINADO
        G-->>UC: Factura = precio acordado + cargos autorizados (RES-04)
    end
    UC->>UoW: facturas.guardar + notificación FacturaEmitida (US-05)
    UC->>UoW: commit()
    UoW->>DB: INSERT factura + conceptos + notificación
    API-->>Admin: 201 FacturaSalida (estado de pago PENDIENTE)
```

## 7. Despliegue y CI/CD

```mermaid
flowchart LR
    dev["Equipo<br/>(commit en GitHub)"] --> gh["GitHub<br/>repositorio"]
    gh --> ci["GitHub Actions"]
    subgraph ci_jobs["Pipeline .github/workflows/ci.yml"]
        j1["pruebas<br/>Ruff + pytest + cobertura ≥ 80 %"]
        j2["pruebas-postgres<br/>integración con PostgreSQL"]
        j3["docker<br/>compose: tests + app /salud"]
        j4["despliegue<br/>deploy hook de Render"]
        j1 & j2 --> j3 --> j4
    end
    ci --> ci_jobs
    j4 --> render["Render<br/>Web Service (Dockerfile)"]
    render --- rpg[("Render PostgreSQL")]
    usuario["Profesor / cliente<br/>navegador"] --> sw["https://…onrender.com/docs<br/>Swagger UI"]
    sw --> render

    subgraph local["Docker Compose (local)"]
        cdb[("db<br/>postgres:16")]
        capp["app<br/>uvicorn :8000"]
        ctest["tests<br/>pytest → cleanpro_pruebas"]
        capp --> cdb
        ctest --> cdb
    end
```
