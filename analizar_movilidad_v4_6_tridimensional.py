import pandas as pd
import json
import warnings
from pathlib import Path

ARCHIVO_EXCEL = "dimensiones_2006_2026_final.xlsx"
ARCHIVO_JSON = "criterios_movilidad_v4_6_tridimensional.json"
HOJA = "documentos"

ANIO_INICIAL = 2006
ANIO_FINAL = 2025

warnings.filterwarnings("ignore", message="This pattern is interpreted as a regular expression.*")
warnings.filterwarnings("ignore", category=pd.errors.PerformanceWarning)

def unir_patrones(patrones):
    if not patrones:
        return r"(?!x)x"
    return "|".join(f"(?:{p})" for p in patrones)

def contiene(serie, patrones, case_sensitive=False):
    return serie.str.contains(
        unir_patrones(patrones),
        case=case_sensitive,
        regex=True,
        na=False
    )

def contiene_familia(serie, info):
    normal = contiene(serie, info.get("patrones", []), False)
    sensibles = contiene(serie, info.get("patrones_case_sensitive", []), True)
    return normal | sensibles

def pct(n, den):
    return round(n / den * 100, 2) if den else 0.0

# 1. CARGA
for archivo in [ARCHIVO_EXCEL, ARCHIVO_JSON]:
    if not Path(archivo).exists():
        raise FileNotFoundError(f"No encuentro: {archivo}")

with open(ARCHIVO_JSON, "r", encoding="utf-8") as f:
    criterios = json.load(f)

print("\nV4.6 cargada: marco tridimensional.")
print("Campos analizados: title + abstract")

df = pd.read_excel(ARCHIVO_EXCEL, sheet_name=HOJA)
print(f"Registros cargados: {len(df):,}")

for col in ["title", "abstract", "year_num"]:
    if col not in df.columns:
        raise ValueError(f"Falta la columna requerida: {col}")

df["year_num"] = pd.to_numeric(df["year_num"], errors="coerce")
df = df[
    (df["year_num"] >= ANIO_INICIAL) &
    (df["year_num"] <= ANIO_FINAL)
].copy()

print(f"Corpus {ANIO_INICIAL}-{ANIO_FINAL}: {len(df):,}")

df["texto"] = (
    df["title"].fillna("").astype(str)
    + " "
    + df["abstract"].fillna("").astype(str)
)

# 2. CONTEXTO MOVILIDAD
ctx = criterios["contexto_movilidad"]

df["MOVILIDAD_FUERTE"] = contiene(df["texto"], ctx["patrones_fuertes"])
df["MOVILIDAD_GENERICA"] = contiene(df["texto"], ctx["patrones_genericos"])
df["FALSO_POSITIVO_NO_MOVILIDAD"] = contiene(
    df["texto"], ctx["falsos_positivos_no_movilidad"]
)

df["MOVILIDAD"] = (
    df["MOVILIDAD_FUERTE"]
    |
    (
        df["MOVILIDAD_GENERICA"]
        & ~df["FALSO_POSITIVO_NO_MOVILIDAD"]
    )
)

# 3. MÉTODO TÉCNICO EXPLÍCITO
metodos = criterios["metodo_tecnico_explicito"]["familias"]
cols_metodo = []

for nombre, info in metodos.items():
    col = "MET_" + nombre
    df[col] = contiene_familia(df["texto"], info)
    cols_metodo.append(col)

df["METODO_TECNICO_EXPLICITO"] = (
    df["MOVILIDAD"] & df[cols_metodo].any(axis=1)
)

# 4. RACIONALIDAD SISTÉMICA
rs = criterios["racionalidad_sistemica"]
cols_sistema = []

for nombre, patrones in rs["familias_fuertes"].items():
    col = "SIS_" + nombre
    df[col] = contiene(df["texto"], patrones)
    cols_sistema.append(col)

debil_cols = []
for i, patron in enumerate(rs["senales_debiles"], start=1):
    col = f"SIS_DEBIL_{i:02d}"
    df[col] = contiene(df["texto"], [patron])
    debil_cols.append(col)

