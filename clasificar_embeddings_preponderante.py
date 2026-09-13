# clasificar_embeddings_preponderante.py
# ============================================================
# CLASIFICACIÓN PREPONDERANTE POR EMBEDDINGS — SIN LLM
#
# Regla:
#   1) Si sim_relevance_avg < UMBRAL_RELEVANCIA:
#         categoria = SIN_CLASIFICAR
#   2) Si supera el umbral:
#         categoria = argmax(
#             sim_TECNICISTA_avg,
#             sim_AMBIENTAL_avg,
#             sim_SOCIAL_HUMANA_avg
#         )
#   3) NO existe categoría MIXTO.
#   4) El margen entre la 1.ª y 2.ª similitud se conserva solo
#      como indicador diagnóstico.
#
# No recalcula embeddings. Usa los valores YA existentes en el XLSX.
# Solo usa librerías estándar de Python.
# ============================================================

from pathlib import Path
import csv
import math
import re
import sys
import zipfile
import xml.etree.ElementTree as ET
from collections import Counter, defaultdict

# ------------------------------------------------------------
# CONFIGURACIÓN
# ------------------------------------------------------------

UMBRAL_RELEVANCIA = 0.35

# Solo para marcar casos que luego podrían auditarse.
# NO cambia la categoría preponderante.
UMBRAL_MARGEN_FRONTERA = 0.03

INPUT_CANDIDATES = [
    "dimensiones_2006_2026_final.xlsx",
    "dimensiones_2006_2026_final(2).xlsx",
]

OUTPUT_DOCUMENTOS = "clasificacion_preponderante.csv"
OUTPUT_RESUMEN = "resumen_categorias_preponderantes.csv"
OUTPUT_EVOLUCION = "evolucion_preponderante_por_anio.csv"
OUTPUT_SENSIBILIDAD = "sensibilidad_umbral_relevancia.csv"

SENSIBILIDAD_UMBRALES = [
    0.30, 0.35, 0.40, 0.42, 0.45, 0.47, 0.50
]

NS_MAIN = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
NS_REL = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
NS_PKG_REL = "http://schemas.openxmlformats.org/package/2006/relationships"

M = "{" + NS_MAIN + "}"
R = "{" + NS_REL + "}"
P = "{" + NS_PKG_REL + "}"


# ------------------------------------------------------------
# UTILIDADES XLSX
# ------------------------------------------------------------

def encontrar_input():
    for name in INPUT_CANDIDATES:
        p = Path(name)
        if p.exists():
            return p

    xlsx = list(Path(".").glob("dimensiones_2006_2026_final*.xlsx"))
    if xlsx:
        return xlsx[0]

    raise FileNotFoundError(
        "No encontré dimensiones_2006_2026_final.xlsx en esta carpeta."
    )


def columna_de_ref(ref):
    """A1 -> A, J245 -> J"""
    return "".join(ch for ch in ref if ch.isalpha())


def valor_celda(cell, shared_strings=None):
    """
    Lee números, strings inline y shared strings.
    El archivo actual usa principalmente inline strings.
    """
    tipo = cell.attrib.get("t")

    if tipo == "inlineStr":
        node = cell.find(M + "is")
        if node is None:
            return ""
        return "".join((t.text or "") for t in node.iter(M + "t"))

    v = cell.find(M + "v")
    if v is None or v.text is None:
        return ""

    raw = v.text

    if tipo == "s" and shared_strings is not None:
        try:
            return shared_strings[int(raw)]
        except Exception:
            return raw

    return raw


def cargar_shared_strings(z):
    path = "xl/sharedStrings.xml"
    if path not in z.namelist():
        return None

    strings = []
    root = ET.fromstring(z.read(path))

    for si in root.findall(M + "si"):
        strings.append("".join((t.text or "") for t in si.iter(M + "t")))

    return strings


def ruta_hoja(z, nombre="documentos"):
    workbook = ET.fromstring(z.read("xl/workbook.xml"))
    relroot = ET.fromstring(z.read("xl/_rels/workbook.xml.rels"))

    rels = {
        rel.attrib["Id"]: rel.attrib["Target"]
        for rel in relroot.findall(P + "Relationship")
    }

    rid = None
    for sheet in workbook.find(M + "sheets"):
        if sheet.attrib.get("name") == nombre:
            rid = sheet.attrib.get(R + "id")
            break

    if rid is None:
        raise ValueError(f"No existe la hoja '{nombre}'.")

    target = rels[rid]

    if target.startswith("/"):
        return target.lstrip("/")

    target = target.lstrip("./")
    return "xl/" + target


