import pandas as pd
import matplotlib.pyplot as plt
import math

# Leer datos
df = pd.read_csv("predominancia_anual_umbral_035.csv")

# Solo hasta 2025
df = df[df["Año"] <= 2025].copy()

# Crear figura
plt.figure(figsize=(12, 7))

plt.plot(df["Año"], df["TECNICISTA"], marker="o", label="TECNICISTA")
plt.plot(df["Año"], df["AMBIENTAL"], marker="o", label="AMBIENTAL")
plt.plot(df["Año"], df["SOCIAL_HUMANA"], marker="o", label="SOCIAL_HUMANA")

plt.title(
    "Predominancia anual de enfoques en la literatura sobre movilidad urbana (2006–2025)"
)
plt.xlabel("Año")
plt.ylabel("Número de artículos")

# Eje Y con saltos de 500
max_y = max(
    df["TECNICISTA"].max(),
    df["AMBIENTAL"].max(),
    df["SOCIAL_HUMANA"].max()
)
top_tick = int(math.ceil(max_y / 500.0) * 500)
plt.yticks(range(0, top_tick + 500, 500))

# Cuadrícula más útil para leer cantidades
plt.grid(True, axis="y", alpha=0.5)
plt.grid(True, axis="x", alpha=0.15)

plt.legend()
plt.xticks(df["Año"], rotation=45)

plt.tight_layout()

# Guardar gráfica
plt.savefig("grafico_predominancia_anual_2006_2025_y500.png", dpi=300)

# Mostrar gráfica
plt.show()

print("Listo: grafico_predominancia_anual_2006_2025_y500.png")