df["N_SENALES_SISTEMA_DEBILES"] = df[debil_cols].sum(axis=1)
df["SIS_HUMANO_UX"] = contiene(
    df["texto"], rs.get("senales_humanas_ux", [])
)

df["RACIONALIDAD_SISTEMICA"] = (
    df["MOVILIDAD"]
    &
    (
        df[cols_sistema].any(axis=1)
        |
        (
            (df["N_SENALES_SISTEMA_DEBILES"] >= rs["umbral_senales_debiles"])
            & ~df["SIS_HUMANO_UX"]
        )
    )
)

# 5. MEDIACIÓN INDIRECTA / ABSTRACTA
mediacion = criterios["mediacion_indirecta"]["familias"]
cols_mediacion = []

for nombre, patrones in mediacion.items():
    col = "MED_" + nombre
    df[col] = contiene(df["texto"], patrones)
    cols_mediacion.append(col)

df["MEDIACION_INDIRECTA"] = (
    df["MOVILIDAD"] & df[cols_mediacion].any(axis=1)
)

# 6. RACIONALIDAD TÉCNICO-INSTRUMENTAL INTEGRADA
df["RACIONALIDAD_TECNICO_INSTRUMENTAL"] = (
    df["MOVILIDAD"]
    &
    (
        df["METODO_TECNICO_EXPLICITO"]
        | df["RACIONALIDAD_SISTEMICA"]
        | df["MEDIACION_INDIRECTA"]
    )
)

# 7. APERTURA HUMANO-SOCIAL (V4.5 CURADA)
ahs = criterios["apertura_humano_social"]["subcategorias"]
cols_ahs = []
cols_audit_ahs = []

for nombre, info in ahs.items():
    pref = "AHS_" + nombre

    fuerte = contiene(df["texto"], info.get("patrones_fuertes", []))
    debil = contiene(df["texto"], info.get("patrones_debiles", []))
    fp = contiene(df["texto"], info.get("falsos_positivos", []))
    ancla = contiene(df["texto"], info.get("anclas_contextuales", []))

    df[pref + "_FUERTE"] = fuerte
    df[pref + "_DEBIL"] = debil
    df[pref + "_ANCLA"] = ancla
    df[pref + "_FP"] = fp

    if info.get("debil_requiere_ancla", False):
        ruta_debil = debil & ancla & ~fp
    else:
        ruta_debil = debil & ~fp

    df[pref] = (
        df["MOVILIDAD"]
        &
        (fuerte | ruta_debil)
    )

    cols_ahs.append(pref)
    cols_audit_ahs.extend([
        pref + "_FUERTE",
        pref + "_DEBIL",
        pref + "_ANCLA",
        pref + "_FP"
    ])

df["APERTURA_HUMANO_SOCIAL"] = (
    df["MOVILIDAD"] & df[cols_ahs].any(axis=1)
)

# 8. RACIONALIDAD AMBIENTAL-ECOLÓGICA
rae = criterios["racionalidad_ambiental_ecologica"]["familias"]
cols_rae = []
cols_audit_rae = []

for nombre, info in rae.items():
    pref = "RAE_" + nombre

    fuerte = contiene(df["texto"], info.get("patrones_fuertes", []))
    debil = contiene(df["texto"], info.get("patrones_debiles", []))
    ancla = contiene(df["texto"], info.get("anclas_contextuales", []))
    fp = contiene(df["texto"], info.get("falsos_positivos", []))

    df[pref + "_FUERTE"] = fuerte
    df[pref + "_DEBIL"] = debil
    df[pref + "_ANCLA"] = ancla
    df[pref + "_FP"] = fp

    if info.get("debil_requiere_ancla", False):
        ruta_debil = debil & ancla & ~fp
    else:
        ruta_debil = debil & ~fp

    df[pref] = (
        df["MOVILIDAD"]
        &
        (fuerte | ruta_debil)
    )

    cols_rae.append(pref)
    cols_audit_rae.extend([
        pref + "_FUERTE",
        pref + "_DEBIL",
        pref + "_ANCLA",
        pref + "_FP"
    ])

df["RACIONALIDAD_AMBIENTAL_ECOLOGICA"] = (
    df["MOVILIDAD"] & df[cols_rae].any(axis=1)
)

