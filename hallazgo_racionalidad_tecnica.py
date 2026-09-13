"""
HALLAZGO: alcance de la racionalidad tecnico-instrumental en la literatura
sobre movilidad urbana, 2006-2025.

No re-ejecuta la deteccion por criterios linguisticos: reutiliza las columnas
ya calculadas en resultado_v4_6_tridimensional_2006_2025.xlsx y les cruza la
relevancia de clasificacion_preponderante.csv. Corre en segundos.

Produce las tablas que sostienen el hallazgo y, sobre todo, las que lo acotan:
  - prevalencia y robustez frente al umbral de relevancia
  - de que sub-criterio depende realmente el 79% (lo que un revisor va a atacar)
  - penetracion cruzada por orientacion (el nucleo del argumento)
  - evolucion anual cruda Y controlada por longitud de abstract
  - composicion relativa por quinquenio
  - residual = margen de error por abajo

Salida: resultado_hallazgo_racionalidad_tecnica.xlsx
"""
import csv
import statistics
from collections import defaultdict

import openpyxl
import pandas as pd

ENTRADA_XLSX = "resultado_v4_6_tridimensional_2006_2025.xlsx"
ENTRADA_CSV = "clasificacion_preponderante.csv"
SALIDA = "resultado_hallazgo_racionalidad_tecnica.xlsx"

UMBRAL_RELEVANCIA = 0.35
BANDA_CONTROL = (150, 250)   # palabras de abstract, para comparar anios sin sesgo de longitud
ORIS = ["TECNICISTA", "AMBIENTAL", "SOCIAL_HUMANA"]
DIMS = [("TEC", "tecnico_instrumental"),
        ("AMB", "ambiental_ecologica"),
        ("HUM", "apertura_humano_social")]


def p(n, d):
    return round(100 * n / d, 2) if d else 0.0


# ------------------------------------------------------------------
# CARGA
# ------------------------------------------------------------------
rel = {}
with open(ENTRADA_CSV, encoding="utf-8-sig") as f:
    for r in csv.DictReader(f):
        k = (r["title"] or "").strip().lower()
        if k:
            rel[k] = float(r["sim_relevance_avg"])

wb = openpyxl.load_workbook(ENTRADA_XLSX, read_only=True, data_only=True)
ws = wb["detalle_corpus"]
it = ws.iter_rows(values_only=True)
hdr = next(it)
ix = {c: i for i, c in enumerate(hdr)}

F = []
for row in it:
    k = str(row[ix["title"]] or "").strip().lower()
    F.append({
        "rel": rel.get(k, 0.0),
        "anio": int(row[ix["year_num"]]),
        "len": len(str(row[ix["abstract"]] or "").split()),
        "ori": row[ix["ORIENTACION_DOMINANTE"]],
        "TEC": bool(row[ix["RACIONALIDAD_TECNICO_INSTRUMENTAL"]]),
        "AMB": bool(row[ix["RACIONALIDAD_AMBIENTAL_ECOLOGICA"]]),
        "HUM": bool(row[ix["APERTURA_HUMANO_SOCIAL"]]),
        "met": bool(row[ix["METODO_TECNICO_EXPLICITO"]]),
        "sis": bool(row[ix["RACIONALIDAD_SISTEMICA"]]),
        "med": bool(row[ix["MEDIACION_INDIRECTA"]]),
    })
wb.close()

sub = [x for x in F if x["rel"] >= UMBRAL_RELEVANCIA]
N = len(sub)
print(f"corpus 2006-2025: {len(F):,} | con relevancia >= {UMBRAL_RELEVANCIA}: {N:,}")

# ------------------------------------------------------------------
# 1. PREVALENCIA Y ROBUSTEZ
# ------------------------------------------------------------------
prevalencia = pd.DataFrame([{
    "racionalidad": nom,
    "pct_sin_umbral": p(sum(x[k] for x in F), len(F)),
    "pct_con_umbral_035": p(sum(x[k] for x in sub), N),
    "n_con_umbral": sum(x[k] for x in sub),
} for k, nom in DIMS])

# ------------------------------------------------------------------
# 2. DE QUE DEPENDE EL HALLAZGO
# ------------------------------------------------------------------
ntec = sum(x["TEC"] for x in sub)
vias = [("met", "metodo_tecnico_explicito"),
        ("sis", "racionalidad_sistemica"),
        ("med", "mediacion_indirecta_abstracta")]
descomposicion = []
for k, nom in vias:
    c = sum(x[k] for x in sub)
    solo = sum(1 for x in sub if x[k] and not any(x[o] for o, _ in vias if o != k))
    descomposicion.append({
        "via_de_activacion": nom, "n": c, "pct_corpus": p(c, N),
        "pct_de_los_tecnico_instrumentales": p(c, ntec),
        "n_solo_por_esta_via": solo, "pct_solo_por_esta_via": p(solo, ntec),
    })
descomposicion.append({
    "via_de_activacion": "TOTAL (OR de las tres)", "n": ntec, "pct_corpus": p(ntec, N),
    "pct_de_los_tecnico_instrumentales": 100.0,
    "n_solo_por_esta_via": None, "pct_solo_por_esta_via": None,
})
descomposicion = pd.DataFrame(descomposicion)

# ------------------------------------------------------------------
# 3. PENETRACION CRUZADA
# ------------------------------------------------------------------
penetracion = []
for o in ORIS:
    g = [x for x in sub if x["ori"] == o]
    fila = {"orientacion_dominante": o, "n": len(g)}
    for k, nom in DIMS:
        fila[f"pct_{nom}"] = p(sum(x[k] for x in g), len(g))
    fila["pct_residual_no_detectado"] = p(
        sum(1 for x in g if not (x["TEC"] or x["AMB"] or x["HUM"])), len(g))
    penetracion.append(fila)
