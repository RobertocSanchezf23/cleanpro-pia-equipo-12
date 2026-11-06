# ADR-002 — Repository por aggregate y Unidad de Trabajo con SQLAlchemy

| Campo | Contenido |
|---|---|
| **Estado** | Aceptada (U3) · Actualizada para el PIA: implementación real con SQLAlchemy 2 |
| **Decisores** | Equipo 12 |

## Contexto
Con Domain Model (ADR-001), los aggregates deben guardarse sin que el dominio conozca SQL. RES-04 exige que la factura quede vinculada al servicio y sus incidencias, y RB-06 que toda incidencia llegue a administración. En la U3 se usaron implementaciones en memoria; el PIA exige persistencia real.

## Alternativas
| Alternativa | Consecuencia |
|---|---|
| Usar la sesión de SQLAlchemy directamente en los endpoints | Rápido, pero mezcla reglas con persistencia (viola DIP) y no se puede probar el dominio sin base de datos. |
| Un repositorio genérico `Repositorio[T]` con CRUD | Menos código, pero sus métodos no hablan el lenguaje del negocio (viola ISP). |
| Mapear los aggregates directamente como modelos ORM | Menos traducción, pero el dominio dependería de SQLAlchemy. |
| **Un Repository por aggregate + Data Mapper + Unidad de Trabajo** | Más código de traducción, pero el dominio queda limpio y cada repositorio expresa lo que el negocio necesita (`ocupaciones_de_cuadrilla`, `existe_para_servicio`). |

## Decisión
- Puertos (interfaces `Protocol`) en `src/application/puertos.py`; implementación en `src/infrastructure/repositorios.py`.
- `SqlCotizaciones`, `SqlServicios`, `SqlFacturas` traducen filas ↔ objetos del dominio (Data Mapper). Las incidencias solo se agregan, nunca se reescriben (evidencia, BN-08).
- `UnidadDeTrabajoSql`: una sesión = una transacción. Si el caso de uso no llama a `commit()`, al salir se hace `rollback()`.
- Las reglas de unicidad más críticas también están en la base: `servicios.cotizacion_id` único (H-06) y `facturas.servicio_id` único (SUP-04).

## Consecuencias
- **Beneficios:** el dominio no conoce la base; las pruebas unitarias no necesitan base de datos; la misma implementación funciona con SQLite (pruebas locales) y PostgreSQL (Docker y Render).
- **Costos:** código de mapeo en ambos sentidos.
- **Riesgos:** dos coordinadores podrían asignar la misma cuadrilla al mismo tiempo (RES-01). La restricción única protege H-06 y SUP-04, pero no el traslape de horarios. **Trabajo posterior:** bloqueo pesimista (`SELECT ... FOR UPDATE`) sobre la cuadrilla.

## Trazabilidad
RB-06, RES-01, RES-04, SUP-04, H-06 · BN-06, BN-08 · PA-01, PA-02 · US-15, US-19, US-20
