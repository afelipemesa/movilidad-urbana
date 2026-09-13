# -*- coding: utf-8 -*-
"""
REGENERA LAS TABLAS Y LAS FIGURAS PUBLICADAS

Funciona de dos maneras, segun lo que haya en la carpeta:

  CLON LIMPIO — solo con data/derived/documentos_scores.csv.gz
    Regenera las figuras del articulo, la Tabla 1 y las tablas de percentiles,
    concentracion, correlaciones y sensibilidad del umbral. Es decir, todas las
    cifras del articulo que se calculan sobre las puntuaciones.

  CON dimensiones.xlsx — la salida completa del paso 1, que no se publica
    Regenera ademas lo que exige el texto de los documentos: la prueba de
    validacion de los ejes, la muestra de frontera del umbral, la exploracion
    bibliografica dirigida y el propio dataset derivado.

Cada paso dice de donde leyo. Los que no pueden correr se saltan con aviso.
"""
import subprocess
import sys
from pathlib import Path

HAY_EXCEL = Path("dimensiones.xlsx").exists()
HAY_DERIVADO = Path("data/derived/documentos_scores.csv.gz").exists()

if not HAY_EXCEL and not HAY_DERIVADO:
    sys.exit("No hay ni dimensiones.xlsx ni data/derived/documentos_scores.csv.gz.")

#  (titulo, script, necesita_excel)
PASOS = [
    ("Dataset derivado",                   "generar_dataset_derivado.py",  True),
    ("Identificadores del corpus",         "generar_identificadores.py",   True),
    ("Tablas de validacion",               "validar_ejes_empiricos.py",    False),
    ("Sensibilidad del umbral",            "sensibilidad_umbral.py",       False),
    ("Exploracion bibliografica dirigida", "exploracion_dirigida.py",      True),
    ("Figuras y tablas",                   "figuras.py",                   False),
]

print("=" * 70)
print("FUENTE:", "dimensiones.xlsx (completa)" if HAY_EXCEL
      else "data/derived/documentos_scores.csv.gz (sin texto)")
print("=" * 70)

saltados = []
for titulo, script, necesita_excel in PASOS:
    if necesita_excel and not HAY_EXCEL:
        saltados.append((titulo, script))
        continue
    print("\n" + "=" * 70)
    print(titulo.upper(), f"  ({script})")
    print("=" * 70)
    if subprocess.run([sys.executable, script]).returncode != 0:
        sys.exit(f"\n{script} termino con error.")

print("\n" + "=" * 70)
print("TERMINADO")
print("=" * 70)
for p in sorted(Path("outputs").rglob("*")) + sorted(Path("data/derived").glob("*.gz")):
    if p.is_file():
        print(f"  {p}")

if saltados:
    print("\nPasos omitidos: necesitan dimensiones.xlsx, que no se publica")
    print("(30-45 MB con titulos y resumenes de Scopus). Se obtiene con el")
    print("paso 1 del README, a partir de las exportaciones de Scopus.")
    for titulo, script in saltados:
        print(f"  - {titulo}  ({script})")
