# ADR-008 — Despliegue en Render y pipeline CI/CD en GitHub Actions

| Campo | Contenido |
|---|---|
| **Estado** | Aceptada (04/11/2026) |
| **Decisores** | Equipo 12 |

## Contexto
La demostración necesita Swagger activo en producción. El PIA permite Railway, Render, Fly.io o equivalente, y pide un pipeline CI/CD activo. El equipo no tiene presupuesto.

## Alternativas
| Alternativa | Consecuencia |
|---|---|
| Railway | Sencillo, pero su plan gratuito es un crédito limitado. |
| Fly.io | Flexible, pero se configura por terminal y pide tarjeta. |
| **Render** | Plan gratuito con servicio web desde un Dockerfile y PostgreSQL administrado; se configura desde el navegador. |

## Decisión
- Render construye la etapa `produccion` del Dockerfile. La base es un PostgreSQL de Render; su URL interna se pone en `DATABASE_URL`.
- Pipeline `.github/workflows/ci.yml` en cada push o pull request:
  1. `pruebas`: Ruff + pytest con cobertura mínima de 80 % (publica el HTML de cobertura).
  2. `pruebas-postgres`: pruebas de integración contra un PostgreSQL de servicio.
  3. `docker`: `docker compose run tests` y `docker compose up app`, y verifica `/salud` y `/docs`.
  4. `despliegue` (solo `main`): llama al *deploy hook* de Render guardado en el secreto `RENDER_DEPLOY_HOOK`. Si los pasos anteriores fallan, no se despliega.

## Consecuencias
- **Beneficios:** solo llega a producción una versión que pasó todas las pruebas; la URL pública sirve para la defensa.
- **Costos:** el plan gratuito de Render duerme el servicio tras un rato sin uso; la primera petición tarda cerca de un minuto. Antes de la demostración se abre `/salud` para despertarlo.
- **Riesgos:** la base gratuita de Render tiene vigencia limitada; alcanza para el periodo de defensa (9 al 20 de noviembre).

## Trazabilidad
Requisitos del PIA "Calidad" (CI/CD) y "Producción" (despliegue + Swagger)
