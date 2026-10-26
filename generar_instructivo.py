# -*- coding: utf-8 -*-
"""Genera el instructivo Word 'Instructivo Garcero C.docx' en D:\\trabajos word
con python-docx y capturas reales de la aplicacion."""
import os
from docx import Document
from docx.shared import Pt, Cm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

CAP = r"C:\Users\Angel\AppData\Local\Temp\opencode\cap_instructivo"
SALIDA = r"D:\trabajos word\Instructivo Garcero C.docx"

VERDE = RGBColor(0x00, 0xB0, 0x50)
NARANJA = RGBColor(0xE2, 0x6B, 0x0A)
AZUL = RGBColor(0x0B, 0x12, 0x20)
GRIS = RGBColor(0x5A, 0x66, 0x78)
BLANCO = RGBColor(0xFF, 0xFF, 0xFF)

doc = Document()

# ---------- Configuracion general ----------
sec = doc.sections[0]
sec.page_width = Cm(21.0)
sec.page_height = Cm(29.7)
sec.left_margin = Cm(2.2)
sec.right_margin = Cm(2.2)
sec.top_margin = Cm(2.0)
sec.bottom_margin = Cm(2.0)

st = doc.styles['Normal']
st.font.name = 'Calibri'
st.font.size = Pt(11)
st.element.rPr.rFonts.set(qn('w:eastAsia'), 'Calibri')

for nombre, tam, color in (('Heading 1', 16, VERDE), ('Heading 2', 13, NARANJA)):
    h = doc.styles[nombre]
    h.font.name = 'Calibri'
    h.font.size = Pt(tam)
    h.font.bold = True
    h.font.color.rgb = color


def sombrear(celda, hex_color):
    tcPr = celda._tc.get_or_add_tcPr()
    shd = OxmlElement('w:shd')
    shd.set(qn('w:val'), 'clear')
    shd.set(qn('w:fill'), hex_color)
    tcPr.append(shd)


def parrafo(texto, tam=11, negrita=False, color=None, espacios=4, alinear=None):
    p = doc.add_paragraph()
    if alinear is not None:
        p.alignment = alinear
    p.paragraph_format.space_after = Pt(espacios)
    r = p.add_run(texto)
    r.font.size = Pt(tam)
    r.bold = negrita
    if color is not None:
        r.font.color.rgb = color
    return p


def viñeta(texto, tam=11):
    p = doc.add_paragraph(style='List Bullet')
    p.paragraph_format.space_after = Pt(2)
    r = p.add_run(texto)
    r.font.size = Pt(tam)
    return p


def numerado(texto, tam=11, negrita_ini=None):
    p = doc.add_paragraph()
    p.paragraph_format.space_after = Pt(4)
    if negrita_ini:
        r0 = p.add_run(negrita_ini)
        r0.bold = True
        r0.font.size = Pt(tam)
    r = p.add_run(texto)
    r.font.size = Pt(tam)
    return p


def caja_titulo(texto, color_fondo):
    tabla = doc.add_table(rows=1, cols=1)
    tabla.alignment = WD_TABLE_ALIGNMENT.CENTER
    celda = tabla.cell(0, 0)
    sombrear(celda, color_fondo)
    p = celda.paragraphs[0]
    r = p.add_run(texto)
    r.bold = True
    r.font.size = Pt(11)
    r.font.color.rgb = BLANCO
    doc.add_paragraph().paragraph_format.space_after = Pt(2)
    return tabla


def tabla_datos(encabezados, filas, ancho_cols=None):
    t = doc.add_table(rows=1, cols=len(encabezados))
    t.style = 'Table Grid'
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    hdr = t.rows[0].cells
    for i, h in enumerate(encabezados):
        hdr[i].text = ''
        p = hdr[i].paragraphs[0]
        r = p.add_run(h)
        r.bold = True
        r.font.size = Pt(10)
        r.font.color.rgb = BLANCO
        sombrear(hdr[i], '0B1220')
    for fila in filas:
        celdas = t.add_row().cells
        for i, v in enumerate(fila):
            celdas[i].text = ''
            p = celdas[i].paragraphs[0]
            p.paragraph_format.space_after = Pt(0)
            r = p.add_run(v)
            r.font.size = Pt(10)
    if ancho_cols:
        for i, w in enumerate(ancho_cols):
            for fila in t.rows:
                fila.cells[i].width = Cm(w)
    doc.add_paragraph().paragraph_format.space_after = Pt(2)
    return t


