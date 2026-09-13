# -*- coding: utf-8 -*-
"""
FIGURAS DEL ARTICULO — tres graficas separadas

  outputs/figures/figura1_volumen.png      articulos por anio y dimension
                                           (en el articulo es la Tabla 1)
  outputs/figures/figura2_composicion.png  participacion relativa
                                           (Figura 1 del articulo)
  outputs/figures/figura3_ejes.png         posicion media de cada orientacion
                                           dentro de cada eje, en percentiles
                                           del propio eje, sobre los 42.208
                                           documentos (Figura 2 del articulo)

Escribe ademas las dos tablas de las que sale la Tabla 1 del articulo.

Entrada : dimensiones.xlsx (hoja 'documentos')
"""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np
import pandas as pd

ENTRADA = "dimensiones.xlsx"
DESTINO = Path("outputs/figures")
TABLAS = Path("outputs/tables")
UMBRAL = 0.35

DIMS = ["TECNICISTA", "AMBIENTAL", "SOCIAL_HUMANA"]
COL = {"TECNICISTA": "#2a78d6", "AMBIENTAL": "#eb6834", "SOCIAL_HUMANA": "#1baf7a"}
LAB = {"TECNICISTA": "Tecnicista", "AMBIENTAL": "Ambiental", "SOCIAL_HUMANA": "Social-humana"}
EJES = ["OBSERVACION_TERRENO", "INTERACCION_ESTRUCTURADA", "INTERACCION_EXPERIENCIAL"]
EJE_LAB = ["Observar\nel desplazamiento", "Preguntar con\ncategorías previas", "Escuchar\nla experiencia"]
c = lambda n: f"sim_{n}_avg"

# ------------------------------------------------------------------ datos
from cargar_corpus import cargar_corpus
df, _hay_texto = cargar_corpus()
for k in [c(x) for x in DIMS + EJES] + ["sim_relevance_avg", "year_num"]:
    df[k] = pd.to_numeric(df[k], errors="coerce")
d = df[(df.year_num >= 2006) & (df.year_num <= 2025) & (df.sim_relevance_avg >= UMBRAL)].copy()
d["ORI"] = np.array(DIMS)[d[[c(x) for x in DIMS]].values.argmax(axis=1)]

t = d.pivot_table(index="year_num", columns="ORI", aggfunc="size", fill_value=0).reindex(columns=DIMS, fill_value=0)
t["TOTAL"] = t.sum(axis=1)
pct = t[DIMS].div(t["TOTAL"], axis=0) * 100
anios = t.index.values
# Posicion media de cada orientacion dentro de cada eje, expresada en
# percentiles del propio eje. Usa los 42.208 documentos -no un corte- y es
# comparable entre ejes: al trabajar sobre rangos, elimina el efecto de que
# cada descriptor se situe a distinta distancia del dominio.
esc = pd.DataFrame({e: (d[c(e)].rank(pct=True) * 100).groupby(d.ORI).mean() for e in EJES})

# ------------------------------------------------------------------ estilo
plt.rcParams.update({
    "font.family": "sans-serif", "font.sans-serif": ["DejaVu Sans"],
    "figure.facecolor": "#fcfcfb", "axes.facecolor": "#fcfcfb",
    "axes.edgecolor": "#c3c2b7", "axes.labelcolor": "#0b0b0b",
    "text.color": "#0b0b0b", "xtick.color": "#52514e", "ytick.color": "#52514e",
    "grid.color": "#e1e0d9", "grid.linewidth": 0.8, "font.size": 10,
})
DESTINO.mkdir(parents=True, exist_ok=True)
TABLAS.mkdir(parents=True, exist_ok=True)

# ------------------------------------------------- tablas 1 del articulo
anual = t.reset_index().rename(columns={"year_num": "anio"})
anual.to_csv(TABLAS / "documentos_por_anio_y_dimension.csv", index=False, encoding="utf-8")

q = t.copy()
q["quinquenio"] = pd.cut(q.index, bins=[2005, 2010, 2015, 2020, 2025],
                         labels=["2006-2010", "2011-2015", "2016-2020", "2021-2025"])
tab1 = q.groupby("quinquenio", observed=True)[DIMS + ["TOTAL"]].sum()
tab1.loc["Total"] = tab1.sum()
for dim in DIMS:
    tab1[f"pct_{dim}"] = (tab1[dim] / tab1["TOTAL"] * 100).round(1)
