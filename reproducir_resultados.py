# -*- coding: utf-8 -*-
"""
REPRODUCE TODO LO PUBLICADO A PARTIR DE dimensiones.xlsx

Genera, en este orden:
  data/derived/documentos_scores.csv.gz   dataset derivado publicable
  outputs/tables/*.csv                    tablas de validacion y sensibilidad
  outputs/figures/figura*.png              Figuras 1, 2 y 3 del articulo

No recalcula embeddings: parte de la salida del paso 1. Si aun no tienes
dimensiones.xlsx, corre antes run_dimension_embeddings.py con
descriptors/dimensiones.json (ver README, paso 1).
"""
import subprocess
import sys
from pathlib import Path

PASOS = [
    ("Dataset derivado", "generar_dataset_derivado.py"),
    ("Tablas de validacion", "validar_ejes_empiricos.py"),
    ("Sensibilidad del umbral", "sensibilidad_umbral.py"),
    ("Exploracion bibliografica dirigida", "exploracion_dirigida.py"),
    ("Figuras y tablas", "figuras.py"),
]

if not Path("dimensiones.xlsx").exists():
    sys.exit("Falta dimensiones.xlsx. Corre antes el paso 1 (ver README).")

for titulo, script in PASOS:
    print("\n" + "=" * 70)
    print(titulo.upper(), f"  ({script})")
    print("=" * 70)
    r = subprocess.run([sys.executable, script])
    if r.returncode != 0:
        sys.exit(f"\n{script} termino con error.")

print("\n" + "=" * 70)
print("TODO REPRODUCIDO")
print("=" * 70)
for p in sorted(Path("outputs").rglob("*")) + [Path("data/derived/documentos_scores.csv.gz")]:
    if p.is_file():
        print(f"  {p}")
