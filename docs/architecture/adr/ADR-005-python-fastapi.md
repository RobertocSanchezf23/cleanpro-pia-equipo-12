# ADR-005 — Implementar el PIA en Python con FastAPI (en lugar de C#)

| Campo | Contenido |
|---|---|
| **Estado** | Aceptada (04/11/2026). Reemplaza el código base en C# de la Unidad 3 |
| **Decisores** | Equipo 12 |

## Contexto
En la U3 el diseño se expresó en C# con implementaciones en memoria. El PIA exige una aplicación funcional con API REST documentada (Swagger/OpenAPI), base de datos, pruebas con cobertura, contenedores y despliegue. Las Unidades 4 y 5 del curso se trabajaron en Python (FastAPI, pytest, SQLAlchemy, GitHub Actions).

## Alternativas
| Alternativa | Consecuencia |
|---|---|
| Continuar en C# / ASP.NET Core | Reutiliza el código de la U3, pero el equipo no practicó pruebas ni CI en .NET durante el curso. |
| Python con Flask | Ligero, pero la documentación OpenAPI y la validación requieren extensiones. |
| **Python con FastAPI** | Swagger UI y OpenAPI automáticos, validación con Pydantic, el mismo stack que las Unidades 4 y 5. |

## Decisión
Python 3.12 (compatible con 3.11+), FastAPI, Pydantic v2, SQLAlchemy 2, pytest y Ruff. El diseño de la U3 se conserva (aggregates, servicios de dominio, Specification, eventos); los nombres pasan a `snake_case` de Python.

## Consecuencias
- **Beneficios:** Swagger activo sin trabajo extra, lo que la demostración necesita; el equipo domina las herramientas.
- **Costos:** reescribir el código de la U3 y actualizar los diagramas.
- **Riesgos:** Python no tiene tipado estático obligatorio. Se mitiga con anotaciones de tipo, Value Objects inmutables (`frozen=True`) y la suite de pruebas.

## Trazabilidad
Requisito del PIA "Implementación" y "Producción" · ADR-001 a ADR-004 (se conservan)
