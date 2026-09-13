# -*- coding: utf-8 -*-
"""
VALIDACION DE LOS TRES EJES EMPIRICOS

Prueba fijada de antemano (antes de correr):
  - los documentos que mencionan encuestas origen-destino o de hogares deben
    concentrarse en el decil superior de INTERACCION_ESTRUCTURADA, y NO en el
    de OBSERVACION_TERRENO ni en el de INTERACCION_EXPERIENCIAL;
  - los documentos con metodos cualitativos, en INTERACCION_EXPERIENCIAL;
  - los documentos de aforos y conteos, en OBSERVACION_TERRENO.
Si la encuesta O-D sigue alta en OBSERVACION_TERRENO, el descriptor no quedo
limpio y hay que volver a redactarlo.

Entrada : dimensiones.xlsx
Salida  : resultado_validacion_ejes.xlsx
"""
import re
from pathlib import Path

import numpy as np
import pandas as pd

ENTRADA = "dimensiones.xlsx"
SALIDA = "resultado_validacion_ejes.xlsx"
TABLAS = Path("outputs/tables")
UMBRAL = 0.35

DIM = ["TECNICISTA", "AMBIENTAL", "SOCIAL_HUMANA"]
EJES = ["OBSERVACION_TERRENO", "INTERACCION_ESTRUCTURADA", "INTERACCION_EXPERIENCIAL"]
VIEJOS = ["PRESENCIA_CAMPO", "CONTACTO_DIRECTO"]
col = lambda n: f"sim_{n}_avg"

OD = [r"\borigin[- ]destination survey(?:s)?\b", r"\bO[- ]?D survey(?:s)?\b",
      r"\bhousehold travel survey(?:s)?\b", r"\bhome[- ]interview survey(?:s)?\b",
      r"\bnational travel survey(?:s)?\b", r"\btravel survey(?:s)?\b",
      r"\broadside interview(?:s)?\b", r"\bon[- ]board (?:interview|survey)(?:s)?\b"]
CUALI = [r"\bethnograph\w*\b", r"\bin[- ]depth interview(?:s)?\b",
         r"\bsemi[- ]structured interview(?:s)?\b", r"\bfocus group(?:s)?\b",
         r"\bparticipant observation\b", r"\bgo[- ]along\b", r"\blife histor(?:y|ies)\b"]
AFORO = [r"\btraffic count(?:s)?\b", r"\bpedestrian count(?:s)?\b", r"\bmanual count(?:s)?\b",
         r"\bturning movement(?:s)?\b", r"\bqueue length(?:s)?\b", r"\bspot speed(?:s)?\b",
         r"\bfield observation(?:s)?\b", r"\bsaturation flow\b"]
rx = lambda ps: re.compile("|".join(f"(?:{p})" for p in ps), re.I)

from cargar_corpus import cargar_corpus, aviso_sin_texto
df, HAY_TEXTO = cargar_corpus()
for c in [col(x) for x in DIM + EJES + VIEJOS] + ["sim_relevance_avg", "year_num"]:
    if c in df.columns:
        df[c] = pd.to_numeric(df[c], errors="coerce")

d = df[(df.year_num >= 2006) & (df.year_num <= 2025) &
       (df.sim_relevance_avg >= UMBRAL)].copy()
Z = (d[[col(x) for x in DIM]] - d[[col(x) for x in DIM]].mean()) / d[[col(x) for x in DIM]].std()
d["CRUDO"] = np.array(DIM)[d[[col(x) for x in DIM]].values.argmax(axis=1)]
d["TIPIF"] = np.array(DIM)[Z.values.argmax(axis=1)]

# La prueba de validacion busca vocabulario en el texto: solo corre con el Excel.
if HAY_TEXTO:
    texto = d["title"].fillna("").astype(str) + " . " + d["abstract"].fillna("").astype(str)
    d["G_OD"] = texto.str.contains(rx(OD), regex=True, na=False)
    d["G_CUALI"] = texto.str.contains(rx(CUALI), regex=True, na=False)
    d["G_AFORO"] = texto.str.contains(rx(AFORO), regex=True, na=False)
else:
    aviso_sin_texto("1. Prueba de validacion de los ejes (encuesta O-D, cualitativo, aforos)")
    d["G_OD"] = d["G_CUALI"] = d["G_AFORO"] = False

print(f"documentos analiticos: {len(d):,}")

# ---- 1. PRUEBA FIJADA DE ANTEMANO -----------------------------------------
filas = []
for g, etiqueta in [("G_OD", "Encuesta O-D / de hogares"),
                    ("G_CUALI", "Metodo cualitativo"),
                    ("G_AFORO", "Aforos y conteos")]:
    fila = {"grupo": etiqueta, "n": int(d[g].sum())}
    for e in EJES:
        dec = d[col(e)] >= d[col(e)].quantile(0.90)
        fila[e] = round(100 * dec[d[g]].mean(), 1)
    filas.append(fila)
prueba = pd.DataFrame(filas)

print("\n" + "=" * 74)
print("1. PRUEBA DE VALIDACION  (% del grupo en el decil superior de cada eje)")
print("=" * 74)
print(prueba.to_string(index=False))
od = prueba[prueba.grupo.str.startswith("Encuesta")].iloc[0]
ok = od["INTERACCION_ESTRUCTURADA"] > od["OBSERVACION_TERRENO"] and \
     od["INTERACCION_ESTRUCTURADA"] > od["INTERACCION_EXPERIENCIAL"]