# 9. ORIENTACIÓN DOMINANTE POR COSINE
sim_cols = {
    "TECNICISTA": "sim_TECNICISTA_avg",
    "AMBIENTAL": "sim_AMBIENTAL_avg",
    "SOCIAL_HUMANA": "sim_SOCIAL_HUMANA_avg"
}

if not all(c in df.columns for c in sim_cols.values()):
    raise ValueError("Faltan columnas de similitud.")

sims = df[list(sim_cols.values())].apply(pd.to_numeric, errors="coerce")
reverse = {v: k for k, v in sim_cols.items()}

df["ORIENTACION_DOMINANTE"] = sims.idxmax(axis=1).map(reverse)
maxv = sims.max(axis=1)
empates = sims.eq(maxv, axis=0).sum(axis=1) > 1
df.loc[empates, "ORIENTACION_DOMINANTE"] = "EMPATE"

# 10. PERFIL TRIDIMENSIONAL MUTUAMENTE EXCLUYENTE
def perfil_tridimensional(row):
    t = bool(row["RACIONALIDAD_TECNICO_INSTRUMENTAL"])
    a = bool(row["RACIONALIDAD_AMBIENTAL_ECOLOGICA"])
    h = bool(row["APERTURA_HUMANO_SOCIAL"])

    if t and a and h:
        return "TECNICO + AMBIENTAL + HUMANO_SOCIAL"
    if t and a:
        return "TECNICO + AMBIENTAL"
    if t and h:
        return "TECNICO + HUMANO_SOCIAL"
    if a and h:
        return "AMBIENTAL + HUMANO_SOCIAL"
    if t:
        return "SOLO_TECNICO"
    if a:
        return "SOLO_AMBIENTAL"
    if h:
        return "SOLO_HUMANO_SOCIAL"
    return "RESIDUAL_NO_DETECTADO"

df["PERFIL_TRIDIMENSIONAL"] = df.apply(perfil_tridimensional, axis=1)

# 11. COMPARACIÓN POR ORIENTACIÓN
comparacion = []

for orientacion in ["TECNICISTA", "AMBIENTAL", "SOCIAL_HUMANA"]:
    sub = df[df["ORIENTACION_DOMINANTE"] == orientacion]
    n = len(sub)

    comparacion.append({
        "orientacion": orientacion,
        "n": n,
        "pct_racionalidad_tecnico_instrumental": round(
            sub["RACIONALIDAD_TECNICO_INSTRUMENTAL"].mean() * 100, 2
        ),
        "pct_racionalidad_ambiental_ecologica": round(
            sub["RACIONALIDAD_AMBIENTAL_ECOLOGICA"].mean() * 100, 2
        ),
        "pct_apertura_humano_social": round(
            sub["APERTURA_HUMANO_SOCIAL"].mean() * 100, 2
        ),
    })

comparacion = pd.DataFrame(comparacion)

print("\n" + "=" * 105)
print("V4.6 — TRES DIMENSIONES POR ORIENTACIÓN")
print("=" * 105)
print(comparacion.to_string(index=False))

# 12. PERFILES QUE SÍ SUMAN 100%
perfiles = (
    df[df["ORIENTACION_DOMINANTE"].isin(["TECNICISTA", "AMBIENTAL", "SOCIAL_HUMANA"])]
    .groupby(["ORIENTACION_DOMINANTE", "PERFIL_TRIDIMENSIONAL"])
    .size()
    .reset_index(name="n")
)

totales = perfiles.groupby("ORIENTACION_DOMINANTE")["n"].transform("sum")
perfiles["pct_orientacion"] = (perfiles["n"] / totales * 100).round(2)

orden_perfiles = [
    "SOLO_TECNICO",
    "SOLO_AMBIENTAL",
    "SOLO_HUMANO_SOCIAL",
    "TECNICO + AMBIENTAL",
    "TECNICO + HUMANO_SOCIAL",
    "AMBIENTAL + HUMANO_SOCIAL",
    "TECNICO + AMBIENTAL + HUMANO_SOCIAL",
    "RESIDUAL_NO_DETECTADO"
]

