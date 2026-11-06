"""La trazabilidad también se prueba: cada escenario Gherkin debe estar en la matriz y cada prueba
mencionada en la matriz debe existir."""
import re
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
MATRIZ = (RAIZ / "docs" / "trazabilidad.md").read_text(encoding="utf-8")
HISTORIAS = (RAIZ / "docs" / "analisis" / "user-stories.md").read_text(encoding="utf-8")
PRUEBAS = {nombre for archivo in (RAIZ / "tests").rglob("test_*.py")
           for nombre in re.findall(r"def (test_\w+)", archivo.read_text(encoding="utf-8"))}


def test_cada_escenario_gherkin_tiene_fila_en_la_matriz():
    escenarios = set(re.findall(r"Scenario: (US-\d{2} E\d)", HISTORIAS))
    assert len(escenarios) >= 40
    faltantes = sorted(e for e in escenarios if f"| {e} |" not in MATRIZ)
    assert faltantes == []


def test_cada_prueba_citada_en_la_matriz_existe():
    citadas = set(re.findall(r"`(test_\w+)`", MATRIZ))
    assert len(citadas) >= 60
    assert sorted(citadas - PRUEBAS) == []


def test_las_22_historias_y_las_15_reglas_estan_en_la_matriz():
    assert all(f"US-{n:02d}" in MATRIZ for n in range(1, 23))
    assert all(f"RB-{n:02d}" in MATRIZ for n in range(1, 16))
