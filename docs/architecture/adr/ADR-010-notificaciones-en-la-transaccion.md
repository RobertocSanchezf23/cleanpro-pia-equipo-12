# ADR-010 — Las notificaciones se guardan en la misma transacción que el cambio

| Campo | Contenido |
|---|---|
| **Estado** | Aceptada (04/11/2026). Concreta la publicación de eventos propuesta en ADR-002 |
| **Decisores** | Equipo 12 |

## Contexto
PA-01 ("los cambios no llegan a administración") es un problema central del BRD. En la Actividad 5 se encontró un riesgo de consistencia: un pedido quedaba confirmado aunque el paso siguiente fallara. Si una incidencia se guarda pero su aviso se pierde, o el aviso sale de algo que se deshizo, se repite PA-01.

## Alternativas
| Alternativa | Consecuencia |
|---|---|
| Enviar el aviso (correo o mensaje) dentro del caso de uso | Si el envío falla después de guardar, el aviso se pierde; si falla antes, se pierde el cambio. |
| Bus de mensajes externo | Demasiada infraestructura para el caso. |
| **Guardar el aviso como registro (tabla `notificaciones`) en la misma transacción** | Patrón *outbox* simplificado: o se guardan los dos o ninguno. |

## Decisión
Los aggregates registran eventos de dominio. Al final de cada caso de uso, `CasoDeUso._confirmar()` (`src/application/base.py`) convierte cada evento en avisos con `notificaciones_para()` y los agrega a la Unidad de Trabajo **antes** del `commit()`. La API los expone en `GET /notificaciones`. El envío real por correo o SMS queda fuera del alcance (FAL-07).

## Consecuencias
- **Beneficios:** no puede existir una incidencia sin su aviso a administración, ni un aviso de algo que no ocurrió (CE-04). Es fácil de probar.
- **Costos:** los avisos se consultan; no llegan solos al teléfono.
- **Trabajo posterior:** un proceso que lea la tabla y envíe correos, marcando cada aviso como enviado.

## Trazabilidad
PA-01, BN-06, CE-04 · RB-06 · US-03, US-05, US-19