# ================= PORTADA =================
portada = os.path.join(CAP, "0_portada.png")
if os.path.exists(portada):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.add_run().add_picture(portada, width=Cm(16.5))
else:
    parrafo("INSTRUCTIVO", 40, True, VERDE, 0, WD_ALIGN_PARAGRAPH.CENTER)
    parrafo("Mapa Garcero C", 30, True, AZUL, 0, WD_ALIGN_PARAGRAPH.CENTER)
doc.add_page_break()

# ================= 1. QUE ES =================
doc.add_heading('1. ¿Qué es esta aplicación?', level=1)
parrafo('Es el SIG (Sistema de Información Geográfica) del Estudio de Impacto Ambiental del '
        'Área de Desarrollo Garcero C (Perenco Colombia Limited, Casanare). Contiene los mapas, '
        'las capas temáticas, los datos del EIA y un asistente inteligente (Geo-IA) para consultar '
        'todo el proyecto sin necesidad de instalar ningún programa: funciona completamente '
        'portable desde una carpeta (USB, escritorio, OneDrive, Google Drive…).')

# ================= 2. COMO INICIAR =================
doc.add_heading('2. Cómo iniciar la aplicación', level=1)
numerado(' Descomprime el archivo ZIP completo (clic derecho → “Extraer todo…”). '
         'Debe quedar la carpeta llamada “MapaGarceroC”.', negrita_ini='1.')
numerado(' Abre la carpeta y haz doble clic en ', negrita_ini='2.')
p = doc.paragraphs[-1]
p.add_run('INICIAR.bat').bold = True
p.add_run(' (o directamente en MapaGarceroC.exe). No necesitas tener Python ni ningún programa instalado.')
numerado(' Se abre una ventana negra (el servidor) y luego el navegador '
         'con la aplicación. Deja la ventana negra abierta mientras uses la app; '
         'para cerrar la aplicación, cierra esa ventana.', negrita_ini='3.')
caja_titulo('💡 Consejo: si Windows te avisa “Windows protegió tu PC”, pulsa '
            '“Más información” y luego “Ejecutar de todas formas”. El archivo no está firmado, pero es seguro.',
            '1A3A26')

# ================= 3. PESTAÑAS =================
doc.add_heading('3. Las pestañas (menú de la izquierda)', level=1)
parrafo('La aplicación tiene 6 vistas en el menú superior. En cada una viven temas distintos del EIA:')
tabla_datos(
    ['Pestaña', '¿Para qué sirve?'],
    [
        ['Mapa (inicio)', 'Mapa interactivo con imagen de satélite y TODAS las capas GIS/KMZ: se cargan, se prenden y se apagan desde aquí.'],
        ['Estrategias (index2)', 'Plataformas, pozos, granjas solares, líneas de flujo y eléctricas, accesos, ampliación de Estación Sardinas, con gráficas.'],
        ['Uso y Aprovechamiento (index3)', 'Captaciones de agua, ocupaciones de cauce, aprovechamiento forestal, préstamo de material, inyección/reinyección, vertimiento, gasoducto.'],
        ['Caracterización (index4)', 'Tarjetas por componente: atmósfera, suelo, geología, hidrología, flora, fauna, socioeconómico… Cada tarjeta tiene un mini mapa con clic para ampliarlo.'],
        ['Zonificación (index5)', 'DOS MAPAS que cargan solos: Sensibilidad Ambiental y Categorías de Manejo (AE/AIR/AI), con el interruptor “Bloque Garcero C”.'],
        ['Gestión y Evaluación (index6)', 'Evaluación de impactos (Conesa), Plan de Manejo Ambiental (PMA), plan 1 % y compensaciones.'],
    ],
    ancho_cols=[4.5, 12.0],
)

