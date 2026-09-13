"""
Parser robusto para exports de Scopus CSV, incluso cuando vienen
corrompidos por un guardado intermedio en Excel (locale con ';' como
separador de listas), que envuelve cada fila en una capa extra de
comillas y rompe el quoting interno de los campos con listas (autores,
afiliaciones, keywords).

Estrategia:
1. Quitar el padding de ';' al final de la linea.
2. Si la linea esta envuelta en comillas dobles, quitar esa capa exterior
   y des-escapar las comillas dobles ("" -> ").
3. En vez de intentar parsear TODOS los campos (los de autores/afiliaciones
   quedan irremediablemente mezclados), extraer con regex unicamente los
   campos que necesitamos para el screening/analisis: Title, Year, Abstract.
   Title+Year se localizan con un ancla fiable: '"<title>","<yyyy>","'.
   Abstract se aproxima como el bloque entre comillas mas largo (>=40
   caracteres) que aparece despues de esa ancla.

Si el archivo NO viene corrompido (CSV estandar RFC4180), el mismo
procedimiento tambien funciona porque el "unwrap" de comillas exteriores
simplemente no se aplica y cae a un fallback de parseo csv estandar.
"""
import csv
import re
import json

TITLE_YEAR_RE = re.compile(r'"([^"]{5,400})","((?:19|20)\d{2})","')
LONG_QUOTED_RE = re.compile(r'"([^"]{40,})"')


def _fix_line(line: str) -> str:
    line = line.rstrip("\n").rstrip("\r").rstrip(";")
    if line.startswith('"') and line.endswith('"'):
        inner = line[1:-1]
        inner = inner.replace('""', '"')
        return inner
    return line


def parse_scopus_csv(path: str):
    """Devuelve una lista de dicts: {row, title, year, abstract}."""
    with open(path, encoding="utf-8-sig", errors="replace") as f:
        raw_lines = f.readlines()

    records = []
    for i, raw in enumerate(raw_lines[1:], start=1):  # salta encabezado
        fixed = _fix_line(raw)
        m = TITLE_YEAR_RE.search(fixed)
        if not m:
            try:
                row = next(csv.reader([fixed]))
                records.append({"row": i, "title": None, "year": None,
                                 "abstract": None, "raw_fallback": row[:5]})
            except Exception:
                records.append({"row": i, "title": None, "year": None,
                                 "abstract": None})
            continue
        title, year = m.group(1), m.group(2)
        tail = fixed[m.end():]
        quoted_segments = LONG_QUOTED_RE.findall(tail)
        abstract = max(quoted_segments, key=len) if quoted_segments else None
        records.append({"row": i, "title": title, "year": year, "abstract": abstract})
    return records


if __name__ == "__main__":
    import sys
    path = sys.argv[1]
    out = sys.argv[2] if len(sys.argv) > 2 else "parsed.json"
    recs = parse_scopus_csv(path)
    n_ok = sum(1 for r in recs if r.get("title") and r.get("abstract"))
    print(f"total filas: {len(recs)} | con title+abstract: {n_ok}")
    with open(out, "w", encoding="utf-8") as f:
        json.dump(recs, f, ensure_ascii=False, indent=1)
    print(f"guardado en {out}")
