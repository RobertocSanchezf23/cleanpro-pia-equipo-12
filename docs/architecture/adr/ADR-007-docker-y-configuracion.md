# ADR-007 — Docker Compose (DB + App + Tests) y configuración por variables de entorno

| Campo | Contenido |
|---|---|
| **Estado** | Aceptada (04/11/2026) |
| **Decisores** | Equipo 12 |

## Contexto
El PIA pide un entorno reproducible con Docker Compose para la base de datos, la aplicación y las pruebas, y separar la configuración del código (12-Factor App). Las credenciales no deben estar en el repositorio.

## Alternativas
| Alternativa | Consecuencia |
|---|---|
| Una sola imagen con todo (app + pytest) | Simple, pero la imagen de producción llevaría herramientas de prueba. |
| **Dockerfile multi-etapa (`base`, `pruebas`, `produccion`)** | Una sola receta; la imagen de producción no incluye pytest ni las pruebas. |
| Archivo de configuración `.ini` en el repositorio | Facilita los secretos filtrados. |
| **Variables de entorno + `.env.example` sin secretos** | El mismo código corre en local, Docker y Render. |

## Decisión
- `Dockerfile` multi-etapa. La etapa `produccion` corre con un usuario sin privilegios y usa `PORT` si la plataforma lo define.
- `docker-compose.yml` con tres servicios: `db` (postgres:16-alpine con healthcheck), `app` (espera a que la base esté sana) y `tests` (corre Ruff y pytest contra la base `cleanpro_pruebas`, separada de la de la aplicación).
- Variables: `DATABASE_URL`, `APP_ENV`, `CARGAR_DATOS_DEMO`, `ZONA_HORARIA` y `POSTGRES_*`. `.env` está en `.gitignore`; `.env.example` solo tiene valores de ejemplo.

## Consecuencias
- **Beneficios:** `docker compose up --build` levanta todo en cualquier computadora; las pruebas nunca borran los datos de la aplicación.
- **Costos:** Docker Desktop pesa y no todas las computadoras lo soportan.
- **Riesgos:** usar los valores por defecto de Compose en un servidor real. Están pensados solo para local; en Render las variables las define la plataforma.

## Trazabilidad
Requisito del PIA "Producción" (Docker Compose, 12-Factor)
