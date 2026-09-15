# -*- coding: utf-8 -*-
"""
REPRODUCE EL ANALISIS COMPLETO DEL ARTICULO, DESDE EL CORPUS

Corre los siete pasos en orden, empezando por el corpus publicado en
data/corpus/: calculo de embeddings, clasificacion preponderante,
exploracion bibliografica dirigida, sensibilidad de los descriptores y del
umbral, validacion de los ejes empiricos, y las figuras y tablas finales.

Si dimensiones.xlsx (la salida del paso 1) ya existe en esta carpeta, no se
recalcula: ese es el unico paso que toma tiempo (9h en CPU, 20-30 min en
GPU -- ver "Entorno de ejecucion recomendado" en el README). Borralo primero
si quieres forzar un recalculo completo desde cero.

Cada paso dice de donde leyo. Si alguno termina en error, el script se
detiene ahi mismo y lo indica.
"""
import subprocess
import sys
from pathlib import Path

HAY_EXCEL = Path("dimensiones.xlsx").exists()

#  (titulo, script)
PASOS = [
    ("Clasificacion preponderante",         "clasificar_embeddings_preponderante.py"),
    ("Exploracion bibliografica dirigida",  "exploracion_dirigida.py"),
    ("Sensibilidad de los descriptores",    "sensibilidad_descriptores.py"),
    ("Sensibilidad del umbral",             "sensibilidad_umbral.py"),
    ("Validacion de los ejes empiricos",    "validar_ejes_empiricos.py"),
    ("Figuras y tablas finales",            "figuras.py"),
]

print("=" * 70)
if HAY_EXCEL:
    print("dimensiones.xlsx ya existe: se reutiliza (paso 1 omitido).")
else:
    print("PASO 1 -- CALCULO DE EMBEDDINGS  (run_dimension_embeddings.py)")
    print("Lee automaticamente los .csv de data/corpus/. Puede tardar horas")
    print("en CPU; ver 'Entorno de ejecucion recomendado' en el README para GPU.")
print("=" * 70)

if not HAY_EXCEL:
    if subprocess.run([sys.executable, "run_dimension_embeddings.py"]).returncode != 0:
        sys.exit("\nrun_dimension_embeddings.py termino con error.")

for titulo, script in PASOS:
    print("\n" + "=" * 70)
    print(titulo.upper(), f"  ({script})")
    print("=" * 70)
    if subprocess.run([sys.executable, script]).returncode != 0:
        sys.exit(f"\n{script} termino con error.")

print("\n" + "=" * 70)
print("TERMINADO -- pipeline completo, desde el corpus hasta las figuras")
print("=" * 70)
for p in sorted(Path("outputs").rglob("*")):
    if p.is_file():
        print(f"  {p}")
