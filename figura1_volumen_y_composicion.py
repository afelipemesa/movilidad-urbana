import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import pandas as pd

ENTRADA = "predominancia_anual_umbral_035.csv"
SALIDA = "figura1_composicion.png"

COL = {"TECNICISTA": "#2a78d6", "AMBIENTAL": "#eb6834", "SOCIAL_HUMANA": "#1baf7a"}
LAB = {"TECNICISTA": "Tecnicista", "AMBIENTAL": "Ambiental", "SOCIAL_HUMANA": "Social-humana"}
DIMS = list(COL)

df = pd.read_csv(ENTRADA)
df = df[df["Año"] <= 2025].copy()
df["TOTAL"] = df[DIMS].sum(axis=1)
for d in DIMS:
    df[d + "_pct"] = df[d] / df["TOTAL"] * 100

plt.rcParams.update({
    "font.family": "sans-serif", "font.sans-serif": ["DejaVu Sans"],
    "figure.facecolor": "#fcfcfb", "axes.facecolor": "#fcfcfb",
    "axes.edgecolor": "#c3c2b7", "axes.labelcolor": "#0b0b0b",
    "text.color": "#0b0b0b", "xtick.color": "#52514e", "ytick.color": "#52514e",
    "grid.color": "#e1e0d9", "grid.linewidth": 0.8, "font.size": 9.5,
})

fig, (axA, axB) = plt.subplots(1, 2, figsize=(10.2, 4.3), dpi=220)

def estilo(ax):
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    for s in ("left", "bottom"):
        ax.spines[s].set_color("#c3c2b7")
    ax.grid(axis="y", zorder=0)
    ax.grid(axis="x", visible=False)
    ax.tick_params(length=0)
    ax.set_xlim(2006, 2028.6)
    ax.set_xticks(range(2006, 2026, 3))

# ---- A: volumen ----
estilo(axA)
for d in DIMS:
    axA.plot(df["Año"], df[d], color=COL[d], linewidth=2.2, solid_capstyle="round", zorder=3)
    dy = {"TECNICISTA": 0, "AMBIENTAL": 6, "SOCIAL_HUMANA": -6}[d]
    axA.annotate(LAB[d], xy=(2025, df[d].iloc[-1]), xytext=(5, dy), textcoords="offset points",
                 va="center", ha="left", color=COL[d], fontsize=8.5, fontweight="bold")
axA.set_ylabel("Artículos por año")
axA.set_title("A. El campo se multiplicó por veinticuatro",
              fontsize=10.5, fontweight="bold", loc="left", pad=10)

# ---- B: composicion ----
estilo(axB)
axB.axhspan(60, 70, color="#2a78d6", alpha=0.07, zorder=0)
for d in DIMS:
    axB.plot(df["Año"], df[d + "_pct"], color=COL[d], linewidth=2.2, solid_capstyle="round", zorder=3)
    dy = {"TECNICISTA": 0, "AMBIENTAL": 6, "SOCIAL_HUMANA": -6}[d]
    axB.annotate(LAB[d], xy=(2025, df[d + "_pct"].iloc[-1]), xytext=(5, dy), textcoords="offset points",
                 va="center", ha="left", color=COL[d], fontsize=8.5, fontweight="bold")
axB.set_ylim(0, 100)
axB.yaxis.set_major_formatter(mticker.PercentFormatter(decimals=0))
axB.set_ylabel("Participación de cada orientación")
axB.set_title("B. Su composición no se movió",
              fontsize=10.5, fontweight="bold", loc="left", pad=10)
axB.annotate("banda 60–70 %", xy=(2007.2, 71.5), fontsize=7.6, color="#52514e")

handles = [plt.Line2D([], [], color=COL[d], lw=2.2, label=LAB[d]) for d in DIMS]
fig.legend(handles=handles, loc="lower center", ncol=3, frameon=False,
           bbox_to_anchor=(0.5, -0.015), fontsize=9)

fig.tight_layout(rect=[0, 0.06, 1, 1])
fig.savefig(SALIDA, facecolor=fig.get_facecolor(), bbox_inches="tight")
print("guardada:", SALIDA)
print()
print("comprobacion — participacion tecnicista por año:")
print("  min %.1f %%   max %.1f %%   media %.1f %%" % (
    df["TECNICISTA_pct"].min(), df["TECNICISTA_pct"].max(), df["TECNICISTA_pct"].mean()))
print("  2006: %.1f %%   2025: %.1f %%" % (df["TECNICISTA_pct"].iloc[0], df["TECNICISTA_pct"].iloc[-1]))
print("  total 2006: %d    total 2025: %d    factor %.1f x" % (
    df["TOTAL"].iloc[0], df["TOTAL"].iloc[-1], df["TOTAL"].iloc[-1] / df["TOTAL"].iloc[0]))
