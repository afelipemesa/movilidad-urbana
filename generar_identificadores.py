# -*- coding: utf-8 -*-
"""
IDENTIFICADORES DEL CORPUS

Reconstruye el corpus exactamente como lo construye run_dimension_embeddings.py
(mismo orden de archivos, mismo filtro title+abstract, misma eliminacion de
duplicados por titulo normalizado) y extrae de cada fila el EID y el DOI.

Publica identificadores, no texto: permite que cualquiera con acceso a Scopus
reconstruya el corpus documento a documento sin redistribuir contenido con
licencia.

Salida : data/derived/corpus_identificadores.csv.gz
"""
import csv, gzip, hashlib, re, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from parse_scopus import parse_scopus_csv, _fix_line

ARCHIVOS = ["2006-2019.csv", "2020-2023.csv", "2024-2025.csv", "2026.csv"]
SALIDA = Path("data/derived/corpus_identificadores.csv.gz")
PUBLICADO = Path("data/derived/documentos_scores.csv.gz")

EID_RE = re.compile(r"2-s2\.0-\d+")
DOI_RE = re.compile(r'"(10\.\d{4,9}/[^"]{1,200})"')

def ids_por_linea(path):
    """EID y DOI de cada fila del CSV, en el mismo orden que parse_scopus_csv."""
    out = []
    with open(path, encoding="utf-8-sig", errors="replace") as f:
        f.readline()                      # encabezado
        for raw in f:
            fixed = _fix_line(raw)
            e = EID_RE.search(fixed)
            d = DOI_RE.search(fixed)
            out.append((e.group(0) if e else "", d.group(1) if d else ""))
    return out

registros = []
for nombre in ARCHIVOS:
    recs = parse_scopus_csv(nombre)
    ids = ids_por_linea(nombre)
    usables = 0
    for r in recs:
        if not (r.get("title") and r.get("abstract")):
            continue
        eid, doi = ids[r["row"] - 1] if r["row"] - 1 < len(ids) else ("", "")
        registros.append({"title": r["title"], "year": r["year"], "eid": eid, "doi": doi})
        usables += 1
    print(f"{nombre:16s} {usables:7,} documentos utilizables")

# misma deduplicacion que run_dimension_embeddings.py
vistos, dedup, dupes = set(), [], 0
for r in registros:
    k = (r["title"] or "").strip().lower()
    if k in vistos:
        dupes += 1
        continue
    vistos.add(k)
    dedup.append(r)
print(f"\nduplicados removidos : {dupes:,}")
print(f"corpus final         : {len(dedup):,}")

# El doc_id NO se reasigna aqui: se toma del dataset ya publicado, uniendo por
# title_hash. Asi los dos archivos casan fila a fila por cualquiera de las dos
# columnas, sin depender del orden interno con que se escribio el Excel.
import pandas as pd

for r in dedup:
    r["title_hash"] = hashlib.sha256(
        (r["title"] or "").strip().lower().encode("utf-8")).hexdigest()

pub = pd.read_csv(PUBLICADO, usecols=["doc_id", "title_hash"])
mapa = dict(zip(pub.title_hash, pub.doc_id))

faltan = [r for r in dedup if r["title_hash"] not in mapa]
if faltan:
    raise SystemExit(f"ERROR: {len(faltan)} documentos no estan en {PUBLICADO}. "
                     "El corpus reconstruido no coincide con el publicado.")

SALIDA.parent.mkdir(parents=True, exist_ok=True)
filas = sorted(dedup, key=lambda r: mapa[r["title_hash"]])
with gzip.open(SALIDA, "wt", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["doc_id", "title_hash", "year", "eid", "doi"])
    for r in filas:
        w.writerow([mapa[r["title_hash"]], r["title_hash"], r["year"], r["eid"], r["doi"]])

con_eid = sum(1 for r in dedup if r["eid"])
con_doi = sum(1 for r in dedup if r["doi"])
print(f"con EID              : {con_eid:,} ({100*con_eid/len(dedup):.1f} %)")
print(f"con DOI              : {con_doi:,} ({100*con_doi/len(dedup):.1f} %)")
print(f"\nArchivo creado       : {SALIDA} ({SALIDA.stat().st_size/1e6:.1f} MB)")
