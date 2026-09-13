# -*- coding: utf-8 -*-
"""
DATASET DERIVADO PUBLICABLE

Convierte la salida completa del paso 1 en el unico archivo de datos que
puede publicarse: un registro por documento con el anio y las similitudes
coseno promediadas entre los tres modelos.

NO contiene titulos, resumenes ni identificadores de Scopus. En su lugar
escribe `title_hash`, SHA-256 del titulo normalizado (minusculas, sin espacios
en los extremos), que permite verificar la correspondencia documento a
documento sin publicar ningun texto con licencia.

`doc_id` es el numero de fila del corpus, que se construye siempre igual:
    2006-2019.csv -> 2020-2023.csv -> 2024-2025.csv -> 2026.csv
    -> eliminacion de duplicados por titulo normalizado
    -> 53.105 documentos numerados 1..53.105

Entrada : dimensiones.xlsx
Salida  : data/derived/documentos_scores.csv.gz
"""
import hashlib
from pathlib import Path

import pandas as pd

ENTRADA = "dimensiones.xlsx"
SALIDA = Path("data/derived/documentos_scores.csv.gz")

COLUMNAS = [
    ("sim_relevance_avg", "sim_relevance"),
    ("sim_TECNICISTA_avg", "sim_TECNICISTA"),
    ("sim_AMBIENTAL_avg", "sim_AMBIENTAL"),
    ("sim_SOCIAL_HUMANA_avg", "sim_SOCIAL_HUMANA"),
    ("sim_OBSERVACION_TERRENO_avg", "sim_OBSERVACION_TERRENO"),
    ("sim_INTERACCION_ESTRUCTURADA_avg", "sim_INTERACCION_ESTRUCTURADA"),
    ("sim_INTERACCION_EXPERIENCIAL_avg", "sim_INTERACCION_EXPERIENCIAL"),
    ("sim_PRESENCIA_CAMPO_avg", "sim_PRESENCIA_CAMPO"),
    ("sim_CONTACTO_DIRECTO_avg", "sim_CONTACTO_DIRECTO"),
]

df = pd.read_excel(ENTRADA, sheet_name="documentos")

out = pd.DataFrame({"doc_id": range(1, len(df) + 1)})
out["title_hash"] = (
    df["title"].fillna("").astype(str).str.strip().str.lower()
    .map(lambda t: hashlib.sha256(t.encode("utf-8")).hexdigest())
)
out["year"] = pd.to_numeric(df["year_num"], errors="coerce").astype("Int64")
for origen, destino in COLUMNAS:
    if origen in df.columns:
        out[destino] = pd.to_numeric(df[origen], errors="coerce")

SALIDA.parent.mkdir(parents=True, exist_ok=True)
out.to_csv(SALIDA, index=False, compression="gzip", encoding="utf-8")

filtradas = [d for _, d in COLUMNAS if d in out.columns]
print(f"documentos      : {len(out):,}")
print(f"columnas        : {list(out.columns)}")
print(f"hashes unicos   : {out.title_hash.nunique():,}")
print(f"texto publicado : ninguno (ni titulos ni resumenes)")
print(f"\nArchivo creado  : {SALIDA}  ({SALIDA.stat().st_size/1e6:.1f} MB)")
