"""Genera docs/api/openapi.json a partir del código. Uso:  python -m herramientas.exportar_openapi"""
import json
from pathlib import Path

from src.api.main import crear_app

DESTINO = Path(__file__).resolve().parents[1] / "docs" / "api" / "openapi.json"


def main() -> None:
    esquema = crear_app().openapi()
    DESTINO.write_text(json.dumps(esquema, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"{DESTINO} ({len(esquema['paths'])} rutas)")


if __name__ == "__main__":
    main()
