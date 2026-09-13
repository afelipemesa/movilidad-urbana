# -*- coding: utf-8 -*-
"""
CARGA DEL CORPUS — con o sin el Excel de trabajo

Los scripts de este repositorio pueden partir de dos sitios:

  1. dimensiones.xlsx, la salida completa del paso 1. No se publica (30-45 MB
     y contiene titulos y resumenes de Scopus). Incluye el texto, asi que
     permite correr TODO.

  2. data/derived/documentos_scores.csv.gz, el dataset derivado publicado.
     Contiene un registro por documento con el anio y las similitudes, pero
     ningun texto. Basta para regenerar las tablas, las figuras y todas las
     cifras del articulo que no dependan de buscar palabras en los documentos.

`cargar_corpus()` toma el primero si esta presente y, si no, el segundo. La
bandera `hay_texto` dice cual de los dos se cargo, para que cada script omita
—diciendolo— las secciones que necesitan el texto.
"""
from pathlib import Path

import pandas as pd

EXCEL = Path("dimensiones.xlsx")
DERIVADO = Path("data/derived/documentos_scores.csv.gz")

CATEGORIAS = ["relevance", "TECNICISTA", "AMBIENTAL", "SOCIAL_HUMANA",
              "OBSERVACION_TERRENO", "INTERACCION_ESTRUCTURADA",
              "INTERACCION_EXPERIENCIAL", "PRESENCIA_CAMPO", "CONTACTO_DIRECTO"]


def cargar_corpus(verbose=True):
    """Devuelve (df, hay_texto) con columnas sim_<categoria>_avg y year_num."""
    if EXCEL.exists():
        df = pd.read_excel(EXCEL, sheet_name="documentos")
        if verbose:
            print(f"fuente: {EXCEL} ({len(df):,} documentos, con texto)")
        return df, True

    if not DERIVADO.exists():
        raise SystemExit(
            f"No encuentro ni {EXCEL} ni {DERIVADO}.\n"
            "Con un clon limpio del repositorio deberia existir el segundo."
        )

    df = pd.read_csv(DERIVADO)
    df = df.rename(columns={"year": "year_num",
                            **{f"sim_{c}": f"sim_{c}_avg" for c in CATEGORIAS}})
    if verbose:
        print(f"fuente: {DERIVADO} ({len(df):,} documentos, sin texto)")
    return df, False


def aviso_sin_texto(que):
    print(f"\n   [omitido] {que}: requiere los titulos y resumenes, que no se\n"
          f"             publican. Corre el paso 1 para obtener dimensiones.xlsx.")
