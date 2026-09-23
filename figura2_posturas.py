# -*- coding: utf-8 -*-
"""
FIGURA 2 — POSTURAS EPISTEMICAS (grafica de puntos)

Misma medida que figura3_ejes.png, presentada como una "fila" por postura.
Para cada postura (observar, preguntar con categorias previas, escuchar), los
42.208 articulos se ordenan segun su cercania semantica a ella, de menor a
mayor; la posicion de cada articulo en ese orden va de 0 a 100 (50 = mitad
del corpus). Cada punto es la posicion media de una dimension.

Entrada : dimensiones.xlsx o data/derived/documentos_scores.csv.gz
Salidas : outputs/figures/figura2_posturas.png
          outputs/tables/figura2_posturas.csv
"""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from cargar_corpus import cargar_corpus

UMBRAL = 0.35
DESTINO = Path("outputs/figures"); TABLAS = Path("outputs/tables")
DIMS = ["TECNICISTA", "AMBIENTAL", "SOCIAL_HUMANA"]
COL = {"TECNICISTA": "#2a78d6", "AMBIENTAL": "#eb6834", "SOCIAL_HUMANA": "#1baf7a"}
LAB = {"TECNICISTA": "Tecnicista", "AMBIENTAL": "Ambiental", "SOCIAL_HUMANA": "Social-humana"}
EJES = ["OBSERVACION_TERRENO", "INTERACCION_ESTRUCTURADA", "INTERACCION_EXPERIENCIAL"]
EJE_LAB = ["Observar\nel desplazamiento", "Preguntar con\ncategorías previas", "Escuchar\nla experiencia"]
c = lambda n: f"sim_{n}_avg"

# ------------------------------------------------------------------ datos
df, _ = cargar_corpus()
for k in [c(x) for x in DIMS + EJES] + ["sim_relevance_avg", "year_num"]:
    df[k] = pd.to_numeric(df[k], errors="coerce")
d = df[(df.year_num >= 2006) & (df.year_num <= 2025) & (df.sim_relevance_avg >= UMBRAL)].copy()
d["ORI"] = np.array(DIMS)[d[[c(x) for x in DIMS]].values.argmax(axis=1)]
pos = pd.DataFrame({e: (d[c(e)].rank(pct=True) * 100).groupby(d.ORI).mean()
                    for e in EJES}).reindex(DIMS)

TABLAS.mkdir(parents=True, exist_ok=True); DESTINO.mkdir(parents=True, exist_ok=True)
tabla = pos.T.round(1)
tabla["distancia_social_tecnicista"] = (pos.loc["SOCIAL_HUMANA"] - pos.loc["TECNICISTA"]).round(1)
tabla.index.name = "postura"
tabla.to_csv(TABLAS / "figura2_posturas.csv", encoding="utf-8")

# ------------------------------------------------------------------ figura
plt.rcParams.update({
    "font.family": "sans-serif", "font.sans-serif": ["DejaVu Sans"],
    "figure.facecolor": "#fcfcfb", "axes.facecolor": "#fcfcfb",
    "text.color": "#0b0b0b", "xtick.color": "#52514e", "ytick.color": "#0b0b0b",
    "font.size": 10,
})
fig, ax = plt.subplots(figsize=(7.4, 3.6), dpi=220)
for s in ("top", "right", "left", "bottom"):
    ax.spines[s].set_visible(False)
ax.tick_params(length=0)

yy = np.array([2, 1, 0])                      # observar arriba, escuchar abajo
for yi in yy:
    ax.plot([0, 100], [yi, yi], color="#e1e0d9", linewidth=6, solid_capstyle="round", zorder=1)
ax.plot([50, 50], [-0.35, 2.3], color="#8a8980", linewidth=1, linestyle=(0, (3, 3)), zorder=2)
ax.annotate("mitad del corpus", xy=(50, 2.36), ha="center", va="bottom", fontsize=8, color="#52514e")

for yi, e in zip(yy, EJES):
    xs = pos[e]
    ax.plot([xs.min(), xs.max()], [yi, yi], color="#c3c2b7", linewidth=2, zorder=2)
    for dim in DIMS:
        xi = pos.loc[dim, e]
        ax.scatter(xi, yi, s=110, color=COL[dim], edgecolor="#fcfcfb", linewidth=2, zorder=4)
        ax.annotate(f"{xi:.0f}", xy=(xi, yi), xytext=(0, -17 if dim == "TECNICISTA" else 9), textcoords="offset points",
                    ha="center", fontsize=8.5, fontweight="bold", color=COL[dim])

ax.set_yticks(yy); ax.set_yticklabels(EJE_LAB, fontsize=9.5)
ax.set_ylim(-0.5, 2.6); ax.set_xlim(-2, 102)
ax.set_xticks([0, 25, 50, 75, 100])
ax.set_xlabel("Posición media en el corpus (0 = más lejos de la postura, 100 = más cerca)")
from matplotlib.lines import Line2D
ax.legend(handles=[Line2D([], [], marker="o", linestyle="", markersize=8, color=COL[k],
                          label=LAB[k]) for k in DIMS],
          frameon=False, fontsize=9, loc="lower center", bbox_to_anchor=(0.5, 1.0),
          ncol=3, handletextpad=0.3, columnspacing=1.6)
fig.tight_layout()
fig.savefig(DESTINO / "figura2_posturas.png", facecolor=fig.get_facecolor(), bbox_inches="tight")
plt.close(fig)

print("posicion media (0-100) de cada dimension en cada postura:")
print(tabla.to_string())
print("\n  guardada:", DESTINO / "figura2_posturas.png")
