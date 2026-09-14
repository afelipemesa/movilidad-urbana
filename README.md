# Una mirada ética al estudio de la movilidad

Código y descriptores del análisis bibliométrico-semántico del artículo *«Una mirada ética al estudio de la movilidad: de cuestión tecnicista a fenómeno humanista»*.

El análisis mide qué orientaciones analíticas predominan en la literatura científica sobre movilidad urbana indexada en Scopus entre 2006 y 2025, y con qué formas de producir conocimiento se construye esa literatura.

**Autor:** Andrés Felipe Mesa Martínez · Universitat Autònoma de Barcelona

---

## Contenido del repositorio

No se incluyen los CSV de Scopus (173 MB), los embeddings cacheados (407 MB) ni los Excel de resultados (30-45 MB cada uno): superan los límites de GitHub y, en el caso de Scopus, su redistribución no está permitida.

Sí se incluye todo lo que define el análisis (código y descriptores) y un dataset derivado que permite auditar los resultados sin reejecutar el cálculo de embeddings:

| Ruta | Contenido |
|---|---|
| `descriptors/dimensiones.json` | Definición vigente de los descriptores. Es el único archivo normativo. |
| `data/derived/documentos_scores.csv.gz` | Un registro por documento (53.105): `doc_id`, `title_hash`, año y similitudes coseno promediadas. |
| `data/derived/corpus_identificadores.csv.gz` | Identificadores de los mismos 53.105 documentos: `doc_id`, `title_hash`, año, `eid` y `doi`. Permite reconstruir el corpus sin redistribuir texto con licencia. |
| `outputs/tables/` | Tablas de validación, de sensibilidad y las dos tablas anuales de las que sale la Tabla 1 del artículo. |
| `outputs/figures/` | Figuras. |

El contenido de `outputs/` se regenera con una sola orden:

```bash
python reproducir_resultados.py
```

No recalcula embeddings, y funciona de dos maneras según lo que haya en la carpeta.

**En un clon limpio**, partiendo solo de `data/derived/documentos_scores.csv.gz`, regenera las dos figuras del artículo, la Tabla 1 y las tablas de percentiles, concentración, correlaciones y sensibilidad del umbral. Es decir, todas las cifras del artículo que se calculan sobre las puntuaciones. Las tablas resultantes son idénticas a las publicadas aquí.

**Con `dimensiones.xlsx` presente** (la salida completa del paso 1, que no se publica) regenera además lo que exige el texto de los documentos: la prueba de validación de los ejes, la muestra de frontera del umbral, la exploración bibliográfica dirigida y el propio dataset derivado. Los pasos que no pueden correr se omiten indicándolo.

### Qué se puede comprobar y qué no

La terminología importa, porque «reproducible» y «replicable» no significan lo mismo, y este repositorio ofrece cosas distintas en cada nivel.

Con un clon de hoy ya se puede comprobar la reproducibilidad computacional: las tablas, las figuras y las cifras del artículo se regeneran a partir de los datos derivados y del código publicados, sin necesidad de acceso a Scopus. También queda garantizada la trazabilidad del corpus, porque los 53.105 documentos están identificados uno a uno mediante `doc_id`, `title_hash`, año, EID y DOI. La reconstrucción del corpus fuente exige más: solo quien tenga acceso a Scopus puede recuperar los registros exactos y repetir el proceso completo, incluido el cálculo de embeddings.

Lo que no puede hacerse desde el repositorio es buscar palabras dentro de los documentos (la exploración bibliográfica dirigida y la prueba de validación de los ejes), porque eso requiere los títulos y resúmenes, que no se redistribuyen.

El dataset derivado no contiene títulos ni resúmenes: únicamente un índice de fila, el año y las puntuaciones. Por esa razón puede publicarse sin infringir la licencia de la base de datos.

### Reconstrucción del corpus

Los CSV exportados de Scopus no se redistribuyen. En su lugar se publica `data/derived/corpus_identificadores.csv.gz`, con el EID de Scopus y el DOI de cada uno de los 53.105 documentos: el EID está presente en el 100 % de los registros y el DOI en el 92,3 %. Los identificadores son referencias, no contenido con licencia.