print(f"\n   >>> La encuesta O-D cae sobre todo en interaccion estructurada: "
      f"{'SI — descriptor limpio' if ok else 'NO — hay que volver a redactar'}")

# ---- 2. CRUCE CON LAS ORIENTACIONES ---------------------------------------
cruces = []
for k, etiqueta in [(0.95, "top 5 %"), (0.90, "top 10 %"), (0.80, "top 20 %")]:
    for e in EJES + [x for x in VIEJOS if col(x) in d.columns]:
        dec = d[col(e)] >= d[col(e)].quantile(k)
        for clf in ["CRUDO", "TIPIF"]:
            r = 100 * dec.groupby(d[clf]).mean()
            cruces.append({
                "corte": etiqueta, "eje": e, "clasificacion": clf.lower(),
                "TECNICISTA": round(r.get("TECNICISTA", np.nan), 1),
                "AMBIENTAL": round(r.get("AMBIENTAL", np.nan), 1),
                "SOCIAL_HUMANA": round(r.get("SOCIAL_HUMANA", np.nan), 1),
                "razon_SOC_TEC": round(r.get("SOCIAL_HUMANA", np.nan) /
                                       max(r.get("TECNICISTA", np.nan), 0.01), 1),
            })
cruce = pd.DataFrame(cruces)
print("\n" + "=" * 74)
print("2. CONCENTRACION POR ORIENTACION, TRES CORTES Y DOS CLASIFICACIONES")
print("=" * 74)
print(cruce[cruce.eje.isin(EJES)].to_string(index=False))

# ---- 2b. POSICION MEDIA EN PERCENTILES (todos los documentos) --------------
# Comparable entre ejes: al trabajar sobre rangos elimina el efecto de que cada
# descriptor se situe a distinta distancia del dominio. No usa ningun corte.
pctl = pd.DataFrame({e: (d[col(e)].rank(pct=True) * 100).groupby(d.CRUDO).mean()
                     for e in EJES}).reindex(DIM).round(1)
pctl_t = pd.DataFrame({e: (d[col(e)].rank(pct=True) * 100).groupby(d.TIPIF).mean()
                       for e in EJES}).reindex(DIM).round(1)
print("\n" + "=" * 74)
print("2b. POSICION MEDIA DE CADA ORIENTACION EN CADA EJE (percentil, n = %d)" % len(d))
print("=" * 74)
print(pctl.to_string())
print("\n   brecha social-humana menos tecnicista, en puntos de percentil:")
print("   ", {e: round(pctl.loc["SOCIAL_HUMANA", e] - pctl.loc["TECNICISTA", e], 1) for e in EJES})

# ---- 3. MEDIAS -------------------------------------------------------------
medias = d.groupby("CRUDO")[[col(e) for e in EJES]].mean().round(4)
medias["n"] = d.groupby("CRUDO").size()
medias_t = d.groupby("TIPIF")[[col(e) for e in EJES]].mean().round(4)
medias_t["n"] = d.groupby("TIPIF").size()

# ---- 4. SEPARACION ENTRE EJES ---------------------------------------------
corr = d[[col(e) for e in EJES + [x for x in VIEJOS if col(x) in d.columns]]].corr().round(3)
print("\n" + "=" * 74)
print("3. CORRELACION ENTRE EJES (sobre el corpus analitico)")
print("=" * 74)
print(corr.to_string())
try:
    cosdesc = pd.read_excel(ENTRADA, sheet_name="coseno_descriptores") if HAY_TEXTO else pd.DataFrame()
    print("\ncoseno entre descriptores: hoja 'coseno_descriptores' del Excel de salida")
except Exception:
    cosdesc = pd.DataFrame()

TABLAS.mkdir(parents=True, exist_ok=True)
if HAY_TEXTO:
    prueba.to_csv(TABLAS / "validacion_ejes_prueba_od.csv", index=False, encoding="utf-8")
cruce[cruce.eje.isin(EJES)].to_csv(TABLAS / "concentracion_ejes_por_orientacion.csv",
                                   index=False, encoding="utf-8")
medias.reset_index().to_csv(TABLAS / "medias_ejes_por_orientacion.csv", index=False, encoding="utf-8")
corr.reset_index().to_csv(TABLAS / "correlacion_entre_ejes.csv", index=False, encoding="utf-8")
pctl.reset_index().to_csv(TABLAS / "percentil_medio_por_orientacion.csv", index=False, encoding="utf-8")

with pd.ExcelWriter(SALIDA, engine="openpyxl") as w:
    prueba.to_excel(w, sheet_name="1_prueba_validacion", index=False)
    cruce.to_excel(w, sheet_name="2_concentracion", index=False)
    medias.reset_index().to_excel(w, sheet_name="3_medias", index=False)
    medias_t.reset_index().to_excel(w, sheet_name="3_medias", index=False,
                                    startrow=len(medias) + 3)
    pctl.reset_index().to_excel(w, sheet_name="2b_percentiles", index=False)
    pctl_t.reset_index().to_excel(w, sheet_name="2b_percentiles", index=False, startrow=len(pctl) + 3)
    corr.reset_index().to_excel(w, sheet_name="4_correlaciones", index=False)
    if not cosdesc.empty:
        cosdesc.to_excel(w, sheet_name="4_correlaciones", index=False,
                         startrow=len(corr) + 3)

print("\nArchivos creados:", SALIDA, "y", TABLAS / "*.csv")
