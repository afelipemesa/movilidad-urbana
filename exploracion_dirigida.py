"""
EXPLORACION BIBLIOGRAFICA DIRIGIDA
Busca literalmente el vocabulario de la etica, la justicia, la responsabilidad
y la ontologia en el corpus relevante, para rastrear donde aparece (y donde no)
dentro del campo.

Se restringe al mismo universo del articulo: 42.208 documentos de 2006 a 2025
con pertinencia >= 0,35. Sin el corte por anio, el corpus incluye 2026 y los
conteos no coinciden con los publicados.

Entrada : dimensiones.xlsx (hoja "documentos")
Salidas : resultado_exploracion_dirigida.xlsx
          outputs/tables/exploracion_dirigida_conteos.csv
          outputs/tables/exploracion_dirigida_cruces.csv
"""
import re
from pathlib import Path

import pandas as pd

ARCHIVO = "dimensiones.xlsx"
UMBRAL = 0.35
SALIDA = "resultado_exploracion_dirigida.xlsx"

PATRONES = {
    "ethic_moral":   r"\b(?:ethic\w*|moral\w*)\b",
    "justicia_mov":  r"\b(?:mobilit\w*|transport\w*)\s+justice\b",
    "responsib":     r"\bresponsib\w*\b",
    "ontolog":       r"\bontolog\w*\b",
    "levinas":       r"\blevinas\b",
}

df = pd.read_excel(ARCHIVO, sheet_name="documentos")
df["sim_relevance_avg"] = pd.to_numeric(df["sim_relevance_avg"], errors="coerce")
df["year_num"] = pd.to_numeric(df["year_num"], errors="coerce")
df = df[(df["sim_relevance_avg"] >= UMBRAL)
        & (df["year_num"] >= 2006) & (df["year_num"] <= 2025)].copy()
print(f"corpus relevante 2006-2025 (>= {UMBRAL}): {len(df):,}")

sims = df[["sim_TECNICISTA_avg", "sim_AMBIENTAL_avg", "sim_SOCIAL_HUMANA_avg"]].apply(pd.to_numeric, errors="coerce")
rev = {"sim_TECNICISTA_avg": "TECNICISTA", "sim_AMBIENTAL_avg": "AMBIENTAL", "sim_SOCIAL_HUMANA_avg": "SOCIAL_HUMANA"}
df["DIM"] = sims.idxmax(axis=1).map(rev)

texto = (df["title"].fillna("").astype(str) + " " + df["abstract"].fillna("").astype(str)).str.lower()
for k, p in PATRONES.items():
    df[k] = texto.str.contains(p, regex=True, na=False)

filas = []
for k in PATRONES:
    n = int(df[k].sum())
    fila = {"termino": k, "n": n, "pct_corpus": round(100 * n / len(df), 3)}
    for d in ["TECNICISTA", "AMBIENTAL", "SOCIAL_HUMANA"]:
        fila[f"n_{d}"] = int(df[df["DIM"] == d][k].sum())
    sub = df[df[k]]
    fila["desde_2018_pct"] = round(100 * (sub["year_num"] >= 2018).mean(), 1) if n else 0
    filas.append(fila)
res = pd.DataFrame(filas)

nj = int(df["justicia_mov"].sum())
cruces = pd.DataFrame([
    {"cruce": "justicia_mov & responsib", "n": int((df["justicia_mov"] & df["responsib"]).sum()), "de_un_total_de": nj},
    {"cruce": "justicia_mov & ontolog",   "n": int((df["justicia_mov"] & df["ontolog"]).sum()),   "de_un_total_de": nj},
    {"cruce": "justicia_mov & levinas",   "n": int((df["justicia_mov"] & df["levinas"]).sum()),   "de_un_total_de": nj},
    {"cruce": "justicia_mov en SOCIAL_HUMANA", "n": int(df[df["DIM"] == "SOCIAL_HUMANA"]["justicia_mov"].sum()), "de_un_total_de": nj},
])

print("\n" + "=" * 88)
print("CONTEOS")
print("=" * 88)
print(res.to_string(index=False))
print("\nCRUCES")
print("-" * 88)
print(cruces.to_string(index=False))

TABLAS = Path("outputs/tables"); TABLAS.mkdir(parents=True, exist_ok=True)
res.to_csv(TABLAS / "exploracion_dirigida_conteos.csv", index=False, encoding="utf-8")
cruces.to_csv(TABLAS / "exploracion_dirigida_cruces.csv", index=False, encoding="utf-8")

with pd.ExcelWriter(SALIDA, engine="openpyxl") as w:
    res.to_excel(w, sheet_name="conteos", index=False)
    cruces.to_excel(w, sheet_name="cruces", index=False)
    cols = [c for c in ["title", "year_num", "DIM"] + list(PATRONES) if c in df.columns]
    df[df[list(PATRONES)].any(axis=1)][cols].to_excel(w, sheet_name="documentos_con_algun_termino", index=False)
print("\nArchivo creado:", SALIDA)