Cualquier persona con acceso a Scopus puede así recuperar los documentos uno a uno y verificar que su corpus es el mismo, comparando el SHA-256 del título normalizado con la columna `title_hash`. Las dos tablas de `data/derived/` comparten `doc_id` y `title_hash`: se pueden unir por cualquiera de las dos columnas.

El archivo `corpus_identificadores.csv.gz` permite identificar y reconstruir el corpus original sin redistribuir títulos ni resúmenes de Scopus. La correspondencia con el dataset derivado se verificó para los 53.105 registros mediante `title_hash` y año.

Lo genera `generar_identificadores.py` a partir de los cuatro CSV originales. Reconstruye el corpus con el mismo orden de lectura, el mismo filtro de título y resumen y la misma eliminación de duplicados por título normalizado que el paso 1 (261 duplicados retirados), y toma el `doc_id` del dataset ya publicado uniendo por `title_hash`, en lugar de reasignarlo.

### Construcción de `doc_id`

Corresponde al número de fila del corpus una vez construido, y el corpus se construye siempre del mismo modo:

```
2006-2019.csv → 2020-2023.csv → 2024-2025.csv → 2026.csv
        ↓  concatenación en ese orden
        ↓  eliminación de duplicados por título normalizado (minúsculas, sin espacios extremos)
   53.105 documentos, numerados 1..53.105
```

La repetición de esos pasos reproduce exactamente la misma numeración.

Cada registro incluye además `title_hash`, el SHA-256 del título normalizado, que permite verificar la correspondencia documento a documento, y comprobar que un corpus descargado posteriormente coincide con el aquí descrito, sin que el repositorio publique ningún título.

### Archivo de descriptores vigente

La definición vigente es `descriptors/dimensiones.json`. Las versiones anteriores (`dimensions.json`, `dimensions_v3.json`) se conservan únicamente en el historial de Git y no deben emplearse para reproducir resultados.

### Obtención del corpus

Consulta ejecutada en Scopus:

```
TITLE-ABS-KEY("urban mobility" OR "urban transport" OR "urban transportation")
AND PUBYEAR > 2005 AND PUBYEAR < 2026
AND DOCTYPE(ar)
```

Scopus limita cada descarga a 20.000 registros: por eso el corpus se exportó en cuatro tramos (`2006-2019.csv`, `2020-2023.csv`, `2024-2025.csv`, `2026.csv`) con los campos de título, año y resumen. Total: **53.105 artículos**.

**Fecha de consulta: 7 de septiembre de 2026.** Scopus se actualiza de forma continua y una consulta posterior devolverá más registros; esa fecha es la que fija el corpus descrito aquí.

---

## Instalación

```bash
git clone https://github.com/afelipemesa/movilidad-urbana.git
cd movilidad-urbana
python -m venv venv
venv\Scripts\activate          # Windows
source venv/bin/activate       # macOS / Linux
pip install -r requirements.txt
```

Los cuatro CSV de Scopus deben situarse en la misma carpeta que los scripts.

### En Google Colab

Para probar el clon limpio sin instalar nada localmente (sin `dimensiones.xlsx` ni los CSV de Scopus: es lo que obtiene cualquier persona que solo tiene el repositorio):

```python
!git clone https://github.com/afelipemesa/movilidad-urbana.git
%cd movilidad-urbana
!pip install -q -r requirements.txt
!python reproducir_resultados.py
```

Para ver una figura generada, en otra celda:

```python
from IPython.display import Image
Image("outputs/figures/figura2_composicion.png")
```

### Entorno de ejecución recomendado

El paso 1 es el único costoso. **Se recomienda ejecutarlo en Google Colab con entorno de ejecución GPU** (menú *Entorno de ejecución → Cambiar tipo de entorno de ejecución → Acelerador por hardware: GPU). El código no requiere modificación alguna: `sentence-transformers` detecta la GPU de forma automática. Con ello el paso 1 baja de unas nueve horas en CPU a unos veinte o treinta minutos.

Al trabajar en Colab conviene montar Google Drive y dirigir allí tanto los CSV de entrada como la carpeta `cache/`, para que los embeddings sobrevivan al cierre de la sesión:

```python
from google.colab import drive
drive.mount('/content/drive')
```

Los pasos 2 a 7 se ejecutan en segundos o minutos y no requieren GPU.

---

## El proceso, paso a paso

