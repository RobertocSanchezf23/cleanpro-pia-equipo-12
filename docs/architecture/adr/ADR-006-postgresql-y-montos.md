# ADR-006 — PostgreSQL en producción, SQLite en desarrollo y montos en centavos

| Campo | Contenido |
|---|---|
| **Estado** | Aceptada (04/11/2026) |
| **Decisores** | Equipo 12 |

## Contexto
El PIA exige persistencia real y Docker Compose con una base de datos. El principal problema de CleanPro es facturar mal (PA-02); un error de redondeo en los montos sería justo ese defecto. Además, el equipo necesita trabajar en su computadora sin instalar un servidor de base de datos.

## Alternativas
| Alternativa | Consecuencia |
|---|---|
| Solo SQLite | Fácil, pero no es una base de producción y Render no conserva archivos entre despliegues. |
| Solo PostgreSQL | Realista, pero obliga a instalarlo o usar Docker para cualquier prueba. |
| **PostgreSQL en Docker/Render y SQLite en local, con la misma capa SQLAlchemy** | Cada entorno usa lo adecuado; `DATABASE_URL` decide. |
| Montos `float` | Errores de redondeo (0.1 + 0.2 ≠ 0.3). |
| **Montos `Decimal` en el dominio y centavos enteros en la base** | Exactos en ambos motores. |

## Decisión
- `DATABASE_URL` elige el motor. Sin la variable se usa `sqlite:///./cleanpro.db`. `normalizar_url()` convierte `postgres://` (formato de Render) a `postgresql+psycopg://`.
- El Value Object `Dinero` usa `Decimal` con redondeo comercial (`ROUND_HALF_UP`) a 2 decimales. La base guarda centavos (`INTEGER`) y las cantidades decimales (m², horas) como texto exacto.
- Las pruebas de integración usan SQLite en memoria o, si existe `TEST_DATABASE_URL`, PostgreSQL. En CI y en Docker se ejecutan contra PostgreSQL.

## Consecuencias
- **Beneficios:** exactitud en todos los montos (CE-01); el mismo código y las mismas pruebas en los dos motores.
- **Costos:** conversión centavos ↔ `Dinero` en los repositorios.
- **Riesgos:** diferencias sutiles entre motores. Se mitigan corriendo las pruebas de integración también en PostgreSQL (job `pruebas-postgres` del pipeline).

## Trazabilidad
PA-02, CE-01, RES-04 · RB-03, RB-11 (cálculos con decimales)
