# Una mirada ética al estudio de la movilidad

Código, descriptores y corpus del análisis bibliométrico-semántico del artículo *«Una mirada ética al estudio de la movilidad: de cuestión tecnicista a fenómeno humanista»*.

El análisis mide qué orientaciones analíticas predominan en la literatura científica sobre movilidad urbana indexada en Scopus entre 2006 y 2025, y con qué formas de producir conocimiento se construye esa literatura.

**Autor:** Andrés Felipe Mesa Martínez · Universitat Autònoma de Barcelona

---

## Contenido del repositorio

Se incluye todo lo necesario para reproducir el análisis completo desde el corpus, sin depender de ningún acceso externo: el código, los descriptores y, en `data/corpus/`, el corpus completo de Scopus —los mismos títulos y resúmenes usados en el análisis publicado, no una muestra ni una versión reducida—. Se publica con fines de ciencia abierta, siguiendo la práctica ya adoptada en otros conjuntos de datos bibliométricos de escala comparable (ver «Referencia metodológica», al final de este documento).

No se incluyen resultados ya calculados: ni la salida del cálculo de embeddings, ni las tablas ni las figuras finales. Todo eso se genera corriendo el pipeline sobre el corpus — es la forma de comprobar que el análisis efectivamente sale de esos documentos, y no de un archivo aparte.

| Ruta | Contenido |
|---|---|
| `descriptors/dimensiones.json` | Definición vigente de los descriptores: pertinencia, tres orientaciones temáticas y tres ejes empíricos. Es el único archivo normativo. |
| `data/corpus/` | Los cuatro CSV originales de Scopus —título, resumen y año— de los 53.105 documentos: `2006-2019.csv`, `2020-2023.csv`, `2024-2025.csv`, `2026.csv` (173 MB en total). El artículo solo usa 2006-2025 (46.907 artículos); `2026.csv` se publica aparte, sin entrar en los resultados (ver «Obtención del corpus»). |

Los embeddings cacheados (~400 MB) y la salida completa del paso 1, `dimensiones.xlsx` (30-45 MB), tampoco se incluyen: son subproductos de correr el código sobre el corpus, no un dato de entrada.

### Todo se genera corriendo el pipeline

```bash
python reproducir_resultados.py
```

corre los siete pasos en orden, empezando por `data/corpus/`: calcula los embeddings (único paso lento — ver «Entorno de ejecución recomendado», más abajo), clasifica los documentos, hace la exploración bibliográfica dirigida, los dos análisis de sensibilidad, valida los ejes empíricos y genera las figuras y tablas finales. Si `dimensiones.xlsx` ya existe de una corrida anterior, ese primer paso se salta automáticamente; bórralo para forzar un recálculo completo.

No hace falta acceso propio a Scopus ni ningún archivo adicional: el corpus ya está en el repositorio.

### Replicar con un corpus nuevo (opcional)

Lo anterior es reproducción: mismo corpus, mismo código, mismos resultados. Quien en cambio quiera *replicar* el estudio —repetir el procedimiento sobre una extracción propia y más reciente de Scopus, en vez de sobre la de este repositorio— puede hacerlo ejecutando la consulta de «Obtención del corpus» con su propio acceso y pasando esos archivos al paso 1 con `--input` (ver «El proceso, paso a paso»). No hace falta subir esa descarga propia a GitHub: se usa en local, igual que el resto de archivos que produce cada corrida.

### Construcción de `doc_id`

Corresponde al número de fila del corpus una vez construido, y el corpus se construye siempre del mismo modo:

```
2006-2019.csv → 2020-2023.csv → 2024-2025.csv → 2026.csv
        ↓  concatenación en ese orden
        ↓  eliminación de duplicados por título normalizado (minúsculas, sin espacios extremos)
   53.105 documentos, numerados 1..53.105
```

La repetición de esos pasos reproduce exactamente la misma numeración. Cada registro incluye además `title_hash`, el SHA-256 del título normalizado, útil para comparar documento a documento con cualquier corpus reconstruido de forma independiente.

### Archivo de descriptores vigente

La definición vigente es `descriptors/dimensiones.json`. Las versiones anteriores (`dimensions.json`, `dimensions_v3.json`) se conservan únicamente en el historial de Git y no deben emplearse para reproducir resultados.

### Obtención del corpus

Consulta ejecutada en Scopus para el corpus analizado en el artículo (2006-2025):

```
TITLE-ABS-KEY(
  "urban mobility"
  OR "urban transport"
  OR "urban transportation"
)
AND PUBYEAR > 2005
AND PUBYEAR < 2026
```

Scopus limita cada descarga a 20.000 registros, así que este tramo se exportó en tres archivos —`2006-2019.csv`, `2020-2023.csv` y `2024-2025.csv`— con los campos de título, año y resumen. Total: **46.907 artículos**, la cifra de la que parte el artículo (ver «Metodología» en el propio texto).