### 1. Similitud semántica de cada documento con cada descriptor

```bash
python run_dimension_embeddings.py --input "2006-2019.csv" "2020-2023.csv" "2024-2025.csv" "2026.csv" --output dimensiones.xlsx --categories-file descriptors/dimensiones.json --embeddings-cache cache/
```

Combina los cuatro archivos, elimina duplicados por título (261 en la corrida original) y, sobre los 53.105 documentos resultantes, calcula con tres modelos de *sentence-transformers* (`all-MiniLM-L6-v2`, `all-mpnet-base-v2`, `allenai-specter`) la similitud coseno de cada título + resumen frente a los descriptores de `descriptors/dimensiones.json`: uno de pertinencia al dominio, tres temáticos (tecnicista, ambiental, social-humana) y tres ejes empíricos (paso 6). Sigue el protocolo de cribado de Marin-Garcia et al. (2024).

**Tiempo de cómputo:** unas nueve horas en CPU (28 minutos el modelo pequeño y alrededor de cuatro horas cada uno de los dos grandes) frente a veinte o treinta minutos en GPU.

El parámetro `--embeddings-cache cache/` almacena los embeddings de los documentos, que son la parte costosa del cálculo. Una vez construida la caché, cualquier modificación posterior de los descriptores se resuelve en segundos: solo hay que recalcular los vectores de los descriptores y los productos coseno. La caché se valida mediante una huella SHA-256 del corpus y se invalida automáticamente si cambian los documentos de entrada.

**Salida:** `dimensiones.xlsx`, con la hoja `documentos` (una fila por documento) y hojas de diagnóstico (coseno entre descriptores, correlaciones brutas y parciales, solapamiento del top-20). Es el insumo de todos los pasos siguientes.

### 2. Clasificación preponderante

```bash
python clasificar_embeddings_preponderante.py
```

Asigna a cada documento una única orientación: `SIN_CLASIFICAR` si su pertinencia es inferior a 0,35; en caso contrario, la dimensión de mayor similitud. No existe categoría mixta.

**Salidas:** `clasificacion_preponderante.csv`, `resumen_categorias_preponderantes.csv`, `evolucion_preponderante_por_anio.csv`, `sensibilidad_umbral_relevancia.csv`.

### 3. Figuras y tablas

```bash
python figuras.py
```

Tres figuras independientes sobre el mismo universo de 42.208 documentos: el número anual de documentos por orientación; su peso relativo, con la banda 60-70 % sombreada; y la posición media de cada orientación dentro de cada eje empírico, expresada en percentiles del propio eje, con los ejes ordenados por cercanía a la persona.

Requiere `dimensiones.xlsx` (paso 1).

**Salidas:** `outputs/figures/figura1_volumen.png`, `figura2_composicion.png` y `figura3_ejes.png`; y, en `outputs/tables/`, `documentos_por_anio_y_dimension.csv` y `tabla1_quinquenios.csv`. En el artículo, el contenido de la primera figura se presenta en forma de tabla (es `tabla1_quinquenios.csv`) y las otras dos corresponden a las Figuras 1 y 2.

### 4. Exploración bibliográfica dirigida

```bash
python exploracion_dirigida.py
```

Busca literalmente en el corpus las raíces `ethic*`, `moral*`, `responsib*`, `ontolog*` y `levinas`, junto con las expresiones `mobility justice`, `transport justice` y `transportation justice`. Opera sobre el mismo universo que el resto del análisis: los 42.208 documentos de 2006 a 2025 con pertinencia igual o superior a 0,35. Sin el corte por año el corpus incluye 2026 y los conteos no coinciden con los publicados.

Sobre los 42.208 documentos del periodo 2006-2025, los resultados son: 196 documentos (0,5 %) mencionan la ética o la moral; 735 (1,7 %) la responsabilidad; 51 emplean alguna de las tres expresiones de justicia, de los cuales 48 son posteriores a 2018 y únicamente 2 mencionan también la responsabilidad; y ninguno menciona a Emmanuel Levinas.

El recuento de `ontolog*` no se utiliza en el artículo. De las 95 apariciones registradas, 72 corresponden a documentos de orientación tecnicista y remiten a ontologías de datos en el sentido informático, no filosófico: el término no discrimina lo que aparenta discriminar.

