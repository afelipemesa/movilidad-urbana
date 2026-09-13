# Una mirada ética al estudio de la movilidad

Código y descriptores del análisis bibliométrico-semántico del artículo *«Una mirada ética al estudio de la movilidad: de cuestión tecnicista a fenómeno humano»*.

El análisis mide qué orientaciones analíticas predominan en la literatura científica sobre movilidad urbana indexada en Scopus entre 2006 y 2025, y con qué formas de producir conocimiento se construye esa literatura.

**Autor:** Andrés Felipe Mesa Martínez · Universitat Autònoma de Barcelona

---

## Los datos no están en este repositorio

Ni los CSV de Scopus (173 MB), ni los embeddings cacheados (407 MB), ni los Excel de resultados (30-45 MB cada uno). Superan los límites de GitHub y, en el caso de Scopus, su redistribución no está permitida.

**Todo se regenera** siguiendo los pasos de abajo. Lo que sí está aquí es lo que define el análisis: el código y los descriptores.

### Cómo obtener el corpus

Consulta ejecutada en Scopus:

```
TITLE-ABS-KEY("urban mobility" OR "urban transport" OR "urban transportation")
AND PUBYEAR > 2005 AND PUBYEAR < 2026
AND DOCTYPE(ar)
```

Scopus limita cada descarga a 20.000 registros, por lo que el corpus se exportó en cuatro tramos (`2006-2019.csv`, `2020-2023.csv`, `2024-2025.csv`, `2026.csv`) con los campos de título, año y resumen. Total: **53.105 artículos**.

> Completar antes de publicar: fecha exacta de la consulta. Scopus se actualiza continuamente y sin esa fecha el corpus no es replicable.

---

## Instalación

```bash
python -m venv venv
venv\Scripts\activate          # Windows
source venv/bin/activate       # macOS / Linux
pip install -r requirements.txt
```

Coloca los cuatro CSV de Scopus en la misma carpeta que los scripts.

---

## El proceso, paso a paso

### 1. Similitud semántica de cada documento con cada orientación

```bash
python run_dimension_embeddings.py --input "2006-2019.csv" "2020-2023.csv" "2024-2025.csv" "2026.csv" --output dimensiones_2006_2026_final.xlsx --embeddings-cache cache/
```

Combina los cuatro archivos, elimina duplicados por título (261 en la corrida original) y, sobre los 53.105 documentos resultantes, calcula con tres modelos de *sentence-transformers* (`all-MiniLM-L6-v2`, `all-mpnet-base-v2`, `allenai-specter`) la similitud coseno de cada título + resumen frente a cuatro descriptores de `dimensions.json`: uno de pertinencia al dominio y tres temáticos (tecnicista, ambiental, social-humana). Sigue el protocolo de cribado de Marin-Garcia et al. (2024).

**Tiempo: unas 9 horas en CPU** (28 min el modelo pequeño, ~4 h cada uno de los dos grandes). En GPU baja a 20-30 minutos sin cambiar nada del código: `sentence-transformers` la detecta sola. `--embeddings-cache cache/` guarda los embeddings de los documentos, de modo que cualquier cambio posterior en los descriptores cuesta **segundos** en lugar de horas. Úsalo siempre.

**Salida:** `dimensiones_2006_2026_final.xlsx` — hoja `documentos` (una fila por documento) y hojas de diagnóstico (coseno entre descriptores, correlaciones brutas y parciales, solapamiento del top-20). Es el insumo de todos los pasos siguientes.

### 2. Clasificación preponderante

```bash
python clasificar_embeddings_preponderante.py
```

Asigna a cada documento una única orientación: `SIN_CLASIFICAR` si su pertinencia es inferior a 0,35; en caso contrario, la dimensión de mayor similitud. No existe categoría mixta.

**Salidas:** `clasificacion_preponderante.csv`, `resumen_categorias_preponderantes.csv`, `evolucion_preponderante_por_anio.csv`, `sensibilidad_umbral_relevancia.csv`.

### 3. Tabla año × categoría

```bash
python generar_predominancia_anual.py
```

**Salida:** `predominancia_anual_umbral_035.csv`.

### 4. Figura de evolución

```bash
python figura1_volumen_y_composicion.py
```

Dos paneles: a la izquierda el número anual de documentos por orientación; a la derecha su peso relativo. La comparación es el punto: el campo se multiplica por veinticuatro mientras su composición permanece estable.

**Salida:** `figura1_composicion.png` — Figura 1 del artículo.

### 5. Detección por criterios lingüísticos

```bash
python analizar_movilidad_v4_6_tridimensional.py
python hallazgo_racionalidad_tecnica.py
```