# ================= 4. COMO CARGAR CAPAS =================
doc.add_heading('4. Cómo cargar las capas en el mapa', level=1)
parrafo('Todo se hace desde la pestaña Mapa (la de inicio):')
numerado(' Pulsa el botón ', negrita_ini='1.')
p = doc.paragraphs[-1]
p.add_run('«GDB locales»').bold = True
p.add_run('. Se abre el panel “Capas locales” con dos secciones: ')
p.add_run('Geodatabases (GDB EIA)').bold = True
p.add_run(' y ')
p.add_run('Capas temáticas EIA (KMZ locales).').bold = True
numerado(' Haz clic en la capa que quieras ver (por ejemplo, ', negrita_ini='2.')
p = doc.paragraphs[-1]
p.add_run('AreaInfluencia').bold = True
p.add_run(' o ').node = None
p.add_run('Zonificación Ambiental').bold = True
p.add_run('). En unos segundos se dibuja en el mapa con sus colores, su leyenda y sus puntos interactivos.')
numerado(' Para quitar una capa, apágala en la leyenda o pulsa el botón rojo “Quitar todo”.', negrita_ini='3.')
parrafo('¿Tienes una capa propia (un archivo SHP, KMZ, KML o una geodatabase .gdb de ArcGIS)?', 11, True)
viñeta('Botón «SHP / KMZ / KML»: abre el explorador de archivos y busca tu archivo en tus carpetas (como cuando adjuntas un archivo).')
viñeta('Botón «Subir carpeta .gdb»: eliges la carpeta File Geodatabase directamente desde tu disco.')
viñeta('También puedes pegar la ruta de un .gdb en el campo del panel «GDB locales» y pulsar “Cargar ruta”.')
viñeta('El sistema convierte las coordenadas a WGS84 automáticamente (funciona con MAGNA-SIRGAS y otros sistemas).')
img = os.path.join(CAP, "3_mapa.png")
if os.path.exists(img):
    doc.add_picture(img, width=Cm(16.2))
    doc.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER
    parrafo('Ilustración 1: la pestaña Mapa y el panel de capas locales.', 9, False, GRIS, 8, WD_ALIGN_PARAGRAPH.CENTER)

# ================= 5. CAPAS INCLUIDAS =================
doc.add_heading('5. Las capas que ya trae el proyecto', level=1)
parrafo('No necesitas archivos externos: todo viaja dentro de la carpeta (en caché portable).')
parrafo('Capas temáticas EIA (KMZ locales):', 11, True)
tabla_datos(
    ['Capa', 'Contenido'],
    [
        ['AreaProyecto', 'Polígono oficial del Área de Desarrollo Garcero C (19.872,68 ha).'],
        ['AreaInfluencia', 'Áreas de influencia por medio: Físicobiótico, Socioeconómico y Componentes (flora, fauna, hidrología, suelos…).'],
        ['CoberturaTierra', 'Coberturas Corine Land Cover: bosques, pastos, aguas, zonas urbanizadas…'],
        ['Zonificación Ambiental', 'Sensibilidad ambiental: Muy Alta, Alta, Moderada, Baja y Muy Baja.'],
        ['Zonificación de Manejo', 'Categorías de manejo: Exclusión (AE), Intervención con Restricciones (AIR) e Intervención (AI).'],
    ],
    ancho_cols=[5.0, 11.5],
)
parrafo('Geodatabases (GDB EIA) — se despliegan con solo hacer clic:', 11, True)
tabla_datos(
    ['Geodatabase', 'Capas'],
    [
        ['GDB EIA Garcero C', '12 capas: hidrografía, cuencas, unidades de paisaje, captaciones, puntos de muestreo, vulnerabilidad de acuíferos…'],
        ['Cartografía Básica', '22 capas: vías, drenajes, construcciones, municipios, límites…'],
    ],
    ancho_cols=[5.0, 11.5],
)

# ================= 6. FUNCIONALIDADES =================
doc.add_heading('6. Funcionalidades principales', level=1)
doc.add_heading('6.1 Prender y apagar capas (leyenda «Capas KMZ EIA»)', level=2)
viñeta('Cada capa tiene una casilla para mostrarla u ocultarla en el mapa.')
viñeta('Dentro de cada capa puedes prender/apagar categorías (ej. “Sensibilidad Muy Alta”) y, en AreaInfluencia, cada componente (Flora, Fauna, Suelos…) con su propio color.')
viñeta('Haz clic sobre un polígono o punto del mapa para ver sus atributos.')
viñeta('Cada categoría permite anotar con video, imagen y una nota breve (botón 🎬 de la leyenda).')
viñeta('Botón “Descargar” de la leyenda: exporta las capas a GeoJSON. También hay descargas KMZ/SHP en varias vistas.')
doc.add_heading('6.2 Mapas de zonificación (index5)', level=2)
parrafo('Al entrar en Zonificación, los dos mapas se cargan automáticamente. '
        'Puedes sincronizarlos (se mueven juntos), consultar la leyenda y usar el interruptor verde '
        '«Bloque Garcero C» para mostrar u ocultar el polígono del proyecto en ambos mapas.')
img = os.path.join(CAP, "1_zonificacion.png")
if os.path.exists(img):
    doc.add_picture(img, width=Cm(16.2))
    doc.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER
    parrafo('Ilustración 2: Zonificación Ambiental y de Manejo con el bloque del proyecto.', 9, False, GRIS, 8, WD_ALIGN_PARAGRAPH.CENTER)