**Salida:** `resultado_exploracion_dirigida.xlsx`.

### 5. Análisis de sensibilidad de los descriptores

```bash
python sensibilidad_descriptores.py
```

Los tres descriptores temáticos no equidistan del descriptor general del dominio, lo que otorga ventaja al tecnicista. El script cuantifica qué parte de esa ventaja corresponde a la geometría del descriptor y qué parte a la señal del corpus, y repite la clasificación con las dimensiones estandarizadas.

**Salida:** `resultado_sensibilidad_descriptores.xlsx`.

### 5b. Sensibilidad del umbral de pertinencia

```bash
python sensibilidad_umbral.py
```

El valor 0,35 no constituye un estándar de *sentence-transformers*, sino un umbral operativo definido para este corpus. El script lo somete a tres pruebas y deposita las tablas en `outputs/tables/`.

**Posición del umbral.** El coseno observado no recorre el intervalo 0-1, sino de 0,065 a 0,806, con media 0,502 y desviación típica 0,113. El valor 0,35 se sitúa en el percentil 10,3, a 1,3 desviaciones por debajo de la media: recorta la décima parte menos pertinente del corpus, y no representa «un parecido del 35 %».

**Efecto de su desplazamiento.**

| Umbral | Retenidos | % del corpus | Tecnicista | Ambiental | Social-humana |
|---|---|---|---|---|---|
| 0,30 | 44.806 | 95,5 % | 66,3 % | 19,6 % | 14,1 % |
| **0,35** | **42.208** | **90,0 %** | **65,7 %** | **19,5 %** | **14,8 %** |
| 0,40 | 37.784 | 80,6 % | 63,7 % | 19,9 % | 16,4 % |
| 0,45 | 32.393 | 69,1 % | 60,6 % | 20,8 % | 18,6 % |
| 0,50 | 25.769 | 54,9 % | 56,0 % | 22,2 % | 21,8 % |

El predominio tecnicista se mantiene entre el 60 % y el 66 % para umbrales de 0,30 a 0,45. Con un corte de 0,50, que descarta casi la mitad del corpus, desciende al 56 % y continúa siendo con holgura la orientación mayoritaria.

**Revisión manual de la frontera.** El archivo `umbral_frontera_muestra.csv` recoge doce títulos de cada una de cuatro bandas, citados como ejemplos bibliográficos para que la decisión pueda inspeccionarse. Se trata de una muestra reducida y de carácter ilustrativo: permite observar qué tipo de documento queda a cada lado del corte, pero no estimar tasas de error ni sostener afirmaciones sobre el corpus completo.

Por debajo de 0,30 el filtro opera correctamente (compresión de datos LiDAR, intercambiadores de calor para diésel, enjambres de drones). Entre 0,32 y 0,35 se pierden trabajos que sí pertenecen al dominio (predicción de flujo de tráfico, cambio de carril, vibración ferroviaria). Entre 0,35 y 0,38 ingresan trabajos urbanos ajenos a la movilidad (contaminación de suelos, metabolismo del agua, confort térmico, ventanas inteligentes).

La banda 0,32-0,38 resulta mixta en ambos sentidos, como ocurriría con cualquier umbral, porque es allí donde el dominio se difumina. En la muestra los falsos negativos son de orientación tecnicista y los falsos positivos ambientales ajenos a la movilidad, lo que sugiere, sin demostrarlo, que rebajar el corte incorporaría más tecnicismo del que excluiría. Esa lectura solo puede contrastarse con la tabla de sensibilidad anterior, que cubre el corpus completo: con umbral 0,30 la proporción tecnicista asciende al 66,3 % y con 0,50 desciende al 56,0 %.

**Robustez de los ejes empíricos.** El resultado del paso 6 se recalcula íntegramente con cada umbral. Brecha social-humana menos tecnicista, en puntos de percentil:

| Umbral | Observación | Interacción estructurada | Interacción experiencial |
|---|---|---|---|
| 0,30 | +19,9 | +29,8 | +41,6 |
| 0,35 | +18,5 | +28,8 | +41,4 |
| 0,40 | +15,6 | +26,3 | +40,4 |
| 0,45 | +12,2 | +23,0 | +39,1 |
| 0,50 | +8,2 | +18,9 | +37,1 |

