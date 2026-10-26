# Verificación de datos del proyecto vs. documentos oficiales

**Fecha:** 7 de octubre de 2026
**Proyecto:** SIG EIA – Área de Desarrollo Garcero C (PERENCO COLOMBIA LIMITED) – Expediente **LAM 0165**
**Alcance:** comprobar que la información publicada en la aplicación coincida con los documentos entregados y, donde no, corregirla o respaldarla con fuentes oficiales.

---

## 1. Documentos entregados (fuente primaria)

| Archivo | Contenido | Páginas |
|---|---|---|
| `D:\ASI.SAS\CAP 1 GENERALIDADES.pdf` | EIA – Capítulo 1 (Generalidades) | 71 |
| `D:\ASI.SAS\CAP 2 DESCRIPCION DEL PROYECTO.pdf` | EIA – Capítulo 2 (Descripción del Proyecto) | 338 |
| `D:\ASI.SAS\Presentación.pdf` | Requerimientos de pestañas de la app | 7 |

La base de conocimiento del asistente (`data/conocimiento_eia.json`) se volvió a extraer de esos PDF con `extraer_eia.py` y **coincide 100 %** con el contenido de los archivos (565 fragmentos). No se modificó: es transcripción literal (conserva, por ejemplo, la errata del propio EIA «río Guanapalalo» y «Cano» sin tilde).

## 2. Fuentes oficiales consultadas por internet

* **MADS – Auto 2888 de 2010** (`www.minambiente.gov.co/wp-content/uploads/2021/09/Auto-2888-de-2010.pdf`)
* **MADS – Auto 3874 de 2010** (`www.minambiente.gov.co/wp-content/uploads/2021/09/auto-3874-de-2010.pdf`)
* **ANLA – Resolución 1171 del 08/06/2023** (Gaceta Ambiental ANLA; proceso SAN0189-00-2020, expediente LAM0165)

Hallazgos relevantes:
* Confirman la licencia original del "Bloque Garcero C" (Resolución 0409 de 2007), el permiso de vertimiento de **8.000 BWPD (14,72 L/s)** sobre el Caño Duya y la negación de ampliarlo a 100.000 BWPD (Resolución 1972 de 2007).
* Confirman el **expediente LAM0165** y los antecedentes: Resolución 1247 de 1997 y Resolución 099 de 2004.
* **Discrepancia detectada entre fuentes oficiales y el EIA** (no corregida en la app porque la app debe ser fiel a los archivos entregados):
  * Resolución 0409: el EIA y un auto oficial citan **9 de marzo de 2007**; otros documentos oficiales citan **12 de marzo de 2007**.
  * Resolución 1972: el EIA cita **20 de diciembre de 2007**; los autos oficiales citan **15 de noviembre de 2007**.
  * Resolución 0312: el cuerpo del EIA cita **29 de marzo de 2016**; los encabezados de tabla del propio EIA citan «0312 (2017)». La app usa 2016 (texto principal).
  * Se recomienda confirmar estas fechas en el expediente LAM0165 (VITAL/ANLA) si se requiere precisión jurídica.

## 3. Verificaciones exitosas (app = documentos)

