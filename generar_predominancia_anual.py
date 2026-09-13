import pandas as pd

# Archivo que ya genera tu script principal
entrada = "evolucion_preponderante_por_anio.csv"

# Leer datos
df = pd.read_csv(entrada)

# Quedarnos solo con año y las 3 categorías relevantes
salida = df[
    [
        "year",
        "TECNICISTA_n",
        "AMBIENTAL_n",
        "SOCIAL_HUMANA_n"
    ]
].copy()

# Renombrar columnas para que queden limpias en Excel
salida = salida.rename(columns={
    "year": "Año",
    "TECNICISTA_n": "TECNICISTA",
    "AMBIENTAL_n": "AMBIENTAL",
    "SOCIAL_HUMANA_n": "SOCIAL_HUMANA"
})

# Guardar archivo listo para Excel
salida.to_csv(
    "predominancia_anual_umbral_035.csv",
    index=False,
    encoding="utf-8-sig"
)

print("Listo: predominancia_anual_umbral_035.csv")
print(salida)