tabla_perfiles_pct = (
    perfiles.pivot(
        index="ORIENTACION_DOMINANTE",
        columns="PERFIL_TRIDIMENSIONAL",
        values="pct_orientacion"
    )
    .reindex(index=["TECNICISTA", "AMBIENTAL", "SOCIAL_HUMANA"])
    .reindex(columns=orden_perfiles)
    .fillna(0)
    .reset_index()
)

tabla_perfiles_n = (
    perfiles.pivot(
        index="ORIENTACION_DOMINANTE",
        columns="PERFIL_TRIDIMENSIONAL",
        values="n"
    )
    .reindex(index=["TECNICISTA", "AMBIENTAL", "SOCIAL_HUMANA"])
    .reindex(columns=orden_perfiles)
    .fillna(0)
    .astype({c: int for c in orden_perfiles})
    .reset_index()
)

print("\nPERFILES TRIDIMENSIONALES (%; CADA FILA SUMA 100)")
print("-" * 105)
print(tabla_perfiles_pct.to_string(index=False))

# 13. SUBCATEGORÍAS AMBIENTALES
res_rae = []

for nombre in rae:
    col = "RAE_" + nombre
    row = {"subcategoria_ambiental": nombre}

    for orientacion in ["TECNICISTA", "AMBIENTAL", "SOCIAL_HUMANA"]:
        sub = df[df["ORIENTACION_DOMINANTE"] == orientacion]
        n = int(sub[col].sum())
        row[f"n_{orientacion}"] = n
        row[f"pct_{orientacion}"] = pct(n, len(sub))

    res_rae.append(row)

res_rae = pd.DataFrame(res_rae)

# 14. RESIDUO REAL
residuo = df[
    df["ORIENTACION_DOMINANTE"].isin(["TECNICISTA", "AMBIENTAL", "SOCIAL_HUMANA"])
    & (df["PERFIL_TRIDIMENSIONAL"] == "RESIDUAL_NO_DETECTADO")
].copy()

# muestras determinísticas para auditoría
muestras = []
for orientacion in ["TECNICISTA", "AMBIENTAL", "SOCIAL_HUMANA"]:
    sub = residuo[residuo["ORIENTACION_DOMINANTE"] == orientacion]
    if len(sub):
        muestras.append(sub.sample(n=min(100, len(sub)), random_state=20260910))

muestra_residuo = pd.concat(muestras, ignore_index=True) if muestras else pd.DataFrame()

# 15. EXPORTAR
cols_base = [
    c for c in [
        "source_file", "row", "title", "abstract", "year_num",
        "sim_TECNICISTA_avg", "sim_AMBIENTAL_avg", "sim_SOCIAL_HUMANA_avg",
        "ORIENTACION_DOMINANTE", "MOVILIDAD",
        "METODO_TECNICO_EXPLICITO", "RACIONALIDAD_SISTEMICA",
        "MEDIACION_INDIRECTA", "RACIONALIDAD_TECNICO_INSTRUMENTAL",
        "RACIONALIDAD_AMBIENTAL_ECOLOGICA", "APERTURA_HUMANO_SOCIAL",
        "PERFIL_TRIDIMENSIONAL"
    ] if c in df.columns
]

cols_detalle = cols_base + cols_ahs + cols_rae

SALIDA = "resultado_v4_6_tridimensional_2006_2025.xlsx"

with pd.ExcelWriter(SALIDA, engine="openpyxl") as writer:
    comparacion.to_excel(writer, sheet_name="tres_dimensiones", index=False)
    tabla_perfiles_pct.to_excel(writer, sheet_name="perfiles_pct_100", index=False)
    tabla_perfiles_n.to_excel(writer, sheet_name="perfiles_n", index=False)
    res_rae.to_excel(writer, sheet_name="subcategorias_ambiental", index=False)

    df[cols_detalle].to_excel(writer, sheet_name="detalle_corpus", index=False)
    residuo[cols_detalle].to_excel(writer, sheet_name="residual_no_detectado", index=False)

    if not muestra_residuo.empty:
        muestra_residuo[cols_detalle].to_excel(
            writer, sheet_name="muestra_residuo_300", index=False
        )

print("\nArchivo creado:", SALIDA)
print("Revisa primero: tres_dimensiones, perfiles_pct_100 y muestra_residuo_300.")