* Área del AD Garcero C: **19.872,68 ha** (polígono ANH 2026, Tabla 1.2). Licencia original: **19.900,54 ha**.
* Traslape territorial: AD = 7 UTM + Resguardo El Médano; AIS = **13 UTM** (La Virgen, El Médano, Agua Verde, El Pellisco, La Independencia, Miralindo, La Libertad de Tujua, La Unión, San Rafael de Guirripa, La Culebra, Remolinos, San Francisco, El Tigre).
* **13** plataformas multipozo (hasta 2,5 ha, hasta 5 pozos c/u) y **65** pozos nuevos; máx. **20** pozos inyectores.
* **100 km** de accesos nuevos (≤10 km c/u), **100 km** de adecuación de vías existentes, **100 km** de líneas de flujo (≤10", ≤15 km c/u), **100 km** de líneas eléctricas MT, DDV **35 m**.
* Ampliación Estación Sardinas: **+9 ha**.
* **2** Granjas Solares Fotovoltaicas: **9,9 MW / 20 ha c/u**; módulos LONGI bifacial **LR7-72HGD-620M**, inversores HUAWEI **SUN2000-330KTL-H1**, centro de transformación **JUPITER-6000K-H1**.
* Inyección/reinyección: **467.329 BWPD** (151.500 autorizados + 315.829 solicitados), **23.366,45 BWPD/pozo**, formaciones Carbonera C1/C3/C5/C7, Guadalupe y Areniscas (LSS), modo DISPOSAL + WATERFLOODING.
* Captación: Caño Tujua y Río Guanapalo **5 l/s**; 18 ocupaciones de cauce; pozos subterráneos Jordán, Paravare y Sardinas **1,5 l/s**; aprovechamiento forestal **3.172,91 m³**; préstamo lateral **30.000 m³** por plataforma.
* Vertimiento autorizado **8.000 BWD** sobre el Caño Duya. Tratamiento: skimming tanks **150 KBWPD**, filtros de cáscara de nuez (3×20, 2×23, 1×25 KBWPD) y **17 bombas** de inyección.
* Gasoducto Chigüiros: **61,8 km**, línea de 4", reducción de 450 a 150 PSI.
* Coordenadas de pozos existentes de la pestaña Zonificación: **verificadas una a una** contra la Tabla 2-24 del Capítulo 2 (reproyectadas de EPSG:9377 a WGS84).
* Marco normativo citado (Res. 0256 de 2018 – Manual de Compensaciones; Res. 601/2006; Decreto 948/1995; Decreto 1076/2015; artículo 43 Ley 99 de 1993).

## 4. Correcciones aplicadas en esta revisión

| Archivo | Corrección |
|---|---|
| `index.html` | Se agregó la Resolución **2102/2020** a la lista de modificaciones y el expediente **LAM 0165**. Formato del área corregido a `19.872,68 ha`. |
| `index2.html` | Se agregó **2102/2020** y expediente LAM 0165; se eliminó el dato no soportado «100 km de mantenimiento de vías» (el EIA no fija km para mantenimiento); gráficas: «Subestaciones» → «Granjas solares», «Pozos nuevos 13» → «Pozos inyectores (máx.) 20»; «Magna Sirgas» → **MAGNA-SIRGAS**; pie con expediente. |
| `index3.html` | «nuevas bombas de inyección de 50 KBWPD» → **17 bombas de inyección** (Cap. 2); Río «Guanapalalo» → **Guanapalo** (nombre usado en el resto del EIA); pie con expediente. |
| `index4.html` | «UT en el AI: 6» → **«UT en el AIS (total): 13»** (Cap. 1); MAGNA-SIRGAS. |
| `index5.html` | Fuente del polígono AD: «Res. 0409/2007» → **Polígono ANH 2026 (EIA Cap. 1, Tabla 1.2)**. |
| `index6.html` | Área AD aclarada (polígono ANH 2026 / licencia 19.900,54 ha); «PTAR de ósmosis inversa» → tratamiento real por **skimming y filtración**; «bombas de 50 KBWPD» → **skimming 150 KBWPD + filtración + reinyección**; «Caño Garcero» → **Caño Duya**; «Guanapalalo» → **Guanapalo**. |
| `estilos.css`, `index*.html` | Paleta de colores unificada con los archivos oficiales de ASI (`D:\ASI.SAS`): zonificación ambiental `#FF0000`→`#FFAA00`→`#FFFF00`→`#61C200`→`#489C00`; manejo `#FF0000`/`#FFFF00`/`#38A800`; significancia Conesa `#00B050`/`#8DB4E2`/`#747474`/`#FFFF00`/`#CC99FF`/`#E26B0A`; acentos, insignias y gráficas en la misma familia. Versión de `estilos.css` elevada a `v=6`/`v=7`. |
| `index.html` | Corregido error al cargar una capa KMZ individualmente: `L.layerGroup()` no implementa `getBounds()` (rompía el zoom, la leyenda y el aviso de carga). Se usa `L.featureGroup()` para el grupo del KMZ y para el contenedor de cada categoría. |
| `data/estado_app.json` | Estadísticas de Caracterización alineadas con los datos del EIA (mismas de `index4.html`): 13 plataformas / 100 km accesos; 4 unidades geológicas / 14 formas; 56 lóticos / 61 lénticos; 3 pozos de captación; 3 estaciones de aire / 28 monitoreos de ruido; bosque de galería 5.309,32 ha / pastos limpios 18.196,22 ha; 84 spp flora / 30 en veda; 122 aves / 45 mamíferos; población AIS 2.397 hab; MAGNA-SIRGAS. |
| `dist\MapaGarceroC\` | Se replicaron los mismos archivos corregidos (datos y colores) para que la versión portable quede igual. |

## 5. Datos que no se pueden comprobar con los PDF entregados

Pertenecen a capítulos del EIA **no entregados** (la propia `Presentación.pdf` los marca como «pendiente incluir»). Se dejaron como están, pero conviene validarlos cuando se suministren:

* Caracterización detallada (suelos, coberturas, flora, fauna, población, ICA) → Capítulo 3/4.
* Zonificación ambiental y de manejo (127.512,29 ha y porcentajes) → Capítulo de zonificación.
* Evaluación de impactos (Conesa), PMA/PSM, plan 1 % y compensaciones (valores de ejecución, presupuestos, fichas) → Capítulos 5 a 9. Varias cifras de la pestaña «1 % y Comp.» son demostrativas.
* Gasoducto/corredores, fichas PMA-AB/BIO/SOC y metas porcentuales de seguimiento → documentos anexos.

## 6. Cómo mantener la base de conocimiento sincronizada

```bat
python extraer_eia.py
```
Vuelve a leer `D:\ASI.SAS\CAP 1 GENERALIDADES.pdf` y `CAP 2 DESCRIPCION DEL PROYECTO.pdf` y regenera `data/conocimiento_eia.json`. El servidor lo carga al iniciar (o al reabrir `MapaGarceroC.exe`). Tras un cambio de PDFs, vuelva a ejecutar este comando y recompile con `python build_portable.py` si usa la versión portable.

---

## 7. Revisión del 16 de octubre de 2026 — nuevos archivos en D:\ASI.SAS

Se revisaron los archivos incorporados recientemente a `D:\ASI.SAS` y se simplificó la vista «Eval. Imptos / PMA & PSM / 1% y Comp.» (`index6.html`).

### 7.1 Archivos revisados por primera vez

| Archivo | Contenido | Relación con la app |
|---|---|---|
| `01. Matriz Escenario Sin Proyecto GARCERO C_V1.xlsx` | Matriz Conesa del escenario **sin proyecto** (ASI S.A.S., 2025-09-01): 15 actividades, 139 interacciones (127 negativas: 52 Irrelevante / 63 Moderado / 12 Severo; 12 positivas: 4 Leve / 8 Poco importante) | Coincide con la diapositiva 57 de «Presentación Tercer Propósito» (2,9 % / 5,8 % / 37,4 % / 8,6 % / 45,3 %). Es el escenario **sin** proyecto; la app muestra el **con** proyecto. |
| `Presentaciones de referencia\Presentacion Tercer Proposito.pptx` | Resultados del EIA presentados en el tercer momento de participación (2026) | **Fuente principal de la pestaña Evaluación**: diapositiva 59 (80 actividades: Irrelevante 123, Moderado 191, Severo 23, Leve 10, Poco importante 66, Importante 8 = 421 evaluaciones); coberturas del AD e inventario forestal (diapositivas 34-35); medidas de manejo del taller comunitario (61-64). |
| `Esquema_Interactivo_EIA_Garcero_C.html` | Esquema de navegación previsto para la app (9 pestañas) | Sustenta la estructura del PMA (abiótico / biótico / socioeconómico + PSM), los 4 tipos de medida (prevención, mitigación, corrección, compensación) y las etapas por cubrir. |
| `Presentaciones de referencia\Entrega_Resultados_MMA ARPA 3D_RV1.pptx` | **Otro proyecto**: Programa Sísmico ARPA 3D (Verano Energy, ~267.025 ha) | No aplica al AD Garcero C. Se verificó que sus cifras (151 interacciones, zonificación sísmica, PDRA/MOP) **no** están en la app. |

### 7.2 Verificaciones exitosas (app = archivos)

* Matriz de significancia del index6: **80 actividades / 421 evaluaciones** (123 / 10 / 66 / 191 / 8 / 23) = diapositiva 59 del Tercer Propósito. ✔
* Coberturas del AD (bosques y humedales): 1.124,22 / 814,32 / 84,70 / 47,76 / 42,91 / 3,00 / 0,80 ha = diapositiva 34. ✔
* Inventario forestal: 108 parcelas, 84 especies, 1.407 individuos, 660,30 m³ y volumen por cobertura = diapositiva 35. ✔
* 1% (Res. 0409/2007, art. 21: cuenca del río Meta — microcuenca del Caño Guanapalo; adición por pozo exploratorio, art. 23); actualización en los **Capítulos 11 y 12** del EIA = CAP 1. ✔
* Préstamo lateral **30.000 m³** por plataforma = CAP 2, Tabla 2-38. Gasoducto de **4" / 61,8 km / 450 → 150 PSI** = CAP 2. ✔
* Res. 0256 de 2018 (Manual de Compensaciones), 1051 de 2017 (Bancos de Hábitat) y 0126 de 2024 (especies amenazadas) = CAP 1 (marco normativo). ✔

### 7.3 Ajustes aplicados en `index6.html`

* **Datos retirados por no poder sustentarse con los archivos entregados** (eran demostrativos): «13 programas / 50 fichas» del PMA, «3 programas / 12 fichas» del PSM, códigos de ficha (PMA-AB-01, PMA-BIO-02, PMA-SOC-03…), distribución de medidas 42/28/16/14 %, umbrales PSM 96-97 %, gráfica radar «normalizado 0-100», tabla duplicada de obligaciones y la sección de terminología.
* **Todas las gráficas muestran sus porcentajes** sobre las barras/segmentos y en las leyendas (significancia, balance, inyección, coberturas e inventario forestal).
* La pestaña «PMA & PSM» quedó con la estructura del Esquema (3 componentes del PMA, 4 tipos de medida, PSM Cap. 8, 4 etapas) y las medidas reales del taller comunitario (diapositivas 61-64).
* La pestaña «1% y Comp.» quedó con lo verificado: KPIs, coberturas, inventario, dos tarjetas de obligaciones y el marco normativo resumido.
* Si ASI/Perenco confirma las cifras reales de fichas de los Capítulos 7 y 8 (no entregados), pueden reincorporarse a la vista y al contexto del asistente Geo-IA.

### 7.4 Reconstrucción de la vista guiada por la Matriz Sin Proyecto (misma fecha, tarde)

A solicitud del usuario, las tres pestañas de `index6.html` se reconstruyeron tomando como fuente principal `01. Matriz Escenario Sin Proyecto GARCERO C_V1.xlsx` (hojas **GRÁFICAS**, **IMPORTANCIA** e **IMPACTOS A EVALUAR**), verificando las cifras celda a celda:

* **Eval. Imptos** (ahora «Escenario sin proyecto»): KPIs (15 actividades · 34 impactos · 139 interacciones · 127 negativas 91,4 % · 12 positivas 8,6 %); interacciones por importancia (Irrelevante 52 · 37,4 %, Moderado 63 · 45,3 %, Severo 12 · 8,6 %, Leve 4 · 2,9 %, Poco importante 8 · 5,8 %); importancia negativa por actividad; acumulación (42 acumulativas 30,2 % / 97 simples 69,8 %); sinergia (59 · 42,4 % / 74 · 53,2 % / 6 · 4,3 % — se corrigieron los porcentajes de la hoja GRÁFICAS, que los calculaba sobre 133 en lugar de las 139 interacciones; los conteos 59/74/6 se verificaron contra la Matriz Cualitativa); importancia global por medio (Abiótico −29,94 · Biótico −30,05 · Socioeconómico −27,47 y +31,38); tabla resumen por actividad (52/63/12/4/8 = 139) y listado de los 34 impactos (12 ABIO · 7 BIO · 15 SOC). Todas las gráficas muestran sus porcentajes.
* **PMA y PSM** (el Excel no contiene información de planes): estructura de los Capítulos 7 y 8 (3 componentes PMA · 4 tipos de medida · PSM con indicadores, umbrales, frecuencia y responsables · 4 etapas) y las medidas de manejo del taller comunitario.
* **1% y Comp.**: KPIs, coberturas e inventario forestal con porcentajes, obligaciones y marco normativo resumido.
* El escenario **con** proyecto (Tercer Propósito: 80 actividades / 421 evaluaciones) ya no se mezcla en la vista; se incorporará cuando se suministre la matriz «Con Proyecto» correspondiente (p. ej. «02. Matriz Escenario Con Proyecto»).

### 7.5 Ajustes de presentación (16-oct, cierre)

* **Gráficas visibles al entrar**: se desactivó la animación global (`Chart.defaults.animation = false`) y se fuerza `resize()+draw()` al cargar, al enfocar la ventana, al volver a la pestaña y al cambiar de pestaña; con esto ninguna gráfica queda en blanco hasta interactuar.
* **Más evidente para exponer**: anillos con cifra central (127 negativas · 42 acumulativas · 74 sinergismo), fuentes de leyendas/etiquetas mayores y resaltado de severos (naranja) y positivos (verde) en la tabla resumen.
* **«Impactos más importantes por medio»** reemplaza el listado completo de 34: se muestran los **4 primeros de cada medio** (Abiótico: ABIO-5 −40, ABIO-12 −34, ABIO-8 −31, ABIO-9 −29; Biótico: BIO-2 −45, BIO-1 −42, BIO-3 −41, BIO-4 −32; Socioeconómico negativos: SOC-11 −38, SOC-2 −31, SOC-13 −31, SOC-9 −28; Socioeconómico positivos: SOC-15 +41, SOC-11 +34, SOC-7 +33, SOC-6 +30), con el índice IMImp y su clasificación Conesa (Moderado / Poco importante), tal como están en la hoja IMPORTANCIA.

### 7.6 Escenario con proyecto integrado (Matriz 02)

Se revisó `02. Matriz Escenario Con Proyecto GARCERO C_V1.xlsx` (misma estructura que la 01: METODOLOGÍA, IMPACTOS A EVALUAR, IDENTIFICACIÓN, ACTIVIDADES, Matriz Cuantitativa, IMPORTANCIA, Matriz Cualitativa, GRÁFICAS; fecha de elaboración 2025-09-01) y se integró en `index6.html`:

* **Eval. Imptos** ahora tiene un selector **Sin proyecto / Con proyecto**:
  * Con proyecto: 80 actividades en 5 etapas (pre-operativa, transversales, construcción, operación, post-operativa); 420 interacciones (337 negativas 80,2 % / 83 positivas 19,8 %); importancia 123 Irrelevante · 191 Moderado · 23 Severo · 10 Leve · 66 Poco importante · 7 Importante (Crítico y Muy importante en 0); naturaleza por etapa (pre-op 7/1 · transversal 71/9 · construcción 198/31 · operación 51/12 · post-op 10/30); acumulación 146 (34,8 %) / 274 (65,2 %) y sinergia 192 (45,7 %) / 212 (50,5 %) / 16 (3,8 %) — conteos verificados en la Matriz Cualitativa, excluyendo 2 bloques **incompletos** de AC_80 en SOC-10/SOC-11 que inflaban la matriz a 422 (no tienen naturaleza ni clasificación y no están en la hoja IMPORTANCIA); importancia global por medio (Abiótico −27,97 / +37,25 · Biótico −29,40 / +27,55 · Socioeconómico −32,08 / +29,33); resumen por etapa y **impactos más significativos por medio** (índice IMImp; Abiótico: ABIO-12 −52 —el único Severo—, ABIO-5 −26, ABIO-1 −25; Biótico: BIO-2 −41, BIO-3 −40, BIO-1 −36, BIO-5 −29; Socio (−): SOC-12 −39, SOC-13 −37, SOC-14 −36, SOC-1 −33; positivos destacados por medio).
  * Solo se listan impactos de clasificación **significativa** (Moderado/Severo y Poco importante), acorde con la metodología (Irrelevante = no significativo).
* **PMA y PSM**: el KPI de etapas pasa de 4 a **5** (pre-operativa · transversales · construcción · operación · post-operativa) y se agrega la fila **Pre-operativa** a las medidas (información y socialización comunitaria · negociación de predios y servidumbres), conforme a las actividades de la Matriz 02.
* **1% y Comp.**: la Matriz 02 no aporta datos de planes; la pestaña se mantiene con lo verificado (Cap. 11 y 12 no entregados).
* **Discrepancia detectada**: la presentación del tercer momento (PPTX) mostró 421 evaluaciones e «Importante 8»; la **Matriz 02 (fuente oficial) muestra 420 e Importante 7**. La app y el asistente Geo-IA usan los valores de la Matriz 02.

### 7.7 Colores del anexo y correcciones de sinergia (16-oct, cierre)

* **Sinergia «sin proyecto» corregida**: los conteos 59 / 74 / 6 (sin sinergia · moderado · muy sinérgico) se verificaron contra la Matriz Cualitativa y son correctos; lo que estaba mal eran los porcentajes de la hoja GRÁFICAS (los calculaba sobre 133 en lugar de las 139 interacciones). La app ahora muestra **59 (42,4 %) · 74 (53,2 %) · 6 (4,3 %)**.
* **Sinergia y acumulación «con proyecto» corregidas**: se contaron todas las interacciones en la Matriz Cualitativa y se excluyeron **2 bloques incompletos de AC_80** (en SOC-10 y SOC-11, sin naturaleza ni clasificación, ausentes en la hoja IMPORTANCIA) que inflaban el total a 422. Resultado coherente con las 420 interacciones: sinergia **192 (45,7 %) · 212 (50,5 %) · 16 (3,8 %)**; acumulación **146 (34,8 %) · 274 (65,2 %)**.
* **Paleta extraída de los formatos condicionales (dxfs) de las matrices 01 y 02** — la app usa ahora exactamente estos colores (`PALETA_CLASES`, `COLOR_NEGATIVO`, `COLOR_POSITIVO`):

| Elemento del anexo | Color |
|---|---|
| IRRELEVANTE | `#00B050` |
| MODERADO | `#FFFF00` |
| SEVERO (clasificación rotulada) | `#E26B0A` |
| CRÍTICO | `#C00000` |
| LEVE | `#8DB4E2` |
| POCO IMPORTANTE | `#BFBFBF` |
| IMPORTANTE | `#B1A0C7` |
| MUY IMPORTANTE | `#7030A0` |
| NEGATIVO (naturaleza) | `#FFCCCC` |
| POSITIVO (naturaleza) | `#D7E4BD` |

* Nota: para los **rangos numéricos** de severidad el anexo usa `#B97135` (naranja oscuro de tema) y para los ceros de la hoja IDENTIFICACIÓN `#E6B8B7`/`#C4D79B`; en la app se usó el color de la clasificación rotulada (`#E26B0A` para «Severo») por ser el más identificable al exponer.
* Acumulación y sinergia (sin convención propia en el anexo) usan colores de la misma familia: `#8DB4E2` → `#FFFF00` → `#E26B0A` (escalando en severidad).
* Las etiquetas internas de las gráficas ahora cambian automáticamente a **texto oscuro** cuando el segmento es claro (rosado `#FFCCCC`, verde `#D7E4BD`, amarillo `#FFFF00`), para que sean legibles.

---

## 8. Verificación de despliegue / portabilidad (16-oct-2026)

* Se construyó el paquete portable completo con `py -3.13 build_portable.py`: **`dist\MapaGarceroC\`** (588 MB, 843 archivos) — `MapaGarceroC.exe` (9,9 MB) + `_internal` (162 MB, con Python 3.13, fiona, pyproj —incluye `proj.db`—, shapely, matplotlib, requests y certifi) + páginas, `lib` (Leaflet local), `data`, `config` (caché GIS, KMZ EIA, clave IA) y `uploads` (319 MB de videos e imágenes).
* **Prueba de arranque del EXE**: abre con su Python interno, detecta la aplicación ya en ejecución y termina sin error (código 0).
* **Prueba tipo «otro dispositivo»**: se copió el paquete a otra ruta y se sirvió en el puerto 8120; responden correctamente `/api/ping`, `index6.html` (con los últimos cambios), `/api/data/estado` y los videos (petición por rangos, HTTP 206). Proceso de prueba detenido y copia eliminada.
* **ZIP de entrega** listo para nube/USB: `ENTREGA\MapaGarceroC_Portable_2026-10-16.zip` (**453,9 MB**). El `LEEME.txt` se actualizó (antes decía 524 MB / 1.213 archivos; ahora 454 MB / 843 archivos).
* **Estado final del disco (una sola copia)**: se conserva ÚNICAMENTE el ZIP de `ENTREGA\` como artefacto de despliegue; la carpeta intermedia `dist\` y `build_tmp\` se eliminaron para no duplicar peso. Para regenerar el paquete: `py -3.13 build_portable.py` y luego `EMPACAR_PARA_DRIVE.bat` (o `tar`).
* **Error frecuente a evitar**: en otro PC debe abrirse el paquete del ZIP (`MapaGarceroC\INICIAR.bat` o `MapaGarceroC.exe`). Si se copia la carpeta del proyecto **fuente** (C:\mapa, sin el .exe), el iniciador pedirá instalar Python — esa carpeta no es la portable.
* Rutas: el código usa `BASE_DIR` relativo (carpeta del EXE cuando está empaquetado); no hay rutas absolutas funcionales en el runtime.
* Internet solo se requiere para: teselas del mapa base (ArcGIS), fuentes de Google (hay respaldo tipográfico) y el asistente Geo-IA. Todo lo demás viaja local (Leaflet, KMZ, caché GIS, videos).
* En un PC con Python 3.13, `iniciar.bat` instala dependencias la primera vez (con internet) y arranca `server.py`; sin Python (o con 3.14), usa el EXE portable incluido.

---

## 9. Legibilidad y despliegue por carpeta (16-oct-2026)

**Letras más grandes para video/proyección.** Como todas las vistas del proyecto usan unidades `rem`, se subió el tamaño base en la raíz de `estilos.css` de 16 px (por defecto) a **17,5 px** (+9 % aproximado) — un solo bloque al final del archivo, marcado como «LEGIBILIDAD PARA VIDEO / PROYECCIÓN». Además las gráficas de `index6.html` pasaron de 13 px a **14 px** (`Chart.defaults.font.size`). Se actualizó `estilos.css?v=10` en las 6 páginas para forzar la recarga. Verificado en navegador: sin desbordes horizontales y con los anillos/barras dibujándose correctamente.

**Imágenes y video nuevos (19-oct-2026).** Se reemplazaron las portadas de las dos primeras tarjetas de **Estrategias** con las imágenes nuevas de `D:\videos garcero C`: `ESTRATEGIA-DE-DESARROLLO-13.jpg` → `assets/estrategias/est_coordenadas_bloque.webp` (Actualización de coordenadas) y `ESTRATEGIA-DE-DESARROLLO-1 1.jpg` → `assets/estrategias/est_vias_nuevas.webp` (Construcción de vías nuevas). El video `usos y usuarios.mp4` se copió como `uploads/video_usos_usuarios.mp4`, se le generó la miniatura `assets/caracterizacion/posters/video_usos_usuarios.webp` y quedó asignado a la tarjeta **Calidad del agua, usos y usuarios** de Caracterización (en el código y en `data/estado_app.json`).

**Sin botones de edición en las tarjetas (19-oct-2026).** Se retiró «Detalle / Editar» de las tarjetas de **Estrategias** (`index2.html`) y «Editar / Detalle» de las tarjetas de **Caracterización** (`index4.html`). En Caracterización también se quitaron el engranaje de gestión de video, el clic de «Subir video» (ahora muestra «Sin video») y el acceso a «Administrar videos del componente», de modo que las tarjetas quedan solo para consulta. La vista **Uso y Ap.** ya se había dejado estática.

**Uso y Aprovechamiento estático (19-oct-2026).** En `index3.html` se retiraron de la interfaz los botones «Exportar a Excel», «Nuevo Permiso / Uso», «Video General» y «Detalle / Editar» de todas las tarjetas. La vista ya no lee permisos del servidor ni del navegador: usa siempre `DEFAULT_PERMISOS` (con las 9 imágenes actuales) y el video general queda fijo en `uploads/video_usos_aprovechamiento.mp4`. Para agregar o cambiar un permiso, se edita directamente `DEFAULT_PERMISOS` en el código. Se conserva el botón «Ver Video» y la búsqueda/filtros por categoría.

**Colores Conesa en Evaluación de Impactos (19-oct-2026).** En `index6.html` los números de la tabla «Resumen de importancia por actividad» y de «Impactos significativos por medio» ahora usan el color exacto de la matriz oficial: Irrelevante verde `#00B050`, Moderado amarillo `#FFFF00`, Severo naranja `#E26B0A`, Leve azul `#8DB4E2`, Poco importante gris `#BFBFBF`, Importante lila `#B1A0C7`, Crítico rojo `#FF0000` y Muy importante morado `#7030A0`. Los conteos en cero quedan en gris tenue. Se añadió la clasificación completa (Crítico y Muy importante) para que los valores coincidan siempre con su etiqueta.

**Miniaturas de video en Caracterización (19-oct-2026).** Los videos de `index4.html` ya no arrancan en negro: se generaron miniaturas WebP con `ffmpeg` (fotograma representativo) en `assets/caracterizacion/posters/` para los 17 videos de `uploads/`, y se añadió `poster` a los `<video>` de tarjetas, detalle, visor ampliado, gestor y figuras. Si un video no tiene miniatura, se usa como respaldo la primera figura del componente. Las miniaturas se actualizan solas al cambiar de video con los chips.

**Zonificación: paneles y apertura inteligente (19-oct-2026).** Los paneles «Porcentajes por área» de `index5.html` pasan de 400 a **540 px** de ancho (con `max-width` para pantallas angostas), de modo que las columnas AI físico-biótica y AD Garcero C se ven completas; el pie de cada tabla se resume a dos líneas («Porcentaje calculado sobre el área de referencia de cada columna. Fuente: Tabla 9.14 del EIA» + verificación). Las leyendas y paneles plegables ahora calculan el espacio disponible al abrirse: si están cerca del borde inferior se despliegan **hacia arriba**, y si están cerca del borde derecho se alinean a la derecha; el alto se limita con scroll interno para no salir del mapa. Las leyendas base se inicializan siempre (aunque no haya KMZ) y conservan su posición arrastrable.

**Ajustes de contenido (19-oct-2026).** En `index6.html` se eliminaron las notas al pie que aparecían resaltadas: «Importancia Conesa: I = ±(3IN+2EX+…)» (escenarios sin/con proyecto) e «Índice = importancia media de cada impacto…» (impactos significativos sin/con proyecto). En `index5.html` la barra superior queda solo con el botón **«Bloque Garcero C»**: se ocultan sector/vereda, Descargar Capas GIS, Porcentajes por área, Importar, Subir .gdb, KMZ EIA, Limpiar y el panel KMZ; los mapas de zonificación cargan solos desde el servidor. `estilos.css` pasa a `v=12`.

**Segunda pasada de legibilidad (19-oct-2026).** La base tipográfica sube a **19 px** y el bloque «LEGIBILIDAD PARA VIDEO / PROYECCIÓN» fija mínimos por familia: navegación lateral a 16,15 px y en una sola línea (barra de 110 px), badges/chips/notas a 15,2–16,2 px, encabezados de tabla a 17,1 px y celdas a 18,05 px. Se ajustaron también las gráficas de `index6.html` (leyendas 16 px, ticks 14–15 px) y los tamaños pequeños incrustados en `index.html` e `index5.html`; el panel Geo-IA (`ia_geo.js`) sube sus textos a 0,85–0,9 rem. Se añadió `min-width: 0` a `.main-wrapper` y ajuste de encabezados para evitar desbordes, y los chips de categoría se limitan para no montarse sobre el chip de ID. `estilos.css` pasa a `v=11` en las 6 páginas. Verificado con capturas a 1600×900 en todas las vistas.

**Despliegue por carpeta (sin ZIP) con instalación automática de Python.** Se reescribió `iniciar.bat` para que la carpeta del proyecto funcione «tal cual» en otro PC. Orden de arranque:

1. `python_portable\python.exe` dentro del proyecto (si algún día se agrega; cero instalación).
2. Python del sistema 3.13 (o 3.x ≤ 3.13) por `py`/`python`.
3. `MapaGarceroC.exe` si existe junto al `.bat` (paquete ZIP; no instala nada).
4. **Instalación automática de Python 3.13**: primero con `winget install Python.Python.3.13 --scope user`; si winget no está, descarga el instalador oficial de python.org (`3.13.13 → 3.13.12 → … → 3.13.7`, se usa el primero disponible) y lo instala en silencio para el usuario. Luego instala dependencias con `pip install -r requirements.txt`.

Verificaciones realizadas: `winget` presente (v1.29) y los instaladores `python-3.13.x-amd64.exe` responden 200; la rama «sin Python» se probó en seco (`MAPA_DRY_RUN=1`) y llega correctamente al mensaje de instalación; la ruta normal arranca el servidor sin cambios. Variables de diagnóstico: `MAPA_DRY_RUN=1` (no instala, solo indica qué haría) y `MAPA_NO_PAUSE=1` (no pausa).

**ZIP reubicado.** `ENTREGA\MapaGarceroC_Portable_2026-10-16.zip` se movió a `C:\Users\Angel\OneDrive\Desktop\Entrega_MapaGarceroC\` para que `C:\mapa` viaje sin duplicados (queda solo el proyecto, 416 MB). El ZIP conserva su respaldo EXE (no requiere Python) y no se modificó para no forzar resincronización en OneDrive.

---

## 10. PMA & PSM reconstruidos con los Capítulos 7 y 8 de Garcero C (20-oct-2026)

Se incorporaron los documentos `CAPITULO 7. PLAN DE MANEJO AMBIENTAL.docx` y `CAPITULO 8. PLAN DE SEGUIMIENTO Y MONITOREO DEL PROYECTO.docx`, ambos del EIA de modificación de licencia del **AD Garcero C (PERENCO COLOMBIA LIMITED)**, elaborados por ASI S.A.S. (2026).

**Contenido verificable de la vista:**
* **PMA (Cap. 7):** 13 programas y 45 fichas → abiótico 4/27, biótico 7/13, socioeconómico 2/5.
* **PSM (Cap. 8):** 3 programas (uno por medio) y 19 fichas → 6 abiótico, 8 biótico, 5 socioeconómico.
* **4 tipos de medida:** prevención (P), mitigación (M), corrección (C) y compensación (CP).
* **Ficha PMA:** 18 campos (secciones 7.1.1–7.1.18); **ficha PSM:** 13 campos (8.1.1.1–8.1.1.13).
* Los listados completos de fichas quedan plegados («Ver las N fichas»); los códigos y nombres se transcribieron de la Tabla 7.1 y la Tabla 8.1.

**Cambios de interfaz:** selector PMA/PSM para mostrar un bloque a la vez, encabezado y pie de la pestaña con la fuente AD Garcero C, y enlace directo `index6.html?plan=psm#tab-pma`. Las cuatro tarjetas KPI son clicables y despliegan un resumen de 3 a 5 claves (PMA, programas, PSM y ficha PMA); también se puede abrir una directamente con `index6.html?clave=pma#tab-pma`. Se eliminó la tabla «Medidas de manejo aplicadas por etapa», que no provenía de estos capítulos.

**Pendiente:** los .docx entregados contienen el listado de fichas y la descripción de su estructura, pero no el desarrollo completo de cada ficha. Si se suministran las fichas detalladas, pueden añadirse metas, indicadores y presupuestos por ficha sin cambiar la estructura de la vista.

---

## 11. Vista 1% y Compensación reconstruida con los Capítulos 11 y 12 (20-oct-2026)

Se reconstruyó la pestaña **1% y Comp.** de `index6.html` con los documentos `CAP 11. PLAN DE INVERSIÓN DEL 1 %.docx` y `CAP 12. PLAN DE COMPENSACIÓN.docx` (ASI S.A.S., 2026; copias en `D:\ASI.SAS`). La vista quedó dividida en dos apartados con selector: **Inversión 1%** y **Compensación**.

**Inversión del 1% (Cap. 11):**
* Valor global del proyecto: **$73.525.000.000**; inversión forzosa del 1%: **$735.250.000** (Tabla 11.10).
* Tabla 11.9 resumida en **3 proyectos**: 3203 Gestión Integral del Recurso Hídrico, 3202 Conservación de la biodiversidad y sus servicios ecosistémicos y 1702 Inclusión Productiva de Pequeños Productores Rurales, con eje, sector y propósito.
* Texto 11.4.4 resumido en cuatro criterios: ámbito (subzona Caño Guanápalo y otros directos al Meta), priorización (cuerpos de agua, rondas hídricas EOT Orocué/San Luis de Palenque y APIC), acciones (conservación, enriquecimiento y aislamiento) y articulación (Plan Departamental y Corporinoquia 2024-2027).
* **Figura 11.6** extraída del .docx y convertida a `assets/figura_11_6.webp` (1351×909). Se muestra con una guía de lectura de sus polígonos, área de influencia, subzona y áreas APIC.
* Requisitos explícitos: mínimo 1%, misma subzona hidrográfica, predios y/o mejoras para conservación, Ley 99/1993 y Decreto 2099/2016; liquidación conforme al Art. 321 de la Ley 1955/2019.

**Compensación (Cap. 12):**
* Tabla 12.2 resumida en seis bloques: qué compensar (**362,60 ha** = 216,68 ha naturales/seminaturales + 145,92 ha transformadas), cuánto (**1.513,43 ha** en el rango geográfico 1), dónde (subzona Caño Guanápalo), cómo (3 acciones), modo/mecanismo/forma (acuerdos de conservación, compensación directa, individual) y valor/plazo (**8 años**).
* Tres acciones: preservar (88,53 ha), rehabilitar (vegetación secundaria y herbazales) y recuperar/uso sostenible (145,92 ha transformadas).
* Presupuesto detallado: **$58.298.743.826,56** (Tabla 12.35). Se dejó una nota de verificación porque la Tabla 12.2 registra **$59.788.243.826,56**; la vista muestra el total del presupuesto detallado.
* Requisitos explícitos: solo impactos residuales, no pérdida neta de biodiversidad, áreas ecológicamente equivalentes y actualización según la intervención real.

**Cambios técnicos:** se retiraron las gráficas y tablas anteriores del 1% (coberturas, inventario forestal, obligaciones y normativa) y su código Chart.js; se incorporaron estilos propios para la ecuación del 1%, los proyectos, la figura, los seis bloques de la Tabla 12.2, las acciones y la barra de composición. Enlaces directos: `index6.html?comp=inversion#tab-compensaciones` y `index6.html?comp=compensacion#tab-compensaciones`. Verificado sin errores de consola ni desbordes horizontales a 1600×1000, 1600×2600 y 1366×768.

---

## 12. Despliegue con Docker (20-oct-2026)

Se agregó soporte de contenedor para el proyecto:

* `Dockerfile` con `python:3.12-slim`, dependencias de `requirements.txt` y las carpetas de escritura.
* `docker-compose.yml` con publicación de puerto configurable (`MAPA_PUERTO`, por defecto 8000), volúmenes para `uploads`, `data` y `config`, healthcheck contra `/api/ping` y reinicio automático.
* `.dockerignore`, `.env.example` y `README_DOCKER.md` con los comandos de consola.
* `server.py` ahora acepta `MAPA_HOST` y `MAPA_PORT`; en Docker escucha en `0.0.0.0:8000` y no abre navegador (`MAPA_NO_BROWSER=1`, `MAPA_NO_PAUSE=1`). El comportamiento local sigue igual (127.0.0.1 y búsqueda entre 8000 y 8010).
* Autenticación básica opcional con `MAPA_AUTH_USER` y `MAPA_AUTH_PASSWORD`; `/api/ping` queda exento para el healthcheck.
* Perfil `tunnel` con Cloudflare Tunnel para publicar un enlace temporal `https://…trycloudflare.com` sin abrir puertos en el router.

**Verificación:** imagen `mapa-garcero-c:latest` construida y contenedor probado en el puerto 8080; `/api/ping` respondió OK, `index6.html` y `assets/figura_11_6.webp` respondieron HTTP 200 con autenticación, y los módulos `fiona`, `pyproj`, `shapely` y `matplotlib` cargaron dentro del contenedor. Se probaron `docker compose up -d`, `docker compose down` y el túnel público con respuesta 401 sin credenciales y 200 con credenciales.
