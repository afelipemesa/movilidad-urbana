"""
ANALISIS DE SENSIBILIDAD ANTE DIFERENCIAS BASALES ENTRE DESCRIPTORES

Los tres descriptores temáticos no se sitúan a la misma distancia del descriptor
general del dominio. Este script cuantifica cuánto de la ventaja observada por la
dimensión tecnicista se explica por esa geometría y cuánto por el corpus, y repite
todo el análisis con las dimensiones estandarizadas para comprobar si las
conclusiones se mantienen.

Entradas : dimensiones.xlsx
Salida   : resultado_sensibilidad_descriptores.xlsx
"""
import numpy as np
import pandas as pd

BASE = "dimensiones.xlsx"
SALIDA = "resultado_sensibilidad_descriptores.xlsx"
UMBRAL = 0.35

C = ["sim_TECNICISTA_avg", "sim_AMBIENTAL_avg", "sim_SOCIAL_HUMANA_avg"]
NOM = ["TECNICISTA", "AMBIENTAL", "SOCIAL_HUMANA"]

# ------------------------------------------------------------------
# CARGA
# ------------------------------------------------------------------
df = pd.read_excel(BASE, sheet_name="documentos")
for c in C + ["sim_relevance_avg", "year_num"]:
    df[c] = pd.to_numeric(df[c], errors="coerce")
d = df[(df.year_num >= 2006) & (df.year_num <= 2025) & (df.sim_relevance_avg >= UMBRAL)].copy()
N = len(d)
print(f"documentos analizados: {N:,}")

Z = (d[C] - d[C].mean()) / d[C].std()
d["ORI_CRUDO"] = np.array(NOM)[d[C].values.argmax(axis=1)]
d["ORI_TIPIF"] = np.array(NOM)[Z.values.argmax(axis=1)]

# ------------------------------------------------------------------
# 1. REPARTO GLOBAL
# ------------------------------------------------------------------
rep = []
for n in NOM:
    rep.append({
        "dimension": n,
        "n_crudo": int((d.ORI_CRUDO == n).sum()),
        "pct_crudo": round(100 * (d.ORI_CRUDO == n).mean(), 1),
        "n_tipificado": int((d.ORI_TIPIF == n).sum()),
        "pct_tipificado": round(100 * (d.ORI_TIPIF == n).mean(), 1),
    })
reparto = pd.DataFrame(rep)
coinciden = round(100 * (d.ORI_CRUDO == d.ORI_TIPIF).mean(), 1)

# ------------------------------------------------------------------
# 2. GEOMETRIA DE LOS DESCRIPTORES vs SEÑAL DEL CORPUS
# ------------------------------------------------------------------
cos = pd.read_excel(BASE, sheet_name="coseno_descriptores").set_index("index")
dom = "URBAN_MOBILITY_TRANSPORT"
geo = {n: float(cos.loc[dom, n]) for n in NOM}
obs = {n: float(d[c].mean()) for n, c in zip(NOM, C)}

filas = []
for n in NOM:
    filas.append({
        "dimension": n,
        "coseno_descriptor_con_dominio": round(geo[n], 4),
        "media_observada_en_documentos": round(obs[n], 4),
    })
geometria = pd.DataFrame(filas)

desc = []
for otra in ["AMBIENTAL", "SOCIAL_HUMANA"]:
    g = geo["TECNICISTA"] - geo[otra]
    o = obs["TECNICISTA"] - obs[otra]
    desc.append({
        "comparacion": f"TECNICISTA - {otra}",
        "brecha_por_geometria": round(g, 4),
        "brecha_observada": round(o, 4),
        "pct_explicado_por_geometria": round(100 * g / o, 1) if o else None,
        "pct_atribuible_al_corpus": round(100 * (1 - g / o), 1) if o else None,
    })
descomposicion = pd.DataFrame(desc)

# ------------------------------------------------------------------
# 3. DIAGNOSTICOS DE VALIDEZ
# ------------------------------------------------------------------
top = {n: set(d.nlargest(20, c)["title"]) for n, c in zip(NOM, C)}
solap = pd.DataFrame(
    [[len(top[a] & top[b]) for b in NOM] for a in NOM], index=NOM, columns=NOM
).reset_index().rename(columns={"index": "dimension"})

