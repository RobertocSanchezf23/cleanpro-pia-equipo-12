# ADR-001 — Domain Model como patrón de lógica de negocio

| Campo | Contenido |
|---|---|
| **Estado** | Aceptada (U3, 14/10/2026) · Actualizada para el PIA (04/11/2026) |
| **Decisores** | Equipo 12 |

## Contexto
CleanPro gestiona el ciclo cotización → servicio → incidencias → factura. El BRD tiene 15 reglas (RB-01 a RB-15), 6 restricciones y 6 situaciones excepcionales. Los problemas principales son los errores de facturación (PA-02), los cambios que no llegan a administración (PA-01) y la poca evidencia de incidencias y extras (PA-04). Casi todas las reglas dependen del **estado** de una cotización o de un servicio concreto (RB-02, RB-07, RB-08, RB-11, RB-14).

## Alternativas
| Alternativa | Consecuencia |
|---|---|
| Transaction Script | Simple, pero repetiría las validaciones de estado y el cálculo del precio en cada endpoint, con el riesgo de seguir facturando mal. |
| Table Module | Útil para reportes por tabla, pero no protege las reglas de un servicio individual (acceso denegado, cargos por autorizar). |
| **Domain Model** | Las reglas viven en `Cotizacion`, `Servicio` y `Factura`, que protegen sus transiciones. Cuesta más diseño y requiere Repository y Unit of Work. |

## Decisión
**Domain Model** en `src/domain` para todas las operaciones que cambian estado (CU-01 a CU-05, más reprogramación, ausencias y recálculo). Las consultas y reportes se resuelven sin el modelo (ADR-004). El catálogo de extras, los clientes y las cuadrillas son datos de referencia.

## Consecuencias
- **Beneficios:** el precio se calcula en un solo lugar (`CalculadoraDePrecio`, RB-03); los estados están protegidos (`_exigir_estado`); los nombres del glosario están en el código; el dominio se prueba sin base de datos (123 pruebas unitarias).
- **Costos:** más clases y más diseño previo.
- **Riesgos:** sobremodelar conceptos simples. Se mitiga dejando catálogo, clientes y cuadrillas como entidades de referencia sin reglas.

## Trazabilidad
BN-01, BN-05, BN-07, BN-08 · RB-02, RB-03, RB-07, RB-08, RB-11, RB-13, RB-14 · RES-03, RES-04 · PA-01, PA-02, PA-04 · CU-01 a CU-05
