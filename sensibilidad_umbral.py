# -*- coding: utf-8 -*-
"""
SENSIBILIDAD DEL UMBRAL DE PERTINENCIA

El umbral de 0,35 no es un estandar de sentence-transformers: es un umbral
operativo definido para este corpus. Este script lo somete a tres pruebas.

  1. Distribucion de la pertinencia: donde cae 0,35 dentro del corpus.
  2. Sensibilidad: cuantos documentos quedan y como se reparten las tres
     orientaciones con umbrales de 0,30 a 0,50.
  3. Frontera: muestra de titulos por encima y por debajo del corte, para
     revision manual.
  4. Robustez de la Figura 3: la escalera de los tres ejes recalculada
     entera con cada umbral.

Entrada : dimensiones.xlsx
Salidas : outputs/tables/umbral_*.csv
"""
from pathlib import Path

import numpy as np
import pandas as pd

ENTRADA = "dimensiones.xlsx"
TABLAS = Path("outputs/tables")
UMBRALES = [0.30, 0.35, 0.40, 0.45, 0.50]

DIM = ["TECNICISTA", "AMBIENTAL", "SOCIAL_HUMANA"]
EJES = ["OBSERVACION_TERRENO", "INTERACCION_ESTRUCTURADA", "INTERACCION_EXPERIENCIAL"]
col = lambda n: f"sim_{n}_avg"

df = pd.read_excel(ENTRADA, sheet_name="documentos")
for c in [col(x) for x in DIM + EJES] + ["sim_relevance_avg", "year_num"]:
    df[c] = pd.to_numeric(df[c], errors="coerce")
r = df["sim_relevance_avg"]
base = df[(df.year_num >= 2006) & (df.year_num <= 2025)].copy()
TABLAS.mkdir(parents=True, exist_ok=True)

# ---- 1. DISTRIBUCION --------------------------------------------------------
dist = pd.DataFrame([{
    "n": len(r), "minimo": round(r.min(), 3), "p5": round(r.quantile(.05), 3),
    "p10": round(r.quantile(.10), 3), "mediana": round(r.median(), 3),
    "p95": round(r.quantile(.95), 3), "maximo": round(r.max(), 3),
    "media": round(r.mean(), 3), "desviacion": round(r.std(), 3),
    "percentil_de_0_35": round(100 * (r < 0.35).mean(), 1),
    "desviaciones_bajo_la_media": round((0.35 - r.mean()) / r.std(), 2),
}])
dist.to_csv(TABLAS / "umbral_distribucion.csv", index=False, encoding="utf-8")
print("1. DISTRIBUCION DE LA PERTINENCIA"); print(dist.T.to_string(header=False))

# ---- 2. SENSIBILIDAD --------------------------------------------------------
filas = []
for u in UMBRALES:
    k = base[base.sim_relevance_avg >= u]
    o = np.array(DIM)[k[[col(x) for x in DIM]].values.argmax(axis=1)]
    filas.append({"umbral": u, "retenidos": len(k),
                  "pct_del_corpus": round(100 * len(k) / len(base), 1),
                  **{f"pct_{n}": round(100 * (o == n).mean(), 1) for n in DIM}})
sens = pd.DataFrame(filas)
sens.to_csv(TABLAS / "umbral_sensibilidad.csv", index=False, encoding="utf-8")
print("\n2. SENSIBILIDAD DEL UMBRAL"); print(sens.to_string(index=False))

# ---- 3. FRONTERA ------------------------------------------------------------
bandas = [(0.20, 0.30, "claramente por debajo"), (0.32, 0.35, "justo por debajo del corte"),
          (0.35, 0.38, "justo por encima del corte"), (0.55, 0.70, "claramente por encima")]
muestras = []
for lo, hi, etiqueta in bandas:
    g = df[(r >= lo) & (r < hi)]
    s = g.sample(n=min(12, len(g)), random_state=7).sort_values("sim_relevance_avg")
    for _, x in s.iterrows():
        muestras.append({"banda": f"{lo:.2f}-{hi:.2f}", "situacion": etiqueta,
                         "n_en_la_banda": len(g),
                         "pertinencia": round(x.sim_relevance_avg, 3),
                         "titulo": str(x.title),
                         "JUICIO_MANUAL": ""})
front = pd.DataFrame(muestras)
front.to_csv(TABLAS / "umbral_frontera_muestra.csv", index=False, encoding="utf-8")
print("\n3. FRONTERA (muestra para revision manual)")
for b in front.banda.unique():
    g = front[front.banda == b]
    print(f"\n  {b}  ({g.situacion.iloc[0]}, n = {g.n_en_la_banda.iloc[0]:,})")
    for _, x in g.iterrows():
        print("    %.3f  %s" % (x.pertinencia, x.titulo[:88]))

# ---- 4. ROBUSTEZ DE LA FIGURA 3 --------------------------------------------
filas = []
for u in UMBRALES:
    a = base[base.sim_relevance_avg >= u].copy()
    a["ORI"] = np.array(DIM)[a[[col(x) for x in DIM]].values.argmax(axis=1)]
    P = pd.DataFrame({e: a[col(e)].rank(pct=True) * 100 for e in EJES})
    P["ORI"] = a.ORI.values
    t = P.groupby("ORI")[EJES].mean()
    fila = {"umbral": u, "n": len(a)}
    for e in EJES:
        fila[f"TEC_{e}"] = round(t.loc["TECNICISTA", e], 1)
        fila[f"SOC_{e}"] = round(t.loc["SOCIAL_HUMANA", e], 1)
        fila[f"brecha_{e}"] = round(t.loc["SOCIAL_HUMANA", e] - t.loc["TECNICISTA", e], 1)
    filas.append(fila)
rob = pd.DataFrame(filas)
rob.to_csv(TABLAS / "umbral_robustez_figura3.csv", index=False, encoding="utf-8")
print("\n4. ROBUSTEZ DE LA FIGURA 3 — brecha social-humana menos tecnicista")
print(rob[["umbral", "n"] + [f"brecha_{e}" for e in EJES]].to_string(index=False))
print("\nTablas creadas en", TABLAS)