La progresión es monótona en los cinco umbrales. Con el corte más exigente la brecha de observación se estrecha de 20 a 8 puntos mientras la de interacción experiencial apenas varía, de 42 a 37: cuanto más estricto es el criterio de pertinencia, más nítido resulta que la observación constituye el terreno compartido y la escucha el que separa.

**Salidas:** `umbral_distribucion.csv`, `umbral_sensibilidad.csv`, `umbral_frontera_muestra.csv`, `umbral_robustez_figura3.csv`.

---

### 6. Ejes empíricos: cómo se produce el conocimiento

```bash
python validar_ejes_empiricos.py
```

Los pasos 1 a 6 miden de qué trata cada documento. Los ejes empíricos miden cómo se produjo el conocimiento, mediante tres descriptores redactados con fronteras mutuas y compuestos únicamente por procedimientos:

| Eje | Contenido |
|---|---|
| `OBSERVACION_TERRENO` | Aforos, conteos de peatones y vehículos, giros, velocidades puntuales, tiempos de viaje y demora, colas, ocupación, auditorías e inspecciones, observación sistemática in situ. |
| `INTERACCION_ESTRUCTURADA` | Encuestas origen-destino y de hogares, encuestas de interceptación y a bordo, cuestionarios, entrevistas estructuradas, diarios estructurados, preferencias declaradas y reveladas, experimentos de elección, escalas de satisfacción, aceptación e intención. |
| `INTERACCION_EXPERIENCIAL` | Entrevistas en profundidad y semiestructuradas, etnografía con participantes, observación participante, grupos focales, historias de vida, *go-along* y *ride-along*, diarios narrativos, talleres participativos, co-diseño, investigación-acción. |

Se calculan en el paso 1, junto con los descriptores temáticos, y son transversales: no compiten entre sí ni con las tres orientaciones, y un mismo documento puede puntuar alto en varios. Residen por ello en el bloque `empirical_axes` del archivo de descriptores y no intervienen en el `argmax` de la clasificación preponderante, que emplea exclusivamente TECNICISTA, AMBIENTAL y SOCIAL_HUMANA.

La distinción entre el segundo y el tercer eje es de orden epistemológico: en una encuesta origen-destino hay una persona delante a la que se pregunta, pero el instrumento fija de antemano lo que esa persona puede responder. Observar, preguntar mediante categorías previas y abrirse al relato producen conocimientos distintos.

La medida empleada son percentiles sobre los 42.208 documentos, sin corte alguno: la posición media de cada orientación dentro del ordenamiento de cada eje. Al operar sobre rangos, la medida resulta comparable entre ejes (elimina el efecto de que cada descriptor se sitúe a distinta distancia del dominio) y no depende de dónde se fije un umbral.

| | Observación | Interacción estructurada | Interacción experiencial |
|---|---|---|---|
| Tecnicista | 46,5 | 43,6 | 41,3 |
| Ambiental | 50,2 | 54,6 | 54,4 |
| Social-humana | 65,1 | 72,4 | 82,7 |
| **Brecha social-humana − tecnicista** | **18,6** | **28,8** | **41,4** |

La misma progresión se obtiene con otras tres medidas: media tipificada (−0,12 / −0,22 / −0,31 frente a +0,51 / +0,79 / +1,21), decil superior (8,5 / 6,2 / 3,3 frente a 17,2 / 26,3 / 41,1) y tamaño del efecto (d de Cohen 0,64 / 1,08 / 1,83): no depende del estadístico elegido.

**Prueba de validación fijada de antemano.** Los documentos que mencionan encuestas origen-destino deben concentrarse en el decil superior de `INTERACCION_ESTRUCTURADA` y no en los otros dos; los de método cualitativo, en `INTERACCION_EXPERIENCIAL`; los de aforos, en `OBSERVACION_TERRENO`. La prueba se cumple en los tres grupos: las encuestas origen-destino alcanzan el 53,3 % de su decil superior en interacción estructurada, los trabajos cualitativos el 62,0 % en interacción experiencial y los de aforos el 18,7 % en observación de terreno, frente al 6,7 % y el 5,3 % en los otros dos ejes. El script repite además la concentración por orientación con tres cortes (5 %, 10 % y 20 %) y las dos clasificaciones, cruda y tipificada.