corr = d[C + ["sim_relevance_avg"]].corr()

def parcial(a, b, ctrl="sim_relevance_avg"):
    rab, rac, rbc = corr.loc[a, b], corr.loc[a, ctrl], corr.loc[b, ctrl]
    den = np.sqrt((1 - rac ** 2) * (1 - rbc ** 2))
    return (rab - rac * rbc) / den if den > 1e-9 else np.nan

pc = pd.DataFrame(index=NOM, columns=NOM, dtype=float)
for i, a in enumerate(C):
    for j, b in enumerate(C):
        pc.iloc[i, j] = 1.0 if i == j else parcial(a, b)
parciales = pc.round(3).reset_index().rename(columns={"index": "dimension"})

brutas = d[C].corr().round(3)
brutas.index = NOM; brutas.columns = NOM
brutas = brutas.reset_index().rename(columns={"index": "dimension"})

# ------------------------------------------------------------------
# 4. SERIE TEMPORAL EN AMBAS VERSIONES
# ------------------------------------------------------------------
serie = []
for a in range(2006, 2026):
    g = d[d.year_num == a]
    fila = {"anio": a, "n": len(g)}
    for n in NOM:
        fila[f"pct_{n}_crudo"] = round(100 * (g.ORI_CRUDO == n).mean(), 1)
        fila[f"pct_{n}_tipificado"] = round(100 * (g.ORI_TIPIF == n).mean(), 1)
    serie.append(fila)
serie = pd.DataFrame(serie)

# ------------------------------------------------------------------
# 6. MUESTRA DE DOCUMENTOS QUE CAMBIAN (para lectura manual)
# ------------------------------------------------------------------
cambian = d[d.ORI_CRUDO != d.ORI_TIPIF].copy()
muestra = cambian.sample(n=min(40, len(cambian)), random_state=20260913)
cols = ["title", "year_num", "ORI_CRUDO", "ORI_TIPIF"] + C
muestra = muestra[cols].rename(columns={"title": "titulo", "year_num": "anio"})
muestra["CODIFICACION_MANUAL"] = ""
muestra["COMENTARIO"] = ""

# ------------------------------------------------------------------
# EXPORTAR
# ------------------------------------------------------------------
with pd.ExcelWriter(SALIDA, engine="openpyxl") as w:
    reparto.to_excel(w, sheet_name="1_reparto_global", index=False)
    geometria.to_excel(w, sheet_name="2_geometria", index=False)
    descomposicion.to_excel(w, sheet_name="2_geometria", index=False, startrow=len(geometria) + 3)
    solap.to_excel(w, sheet_name="3_validez", index=False)
    brutas.to_excel(w, sheet_name="3_validez", index=False, startrow=len(solap) + 3)
    parciales.to_excel(w, sheet_name="3_validez", index=False, startrow=len(solap) + len(brutas) + 6)
    serie.to_excel(w, sheet_name="4_serie_temporal", index=False)
    muestra.to_excel(w, sheet_name="6_muestra_para_codificar", index=False)

print("\n" + "=" * 78)
print("1. REPARTO GLOBAL")
print("=" * 78)
print(reparto.to_string(index=False))
print(f"\n   ambos criterios coinciden en el {coinciden} % de los documentos")
print(f"   documentos que cambian de categoria: {len(cambian):,}")
print("\n" + "=" * 78)
print("2. GEOMETRIA DE LOS DESCRIPTORES vs SEÑAL DEL CORPUS")
print("=" * 78)
print(geometria.to_string(index=False)); print()
print(descomposicion.to_string(index=False))
print("\n" + "=" * 78)
print("3. VALIDEZ: solapamiento del top-20 y correlaciones parciales")
print("=" * 78)
print(solap.to_string(index=False)); print()
print("correlacion parcial controlando relevancia:")
print(parciales.to_string(index=False))
print("\nArchivo creado:", SALIDA)