Este repositorio incluye además `2026.csv`, con documentos publicados en lo que va de 2026. **Esta parte no se usó en el análisis del artículo**: 2026 es un año en curso y, por tanto, incompleto, así que se excluyó de los resultados longitudinales para no distorsionar la comparación entre años. Se publica de todos modos, junto al resto del corpus, por transparencia y para mantener el conjunto de datos lo más actualizado posible; quien corra el pipeline completo puede incluirlo o excluirlo según lo que necesite (ver la nota sobre el corte por año en el paso 3, más abajo). Con los cuatro archivos, el corpus publicado en `data/corpus/` suma **53.105 artículos** en total.

**Fecha de consulta: 7 de septiembre de 2026.** Scopus se actualiza de forma continua: una consulta posterior devolverá más registros, tanto para el tramo 2006-2025 como para 2026; esa fecha es la que fija el corpus descrito aquí.

Los cuatro CSV resultantes de esta consulta son exactamente los que se publican en `data/corpus/`, en este mismo repositorio.

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

El corpus ya viene incluido en `data/corpus/`: no hace falta descargar ni aportar ningún archivo propio para reproducir el análisis.

### En Google Colab

```python
!git clone https://github.com/afelipemesa/movilidad-urbana.git
%cd movilidad-urbana
!pip install -q -r requirements.txt
!python reproducir_resultados.py
```

El paso de embeddings (el único lento) se beneficia de GPU — ver «Entorno de ejecución recomendado», a continuación. Más abajo, en «El proceso, paso a paso», está este mismo recorrido separado en siete celdas, una por cada script.

### Entorno de ejecución recomendado

El paso 1 (cálculo de embeddings) es el único costoso de todo el pipeline. **Se recomienda correrlo en Google Colab con entorno de ejecución GPU** (menú *Entorno de ejecución → Cambiar tipo de entorno de ejecución → Acelerador por hardware: GPU). El código no requiere ninguna modificación: `sentence-transformers` detecta la GPU automáticamente. Con ello baja de unas nueve horas en CPU a veinte o treinta minutos (28 minutos el modelo pequeño y alrededor de cuatro horas cada uno de los dos grandes, en CPU).

Al trabajar en Colab conviene montar Google Drive y dirigir ahí la carpeta `cache/`, para que los embeddings sobrevivan al cierre de la sesión:

```python
from google.colab import drive
drive.mount('/content/drive')
```

Los pasos 2 a 7 se ejecutan en segundos o minutos y no requieren GPU.

---

## El proceso, paso a paso

Siete pasos, siempre en este orden, todos partiendo de `data/corpus/`. `python reproducir_resultados.py` (sección «Todo se genera corriendo el pipeline») los encadena automáticamente; aquí van uno por uno para ver qué produce cada uno.

**Paso 1. Similitud semántica de cada documento con cada descriptor**

```bash
python run_dimension_embeddings.py
```

En Colab: `!python run_dimension_embeddings.py`

Sin `--input`, toma automáticamente los cuatro CSV de `data/corpus/`, en orden alfabético. Para usar un corpus propio en su lugar (ver «Replicar con un corpus nuevo», más arriba), se pasa explícitamente: `--input archivo1.csv archivo2.csv`. Si algún nombre tiene espacios —frecuente en descargas de Scopus, del tipo `scopus (1).csv`— conviene quitarlos antes, porque si no cada espacio se lee como si fuera un archivo aparte.

Primero, el script integra los archivos del corpus y elimina los registros duplicados por título, obteniendo un total de 53.105 documentos. Para cada uno, representa conjuntamente el título y el resumen mediante tres modelos de *sentence-transformers*: `all-MiniLM-L6-v2`, `all-mpnet-base-v2` y `allenai-specter`. A partir de estas representaciones calcula la similitud coseno con los descriptores definidos en `descriptors/dimensiones.json`: uno de pertinencia al dominio, tres correspondientes a las orientaciones temáticas —tecnicista, ambiental y social-humana— y tres asociados a los ejes empíricos analizados en el paso 6. El procedimiento toma como referencia el protocolo de cribado semántico propuesto por Marin-Garcia et al. (2024).

El parámetro `--embeddings-cache cache/` (activo por defecto en `reproducir_resultados.py`, opcional si se corre este script suelto) guarda los embeddings de los documentos, la parte costosa del cálculo: una vez construida la caché, cualquier cambio posterior en los descriptores se resuelve en segundos. La caché se valida con una huella SHA-256 del corpus y se invalida sola si cambian los documentos de entrada.

**Salida:** `dimensiones.xlsx`, con la hoja `documentos` (una fila por documento) y hojas de diagnóstico (coseno entre descriptores, correlaciones brutas y parciales, solapamiento del top-20). Es el insumo de todos los pasos siguientes.

**Paso 2. Clasificación preponderante**

```bash
python clasificar_embeddings_preponderante.py
```

En Colab: `!python clasificar_embeddings_preponderante.py`

Asigna a cada documento una única orientación: `SIN_CLASIFICAR` si su pertinencia es inferior a 0,35; en caso contrario, la dimensión de mayor similitud. No existe categoría mixta.

**Salidas:** `clasificacion_preponderante.csv`, `resumen_categorias_preponderantes.csv`, `evolucion_preponderante_por_anio.csv`, `sensibilidad_umbral_relevancia.csv`.