**Separación entre los ejes.** Coseno entre descriptores: observación ↔ estructurada 0,603; observación ↔ experiencial 0,685; estructurada ↔ experiencial 0,596: el par que resultaba necesario distinguir es el más separado. Correlación documental parcial, controlando pertinencia: 0,197, 0,431 y 0,348. Solapamiento del top-20 entre los tres ejes: 0, 1 y 0 documentos.

Correlación parcial de cada eje con las orientaciones, controlando pertinencia:

| Eje | TECNICISTA | AMBIENTAL | SOCIAL_HUMANA |
|---|---|---|---|
| Observación de terreno | +0,149 | +0,022 | +0,135 |
| Interacción estructurada | −0,122 | +0,008 | +0,252 |
| Interacción experiencial | **−0,396** | −0,044 | **+0,639** |

La observación constituye el eje compartido por las tres orientaciones. La separación aparece, y crece, a medida que el método se aproxima a la persona en calidad de interlocutora.

Los descriptores `PRESENCIA_CAMPO` y `CONTACTO_DIRECTO`, procedentes de una versión anterior, se conservan en el bloque `exploratory_descriptors`: el primero mezclaba observación con encuesta y el segundo resultó excesivamente asociado a la interacción experiencial (r = 0,942). Se mantienen únicamente para permitir la comparación con esa corrida.

Con la caché construida, este paso requiere un par de minutos.

**Salida:** `resultado_validacion_ejes.xlsx` y las tablas correspondientes en `outputs/tables/`.

---

## Archivos de este repositorio

| Archivo | Función |
|---|---|
| `parse_scopus.py` | Utilidad: repara y parsea los CSV de Scopus. No se ejecuta de forma independiente. |
| `run_dimension_embeddings.py` | Paso 1 |
| `clasificar_embeddings_preponderante.py` | Paso 2 |
| `figuras.py` | Paso 3: las tres figuras en `outputs/figures/` y las dos tablas anuales en `outputs/tables/` |
| `exploracion_dirigida.py` | Paso 4 |
| `sensibilidad_descriptores.py` | Paso 5 |
| `sensibilidad_umbral.py` | Paso 5b |
| `validar_ejes_empiricos.py` | Paso 6 |
| `generar_dataset_derivado.py` | Construye `data/derived/documentos_scores.csv.gz` |
| `generar_identificadores.py` | Construye `data/derived/corpus_identificadores.csv.gz` (EID y DOI) |
| `cargar_corpus.py` | Utilidad: toma `dimensiones.xlsx` si existe y, si no, el dataset derivado publicado |
| `reproducir_resultados.py` | Regenera dataset derivado, tablas y figuras en una sola ejecución |
| `descriptors/dimensiones.json` | Descriptores vigentes: pertinencia, tres orientaciones y tres ejes empíricos |

---

## Alcance y límites

- La dimensión social-humana agrupa el registro social-descriptivo y el ético-normativo: los embeddings sobre título y resumen no los discriminan como ejes independientes. Se trata de un límite del instrumento y no de evidencia sobre la literatura. Los dos textos separados se conservan en el historial de Git, en `dimensions.json`, bajo `_nivel2_referencia_no_usado_por_el_pipeline`.
- Las asignaciones dimensionales expresan afinidad semántica predominante y no pertenencia disciplinar. El 24,5 % de los documentos presenta un margen inferior a 0,03 entre sus dos dimensiones más altas.
- El análisis opera sobre título y resumen. Un trabajo que haya empleado determinado procedimiento sin declararlo en el resumen no puntúa en el eje correspondiente: lo que se mide es la forma en que la investigación se presenta públicamente.

---

## Uso de inteligencia artificial

El código de este repositorio se escribió y depuró con asistencia de Claude (Anthropic) y ChatGPT (OpenAI), y fue revisado y validado íntegramente por el autor, responsable del diseño del análisis, de la definición de los descriptores y de la interpretación de los resultados.

## Referencia metodológica

Marin-Garcia, J. A., Martinez-Tomas, J., Juarez-Tarraga, A., y Santandreu-Mascarell, C. (2024). *Protocol paper: From chaos to order. Augmenting manual article screening with sentence transformers in management systematic reviews.* WPOM-Working Papers on Operations Management, 15, 172-208. https://doi.org/10.4995/wpom.22282