doc.add_heading('6.3 Mini mapas de Caracterización (index4)', level=2)
parrafo('Cada tarjeta muestra un mini mapa temático del componente. Haz clic sobre el mapa para '
        'verlo ampliado en una ventana (igual que las imágenes). También puedes hacer clic en una '
        'tarjeta para abrir su detalle completo.')
img = os.path.join(CAP, "2_caracterizacion.png")
if os.path.exists(img):
    doc.add_picture(img, width=Cm(16.2))
    doc.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER
    parrafo('Ilustración 3: tarjetas de caracterización con sus mini mapas ampliables.', 9, False, GRIS, 8, WD_ALIGN_PARAGRAPH.CENTER)
doc.add_heading('6.4 Asistente Geo-IA', level=2)
parrafo('En cada vista hay un asistente (icono 🤖). Pregúntale sobre el EIA o sobre cómo usar la '
        'aplicación; por ejemplo:')
viñeta('“¿Cuántos pozos contempla el proyecto?” (datos del EIA).')
viñeta('“¿Cómo despliego los mapas?” (te guía paso a paso por los botones).')
viñeta('“¿Dónde está la zonificación?” (te dice la pestaña exacta y qué verás ahí).')
viñeta('La conversación se mantiene al cambiar de vista y solo se reinicia cuando se apaga la aplicación.')
parrafo('El asistente necesita internet. Las capas y los mapas, en cambio, funcionan sin internet.', 10, False, GRIS)

# ================= 7. PORTABLE =================
doc.add_heading('7. Llevarlo a otro computador (portable)', level=1)
numerado(' Copia la carpeta completa ', negrita_ini='1.')
p = doc.paragraphs[-1]
p.add_run('MapaGarceroC').bold = True
p.add_run(' (no solo el .exe) a una USB, OneDrive, Google Drive o a la carpeta de otro PC.')
numerado(' En el otro PC: descomprime si viene en ZIP, abre la carpeta en Documentos o Escritorio '
         'y haz doble clic en ', negrita_ini='2.')
p = doc.paragraphs[-1]
p.add_run('INICIAR.bat').bold = True
p.add_run('. No hace falta instalar nada: el proyecto lleva su propio Python interno.')
parrafo('Lo que edites (estrategias, permisos, imágenes, anotaciones) se guarda dentro de la carpeta '
        '(data/estado_app.json y uploads/), así que viaja con ella.')

# ================= 8. PROBLEMAS =================
doc.add_heading('8. Problemas frecuentes y soluciones', level=1)
tabla_datos(
    ['Problema', 'Solución'],
    [
        ['“Windows protegió tu PC” al abrir el .exe', 'Botón “Más información” → “Ejecutar de todas formas”. Es normal: el archivo no está firmado.'],
        ['La ventana negra se cierra sola', 'Revisa los archivos inicio_log.txt y error_inicio.txt junto al .exe (ábrelos con el Bloc de notas). Causa más común: se copió solo el .exe, no la carpeta completa.'],
        ['No se pueden guardar datos', 'La carpeta debe permitir escritura: copia el proyecto a Documentos, Escritorio o USB (evita “Archivos de programa”).'],
        ['La IA (Geo-IA) no responde', 'Necesita internet. Revisa que la clave esté configurada en config/ia_config.json (viene incluida y cifrada en el paquete).'],
        ['El fondo del mapa sale gris', 'Es la imagen satelital de fondo: necesita internet. Las capas y leyesendas siguen funcionando sin internet.'],
        ['El ZIP no extrae o falla a mitad', 'Borra la carpeta y extrae de nuevo completo (si hace falta, con 7-Zip).'],
        ['Dos aplicaciones abiertas a la vez', 'La segunda detección abre el navegador hacia la primera y no duplica el servidor.'],
    ],
    ancho_cols=[6.0, 10.5],
)

caja_titulo('📞 Soporte rápido: si algo falla, lee inicio_log.txt junto al programa '
            'y revísalo con el Bloc de notas: ahí dice exactamente qué pasó.', '4A1F17')

# ---------- Pie de pagina ----------
pie = sec.footer.paragraphs[0]
pie.alignment = WD_ALIGN_PARAGRAPH.CENTER
r = pie.add_run('Mapa Garcero C · SIG EIA Perenco Colombia Limited · Casanare · Instructivo v1')
r.font.size = Pt(8)
r.font.color.rgb = GRIS

doc.save(SALIDA)
print("OK -> " + SALIDA)
print("Tamano: {:.0f} KB".format(os.path.getsize(SALIDA) / 1024))