# ------------------------------------------------------------
# CLASIFICACIÓN
# ------------------------------------------------------------

def clasificar(sim_rel, sim_tec, sim_amb, sim_soc, umbral):
    sims = {
        "TECNICISTA": sim_tec,
        "AMBIENTAL": sim_amb,
        "SOCIAL_HUMANA": sim_soc,
    }

    ordenadas = sorted(
        sims.items(),
        key=lambda kv: kv[1],
        reverse=True
    )

    primera_cat, primera_sim = ordenadas[0]
    segunda_cat, segunda_sim = ordenadas[1]
    margen = primera_sim - segunda_sim

    if sim_rel < umbral:
        categoria = "SIN_CLASIFICAR"
    else:
        categoria = primera_cat

    return {
        "categoria": categoria,
        "sim_max": primera_sim,
        "segunda_categoria": segunda_cat,
        "sim_segunda": segunda_sim,
        "margen": margen,
        "caso_frontera": "SI" if margen < UMBRAL_MARGEN_FRONTERA else "NO",
    }


# ------------------------------------------------------------
# MAIN
# ------------------------------------------------------------

def main():
    input_path = encontrar_input()

    print("=" * 66)
    print("CLASIFICACIÓN PREPONDERANTE POR EMBEDDINGS — SIN LLM")
    print("=" * 66)
    print(f"Archivo: {input_path.name}")
    print(f"Umbral de relevancia: {UMBRAL_RELEVANCIA:.2f}")
    print("Categorías: TECNICISTA / AMBIENTAL / SOCIAL_HUMANA")
    print("MIXTO: NO")
    print()

    resumen = Counter()
    resumen_frontera = Counter()
    por_anio = defaultdict(Counter)
    sensibilidad = {
        u: Counter() for u in SENSIBILIDAD_UMBRALES
    }

    total = 0

    with zipfile.ZipFile(input_path) as z:
        shared = cargar_shared_strings(z)
        sheet_path = ruta_hoja(z, "documentos")

        with z.open(sheet_path) as xml_file, \
             open(OUTPUT_DOCUMENTOS, "w", newline="", encoding="utf-8-sig") as fout:

            writer = csv.writer(fout)
            writer.writerow([
                "source_file",
                "row",
                "title",
                "year",
                "sim_relevance_avg",
                "sim_TECNICISTA_avg",
                "sim_AMBIENTAL_avg",
                "sim_SOCIAL_HUMANA_avg",
                "categoria_preponderante",
                "sim_max_dimension",
                "segunda_categoria",
                "sim_segunda_dimension",
                "margen_primera_segunda",
                "caso_frontera_margen_menor_0_03",
            ])

            # Header esperado:
            # A source_file
            # B row
            # C title
            # D year
            # E abstract
            # F year_num
            # G sim_relevance_avg
            # H sim_TECNICISTA_avg
            # I sim_AMBIENTAL_avg
            # J sim_SOCIAL_HUMANA_avg

            for event, elem in ET.iterparse(xml_file, events=("end",)):
                if elem.tag != M + "row":
                    continue

                numero_fila = int(elem.attrib.get("r", "0"))

                if numero_fila == 1:
                    elem.clear()
                    continue

                vals = {}

                for cell in elem.findall(M + "c"):
                    col = columna_de_ref(cell.attrib.get("r", ""))
                    if col in {"A", "B", "C", "D", "F", "G", "H", "I", "J"}:
                        vals[col] = valor_celda(cell, shared)

                try:
                    source_file = vals.get("A", "")
                    source_row = vals.get("B", "")
                    title = vals.get("C", "")
                    year = int(float(vals.get("F", vals.get("D", ""))))

                    sim_rel = float(vals["G"])
                    sim_tec = float(vals["H"])
                    sim_amb = float(vals["I"])
                    sim_soc = float(vals["J"])
                except Exception:
                    elem.clear()
                    continue

                resultado = clasificar(
                    sim_rel,
                    sim_tec,
                    sim_amb,
                    sim_soc,
                    UMBRAL_RELEVANCIA
                )

                cat = resultado["categoria"]

                resumen[cat] += 1
                por_anio[year][cat] += 1
                por_anio[year]["TOTAL"] += 1

                if resultado["caso_frontera"] == "SI":
                    resumen_frontera[cat] += 1

                # Sensibilidad del umbral de relevancia.
                # La dimensión ganadora NO cambia; solo cambia si el paper
                # queda o no queda clasificado.
                dim_ganadora = max(
                    [
                        ("TECNICISTA", sim_tec),
                        ("AMBIENTAL", sim_amb),
                        ("SOCIAL_HUMANA", sim_soc),
                    ],
                    key=lambda x: x[1]
                )[0]

                for u in SENSIBILIDAD_UMBRALES:
                    sensibilidad[u][
                        dim_ganadora if sim_rel >= u else "SIN_CLASIFICAR"
                    ] += 1

                writer.writerow([
                    source_file,
                    source_row,
                    title,
                    year,
                    f"{sim_rel:.6f}",
                    f"{sim_tec:.6f}",
                    f"{sim_amb:.6f}",
                    f"{sim_soc:.6f}",
                    cat,
                    f"{resultado['sim_max']:.6f}",
                    resultado["segunda_categoria"],
                    f"{resultado['sim_segunda']:.6f}",
                    f"{resultado['margen']:.6f}",
                    resultado["caso_frontera"],
                ])

                total += 1

                if total % 5000 == 0:
                    print(f"Procesados: {total:,}")

                elem.clear()

    # --------------------------------------------------------
    # Resumen total
    # --------------------------------------------------------

    orden_cats = [
        "TECNICISTA",
        "AMBIENTAL",
        "SOCIAL_HUMANA",
        "SIN_CLASIFICAR",
    ]

    with open(OUTPUT_RESUMEN, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(["categoria", "n", "porcentaje", "casos_frontera_margen_lt_0_03"])

        for cat in orden_cats:
            n = resumen[cat]
            pct = (100 * n / total) if total else 0
            w.writerow([
                cat,
                n,
                f"{pct:.4f}",
                resumen_frontera[cat],
            ])

        w.writerow(["TOTAL", total, "100.0000", sum(resumen_frontera.values())])

    # --------------------------------------------------------
    # Evolución por año
    # --------------------------------------------------------

    with open(OUTPUT_EVOLUCION, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow([
            "year",
            "TOTAL",
            "TECNICISTA_n",
            "TECNICISTA_pct",
            "AMBIENTAL_n",
            "AMBIENTAL_pct",
            "SOCIAL_HUMANA_n",
            "SOCIAL_HUMANA_pct",
            "SIN_CLASIFICAR_n",
            "SIN_CLASIFICAR_pct",
        ])

        for year in sorted(por_anio):
            c = por_anio[year]
            n_total = c["TOTAL"]

            row = [year, n_total]

            for cat in orden_cats:
                n = c[cat]
                pct = (100 * n / n_total) if n_total else 0
                row.extend([n, f"{pct:.4f}"])

            w.writerow(row)

    # --------------------------------------------------------
    # Sensibilidad del umbral
    # --------------------------------------------------------

    with open(OUTPUT_SENSIBILIDAD, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow([
            "umbral_relevancia",
            "TECNICISTA",
            "AMBIENTAL",
            "SOCIAL_HUMANA",
            "SIN_CLASIFICAR",
            "CLASIFICADOS",
            "pct_clasificados",
        ])

        for u in SENSIBILIDAD_UMBRALES:
            c = sensibilidad[u]
            clasificados = (
                c["TECNICISTA"]
                + c["AMBIENTAL"]
                + c["SOCIAL_HUMANA"]
            )
            pct = 100 * clasificados / total if total else 0

            w.writerow([
                f"{u:.2f}",
                c["TECNICISTA"],
                c["AMBIENTAL"],
                c["SOCIAL_HUMANA"],
                c["SIN_CLASIFICAR"],
                clasificados,
                f"{pct:.4f}",
            ])

    # --------------------------------------------------------
    # Consola
    # --------------------------------------------------------

    print()
    print("=" * 66)
    print("RESULTADO")
    print("=" * 66)

    for cat in orden_cats:
        n = resumen[cat]
        pct = 100 * n / total if total else 0
        print(f"{cat:18s}: {n:>7,}  ({pct:6.2f} %)")

    print("-" * 66)
    print(f"{'TOTAL':18s}: {total:>7,}")
    print()

    print(
        "Casos frontera por margen < "
        f"{UMBRAL_MARGEN_FRONTERA:.2f}: "
        f"{sum(resumen_frontera.values()):,}"
    )
    print("(siguen teniendo categoría; solo quedan marcados para auditoría)")
    print()

    print("Archivos creados:")
    print(" -", OUTPUT_DOCUMENTOS)
    print(" -", OUTPUT_RESUMEN)
    print(" -", OUTPUT_EVOLUCION)
    print(" -", OUTPUT_SENSIBILIDAD)


if __name__ == "__main__":
    main()
