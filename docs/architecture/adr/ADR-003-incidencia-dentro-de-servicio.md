# ADR-003 — Incidencias y cargos adicionales dentro del aggregate Servicio

| Campo | Contenido |
|---|---|
| **Estado** | Aceptada (U3) · Se mantiene en el PIA; `CargoAdicional` pasa a ser Entity con id propio |
| **Decisores** | Equipo 12 |

## Contexto
Varias reglas relacionan al servicio con todas sus incidencias a la vez: RES-03 (las incidencias se documentan antes de terminar), RB-14 (no facturar con cargos sin autorizar), RB-11 (el acceso denegado cambia el estado del servicio), RB-13 (un recálculo pendiente impide terminar) y SUP-03 (cada incidencia pertenece a un solo servicio).

## Alternativas
| Alternativa | Consecuencia |
|---|---|
| Incidencia como aggregate propio | Aggregates más pequeños, pero RB-11, RB-13 y RB-14 tendrían que coordinar dos aggregates en la misma operación. |
| **Incidencia y CargoAdicional dentro de Servicio** | El servicio protege todas sus reglas en una sola transacción. Cuesta cargar el servicio completo. |

## Decisión
`Incidencia` y `CargoAdicional` son entities internas de `Servicio`. Solo se crean o modifican desde la raíz: `registrar_incidencia()`, `registrar_acceso_denegado()`, `registrar_ausencia()` y `autorizar_cargo()`. En el PIA, el cargo tiene id propio (`SRV-…-C1`) porque el coordinador autoriza **un** cargo concreto desde la API, y puede venir de un servicio adicional, de un material especial o de una reprogramación de última hora (H-07, H-10).

## Consecuencias
- **Beneficios:** `SERVICIO_FACTURABLE` revisa los cargos sin consultar otra fuente; no hay incidencias sueltas; el evento `IncidenciaRegistrada` sale de la raíz.
- **Costos:** cada operación carga todas las incidencias del servicio (son pocas por servicio).
- **Riesgos:** supervisor y coordinador modificando el mismo servicio a la vez. **Trabajo posterior:** concurrencia optimista con una columna de versión.

## Trazabilidad
RB-06, RB-11, RB-12, RB-13, RB-14 · RES-03 · SUP-03 · US-11, US-12, US-15, US-16 · PA-01, PA-04
