"""
Pipeline de EMBEDDINGS para mapear como ha evolucionado la forma de
estudiar la movilidad/transporte urbano entre 2006 y hoy.

Para cada documento calcula, con 3 modelos de sentence-transformers, la
similitud coseno contra:
  - "relevance": la misma categoria objetivo del paso de screening
    (para poder filtrar ruido evidente sin haber gastado un paso aparte).
  - "dimensions": las orientaciones analiticas -- actualmente TECNICISTA,
    AMBIENTAL, SOCIAL_HUMANA -- en version SOLO POSITIVA (sin mezclar
    exclusiones en el texto, que es lo que distorsiona el embedding).
    SOCIAL_HUMANA combina computacionalmente lo social-descriptivo y lo
    etico-normativo: las pruebas mostraron que sentence-transformers sobre
    titulo+abstract no logran discriminarlos como dos ejes independientes
    (correlacion residual ~0.71 incluso controlando relevancia, R^2=0.91
    al regresar ETICO sobre SOCIAL+relevancia, con un residuo sin validez
    aparente). Eso es un limite del INSTRUMENTO, no evidencia de que la
    literatura no distinga lo social de lo etico -- esa distincion se
    trabaja aparte, en un segundo nivel de analisis (clasificacion por LLM
    sobre el subconjunto SOCIAL_HUMANA, no con este script).

Esto NO decide si un documento "es" tecnicista o no: te da un score
continuo de parecido a cada orientacion, para poder ver como cambia el
promedio (o la proporcion de documentos con score alto) por anio.

Salida: xlsx con
  - hoja "documentos": una fila por documento con sus similitudes (relevancia + cada dimension).
  - hoja "evolucion_por_anio": promedio de cada dimension por anio +
    cantidad de documentos, calculado sobre TODOS los documentos y
    (si se pasa --min-relevance) tambien sobre el subconjunto filtrado
    por relevancia minima.
  - hoja "correlacion_dimensiones": correlacion entre las dimensiones a
    nivel documento (para detectar solapamiento entre descriptores).
  - hoja "top_muestra_por_dimension": los 30 documentos con mayor similitud
    a cada dimension, para revisar a ojo si el descriptor esta capturando
    el constructo correcto.

USO:
    python run_dimension_embeddings.py --input Scopus.csv --output dimensiones.xlsx
    python run_dimension_embeddings.py --input Scopus.csv --output dimensiones.xlsx --sample 500
    python run_dimension_embeddings.py --input Scopus.csv --output dimensiones.xlsx --min-relevance 0.45

CACHE DE EMBEDDINGS (para no repetir horas de computo si solo cambias el
texto de una categoria en dimensions.json):
    python run_dimension_embeddings.py --input Scopus.csv --output dimensiones.xlsx --embeddings-cache cache/
Si vuelves a correrlo con el MISMO corpus (mismos archivos --input, mismo
--sample) pero un dimensions.json distinto, reutiliza los embeddings de los
53.000 documentos guardados en cache/ y solo recalcula la similitud contra
el texto de categoria nuevo (segundos en vez de horas). Si el corpus
cambia (otro --input, otro --sample), el cache se detecta como invalido y
se recalcula todo normalmente.
"""
import argparse
import hashlib
import json
import os
import random
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from parse_scopus import parse_scopus_csv

MODELS = [
    "sentence-transformers/all-MiniLM-L6-v2",
    "sentence-transformers/all-mpnet-base-v2",
    "allenai-specter",
]


def load_categories(path):
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    cats = {}
    cats.update(data.get("relevance", {}))
    cats.update(data.get("dimensions", {}))
    relevance_names = list(data.get("relevance", {}).keys())
    dimension_names = list(data.get("dimensions", {}).keys())
    return cats, relevance_names, dimension_names