El primero marca, mediante expresiones regulares definidas en `criterios_movilidad_v4_6_tridimensional.json`, la presencia de tres racionalidades en título y resumen: técnico-instrumental, ambiental-ecológica y de apertura humano-social. Es **multietiqueta**: un documento puede activar varias o ninguna. Mide qué formas de producir conocimiento operan en un texto, no cuál predomina.

El segundo reutiliza esas columnas —no repite la detección, corre en segundos— y tabula el resultado sobre el mismo universo que la figura.

**Salidas:** `resultado_v4_6_tridimensional_2006_2025.xlsx`, `resultado_hallazgo_racionalidad_tecnica.xlsx`.

### 6. Exploración bibliográfica dirigida

```bash
python exploracion_dirigida.py
```

Busca literalmente en el corpus `ethic*`, `moral*`, `mobility/transport(ation) justice`, `responsib*`, `ontolog*` y `levinas`.

**Salida:** `resultado_exploracion_dirigida.xlsx`.

### 7. Análisis de sensibilidad de los descriptores

```bash
python sensibilidad_descriptores.py
```

Los tres descriptores temáticos no equidistan del descriptor general del dominio, lo que da ventaja al tecnicista. Este script cuantifica qué parte de esa ventaja es geometría del descriptor y qué parte es señal del corpus, y repite la clasificación con las dimensiones estandarizadas.

**Salida:** `resultado_sensibilidad_descriptores.xlsx`.

### 8. Contacto experiencial (extensión)

```bash
python run_dimension_embeddings.py --input "2006-2019.csv" "2020-2023.csv" "2024-2025.csv" "2026.csv" --output dimensiones_v3_experiencial.xlsx --categories-file dimensions_v3.json --embeddings-cache cache/
```

`dimensions_v3.json` añade un cuarto descriptor —**contacto experiencial**— redactado sin vocabulario temático y compuesto únicamente por procedimientos de investigación (etnografía, observación participante, entrevistas, métodos de acompañamiento, análisis cualitativo). Mide *cómo* se produce el conocimiento, no *de qué* trata, y funciona como polo opuesto del descriptor tecnicista.

Con la caché ya construida, **tarda un par de minutos**. Deben aparecer tres líneas indicando que reutiliza los embeddings; si empieza a codificar documentos, la caché no coincide con el corpus.

---

## Archivos de este repositorio

| Archivo | Función |
|---|---|
| `parse_scopus.py` | Utilidad: repara y parsea los CSV de Scopus. No se ejecuta sola. |
| `run_dimension_embeddings.py` | Pasos 1 y 8 |
| `clasificar_embeddings_preponderante.py` | Paso 2 |
| `generar_predominancia_anual.py` | Paso 3 |
| `figura1_volumen_y_composicion.py` | Paso 4 |
| `analizar_movilidad_v4_6_tridimensional.py` | Paso 5a |
| `hallazgo_racionalidad_tecnica.py` | Paso 5b |
| `exploracion_dirigida.py` | Paso 6 |
| `sensibilidad_descriptores.py` | Paso 7 |
| `dimensions.json` | Descriptores del análisis principal |
| `dimensions_v3.json` | Descriptores con contacto experiencial |
| `criterios_movilidad_v4_6_tridimensional.json` | Criterios lingüísticos del paso 5 |

---

## Alcance y límites

- La **detección por criterios lingüísticos** (paso 5) es un diccionario construido para este trabajo, no un instrumento validado externamente. Uno de sus tres componentes, `racionalidad_sistemica`, concentra el 88,4 % de las activaciones técnico-instrumentales. Los criterios son públicos y pueden inspeccionarse en el JSON.
- La dimensión **social-humana agrupa** el registro social-descriptivo y el ético-normativo: los embeddings sobre título y resumen no los discriminan como ejes independientes. Es un límite del instrumento, no evidencia sobre la literatura. Los dos textos separados quedan guardados en `dimensions.json` bajo `_nivel2_referencia_no_usado_por_el_pipeline`.
- Las asignaciones dimensionales expresan **afinidad semántica predominante, no pertenencia disciplinar**. El 24,5 % de los documentos presenta un margen inferior a 0,03 entre sus dos dimensiones más altas.

---

## Uso de inteligencia artificial

El código de este repositorio se escribió y depuró con asistencia de Claude (Anthropic) y ChatGPT (OpenAI), y fue revisado y validado íntegramente por el autor, responsable del diseño del análisis, de la definición de los descriptores y de la interpretación de los resultados.

## Referencia metodológica

Marin-Garcia, J. A., Martinez-Tomas, J., Juarez-Tarraga, A., y Santandreu-Mascarell, C. (2024). *Protocol paper: From chaos to order. Augmenting manual article screening with sentence transformers in management systematic reviews.* WPOM-Working Papers on Operations Management, 15, 172-208. https://doi.org/10.4995/wpom.22282