fila = {"orientacion_dominante": "TOTAL CORPUS", "n": N}
for k, nom in DIMS:
    fila[f"pct_{nom}"] = p(sum(x[k] for x in sub), N)
fila["pct_residual_no_detectado"] = p(
    sum(1 for x in sub if not (x["TEC"] or x["AMB"] or x["HUM"])), N)
penetracion.append(fila)
penetracion = pd.DataFrame(penetracion)

# ------------------------------------------------------------------
# 4. EVOLUCION ANUAL: CRUDA Y CONTROLADA POR LONGITUD
# ------------------------------------------------------------------
por = defaultdict(list)
for x in sub:
    por[x["anio"]].append(x)

lo, hi = BANDA_CONTROL
evol = []
for a in sorted(por):
    g = por[a]
    gc = [x for x in g if lo <= x["len"] <= hi]
    fila = {"anio": a, "n": len(g),
            "mediana_palabras_abstract": statistics.median(x["len"] for x in g)}
    for k, nom in DIMS:
        fila[f"pct_{nom}"] = p(sum(x[k] for x in g), len(g))
    fila["n_banda_control"] = len(gc)
    for k, nom in DIMS:
        fila[f"pct_{nom}_control_longitud"] = p(sum(x[k] for x in gc), len(gc)) if len(gc) >= 40 else None
    evol.append(fila)
evolucion = pd.DataFrame(evol)

def bloque(a0, a1, control=False):
    g = [x for a in por if a0 <= a <= a1 for x in por[a]]
    return [x for x in g if lo <= x["len"] <= hi] if control else g

cambio = []
for k, nom in DIMS:
    g0, g1 = bloque(2006, 2010), bloque(2021, 2025)
    c0, c1 = bloque(2006, 2010, True), bloque(2021, 2025, True)
    crudo = p(sum(x[k] for x in g1), len(g1)) - p(sum(x[k] for x in g0), len(g0))
    ctrl = p(sum(x[k] for x in c1), len(c1)) - p(sum(x[k] for x in c0), len(c0))
    cambio.append({
        "racionalidad": nom,
        "pct_2006_2010": p(sum(x[k] for x in g0), len(g0)),
        "pct_2021_2025": p(sum(x[k] for x in g1), len(g1)),
        "cambio_crudo_pp": round(crudo, 2),
        "pct_2006_2010_control": p(sum(x[k] for x in c0), len(c0)),
        "pct_2021_2025_control": p(sum(x[k] for x in c1), len(c1)),
        "cambio_controlado_pp": round(ctrl, 2),
        "pct_del_cambio_atribuible_a_longitud": round(100 * (crudo - ctrl) / crudo, 1) if crudo else None,
    })
cambio = pd.DataFrame(cambio)

# ------------------------------------------------------------------
# 5. COMPOSICION RELATIVA POR QUINQUENIO
# ------------------------------------------------------------------
composicion = []
for nom, (a0, a1) in [("2006-2010", (2006, 2010)), ("2011-2015", (2011, 2015)),
                      ("2016-2020", (2016, 2020)), ("2021-2025", (2021, 2025))]:
    g = bloque(a0, a1)
    t = {k: sum(x[k] for x in g) for k, _ in DIMS}
    s = sum(t.values())
    fila = {"periodo": nom, "n_documentos": len(g)}
    for k, nombre in DIMS:
        fila[f"share_{nombre}"] = p(t[k], s)
    composicion.append(fila)
composicion = pd.DataFrame(composicion)

# ------------------------------------------------------------------
# 6. LIMITES
# ------------------------------------------------------------------
resid = sum(1 for x in sub if not (x["TEC"] or x["AMB"] or x["HUM"]))
limites = pd.DataFrame([
    {"indicador": "documentos analizados (relevancia >= 0.35)", "valor": N},
    {"indicador": "con racionalidad tecnico-instrumental", "valor": ntec},
    {"indicador": "prevalencia tecnico-instrumental (%)", "valor": p(ntec, N)},
    {"indicador": "residual sin ninguna racionalidad detectada", "valor": resid},
    {"indicador": "residual (%)", "valor": p(resid, N)},
    {"indicador": "techo maximo si todo el residual fuera tecnico (%)", "valor": p(ntec + resid, N)},
])

# ------------------------------------------------------------------
# EXPORTAR
# ------------------------------------------------------------------
with pd.ExcelWriter(SALIDA, engine="openpyxl") as w:
    prevalencia.to_excel(w, sheet_name="1_prevalencia", index=False)
    descomposicion.to_excel(w, sheet_name="2_de_que_depende", index=False)
    penetracion.to_excel(w, sheet_name="3_penetracion_cruzada", index=False)
    evolucion.to_excel(w, sheet_name="4_evolucion_anual", index=False)
    cambio.to_excel(w, sheet_name="5_cambio_y_artefacto", index=False)
    composicion.to_excel(w, sheet_name="6_composicion_relativa", index=False)
    limites.to_excel(w, sheet_name="7_limites", index=False)

for nombre, t in [("1_prevalencia", prevalencia), ("2_de_que_depende", descomposicion),
                  ("3_penetracion_cruzada", penetracion), ("5_cambio_y_artefacto", cambio),
                  ("6_composicion_relativa", composicion), ("7_limites", limites)]:
    print("\n" + "=" * 100)
    print(nombre.upper())
    print("=" * 100)
    print(t.to_string(index=False))

print("\nArchivo creado:", SALIDA)
