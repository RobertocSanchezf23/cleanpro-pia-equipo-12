# ADR-004 — CQRS básico: comandos por el dominio, consultas directas

| Campo | Contenido |
|---|---|
| **Estado** | Aceptada (U3) · Implementada en el PIA |
| **Decisores** | Equipo 12 |

## Contexto
El BRD pide 5 reportes (REP-01 a REP-05) y consultas para varios roles (US-17, US-21, CE-05). Leerlos a través de los aggregates obliga a cargar objetos completos solo para mostrar una tabla y llena los repositorios de métodos de reporte (hallazgo SOLID S-5 de la U3).

## Alternativas
| Alternativa | Consecuencia |
|---|---|
| Leer todo a través de repositorios y aggregates | Un solo modelo, pero lento y con repositorios que mezclan responsabilidades. |
| CQRS completo con bases separadas | Demasiado para el caso; agrega consistencia eventual sin necesidad. |
| **CQRS básico sobre la misma base** | Separación clara sin infraestructura extra. |

## Decisión
- **Comandos:** los métodos de `ServicioDeCotizaciones`, `ProgramacionDeServicios`, `EjecucionDeServicios` y `FacturacionDeServicios` pasan por el dominio y se confirman con la Unidad de Trabajo.
- **Consultas:** `ServicioDeConsultas` (`src/application/consultas.py`) delega en `LectorSql` (`src/infrastructure/lecturas.py`), que hace consultas SQL y devuelve diccionarios planos. Nunca modifican datos.

## Consecuencias
- **Beneficios:** los repositorios quedan pequeños; un reporte no puede romper una invariante; cada lado cambia por razones distintas.
- **Costos:** dos formas de leer los mismos datos.
- **Riesgos:** que alguien use una consulta para escribir. Se mitiga porque `LectorSql` no tiene métodos de escritura ni llama a `commit()`.

## Trazabilidad
REP-01 a REP-05 · US-17, US-19, US-21 · BN-10 · CE-05
