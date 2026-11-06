# ADR-009 — Rol de la operación en el encabezado X-Rol (sin autenticación)

| Campo | Contenido |
|---|---|
| **Estado** | Aceptada (04/11/2026) |
| **Decisores** | Equipo 12 |

## Contexto
RB-15 define qué rol puede hacer cada operación (solo el coordinador autoriza cargos y reprogramaciones; administración solo factura y consulta). El BRD no incluye gestión de usuarios ni inicio de sesión, y el PIA evalúa reglas de negocio, no seguridad de acceso.

## Alternativas
| Alternativa | Consecuencia |
|---|---|
| Sin roles | Incumple RB-15. |
| Autenticación completa (usuarios, contraseñas, JWT) | Fuera del alcance del BRD; agregaría mucho código sin relación con las reglas del negocio. |
| **El cliente de la API declara el rol en `X-Rol` y el dominio valida el permiso** | RB-15 queda en el dominio y se prueba; la autenticación puede agregarse después sin tocar las reglas. |

## Decisión
Cada endpoint que cambia estado recibe `X-Rol`. La API lo convierte en el enum `Rol` y lo pasa al dominio, que llama a `exigir_rol()` y responde `403` si no corresponde. Se documenta como FAL-06 en el BRD.

## Consecuencias
- **Beneficios:** las reglas de autorización están junto a las reglas de negocio y tienen pruebas; Swagger permite probar cada rol.
- **Riesgos:** cualquiera que conozca la API puede declarar el rol que quiera. **No debe usarse así en producción real.** Trabajo posterior: obtener el rol de un token firmado (OAuth2/JWT) en `src/api/dependencias.py` sin cambiar el dominio.

## Trazabilidad
RB-15 · FAL-06, H-13 · US-04 E3, US-06 E4, US-11 E2