tab1.reset_index().to_csv(TABLAS / "tabla1_quinquenios.csv", index=False, encoding="utf-8")
print("  guardada:", TABLAS / "tabla1_quinquenios.csv")
print(tab1.to_string())


def lienzo():
    fig, ax = plt.subplots(figsize=(7.4, 3.7), dpi=220)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    for s in ("left", "bottom"):
        ax.spines[s].set_color("#c3c2b7")
    ax.grid(axis="y", zorder=0); ax.grid(axis="x", visible=False); ax.tick_params(length=0)
    return fig, ax

def guardar(fig, nombre):
    fig.tight_layout()
    ruta = DESTINO / nombre
    fig.savefig(ruta, facecolor=fig.get_facecolor(), bbox_inches="tight")
    plt.close(fig); print("  guardada:", ruta)

def serie(ax, datos, dy):
    ax.set_xlim(2006, 2029.8); ax.set_xticks(range(2006, 2026, 2))
    for dim in DIMS:
        ax.plot(anios, datos[dim], color=COL[dim], linewidth=2.4, solid_capstyle="round", zorder=3)
        ax.annotate(LAB[dim], xy=(2025, datos[dim].iloc[-1]), xytext=(6, dy[dim]),
                    textcoords="offset points", va="center", ha="left",
                    color=COL[dim], fontsize=9, fontweight="bold")

print("figuras del articulo\n")

# ---- 1. volumen
fig, ax = lienzo()
serie(ax, t[DIMS], {"TECNICISTA": 0, "AMBIENTAL": 7, "SOCIAL_HUMANA": -7})
ax.set_ylabel("Artículos por año"); ax.set_xlabel("Año")
guardar(fig, "figura1_volumen.png")

# ---- 2. composicion
fig, ax = lienzo()
ax.axhspan(60, 70, xmin=0, xmax=(2025 - 2006) / (2029.8 - 2006), color="#2a78d6", alpha=0.07, zorder=0)
serie(ax, pct, {"TECNICISTA": 0, "AMBIENTAL": 7, "SOCIAL_HUMANA": -7})
ax.set_ylim(0, 100); ax.yaxis.set_major_formatter(mticker.PercentFormatter(decimals=0))
ax.set_ylabel("Participación de cada dimensión"); ax.set_xlabel("Año")
ax.annotate("banda 60–70 %", xy=(2006.5, 71.5), fontsize=8.5, color="#52514e")
guardar(fig, "figura2_composicion.png")

# ---- 3. ejes empiricos
fig, ax = lienzo()
x = np.arange(len(EJES))
dyl = {"TECNICISTA": -2.5, "AMBIENTAL": 2.5, "SOCIAL_HUMANA": 0}
for dim in DIMS:
    y = [esc.loc[dim, e] for e in EJES]
    ax.plot(x, y, color=COL[dim], linewidth=2.6, marker="o", markersize=8,
            markerfacecolor=COL[dim], markeredgecolor="#fcfcfb", markeredgewidth=2, zorder=3)
    for xi, yi in zip(x, y):
        ax.annotate(f"{yi:.0f}", xy=(xi, yi), xytext=(0, 12 if dim != "TECNICISTA" else -18),
                    textcoords="offset points", ha="center", fontsize=9,
                    color=COL[dim], fontweight="bold")
    ax.annotate(LAB[dim], xy=(x[-1], y[-1]), xytext=(14, dyl[dim]), textcoords="offset points",
                va="center", ha="left", color=COL[dim], fontsize=9, fontweight="bold")
ax.set_xlim(-0.3, 2.7); ax.set_xticks(x); ax.set_xticklabels(EJE_LAB, fontsize=9.5)
ax.tick_params(axis="x", pad=12)
ax.set_ylim(30, 92); ax.set_yticks([40, 50, 60, 70, 80, 90])
ax.set_ylabel("Posición media dentro de cada eje\n(percentil)")
ax.set_xlabel("Forma de acercarse a quien se desplaza")
guardar(fig, "figura3_ejes.png")

# ------------------------------------------------------------------ control
print("\ndocumentos:", f"{len(d):,}")
print("tecnicista: min %.1f  max %.1f  media %.1f | 2006 %.1f  2025 %.1f | factor %.1f x" % (
    pct.TECNICISTA.min(), pct.TECNICISTA.max(), pct.TECNICISTA.mean(),
    pct.TECNICISTA.iloc[0], pct.TECNICISTA.iloc[-1], t.TOTAL.iloc[-1] / t.TOTAL.iloc[0]))
print("\nposicion media en cada eje (percentil):")
print(esc.reindex(DIMS).round(1).to_string())
