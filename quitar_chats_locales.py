# -*- coding: utf-8 -*-
"""Ligera la aplicacion: elimina los chatbots individuales de las vistas 2-6.
El unico asistente que queda es el ORIGINAL de la vista Mapa (index.html, boton
Geo-IA). El boton de las demas vistas lleva a index.html?chat=1, que abre el
mismo chat con la conversacion de la sesion conservada."""
import io

PAGINAS = [
    ("index2.html", "Asistente IA: proxy local", "GEO-IA (Estrategias)"),
    ("index3.html", "Configuración de la IA: proxy local", "GEO-IA (Uso y Aprov.)"),
    ("index4.html", "INTEGRACIÓN CON IA (proxy local", "GEO-IA (Caracterización)"),
    ("index5.html", "ASISTENTE GEO-IA (Zonificación)", "GEO-IA (Zonificación)"),
    ("index6.html", "ASISTENTE GEO-IA (Evaluación Ambiental", "GEO-IA (Evaluación)"),
]

NAV_VIEJO = """      <li class="nav-item" id="btn-toggle-ai" style="margin-top: auto; margin-bottom: 20px; color: var(--accent-blue);">
        <i data-lucide="sparkles"></i>
        <span>Geo-IA</span>
      </li>"""

NAV_NUEVO = """      <a href="index.html?chat=1" class="nav-item" style="margin-top: auto; margin-bottom: 20px; color: var(--accent-blue);" title="Abrir el asistente Geo-IA (se abre en la vista Mapa con tu conversación)">
        <i data-lucide="sparkles"></i>
        <span>Geo-IA</span>
      </a>"""

def recortar(texto, inicio, fin):
    """Elimina desde la linea que contiene `inicio` (incluida) hasta la linea
    que cierra la funcion que empieza con `fin` (incluida). Devuelve (nuevo, ok)."""
    lineas = texto.split("\n")
    i_inicio = None
    for i, ln in enumerate(lineas):
        if inicio in ln:
            i_inicio = i
            break
    if i_inicio is None:
        return texto, False
    i_fn = None
    for i, ln in enumerate(lineas):
        if fin in ln and i > i_inicio:
            i_fn = i
            break
    if i_fn is None:
        return texto, False
    # cerrar la funcion removeLoading: 3 lineas despues de 'if (el) el.remove();'
    i_cierre = None
    for i in range(i_fn, min(i_fn + 10, len(lineas))):
        if "el.remove" in lineas[i]:
            i_cierre = i + 1  # la linea '}' siguiente
            while i_cierre < len(lineas) and lineas[i_cierre].strip() not in ("}", "    }"):
                i_cierre += 1
            break
    if i_cierre is None:
        return texto, False
    # quitar tambien la linea en blanco anterior si sobra
    i_desde = i_inicio
    while i_desde > 0 and lineas[i_desde - 1].strip() == "":
        i_desde -= 1
    del lineas[i_desde:i_cierre + 1]
    return "\n".join(lineas), True

def quitar_panel_html(texto):
    """Elimina el bloque <div id="ai-panel" ...> ... </div> (balance por divs)."""
    i = texto.find('<div id="ai-panel"')
    if i < 0:
        return texto, False
    # balance de <div</div> desde la posicion del panel
    j = i
    nivel = 0
    while j < len(texto):
        if texto.startswith("<div", j):
            nivel += 1
            j += 4
        elif texto.startswith("</div", j):
            nivel -= 1
            j += 5
            if nivel == 0:
                break
        else:
            j += 1
    if nivel != 0:
        return texto, False
    j = texto.find(">", j) + 1  # cerrar el tag </div>
    return texto[:i] + texto[j:], True

def main():
    base = r"C:\mapa"
    for archivo, marca_js, _nombre in PAGINAS:
        ruta = base + "\\" + archivo
        with io.open(ruta, "r", encoding="utf-8") as f:
            t = f.read()
        ok1 = True
        if NAV_VIEJO in t:
            t = t.replace(NAV_VIEJO, NAV_NUEVO)
        else:
            print("AVISO {}: no encontre el nav Geo-IA esperado".format(archivo))
        t, ok2 = quitar_panel_html(t)
        t, ok3 = recortar(t, marca_js, "function removeLoading(id) {")
        t = t.replace("\n\n\n", "\n\n")
        with io.open(ruta, "w", encoding="utf-8") as f:
            f.write(t)
        print("{} -> nav:{}, panel:{}, js:{}".format(archivo, "ok" if not ok1 or NAV_VIEJO not in t else "?", ok2, ok3))

if __name__ == "__main__":
    main()