def corpus_fingerprint(records):
    """Huella del corpus (orden+titulos) para saber si un cache de embeddings
    de documentos sigue siendo valido (mismo --input/--sample) o hay que
    recalcular todo desde cero."""
    h = hashlib.sha256()
    for r in records:
        h.update((r.get("title") or "").strip().lower().encode("utf-8"))
        h.update(b"|")
    return h.hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, nargs="+",
                         help="Ruta a uno o varios Scopus.csv exportados (Scopus limita a 20000 por descarga, "
                              "asi que si tuviste que partir el corpus en varios archivos por rango de anios, "
                              "pasalos todos juntos aqui, separados por espacio: "
                              "--input parte1.csv parte2.csv parte3.csv")
    parser.add_argument("--output", default="dimensiones.xlsx", help="Ruta del xlsx de salida")
    parser.add_argument("--categories-file", default=os.path.join(os.path.dirname(os.path.abspath(__file__)), "dimensions.json"))
    parser.add_argument("--sample", type=int, default=None, help="Si se pasa, procesa una muestra ALEATORIA (semilla fija, reproducible) de N documentos del total combinado -- no los primeros N, porque los CSV de Scopus vienen ordenados por anio y eso sesgaria la muestra hacia un solo rango de anios. Util para pruebas rapidas.")
    parser.add_argument("--min-relevance", type=float, default=None, help="Si se pasa, la hoja de evolucion tambien se calcula solo con documentos con sim_relevance_avg >= este valor")
    parser.add_argument("--keep-per-model", action="store_true", help="Ademas del promedio, guarda la similitud de cada modelo por separado")
    parser.add_argument("--embeddings-cache", default=None,
                         help="Carpeta para guardar/reusar los embeddings de los documentos por modelo. "
                              "Si el corpus (--input/--sample) no cambia, evita repetir la codificacion "
                              "de todos los documentos cuando solo cambias el texto de una categoria en "
                              "dimensions.json -- esa parte tarda segundos, no horas, con el cache activo.")
    args = parser.parse_args()

    from sentence_transformers import SentenceTransformer  # import tardio

    records = []
    for path in args.input:
        print(f"Leyendo y reparando {path} ...")
        file_records = parse_scopus_csv(path)
        file_records = [r for r in file_records if r.get("title") and r.get("abstract")]
        print(f"  -> {len(file_records)} documentos utilizables en este archivo")
        for r in file_records:
            r["source_file"] = os.path.basename(path)
        records.extend(file_records)

    # Quita duplicados por si algun documento quedo repetido entre archivos
    # (p.ej. por solapamiento de rangos de anios al exportar por partes).
    seen = set()
    deduped = []
    n_dupes = 0
    for r in records:
        key = (r["title"] or "").strip().lower()
        if key in seen:
            n_dupes += 1
            continue
        seen.add(key)
        deduped.append(r)
    if n_dupes:
        print(f"Se removieron {n_dupes} documentos duplicados (mismo titulo) entre los archivos.")
    records = deduped

    if args.sample and args.sample < len(records):
        # Muestra ALEATORIA (semilla fija = reproducible), no los primeros N:
        # cada CSV de Scopus viene ordenado por anio descendente, asi que
        # tomar los primeros N sesgaria la muestra hacia un solo rango de
        # anios (esto ya nos habia confundido antes con el "bug" del anio
        # 2019 que en realidad era orden del CSV, no un error de parseo).
        rng = random.Random(42)
        records = rng.sample(records, args.sample)
    print(f"\nTotal documentos combinados con title+abstract utilizables: {len(records)}")
    if not records:
        print("No se encontro ningun documento con title+abstract. Revisa el formato del CSV.")
        sys.exit(1)

    cats, relevance_names, dimension_names = load_categories(args.categories_file)
    cat_names = list(cats.keys())
    print(f"Relevancia: {relevance_names} | Dimensiones: {dimension_names}")

    texts = [f"{r['title']}. {r['abstract']}" for r in records]
    df = pd.DataFrame(records)[["source_file", "row", "title", "year", "abstract"]]
    df["year_num"] = pd.to_numeric(df["year"], errors="coerce")

    sims_by_cat_model = {cat: [] for cat in cat_names}
    cat_cosine_by_model = []  # coseno entre los propios textos de categoria, uno por modelo

    fingerprint = corpus_fingerprint(records) if args.embeddings_cache else None
    if args.embeddings_cache:
        os.makedirs(args.embeddings_cache, exist_ok=True)

    for model_name in MODELS:
        short = model_name.split("/")[-1]
        doc_emb = None
        cache_path = os.path.join(args.embeddings_cache, f"{short}.npz") if args.embeddings_cache else None

        if cache_path and os.path.exists(cache_path):
            cached = np.load(cache_path, allow_pickle=False)
            if str(cached["fingerprint"]) == fingerprint and int(cached["n_docs"]) == len(records):
                doc_emb = cached["doc_emb"]
                print(f"Modelo {short}: reusando embeddings de documentos en cache ({cache_path}) -- no se vuelve a codificar el corpus.")
            else:
                print(f"Modelo {short}: el cache en {cache_path} no coincide con el corpus actual (cambio --input/--sample), se recalcula.")

        print(f"Cargando modelo {short} (se descarga la primera vez) ...")
        model = SentenceTransformer(model_name)

        if doc_emb is None:
            print(f"  Codificando {len(texts)} documentos con {short} (esta es la parte lenta) ...")
            doc_emb = model.encode(texts, show_progress_bar=True, batch_size=32,
                                    normalize_embeddings=True)
            if cache_path:
                np.savez(cache_path, doc_emb=doc_emb, fingerprint=fingerprint, n_docs=len(records))
                print(f"  -> Guardado en cache: {cache_path}")

        cat_texts = [cats[c] for c in cat_names]
        cat_emb = model.encode(cat_texts, normalize_embeddings=True)
        for ci, cname in enumerate(cat_names):
            sims = doc_emb @ cat_emb[ci]
            sims_by_cat_model[cname].append(sims)
            if args.keep_per_model:
                df[f"sim_{cname}_{short}"] = sims
        # coseno entre los textos de categoria mismos (no depende de los documentos):
        # si dos categorias ya estan cerca en este espacio, cualquier documento
        # tendera a puntuar parecido en ambas, sin importar que tan bien
        # redactamos el resto del texto.
        cat_cosine_by_model.append(cat_emb @ cat_emb.T)
        del model

    for cname in cat_names:
        stacked = np.vstack(sims_by_cat_model[cname])
        df[f"sim_{cname}_avg"] = stacked.mean(axis=0)

    rel_col = f"sim_{relevance_names[0]}_avg"
    df = df.rename(columns={rel_col: "sim_relevance_avg"})
    dim_cols = [f"sim_{d}_avg" for d in dimension_names]

    df = df.sort_values("year_num").reset_index(drop=True)

    def evolucion(sub_df):
        g = sub_df.groupby("year_num")[dim_cols + ["sim_relevance_avg"]].mean()
        g["n_documentos"] = sub_df.groupby("year_num").size()
        return g.reset_index()

    valid = df.dropna(subset=["year_num"])
    evol_todos = evolucion(valid)

    # Diagnostico: que tan correlacionadas estan las dimensiones entre si
    # (a nivel documento). Si dos dimensiones deberian ser conceptualmente
    # distintas pero salen con correlacion muy alta (ej. > 0.85-0.9), es
    # señal de que sus descriptores en dimensions.json se solapan demasiado
    # en vocabulario/semantica y conviene revisarlos, no solo confiar en
    # que "se leen distinto" en el papel.
    corr_dims = df[dim_cols].corr()
    print("\nCorrelacion entre dimensiones (a nivel documento) -- valores altos (>0.85-0.9) sugieren que los descriptores se solapan demasiado:")
    print(corr_dims.round(3).to_string())

    # Diagnostico 2: coseno entre los propios TEXTOS de categoria (promedio
    # entre los 3 modelos), sin pasar por ningun documento. Si dos
    # descriptores ya estan cerca en este espacio, cualquier documento va a
    # puntuar parecido en ambos sin importar que tan bien redactamos el
    # resto -- esto aisla el problema en el texto mismo, antes de mirar el
    # corpus.
    cat_cosine_avg = np.mean(cat_cosine_by_model, axis=0)
    cat_cosine_df = pd.DataFrame(cat_cosine_avg, index=cat_names, columns=cat_names)
    print("\nCoseno entre los TEXTOS de categoria (relevancia + dimensiones), promedio de los 3 modelos -- no depende del corpus:")
    print(cat_cosine_df.round(3).to_string())

    # Diagnostico 3: correlacion PARCIAL entre cada par de dimensiones,
    # controlando por sim_relevance_avg (formula clasica de correlacion
    # parcial de 1 variable de control). Si la correlacion bruta es alta
    # solo porque los documentos muy "on-topic" puntuan alto en todo, la
    # parcial debería bajar bastante; si sigue alta, el solapamiento es
    # real y no un artefacto de relevancia general.
    corr_all = df[dim_cols + ["sim_relevance_avg"]].corr()

    def partial_corr(a, b, control, corr_table):
        r_ab = corr_table.loc[a, b]
        r_ac = corr_table.loc[a, control]
        r_bc = corr_table.loc[b, control]
        denom = np.sqrt((1 - r_ac ** 2) * (1 - r_bc ** 2))
        return (r_ab - r_ac * r_bc) / denom if denom > 1e-9 else np.nan

    corr_partial = pd.DataFrame(index=dim_cols, columns=dim_cols, dtype=float)
    for a in dim_cols:
        for b in dim_cols:
            corr_partial.loc[a, b] = 1.0 if a == b else partial_corr(a, b, "sim_relevance_avg", corr_all)
    print("\nCorrelacion PARCIAL entre dimensiones, controlando por sim_relevance_avg (cuanto queda despues de sacar el factor comun de 'que tan on-topic es el documento'):")
    print(corr_partial.round(3).to_string())

    # Diagnostico 4: solapamiento del top-20 documentos entre cada par de
    # dimensiones (cuantos titulos aparecen en el top-20 de ambas).
    top20_sets = {d: set(df.sort_values(f"sim_{d}_avg", ascending=False).head(20)["title"]) for d in dimension_names}
    overlap_rows = []
    for d1 in dimension_names:
        row = {"dimension": d1}
        for d2 in dimension_names:
            row[d2] = len(top20_sets[d1] & top20_sets[d2])
        overlap_rows.append(row)
    top20_overlap = pd.DataFrame(overlap_rows).set_index("dimension")
    print("\nSolapamiento del top-20 documentos entre dimensiones (20 = identicas, 0 = sin solapamiento):")
    print(top20_overlap.to_string())

    # Muestra de los N documentos con mayor similitud a cada dimension, para
    # revisar a ojo si "suenan" al constructo correcto antes de dar por
    # buena una definicion (mas informativo que seguir retocando palabras
    # a ciegas). No decide nada, es solo para inspeccion manual.
    top_n = 30
    top_rows = []
    for cname in dimension_names:
        col = f"sim_{cname}_avg"
        top = df.sort_values(col, ascending=False).head(top_n)
        for _, r in top.iterrows():
            top_rows.append({
                "dimension": cname,
                "sim": r[col],
                "title": r["title"],
                "year": r["year"],
                "abstract": r["abstract"][:500],
            })
    top_muestra = pd.DataFrame(top_rows)

    sheets = {
        "documentos": df,
        "evolucion_por_anio_todos": evol_todos,
        "correlacion_dimensiones": corr_dims.reset_index(),
        "coseno_descriptores": cat_cosine_df.reset_index(),
        "correlacion_parcial_relev": corr_partial.reset_index(),
        "solapamiento_top20": top20_overlap.reset_index(),
        "top_muestra_por_dimension": top_muestra,
    }

    if args.min_relevance is not None:
        filtrado = valid[valid["sim_relevance_avg"] >= args.min_relevance]
        print(f"Documentos con relevancia >= {args.min_relevance}: {len(filtrado)} de {len(valid)}")
        evol_filtrado = evolucion(filtrado)
        sheets["evolucion_por_anio_filtrado"] = evol_filtrado

    with pd.ExcelWriter(args.output, engine="openpyxl") as writer:
        for name, sdf in sheets.items():
            sdf.to_excel(writer, sheet_name=name[:31], index=False)

    print(f"\nListo. Guardado en: {args.output}")
    print("\nPromedio por dimension, ultimos 5 anios disponibles:")
    print(evol_todos.tail(5).to_string(index=False))


if __name__ == "__main__":
    main()