**Paso 3. Exploración bibliográfica dirigida**

```bash
python exploracion_dirigida.py
```

En Colab: `!python exploracion_dirigida.py`

Busca literalmente en el corpus las raíces `ethic*`, `moral*`, `responsib*`, `ontolog*` y `levinas`, junto con las expresiones `mobility justice`, `transport justice` y `transportation justice`. Opera sobre el mismo universo que el resto del análisis: los 42.208 documentos de 2006 a 2025 con pertinencia igual o superior a 0,35. Sin el corte por año el corpus incluye 2026 y los conteos no coinciden con los publicados.

Sobre los 42.208 documentos del periodo 2006-2025, los resultados son: 196 documentos (0,5 %) mencionan la ética o la moral; 735 (1,7 %) la responsabilidad; 51 emplean alguna de las tres expresiones de justicia, de los cuales 48 son posteriores a 2018 y únicamente 2 mencionan también la responsabilidad; y ninguno menciona a Emmanuel Levinas.

El recuento de `ontolog*` no se utiliza en el artículo. De las 95 apariciones registradas, 72 corresponden a documentos de orientación tecnicista y remiten a ontologías de datos en el sentido informático, no filosófico: el término no discrimina lo que aparenta discriminar.

**Salida:** `resultado_exploracion_dirigida.xlsx`.

**Paso 4. Análisis de sensibilidad de los descriptores**

```bash
python sensibilidad_descriptores.py
```

En Colab: `!python sensibilidad_descriptores.py`

Los tres descriptores temáticos no equidistan del descriptor general del dominio, lo que otorga ventaja al tecnicista. El script cuantifica qué parte de esa ventaja corresponde a la geometría del descriptor y qué parte a la señal del corpus, y repite la clasificación con las dimensiones estandarizadas.

**Salida:** `resultado_sensibilidad_descriptores.xlsx`.

**Paso 5. Sensibilidad del umbral de pertinencia**

```bash
python sensibilidad_umbral.py
```

En Colab: `!python sensibilidad_umbral.py`

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

**Paso 6. Ejes empíricos: cómo se produce el conocimiento**

```bash
python validar_ejes_empiricos.py
```

En Colab: `!python validar_ejes_empiricos.py`

Los pasos 1 a 5 miden de qué trata cada documento. Los ejes empíricos miden cómo se produjo el conocimiento, mediante tres descriptores redactados con fronteras mutuas y compuestos únicamente por procedimientos:

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

**Paso 7. Figuras y tablas finales**

```bash
python figuras.py
```

En Colab: `!python figuras.py`

Tres figuras independientes sobre el mismo universo de 42.208 documentos, ya con las orientaciones y los ejes empíricos del paso 6 definidos: el número anual de documentos por orientación; su peso relativo, con la banda 60-70 % sombreada; y la posición media de cada orientación dentro de cada eje empírico, expresada en percentiles del propio eje, con los ejes ordenados por cercanía a la persona.

**Salidas:** `outputs/figures/figura1_volumen.png`, `figura2_composicion.png` y `figura3_ejes.png`; y, en `outputs/tables/`, `documentos_por_anio_y_dimension.csv` y `tabla1_quinquenios.csv`. En el artículo, la primera se presenta en forma de tabla (es `tabla1_quinquenios.csv`) y las otras dos corresponden a las Figuras 1 y 2.

Para verlas en Colab, en otra celda:

```python
from IPython.display import Image, display

display(Image("outputs/figures/figura1_volumen.png"))
display(Image("outputs/figures/figura2_composicion.png"))
display(Image("outputs/figures/figura3_ejes.png"))
```

---

## Archivos de este repositorio

| Archivo | Función |
|---|---|
| `parse_scopus.py` | Utilidad interna de `run_dimension_embeddings.py`. No se ejecuta de forma independiente. |
| `run_dimension_embeddings.py` | Paso 1 — por defecto lee `data/corpus/` |
| `clasificar_embeddings_preponderante.py` | Paso 2 |
| `exploracion_dirigida.py` | Paso 3 |
| `sensibilidad_descriptores.py` | Paso 4 |
| `sensibilidad_umbral.py` | Paso 5 |
| `validar_ejes_empiricos.py` | Paso 6 |
| `figuras.py` | Paso 7: las tres figuras y las dos tablas anuales |
| `cargar_corpus.py` | Utilidad interna: carga `dimensiones.xlsx` para los scripts que lo necesitan |
| `reproducir_resultados.py` | Encadena los siete pasos en orden, desde `data/corpus/` |
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

Huotala, A., Kuutila, M., & Mäntylä, M. (2025). *SESR-Eval: Dataset for evaluating LLMs in the title-abstract screening of systematic reviews.* En *Proceedings of the 19th ACM/IEEE International Symposium on Empirical Software Engineering and Measurement (ESEM '25).* https://doi.org/10.5281/zenodo.16408882 — precedente citado para la publicación abierta del corpus completo (ver «Contenido del repositorio»).
