# -*- coding: utf-8 -*-
"""Mini servidor para el prototipo SIG - Perenco Garcero C

Uso local:
    python server.py

Uso en Docker (o detrás de un proxy):
    MAPA_HOST=0.0.0.0 MAPA_PORT=8000 MAPA_NO_BROWSER=1 MAPA_NO_PAUSE=1 python server.py

Abre: http://localhost:8000

Funciones:
  * Sirve todas las paginas (.html, .js, .css) y la carpeta /uploads
  * POST /api/upload -> guarda imagenes y videos dentro de la carpeta uploads
  * GET/POST /api/data/estado -> lee/fusiona los datos portables de la app
    (estrategias, permisos, caracterizacion, imagenes de terreno y anotaciones KMZ)
    en data/estado_app.json para que viajen de PC a PC junto al proyecto
  * POST /api/gis/convert -> convierte SHP (.zip), KMZ/KML y File Geodatabase (.gdb.zip) a GeoJSON WGS84
  * POST /api/chat  -> asistente IA basado en Gemini + base de conocimiento del EIA
"""
import os
import re
import io
import sys
import json
import base64
import hmac
import time
import math
import gzip
import html
import socket
import shutil
import hashlib
import zipfile
import tempfile
import threading
import unicodedata
import webbrowser
import http.server
import socketserver
import xml.etree.ElementTree as ET
from urllib.parse import urlparse, parse_qs

import requests


def _dir_base_aplicacion():
    """Carpeta de trabajo de la app.

    * Con Python instalado: la carpeta de este archivo (server.py).
    * Empaquetada con PyInstaller (MapaGarceroC.exe): la carpeta del ejecutable.

    Así los datos editables (uploads, data, config) viven SIEMPRE junto al
    proyecto/EXE y todo el paquete es portable de un computador a otro sin
    instalar Python."""
    if getattr(sys, "frozen", False):
        return os.path.dirname(os.path.abspath(sys.executable))
    return os.path.dirname(os.path.abspath(__file__))


BASE_DIR = _dir_base_aplicacion()
UPLOAD_DIR = os.path.join(BASE_DIR, "uploads")
CONFIG_DIR = os.path.join(BASE_DIR, "config")
CONOCIMIENTO = os.path.join(BASE_DIR, "data", "conocimiento_eia.json")
DATA_DIR = os.path.join(BASE_DIR, "data")
ESTADO_FILE = os.path.join(DATA_DIR, "estado_app.json")
PORT = 8000

# Identificador ÚNICO de esta sesión del servidor: cambia cada vez que se
# arranca la aplicación. La página lo usa para recordar la vista de capas KMZ
# (encendido/apagado, colores, mapa) SOLO mientras el proyecto siga corriendo:
# al apagar y volver a abrir la app, el token es otro y todo reinicia limpio.
SESION_ID = hashlib.sha256(os.urandom(16)).hexdigest()[:16]

# Extensiones permitidas (imagenes y videos)
ALLOWED_EXT = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp",
               ".mp4", ".webm", ".ogv", ".ogg", ".mov", ".m4v"}
ALLOWED_MIME = {
    "image/png",
    "image/jpeg",
    "image/gif",
    "image/webp",
    "image/bmp",
}
ALLOWED_VIDEO_MIME = {
    "video/mp4",
    "video/webm",
    "video/ogg",
    "video/quicktime",
    "application/ogg",
}
MAX_SIZE = 25 * 1024 * 1024  # 25 MB para imagenes
MAX_VIDEO_SIZE = 1024 * 1024 * 1024  # 1 GB para videos

# ---------- Configuracion de la IA (Gemini) ----------

STOPWORDS = set(
    "el la los las un una unos unas de del que y o a al con por para en es su se "
    "no me mi tu como mas pero este esta estos estas ese esa esos esas lo le les "
    "sus si ya fue han estar tener tiene tiene decir dijo donde cuando muy puede "
    "todos toda cual quien cuales otro otra otros otras dentro sobre entre hacia "
    "hasta desde antes despues cada mismo misma mismos mismas yo tu nosotros ellas "
    "ellos hay hayan haber hemos hacen hacer hace porque tambien solo si misma "
    "ambas veces dia".split()
)

# Palabras clave del proyecto (normalizadas a minusculas SIN tildes y por palabra,
# igual que devuelve normalizar()). Se usan para reconocer preguntas del EIA.
TEMAS_PROYECTO = [
    "garcero", "perenco", "casanare", "orocue", "palenque", "bloque",
    "eia", "licencia", "ambiental", "ambiente", "impacto", "resolucion",
    "anla", "expediente", "normativo",
    "plataforma", "plataformas", "pozo", "pozos", "sardinas", "jordan",
    "paravare", "guasar", "candalay", "jorcán", "jorcan", "pirito",
    "capachos", "estacion", "subestacion", "facilidad",
    "captacion", "captaciones", "tujua", "guanapalo", "guirripa", "duya",
    "cano", "rio", "hidrico", "cauce", "ocupaciones", "caudal", "aguas",
    "inyeccion", "reinyeccion", "reinyecta", "bwpd", "recobro",
    "formacion", "carbonera", "guadalupe", "arenisca", "areniscas",
    "subsuelo", "lodos", "piscinas", "skimmer", "tea", "quema",
    "influencia", "socioeconomico", "abiotico", "biotico", "utm",
    "vereda", "veredas", "municipio", "municipios", "resguardo",
    "medano", "indigena", "territorial",
    "granja", "solar", "fotovoltaica", "mw", "paneles", "modulos",
    "inversores", "linea", "lineas", "flujo", "electrica", "electricas",
    "acceso", "accesos", "via", "vias", "carretera", "tuberia",
    "forestal", "aprovechamiento", "prestamo", "material", "terraplenes",
    "hidrocarburo", "hidrocarburos", "petroleo", "gas", "explotacion",
    "exploracion", "produccion", "perforacion",
    "zonificacion", "cobertura", "coberturas", "paisaje", "componente",
    "componentes", "generalidades", "metodologia", "caracterizacion",
    "caracteriza", "medidas", "mitigacion", "compensacion", "manejo",
    "monitoreo", "vertimiento", "vertimientos", "residuales", "emision",
    "emisiones", "atmosfericas", "proyecto", "obras", "estudio",
    "objetivos", "antecedentes", "solicitado", "solicitar", "solicitud",
    "clasificacion", "recursos", "afectacion", "estudio de impacto",
    "magna", "sirgas", "coordenadas", "geologico", "geotecnia",
    "hidrogeologia", "vulnerabilidad", "acuifero", "drenaje",
    "permiso", "permisos", "residuo", "residuos", "solido", "solidos",
    "solicita", "solicitan", "maneja", "manejan", "objetivo",
    "19872", "467329", "315829", "151500", "3172",
]

_PALABRAS_GENERICAS = {
    "hola", "buenas", "buen", "buenos", "dia", "dias", "tarde", "noche",
    "noches", "que", "tal", "hey", "hello", "hi", "saludos", "cordiales",
    "gracias", "adios", "chao", "bien", "mal", "ok", "okay", "si", "no",
    "por", "favor", "porfavor", "help", "ayuda", "ayudame", "dime", "ver",
    "como", "donde", "cuando", "porque", "quien", "cual", "cuales",
    "link", "enlace", "pagina", "web", "site", "google", "youtube",
    "tu", "yo", "mi", "conmigo", "tengo", "puedo", "puedes", "quiero",
    "fotos", "imagen", "imagenes", "video", "videos",
    "math", "calculo", "calcular", "resolver", "suma", "sumar", "resta",
    "multiplicacion", "division", "dame", "dale", "envia", "manda",
    "cuanto", "cuantos", "cuanta", "cuantas", "eres", "sabes", "nombre",
    "haz", "hacer", "metete", "pasa", "explica", "habla", "cuentame",
    "capital", "presidente", "pais", "mundo", "tiempo", "hora", "fecha",
    "dia", "semana", "ano", "ayer", "hoy", "manana",
}

# Palabras del proyecto que son SOLO numeros (para no descartarlas al filtrar digitos).
TEMAS_NUMERICOS = {t for t in TEMAS_PROYECTO if t.isdigit()}


def _tokens_significativos(mensaje):
    """Tokens con contenido real: quita stopwords, genéricos y numeros sueltos."""
    terminos = set(normalizar(mensaje))
    sig = set()
    for t in terminos:
        if t.isdigit():
            if t in TEMAS_NUMERICOS:
                sig.add(t)
            continue
        if t in STOPWORDS or t in _PALABRAS_GENERICAS:
            continue
        sig.add(t)
    return sig


def _coincide_tema(tok, temas):
    """True si el token coincide con un tema del proyecto, tolerando plurales,
    femeninos y sufijos verbales comunes (mini-stemming en espanol)."""
    if tok in temas:
        return True
    t = tok
    for _ in range(4):
        if t.endswith("ciones") and len(t) > 7:
            t = t[:-6] + "cion"
        elif t.endswith("imientos") and len(t) > 8:
            t = t[:-8]
        elif (t.endswith("es") or t.endswith("as") or t.endswith("os")) and len(t) > 4:
            t = t[:-2]
        elif t.endswith("s") and not t.endswith("ss") and len(t) > 3:
            t = t[:-1]
        elif t.endswith("an") or t.endswith("en") or t.endswith("on"):
            if len(t) > 4:
                t = t[:-2]
        elif (t.endswith("ar") or t.endswith("er") or t.endswith("ir")) and len(t) > 4:
            t = t[:-2]
        else:
            break
        if t in temas:
            return True
    return False


def es_pregunta_proyecto(mensaje):
    """True si la consulta parece ser sobre el EIA del Bloque Garcero C.
    Bloquea lo obvio (mates, enlaces, saludos sueltos o preguntas ajenas) y
    deja pasar las preguntas abiertas sobre el proyecto (Gemini tambien
    rechaza en su instruccion cualquier tema ajeno)."""
    m = (mensaje or "").lower()
    # 1) Operaciones matematicas: '2+2', 'cuanto es 5 * 3', '3x4'...
    if re.search(r"\d\s*[+\-*xX/]\s*\d", m):
        return False
    # 2) Pedir/dar enlaces o urls
    if re.search(r"https?://|www\.|\.com\b|\.net\b|\.org\b|\.pdf\b|\.co\b",
                 m.replace(" ", "")):
        return False
    # 3) Expresiones con contenido sustantivo
    sig = _tokens_significativos(mensaje)
    if not sig:
        return False
    temas = set(TEMAS_PROYECTO)
    if any(_coincide_tema(t, temas) for t in sig):
        return True
    # 4) Pregunta abierta con varias palabras sustantivas: se deja pasar
    #    (la instruccion del sistema rechaza lo que no sea del proyecto).
    if len(sig) >= 4:
        return True
    return False


def _semilla_ia():
    """Semilla interna para descifrar la clave de Gemini. NO viaja en el archivo
    de configuración: se reconstruye a partir de fragmentos del propio código,
    para que quien se lleve config/ia_config.json se lleve basura ilegible."""
    a = "Perenco"
    b = "Garcero-C"
    c = "LAM0165"
    d = "geoiadesk"
    e = "9b7c" + "2f41"
    return (a + "|" + b + "|" + c + "|" + d + "|" + e).encode("utf-8")


def _descifrar_clave_ia(enc):
    """Descifra GEMINI_API_KEY_ENC (cifrado XOR en modo contador con SHA-256).
    El archivo config/ia_config.json SOLO contiene el texto cifrado: si alguien
    lo extrae del paquete, no obtiene ninguna clave utilizable."""
    import base64
    try:
        datos = base64.b64decode(str(enc or "").strip())
    except Exception:
        return ""
    if not datos:
        return ""
    semilla = _semilla_ia()
    salida = bytearray()
    bloque = 0
    while bloque * 32 < len(datos):
        stream = hashlib.sha256(semilla + bloque.to_bytes(8, "little")).digest()
        for j in range(32):
            i = bloque * 32 + j
            if i >= len(datos):
                break
            salida.append(datos[i] ^ stream[j])
        bloque += 1
    try:
        return salida.decode("utf-8")
    except Exception:
        return ""


def cargar_config_ia():
    clave = os.environ.get("GEMINI_API_KEY", "").strip()
    modelo = os.environ.get("GEMINI_MODEL", "gemini-flash-lite-latest").strip()
    ruta = os.path.join(CONFIG_DIR, "ia_config.json")
    if not clave and os.path.exists(ruta):
        try:
            with open(ruta, "r", encoding="utf-8") as f:
                cfg = json.load(f)
            clave = str(cfg.get("GEMINI_API_KEY", "")).strip()
            if not clave:
                # La clave viaja CIFRADA; aquí se reconstruye solo en memoria.
                clave = _descifrar_clave_ia(cfg.get("GEMINI_API_KEY_ENC", ""))
            modelo = str(cfg.get("GEMINI_MODEL", modelo)).strip()
        except Exception:
            pass
    return {"key": clave, "model": modelo or "gemini-flash-lite-latest"}


def normalizar(texto):
    texto = unicodedata.normalize("NFD", texto or "")
    texto = "".join(c for c in texto if unicodedata.category(c) != "Mn")
    return re.findall(r"[a-z0-9]+", texto.lower())


def cargar_conocimiento():
    if not os.path.exists(CONOCIMIENTO):
        return []
    try:
        with open(CONOCIMIENTO, "r", encoding="utf-8") as f:
            return [t for t in json.load(f) if t.get("texto")]
    except Exception:
        return []


_CONOCIMIENTO = cargar_conocimiento()
# Contexto reducido (antes 12000): respuestas más rápidas con la misma precisión.
MAX_CONTEXTO = 6000


def recuperar_contexto(pregunta, limite=MAX_CONTEXTO):
    if not _CONOCIMIENTO:
        return ""
    terminos = [t for t in normalizar(pregunta) if t not in STOPWORDS and len(t) > 2]
    if not terminos:
        return ""

    puntuados = []
    for trozo in _CONOCIMIENTO:
        cuerpo = (trozo.get("texto") or "").lower()
        palabras = re.findall(r"[a-z0-9]+", cuerpo)
        score = sum(palabras.count(t) for t in terminos)
        if score > 0:
            puntuados.append((score, trozo))

    puntuados.sort(key=lambda x: x[0], reverse=True)
    partes, total = [], 0
    for score, trozo in puntuados:
        texto = trozo["texto"].strip()
        if total + len(texto) > limite:
            continue
        partes.append(f"[{trozo['fuente']} - pag. {trozo['pagina']}]\n{texto}")
        total += len(texto)
    return "\n\n".join(partes)


def consultar_gemini(mensaje, sistema):
    cfg = cargar_config_ia()
    if not cfg["key"] or cfg["key"].startswith("PEGA_TU"):
        return {"ok": False, "clave": True, "respuesta": (
            "La IA no esta configurada: falta la API key de Gemini. "
            "Pega tu clave en config/ia_config.json y reinicia el servidor."
        )}

    cuerpo = {
        "contents": [{"parts": [{"text": mensaje}]}],
        "systemInstruction": {"parts": [{"text": sistema}]},
        "generationConfig": {"temperature": 0.3, "maxOutputTokens": 700},
    }
    url = "https://generativelanguage.googleapis.com/v1beta/models/{}:generateContent?key={}".format(
        cfg["model"], cfg["key"]
    )

    # Modelos de respaldo estables (los 2.5 ya estan desactivados para cuentas nuevas).
    alternativos = ["gemini-flash-lite-latest", "gemini-3.5-flash", "gemini-flash-latest"]
    candidatos = [cfg["model"]] + [m for m in alternativos if m != cfg["model"]]

    r = None
    for modelo in candidatos:
        url = "https://generativelanguage.googleapis.com/v1beta/models/{}:generateContent?key={}".format(
            modelo, cfg["key"]
        )
        try:
            r = requests.post(url, json=cuerpo, timeout=120)
        except requests.exceptions.RequestException as e:
            return {"ok": False, "respuesta": "Error de conexion con Gemini: {}. Revisa tu red.".format(e)}
        # 200 = exito; si no, probamos el siguiente modelo.
        if r.status_code == 200 and r.text.strip():
            try:
                if r.json().get("candidates"):
                    break
            except ValueError:
                pass
        time.sleep(0.3)

    try:
        data = r.json()
    except (ValueError, AttributeError):
        return {"ok": False, "respuesta": "Respuesta invalida de Gemini (HTTP {}).".format(
            r.status_code if r else "sin respuesta"
        )}

    if r.status_code != 200 or not data.get("candidates"):
        try:
            msg = data["error"]["message"]
        except (KeyError, TypeError):
            msg = ""
        if r.status_code == 503:
            return {"ok": False, "respuesta": (
                "Gemini está saturado temporalmente (HTTP 503, alta demanda). "
                "Intenta de nuevo en unos segundos."
            )}
        return {"ok": False, "respuesta": (
            "Gemini devolvio un error (HTTP {}): {}. Verifica la API key en config/ia_config.json.".format(
                r.status_code, msg or "sin detalle"
            )
        )}

    try:
        texto = data["candidates"][0]["content"]["parts"][0]["text"]
    except (KeyError, IndexError, TypeError):
        return {"ok": False, "respuesta": "Gemini respondio sin contenido de texto."}

    return {"ok": True, "respuesta": texto.strip()}


# ---------- Guia de uso de la aplicacion (preguntas "como/ donde") ----------
# Texto oficial que GEO-IA usa para guiar al usuario paso a paso por el
# proyecto: pestanas, botones, capas, ubicacion de cada tema y datos portables.

GUIA_APP = """\
PESTANAS DE LA APLICACION (menu superior; cada una es una vista):
- MAPA (inicio): mapa interactivo con imagen de satelite y todas las capas GIS/KMZ del EIA (geodatabases, KMZ EIA, SHP, KML).
- ESTRATEGIAS (index2): estrategias de desarrollo, plataformas, pozos, granjas solares, lineas de flujo y electricas, accesos, ampliacion Estacion Sardinas, con graficas.
- USO Y APROVECHAMIENTO (index3): captaciones de agua (Canos Tujua, Guanapalo), ocupaciones de cauce, aprovechamiento forestal, prestamo de material, gasoducto Chiguirios, inyeccion/reinyeccion y vertimiento.
- CARACTERIZACION (index4): tarjetas por componente (atmosfera, suelo, geologia, hidrologia, flora, fauna, socioeconomico...), cada una con mini mapa (clic para ampliarlo), estadisticas y graficas.
- ZONIFICACION (index5): dos mapas sincronizados: Sensibilidad Ambiental (Muy Alta a Muy Baja) y Categorias de Manejo (AE, AIR, AI). El interruptor verde «Bloque Garcero C» muestra/oculta el poligono del proyecto en ambos mapas.
- GESTION Y EVALUACION (index6): evaluacion de impactos (metodologia Conesa), Plan de Manejo Ambiental (PMA), PSM, plan 1 % y compensaciones.

COMO DESPLEGAR CAPAS EN EL MAPA (index):
- Boton «SHP / KMZ / KML»: abre el explorador de archivos para buscar una capa en tus carpetas (zip, kmz, kml). El sistema la convierte sola a WGS84.
- Boton «Subir carpeta .gdb»: eliges la carpeta File Geodatabase de ArcGIS desde tu disco.
- Boton «GDB locales»: lista las geodatabases incluidas (GDB EIA Garcero C con 12 capas y Cartografia Basica con 22, en cache portable) y las capas KMZ EIA. Al hacer clic en una se despliega con tiles, leyenda y puntos interactivos; clic sobre un punto/area abre sus atributos.
- Boton «KMZ EIA»: lista las capas tematicas locales (AreaProyecto, AreaInfluencia, CoberturaTierra, ZonificacionAmbiental, ZonificacionManejo); clic para aplicarlas.
- Leyenda «Capas KMZ EIA»: prender/apagar archivos, categorias y componentes; cada categoria permite anotar (video, imagen, nota). Los cambios de vista se recuerdan mientras el proyecto este encendido.

DONDE ESTA CADA TEMA (guia rapida):
- Pozos, plataformas, granjas solares, accesos, lineas, Estacion Sardinas: pestana ESTRATEGIAS.
- Agua, captaciones, ocupaciones de cauce, aprovechamiento forestal, inyeccion, vertimiento, gasoducto: pestana USO Y APROVECHAMIENTO.
- Medio abiotico, biotico y socioeconomico, coberturas (Corine), suelo, flora, fauna, hidrologia, atmosfera: pestana CARACTERIZACION (tarjetas con mini mapas).
- Sensibilidad ambiental, categorias de manejo AE/AIR/AI, bloque de Garcero C: pestana ZONIFICACION.
- Impactos, PMA, PSM, plan 1 %, compensaciones: pestana GESTION Y EVALUACION.
- Capas, geodatabases, KMZ EIA y mapa interactivo: pestana MAPA.

DATOS PORTABLES: lo que se edita o sube (estrategias, permisos, caracterizacion, imagenes, videos, anotaciones) vive en data/estado_app.json y en la carpeta uploads/, junto al proyecto; al copiar la carpeta completa a otro PC, los cambios viajan.

ASISTENTE GEO-IA: necesita internet y la clave de Gemini en config/ia_config.json (viene cifrada dentro del paquete; no es visible para el usuario).

COMO ARRANCAR: doble clic en INICIAR.bat (o en MapaGarceroC.exe). Deja la ventana negra abierta; ahi se sirve http://localhost:8000. Si algo falla, revisa inicio_log.txt. Si la IA no responde, revisa la configuracion de la clave y la conexion a internet.
"""

# Palabras/frases que indican una pregunta de USO/UBICACION (no de datos del EIA)
GUIA_PISTAS = [
    "como despleg", "desplegar", "despliego", "despliegue",
    "como funciona", "como funcionan", "como usar", "como se usa", "como lo uso",
    "como abro", "como abrir", "como cargo", "como cargar", "como subir",
    "como importar", "como exportar", "como descargar", "como anotar",
    "como hago", "como puedo", "como activo", "como prendo", "como apago",
    "como instalar", "como iniciar", "como ejecutar", "como correr",
    "donde esta", "donde esta", "donde encuentro", "donde queda", "donde puedo",
    "donde veo", "donde cargo", "donde subo", "donde se guarda", "donde se ve",
    "pestana", "boton", "botones", "menu", "menu superior",
    "tutorial", "guia", "guiam", "instrucciones", "ayudame a", "ayudame con",
    "explicame como", "explica como", "enseñame", "ensename",
    "no se usar", "no se como", "no se usar", "no puedo ver", "no puedo abrir",
    "iniciar.bat", "iniciar bat", "mapa garcero", "que vista", "en que vista",
    "que pestana", "que boton", "para que sirve", "que contiene",
    "bloque garcero", "como se ve", "se puede activar", "prender", "apagar la capa",
]


def _es_pregunta_guia(mensaje):
    """True si el usuario pregunta COMO se usa la aplicacion o DONDE esta algo."""
    m = " ".join(normalizar(mensaje))
    if not m:
        return False
    return any(pista in m for pista in GUIA_PISTAS)


def _responder_guia(mensaje):
    """Responde preguntas de uso/ubicacion con la guia oficial de la app.
    Usa Gemini (con la guia como contexto) o, si no hay clave, el texto estatico."""
    cfg = cargar_config_ia()
    if cfg["key"]:
        sistema = (
            "Eres GEO-IA, asistente de la aplicacion SIG del EIA del Area de Desarrollo "
            "Garcero C (Perenco Colombia Limited, Casanare). El usuario te pregunta COMO "
            "USAR LA APLICACION o DONDE ESTA cierta informacion dentro del proyecto. "
            "Responde SIEMPRE con la GUIA OFICIAL que se te da a continuacion: indica la "
            "pestana o boton exacto, el paso a paso corto y el tema solicitado. Si la guia "
            "no cubre algo, di que no esta documentado. Responde corto, claro y directo."
        )
        return consultar_gemini(
            mensaje,
            sistema + "\n\n=== GUIA OFICIAL DE LA APLICACION ===\n" + GUIA_APP,
        )
    return {"ok": True, "respuesta": GUIA_APP}


def manejar_chat(handler, cuerpo):
    mensaje = (cuerpo.get("mensaje") or "").strip()
    if not mensaje:
        send_json(handler, {"ok": False, "respuesta": "Escribe una consulta primero."}, 400)
        return

    palabras = set(normalizar(mensaje))
    if palabras and palabras.issubset({
        "hola", "buenas", "buen", "buenos", "dia", "dias", "tarde", "noche",
        "noches", "que", "tal", "hey", "hello", "hi", "saludos", "cordiales",
    }) and len(palabras) <= 4:
        send_json(handler, {"ok": True, "respuesta": (
            "¡Hola! Soy GEO-IA, asistente del EIA del Área Garcero C (Perenco, Casanare). "
            "Solo puedo responder sobre el proyecto. "
            "¿En qué puedo servirte? Por ejemplo:\n\n"
            "• ¿Qué caracteriza el medio abiótico?\n"
            "• ¿Cuántos pozos contempla el proyecto?\n"
            "• ¿Cuál es el área de influencia socioeconómica?\n"
            "• ¿Cuántas plataformas tiene el proyecto?\n"
            "• ¿Qué obras se han solicitado?\n"
            "• ¿Cuál es el caudal de inyección/reinyección?\n"
            "• ¿Qué municipios componen el área de influencia?\n\n"
            "Escríbeme sobre el EIA del Bloque Garcero C."
        )})
        return

    # Preguntas de USO/UBICACION («¿cómo despliego los mapas?», «¿dónde está la
    # zonificación?»...): se responden con la guía oficial de la aplicación.
    if _es_pregunta_guia(mensaje):
        send_json(handler, _responder_guia(mensaje))
        return

    if not es_pregunta_proyecto(mensaje):
        send_json(handler, {"ok": True, "respuesta": (
            "⚠️ Solo puedo responder preguntas sobre el **EIA del Área de Desarrollo "
            "Garcero C (Perenco Colombia Limited, Casanare)**.\n\n"
            "No estoy autorizado para responder cálculos matemáticos, dar enlaces web, "
            "ni responder preguntas ajenas al proyecto.\n\n"
            "**Ejemplos de lo que sí puedo responder:**\n"
            "• Características del proyecto y sus obras\n"
            "• Datos del EIA (área, plataformas, pozos, captaciones)\n"
            "• Municipios y UTM del área de influencia\n"
            "• Medios abiótico, biótico y socioeconómico\n"
            "• Resoluciones y licencias ambientales\n"
            "• Componentes y zonificaciones del proyecto\n\n"
            "¿Sobre qué tema del EIA quieres información?"
        )})
        return

    sistema = (cuerpo.get("sistema") or "").strip() or (
        "Eres GEO-IA, asistente experto ÚNICAMENTE en el EIA del Área de Desarrollo "
        "Garcero C (Perenco Colombia Limited, Casanare). ESTÁ PROHIBIDO responder preguntas "
        "que no sean sobre este proyecto. Si te preguntan algo que no sea del EIA (matemáticas, "
        "enlaces web, preguntas personales, cálculos, etc.), rechaza amablemente y recuerda al "
        "usuario que solo respondes sobre el proyecto.\n"
        "FORMATO OBLIGATORIO (respuestas fáciles de leer):\n"
        "1) Una frase corta inicial (máximo 1 línea) que responda directamente.\n"
        "2) De 3 a 6 viñetas que empiecen con \"• \" con los datos clave; escribe en **negrita** "
        "las cifras y nombres importantes.\n"
        "3) Si tienes la fuente, cierra con \"Fuente: CAP n.º, pág. n.º\".\n"
        "No uses párrafos largos, no repitas la pregunta y no superes 120 palabras."
    )

    contexto = recuperar_contexto(mensaje)
    if contexto:
        contexto_final = (
            "A continuacion tienes TROZOS OFICIALES extraidos de los documentos "
            "del EIA real (CAP 1 y CAP 2). Usalos como fuente principal de verdad "
            "para responder, citando entre parentesis el capitulo y la pagina cuando sea util.\n\n"
            + contexto
        )
    else:
        contexto_final = (
            "No se encontro un fragmento especifico en la base de conocimiento para "
            "esta consulta. Responde con tus conocimientos tecnicos y los datos que "
            "se te indican en la instruccion del sistema. SI la consulta no es sobre "
            "el EIA del Bloque Garcero C, rechaza responder."
        )

    sistema_total = sistema + "\n\n=== CONTEXTO DEL EIA (CAP 1 / CAP 2) ===\n" + contexto_final
    respuesta = consultar_gemini(mensaje, sistema_total)
    send_json(handler, respuesta)


# ---------- Utilidades generales ----------

def send_json(handler, data, status=200):
    body = json.dumps(data, ensure_ascii=False).encode("utf-8")
    extra = {}
    if len(body) > 1024 and "gzip" in (handler.headers.get("Accept-Encoding") or "").lower():
        body = gzip.compress(body, 6)
        extra["Content-Encoding"] = "gzip"
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json; charset=utf-8")
    for k, v in extra.items():
        handler.send_header(k, v)
    handler.send_header("Content-Length", str(len(body)))
    handler.end_headers()
    handler.wfile.write(body)


# ---------- Estado portable de la aplicacion (data/estado_app.json) ----------
# Las imagenes y los datos editables (estrategias, permisos, caracterizacion, etc.)
# se guardan aqui para que viajen con el proyecto de un computador a otro.
# El POST es PARCIAL: las claves recibidas se fusionan sobre el archivo existente.

def _leer_estado():
    if not os.path.isfile(ESTADO_FILE):
        return {}
    try:
        with open(ESTADO_FILE, "r", encoding="utf-8") as fh:
            datos = json.load(fh)
        return datos if isinstance(datos, dict) else {}
    except Exception:
        return {}


def _fusionar_estado(parche):
    os.makedirs(DATA_DIR, exist_ok=True)
    actual = _leer_estado()
    for clave, valor in (parche or {}).items():
        if valor is not None:
            actual[clave] = valor
    try:
        with open(ESTADO_FILE, "w", encoding="utf-8") as fh:
            json.dump(actual, fh, ensure_ascii=False, indent=2)
    except Exception:
        pass
    return actual


def sanitize_name(name):
    name = os.path.basename(name or "")
    name = re.sub(r"[^A-Za-z0-9._-]", "_", name)
    name = re.sub(r"_+", "_", name)
    return name[:80] or "imagen"


# ---------- Conversion de capas GIS (SHP / KMZ / GDB) ----------
# Lee SHP (.zip), KML/KMZ y File Geodatabase (.gdb empaquetada en .zip) y los
# convierte a GeoJSON en EPSG:4326 (WGS84) para render en Leaflet.
# Requiere: pip install fiona pyproj  (fiona incluye GDAL nativo).

GIS_MAX_BYTES = 2 * 1024 * 1024 * 1024
GIS_FEATURES_MAX = 200000
# Límite de features al cargar una geodatabase local (para que sea ágil y el mapa no se sature).
# Se mantiene acotado para que el navegador pueda dibujar la capa sin congelarse.
GIS_LOCAL_FEATURES_MAX = 12000
GIS_LAYER_MAX = 8000          # tope de features por capa individual (evita que una sola capa acapare todo)
GIS_SIMPLIFY_M = 50.0  # simplificación Douglas-Peucker (en unidades del CRS origen) antes de reproyectar
# Para geodatabases de fondo pesado (Cartografia_Basica: MDANMu, Depart, Paises...), se aligera más:
# simplificación previa más fuerte + simplificación post-reproyección. Los datos de EIA
# (GDB_EIA_GARCERO_C) y cualquier otra GDB conservan su precisión actual (GIS_SIMPLIFY_M).
GIS_SIMPLIFY_M_PESADO = 300.0
GIS_SIMPLIFY_POST_PESADO = 0.0003
# Presupuesto de vértices POR feature para GDB pesadas: si un polígono gigante sigue con demasiados
# puntos tras simplificar, se vuelve a simplificar con tolerancia creciente hasta ceder el presupuesto.
# Así el redibujo del mapa (pan/zoom) no se congela, y los polígonos pequeños ni se tocan.
GIS_PESADO_VERTICES_MAX = 3000
_GDB_PESADO_PATTERNS = ("cartografia", "cartografía")
# Versión del formato de caché: al subirla, las GDB se regeneran automáticamente (p. ej. al ajustar
# valores de simplificación más livianos).
GIS_CACHE_VERSION = 4
GIS_CACHE_DIR = os.path.join(BASE_DIR, "config", "gis_cache")
# Tiles raster generados bajo demanda (tipo "Google Maps") para que el mapa no se congele al hacer zoom.
GIS_TILES_DIR = os.path.join(BASE_DIR, "config", "gis_tiles")
GIS_TILES_MAX_ZOOM = 18

# ---------- Capas tematicas KMZ locales (AreaInfluencia, CoberturaTierra, Zonificaciones...) ----------
# Igual que las GDB, los KMZ se leen del disco del servidor (sin subirlos) desde las rutas de
# config/gis_kmz_paths.txt. La conversion se cachea y se simplifica para que el mapa no se congele.
GIS_KMZ_SIMPLIFY = 0.0001        # tolerancia Douglas-Peucker en grados (~11 m). Equilibrio fidelidad/fluidez.
GIS_KMZ_VERTICES_MAX = 1200      # presupuesto de vertices por entidad tras simplificar.
GIS_KMZ_COORD_DEC = 5            # decimales de salida (~1 m) para aligerar el GeoJSON.
GIS_KMZ_MIN_CATEGORIA = 2        # minimo de valores distintos para considerar un campo como categoria.
GIS_KMZ_MAX_CATEGORIA = 80       # maximo de valores distintos para considerar un campo como categoria.
# Campos que NO sirven como categoria (geometria, identificadores, metadatos constantes, texto largo).
_CAMPOS_KMZ_IGNORAR = {
    "SHAPE", "SHAPE_LENGTH", "SHAPE_AREA", "EXPEDIENTE", "OPERADOR", "PROYECTO",
    "SECTOR", "DESCRIP", "OBSERV", "NAME", "_CAPA",
}
# Orden de preferencia para elegir categoria/subcategoria por defecto.
_CAMPOS_KMZ_PRIORIDAD = [
    "ZONMANEJO", "ZONAMBIE", "COMPONENTE", "N1_COBERT", "AREA_INFL",
    "N2_COBERT", "N3_COBERT", "N4_COBERT", "N5_COBERT", "N6_COBERT",
    "GRUPO_COMP", "NOMENCLAT",
]

# Capas que suelen ser rasters exportados a polígonos (Pendiente, Elevación, MDS/MDT, Costo...):
# ocupan mucho tiempo de lectura y el mapa no las muestra bien; se omiten al cargar una GDB local.
_GDB_SKIP_PATTERNS = ("pendiente", "elevacion", "elevación", "mds", "mdt", "raster", "costo", "rasgo")

# Carpetas donde se buscan geodatabases locales (*.gdb) para mostrarlas en "GDB locales".
# La raíz config/gdb es PORTABLE: sirve sin importar dónde esté el proyecto (USB, otro
# computador...). Se ignoran las rutas que no existan. Agrega más raíces en
# config/gis_paths.txt (una por línea) si hay GDB en otro disco o carpeta de red.
RUTAS_GDB = [os.path.join(BASE_DIR, "config", "gdb")]

# Carpetas/archivos donde buscar capas tematicas KMZ locales. La raiz config/kmz es PORTABLE;
# escribe mas rutas en config/gis_kmz_paths.txt (una por linea, rutas que no existan se ignoran).
RUTAS_KMZ = [os.path.join(BASE_DIR, "config", "kmz")]


def _resolver_ruta_config(linea):
    """Resuelve una ruta escrita en config/gis_paths.txt o gis_kmz_paths.txt.

    Las rutas relativas (p. ej. 'config/kmz') se resuelven contra la carpeta de la
    aplicacion, para que el paquete siga funcionando se copie donde se copie."""
    linea = os.path.expandvars(os.path.expanduser(linea.strip()))
    if not os.path.isabs(linea):
        linea = os.path.join(BASE_DIR, linea)
    return os.path.normpath(linea)


def _leer_rutas_extra(nombre_archivo):
    """Lee las rutas (una por linea, '#' = comentario) de un archivo de config."""
    rutas = []
    ruta_cfg = os.path.join(CONFIG_DIR, nombre_archivo)
    try:
        if os.path.isfile(ruta_cfg):
            with open(ruta_cfg, "r", encoding="utf-8") as fh:
                for linea in fh:
                    linea = linea.strip()
                    if linea and not linea.startswith("#"):
                        rutas.append(_resolver_ruta_config(linea))
    except Exception:
        pass
    return rutas


def _extraer_zip_seguro(raw, tmp):
    """Descomprime un zip evitando rutas fuera del directorio temporal."""
    try:
        zf = zipfile.ZipFile(io.BytesIO(raw))
    except zipfile.BadZipFile:
        return False
    base = os.path.realpath(tmp)
    for member in zf.infolist():
        target = os.path.realpath(os.path.join(tmp, member.filename))
        if not target.startswith(base + os.sep):
            continue
        if member.is_dir():
            os.makedirs(target, exist_ok=True)
            continue
        os.makedirs(os.path.dirname(target), exist_ok=True)
        with zf.open(member) as s, open(target, "wb") as d:
            shutil.copyfileobj(s, d)
    zf.close()
    return True


def _a_geojson(g):
    if g is None:
        return None
    if isinstance(g, dict):
        return g
    try:
        return dict(g)
    except Exception:
        return g


_TRANSFORM_CACHE = {}


def _walk_coords(c, tr):
    """Recorre coordenadas anidadas reproyectando cada par (x, y)."""
    if not c:
        return c
    if isinstance(c[0], (int, float)):
        x, y = c[0], c[1]
        try:
            o = tr.transform(x, y)
            out = [float(o[0]), float(o[1])]
        except Exception:
            out = [x, y]
        if len(c) > 2:
            out.extend(float(v) for v in c[2:])
        return out
    return [_walk_coords(x, tr) for x in c]


def _reproyectar_a_wgs84(g, tr):
    if g is None:
        return None
    if g.get("type") == "GeometryCollection":
        return {"type": "GeometryCollection",
                "geometries": [_reproyectar_a_wgs84(x, tr) for x in (g.get("geometries") or [])]}
    g["coordinates"] = _walk_coords(g.get("coordinates") or [], tr)
    return g


def _transformar_a_wgs84(geom, fcrs, simplificar_m=None, pesado=False):
    """Reproyecta una geometria GeoJSON a EPSG:4326 usando el CRS de la fuente.
    Si simplificar_m > 0, simplifica ANTES de reproyectar (requiere shapely).
    Si pesado=True, además simplifica DESPUÉS de reproyectar a WGS84 con
    GIS_SIMPLIFY_POST_PESADO (para GDB de fondo con polígonos gigantes).
    El par (CRS, Transformer) se cachea para no recrearlo por cada feature."""

    def _simpl_post(salida):
        if not pesado or not salida or not isinstance(salida, dict):
            return salida
        try:
            from shapely.geometry import shape

            shp = shape(salida)
            if shp is None or shp.is_empty or shp.geom_type in ("Point", "MultiPoint"):
                return salida
            tol = GIS_SIMPLIFY_POST_PESADO
            for _ in range(12):
                shp = shp.simplify(tol, preserve_topology=True)
                if not shp.is_empty:
                    n = shp.wkt.count(',')
                    if n <= GIS_PESADO_VERTICES_MAX:
                        break
                tol *= 2
            if not shp.is_empty:
                salida = shp.__geo_interface__
        except Exception:
            pass
        return salida

    if geom is None or fcrs is None or (isinstance(fcrs, dict) and not fcrs):
        return _a_geojson(geom)
    try:
        from pyproj import CRS

        src = CRS.from_user_input(fcrs)
        dst = CRS.from_epsg(4326)
        if src.is_geographic and src.equals(dst):
            return _simpl_post(_a_geojson(geom))
        clave = (str(src), str(dst))
        tr = _TRANSFORM_CACHE.get(clave)
        if tr is None:
            from pyproj.transformer import Transformer

            tr = Transformer.from_crs(src, dst, always_xy=True)
            _TRANSFORM_CACHE[clave] = tr

        g = _a_geojson(geom)
        if simplificar_m:
            try:
                from shapely.geometry import shape

                shp = shape(g)
                if shp is not None and not shp.is_empty and shp.geom_type not in ("Point", "MultiPoint"):
                    tol = simplificar_m
                    if pesado and shp.geom_type in ("LineString", "MultiLineString"):
                        tol = GIS_SIMPLIFY_M
                    shp = shp.simplify(tol, preserve_topology=True)
                g = shp.__geo_interface__
            except Exception:
                pass
        return _simpl_post(_reproyectar_a_wgs84(g, tr))
    except Exception:
        return _a_geojson(geom)


def _a_json_safe(v):
    """Convierte valores de atributos (fecha, bytes, etc.) a tipos JSON puros."""
    if v is None or isinstance(v, (str, int, float, bool)):
        return v
    import datetime as _dt
    if isinstance(v, (_dt.datetime, _dt.date, _dt.time)):
        return v.isoformat()
    try:
        return str(v)
    except Exception:
        return None


def _leer_features(path, layer=None, driver=None, nombre_capa="capa",
                   excluir_sin_geometria=False, limite=GIS_FEATURES_MAX,
                   simplificar_m=GIS_SIMPLIFY_M, pesado=False):
    """Lee una capa (SHP o GDB) con fiona y la devuelve como FeatureCollection WGS84.
    pesado=True aplica además simplificación post-reproyección (solo GDB de fondo)."""
    try:
        import fiona
    except ImportError:
        return None, "Falta instalar 'fiona' (pip install fiona)."
    try:
        if layer is None:
            src = fiona.open(path, driver=driver) if driver else fiona.open(path)
        else:
            src = fiona.open(path, layer=layer)
    except Exception as e:
        return None, str(e)

    with src:
        if excluir_sin_geometria and not src.schema.get("geometry"):
            return {"type": "FeatureCollection", "features": []}, None
        fcrs = src.crs
        salida = []
        for f in src:
            geom = f.get("geometry")
            if geom is None:
                continue
            props = {k: _a_json_safe(v) for k, v in (f.get("properties") or {}).items()}
            props["_capa"] = nombre_capa
            g = _transformar_a_wgs84(geom, fcrs, simplificar_m=simplificar_m, pesado=pesado)
            if g is None:
                continue
            salida.append({"type": "Feature", "properties": props, "geometry": g})
            if len(salida) >= limite:
                break
    return {"type": "FeatureCollection", "features": salida}, None


# ---------- Parser de KML/KMZ (el driver KML de GDAL no viene en el wheel) ----------

def _kml_localname(tag):
    return tag.rsplit("}", 1)[-1]


def _kml_coord_pairs(texto):
    pares = []
    for trozo in re.split(r"[\s]+", texto.strip()):
        if not trozo:
            continue
        partes = trozo.split(",")
        if len(partes) >= 2:
            try:
                pares.append([float(partes[0]), float(partes[1])])
            except ValueError:
                pass
    return pares


def _kml_descendiente(elem, local):
    for e in elem.iter():
        if e is not elem and _kml_localname(e.tag) == local:
            return e
    return None


def _kml_descendientes(elem, local):
    return [e for e in elem.iter() if e is not elem and _kml_localname(e.tag) == local]


def _kml_coords_de(elem):
    c = _kml_descendiente(elem, "coordinates")
    return _kml_coord_pairs(c.text) if c is not None and c.text else []


def _kml_parsear_geometria(el):
    name = _kml_localname(el.tag)
    if name == "Point":
        pts = _kml_coords_de(el)
        return [{"type": "Point", "coordinates": pts[0]}] if pts else []
    if name in ("LineString", "LinearRing"):
        pts = _kml_coords_de(el)
        return [{"type": "LineString", "coordinates": pts}] if len(pts) >= 2 else []
    if name == "Polygon":
        rings = [c for r in _kml_descendientes(el, "LinearRing") if len(c := _kml_coords_de(r)) >= 3]
        if not rings:
            return []
        return [{"type": "Polygon", "coordinates": rings}]
    if name == "MultiGeometry":
        geoms = []
        for hijo in el:
            geoms.extend(_kml_parsear_geometria(hijo))
        return geoms
    return []


def _kml_extraer_geometrias(el):
    """Recorre el arbol; al encontrar una geometria la parsea sin volver a bajar."""
    if _kml_localname(el.tag) in ("Point", "LineString", "LinearRing", "Polygon", "MultiGeometry"):
        return _kml_parsear_geometria(el)
    res = []
    for hijo in el:
        res.extend(_kml_extraer_geometrias(hijo))
    return res


_KML_NULL_RE = re.compile(r"<\s*/?\s*Null\s*>", re.I)
_KML_TR_RE = re.compile(r"<tr[^>]*>(.*?)</tr>", re.I | re.S)
_KML_TD_RE = re.compile(r"<td[^>]*>(.*?)</td>", re.I | re.S)
_KML_TAG_RE = re.compile(r"<[^>]+>")


def _kml_sanear(texto):
    """ArcGIS exporta el campo <name> como '<Null>' crudo, lo que rompe el XML."""
    return _KML_NULL_RE.sub("", texto)


def _kml_texto_celda(valor):
    return html.unescape(_KML_TAG_RE.sub("", valor or "")).strip()


def _kml_desc_a_props(desc):
    """Extrae campos de la tabla HTML que ArcGIS incrusta en <description>.

    Devuelve {CLAVE: valor} limpio (sin tags ni entidades, '<Null>' como vacio)."""
    props = {}
    if not desc:
        return props
    for fila in _KML_TR_RE.findall(desc):
        celdas = _KML_TD_RE.findall(fila)
        if len(celdas) < 2:
            continue
        clave = _kml_texto_celda(celdas[0])
        valor = _kml_texto_celda(celdas[1])
        if not clave:
            continue
        if valor.lower() in ("<null>", "null", "none"):
            valor = ""
        props[clave] = valor
    return props


def _kml_a_featurecollection(texto, nombre_capa):
    try:
        root = ET.fromstring(_kml_sanear(texto))
    except ET.ParseError:
        return None, "El archivo KMZ/KML está corrupto o no es válido."
    features = []
    for pm in root.iter():
        if _kml_localname(pm.tag) != "Placemark":
            continue
        props = {}
        n = _kml_descendiente(pm, "name")
        if n is not None and n.text:
            props["name"] = n.text.strip()
        d = _kml_descendiente(pm, "description")
        if d is not None and d.text:
            for k, v in _kml_desc_a_props(d.text).items():
                props[k] = v
        props["_capa"] = nombre_capa
        for geom in _kml_extraer_geometrias(pm):
            features.append({"type": "Feature", "properties": dict(props), "geometry": geom})
            if len(features) >= GIS_FEATURES_MAX:
                break
        if len(features) >= GIS_FEATURES_MAX:
            break
    if not features:
        return None, "El KMZ/KML no contiene Placemarks (puntos, líneas o polígonos)."
    return {"type": "FeatureCollection", "features": features}, None


def _procesar_contenido_zip(tmp, nombre):
    """Detecta dentro de tmp una .gdb, un .shp o un .kml y devuelve el GeoJSON."""
    gdb_dirs, shp_files, kml_files = [], [], []
    for root, dirs, files in os.walk(tmp):
        for d in dirs:
            if d.lower().endswith(".gdb"):
                gdb_dirs.append(os.path.join(root, d))
        for f in files:
            low = f.lower()
            if low.endswith(".shp"):
                shp_files.append(os.path.join(root, f))
            elif low.endswith(".kml"):
                kml_files.append(os.path.join(root, f))

    geo_feats, errores, total = [], [], 0
    tipo = "zip"
    import fiona

    if gdb_dirs:
        tipo = "gdb"
        for gdb in gdb_dirs[:3]:
            try:
                layers = fiona.listlayers(gdb)
            except Exception as e:
                errores.append(str(e))
                continue
            pesado = any(p in os.path.basename(gdb).lower() for p in _GDB_PESADO_PATTERNS)
            for lay in layers:
                restante = GIS_LOCAL_FEATURES_MAX - total
                if restante <= 0:
                    break
                fc, err = _leer_features(gdb, layer=lay,
                                         nombre_capa="{} / {}".format(os.path.basename(gdb).replace(".gdb", ""), lay),
                                         limite=restante,
                                         simplificar_m=(GIS_SIMPLIFY_M_PESADO if pesado else GIS_SIMPLIFY_M),
                                         pesado=pesado)
                if err or fc is None:
                    errores.append(err or "")
                    continue
                geo_feats.extend(fc["features"])
                total += len(fc["features"])
                if total >= GIS_LOCAL_FEATURES_MAX:
                    break
            if total >= GIS_LOCAL_FEATURES_MAX:
                break
    elif shp_files:
        tipo = "shapefile"
        for shp in shp_files[:10]:
            fc, err = _leer_features(shp, driver="ESRI Shapefile", nombre_capa=os.path.basename(shp))
            if err or fc is None:
                errores.append(err or "")
                continue
            geo_feats.extend(fc["features"])
            total += len(fc["features"])
            if total >= GIS_FEATURES_MAX:
                break
    elif kml_files:
        tipo = "kml"
        with open(kml_files[0], "r", encoding="utf-8", errors="replace") as fh:
            fc, err = _kml_a_featurecollection(fh.read(), nombre)
        if err:
            return {"ok": False, "error": err}
        geo_feats = fc["features"]
        total = len(geo_feats)
    else:
        return {"ok": False, "error": "El ZIP no contiene una File Geodatabase (.gdb), un .shp ni un .kml."}

    if not geo_feats:
        detalle = (" ({})".format("; ".join(errores[:3]))) if errores else ""
        return {"ok": False, "error": "No se encontraron geometrías para dibujar." + detalle}

    return {"ok": True, "tipo": tipo, "capa": nombre,
            "crs_original": "Reproyectado a WGS84 (EPSG:4326) autom.",
            "features": total, "truncado": total >= GIS_FEATURES_MAX,
            "geojson": {"type": "FeatureCollection", "features": geo_feats}}


def _procesar_archivo_gdb(nombre, raw, tmp):
    """Subida de un archivo .gdb único. Si por dentro es un ZIP se trata como tal;
    si no, se intenta abrir con distintos drivers de fiona."""
    try:
        import fiona
    except ImportError:
        return {"ok": False, "error": "Falta instalar 'fiona' (pip install fiona)."}
    try:
        es_zip = zipfile.is_zipfile(io.BytesIO(raw))
    except Exception:
        es_zip = False
    if es_zip:
        if not _extraer_zip_seguro(raw, tmp):
            return {"ok": False, "error": "El archivo .gdb no es un ZIP válido."}
        return _procesar_contenido_zip(tmp, nombre)

    ruta = os.path.join(tmp, os.path.basename(nombre) or "capa.gdb")
    try:
        with open(ruta, "wb") as fh:
            fh.write(raw)
    except Exception:
        return {"ok": False, "error": "No se pudo guardar el archivo .gdb."}

    errores = []
    pesado = any(p in nombre.lower() for p in _GDB_PESADO_PATTERNS)
    for drv in ("OpenFileGDB", "GPKG", "SQLite", "GeoJSON", "ESRI Shapefile", "GML", "DXF"):
        try:
            fc, err = _leer_features(ruta, layer=None, driver=drv, nombre_capa=nombre,
                                     simplificar_m=(GIS_SIMPLIFY_M_PESADO if pesado else GIS_SIMPLIFY_M),
                                     pesado=pesado)
            if err is None and fc and fc.get("features"):
                return {"ok": True, "tipo": "gdb", "capa": nombre,
                        "crs_original": "Reproyectado a WGS84 (EPSG:4326) autom.",
                        "features": len(fc["features"]),
                        "truncado": len(fc["features"]) >= GIS_FEATURES_MAX,
                        "geojson": fc}
            if err:
                errores.append(err)
        except Exception as e:
            errores.append(str(e))
    return {"ok": False,
            "error": "No se pudieron leer geometrías del archivo .gdb. Si es la carpeta File Geodatabase de ArcGIS "
                     "(como 'GDB_EIA_GARCERO_C.gdb'), comprímela a .zip y súbela con «Importar capas GIS»."
                     + ((" Detalle: " + errores[0]) if errores else "")}


def convertir_capas_gis(nombre, raw):
    nombre = nombre or "capa"
    bajo = nombre.lower()

    with tempfile.TemporaryDirectory() as tmp:
        # --- KML suelto ---
        if bajo.endswith(".kml"):
            try:
                texto_kml = raw.decode("utf-8", errors="replace")
            except Exception:
                return {"ok": False, "error": "No se pudo leer el archivo KML."}
            fc, err = _kml_a_featurecollection(texto_kml, nombre)
            if err:
                return {"ok": False, "error": err}
            return {"ok": True, "tipo": "kml", "capa": nombre, "crs_original": "EPSG:4326",
                    "features": len(fc["features"]), "geojson": fc}

        # --- Archivo .gdb subido como archivo único ---
        if bajo.endswith(".gdb"):
            return _procesar_archivo_gdb(nombre, raw, tmp)

        # --- ZIP o KMZ ---
        if not bajo.endswith((".zip", ".kmz")):
            return {"ok": False, "error": "Formato no soportado. Usa .zip (SHP o .gdb), .kmz, .kml o un archivo .gdb."}
        if not _extraer_zip_seguro(raw, tmp):
            return {"ok": False, "error": "El archivo .zip/.kmz no es válido o está dañado."}

        # KMZ: extraer el primer .kml que contenga
        if bajo.endswith(".kmz"):
            for root, _dirs, files in os.walk(tmp):
                for f in files:
                    if f.lower().endswith(".kml"):
                        with open(os.path.join(root, f), "r", encoding="utf-8", errors="replace") as fh:
                            texto_kml = fh.read()
                        fc, err = _kml_a_featurecollection(texto_kml, nombre)
                        if err:
                            return {"ok": False, "error": err}
                        return {"ok": True, "tipo": "kmz", "capa": nombre, "crs_original": "EPSG:4326",
                                "features": len(fc["features"]), "geojson": fc}
            return {"ok": False, "error": "No se encontró un archivo .kml dentro del KMZ."}

        # ZIP genérico: detectar .gdb, .shp o .kml dentro
        return _procesar_contenido_zip(tmp, nombre)


def _cache_gdb_ids():
    """Ids de geodatabases con GeoJSON guardado en config/gis_cache/<id>.json.

    En un computador distinto al de origen los .gdb originales no existen, pero el
    GeoJSON convertido sí viaja en la carpeta config/gis_cache. Con esto las capas
    se pueden listar y cargar igual (modo portable)."""
    salida = []
    try:
        nombres = os.listdir(GIS_CACHE_DIR)
    except OSError:
        return salida
    for nombre in nombres:
        if not re.fullmatch(r"[0-9a-f]{32}\.json", nombre):
            continue
        gdb_id = nombre[:-5]
        cc = _cache_gdb_por_id(gdb_id)
        if not cc:
            continue
        salida.append({
            "id": gdb_id,
            "capa": cc.get("capa") or "GDB",
            "capas": len(cc.get("capas") or []),
            "features": cc.get("features") or 0,
            "mtime": cc.get("mtime") or 0.0,
            "version": cc.get("version") or 0,
            "tiles": os.path.isdir(os.path.join(GIS_TILES_DIR, gdb_id)),
        })
    return salida


def _descubrir_gdb():
    """Barre RUTAS_GDB (y config/gis_paths.txt) buscando carpetas *.gdb locales.

    Tambien incluye las GDB que solo existen como GeoJSON en cache (config/gis_cache),
    identificadas con la pseudo-ruta 'cache://<id>', para que las capas se carguen en
    cualquier computador aunque alli no este la geodatabase original."""
    rutas = list(RUTAS_GDB) + _leer_rutas_extra("gis_paths.txt")
    encontradas, vistos = [], set()
    import fiona
    for raiz in rutas:
        raiz = os.path.normpath(raiz)
        if not os.path.isdir(raiz):
            continue
        for p, subdirs, _fi in os.walk(raiz):
            profundidad = p[len(raiz):].count(os.sep)
            if profundidad >= 3:
                subdirs[:] = []
                continue
            quitar = []
            for d in subdirs:
                if d.lower().endswith(".gdb"):
                    ruta = os.path.normpath(os.path.join(p, d))
                    if ruta.lower() not in vistos:
                        vistos.add(ruta.lower())
                        n_capas = 0
                        try:
                            n_capas = len(fiona.listlayers(ruta))
                        except Exception:
                            n_capas = 0
                        encontradas.append({"ruta": ruta, "nombre": d,
                                            "carpeta": os.path.dirname(ruta),
                                            "capas": n_capas})
                    quitar.append(d)
            for q in quitar:
                subdirs.remove(q)

    # --- GDB presentes solo como cache (portabilidad a otro PC) ---
    bases_vistas = {e["nombre"].lower().replace(".gdb", "") for e in encontradas}
    mejores = {}
    for c in _cache_gdb_ids():
        clave_capa = (c["capa"] or "").lower()
        if not clave_capa or clave_capa in bases_vistas:
            continue
        prev = mejores.get(clave_capa)
        # Se prefiere la cache que ya tiene tiles pre-renderizados (carga instantanea),
        # luego la version mas nueva del formato y por ultimo la mas reciente.
        if prev is None or (c["tiles"], c["version"], c["mtime"]) > (
                prev["tiles"], prev["version"], prev["mtime"]):
            mejores[clave_capa] = c
    for c in mejores.values():
        encontradas.append({
            "ruta": "cache://" + c["id"],
            "nombre": c["capa"] + ".gdb",
            "carpeta": "Caché integrada (portable, sin archivo .gdb)",
            "capas": c["capas"],
        })

    encontradas.sort(key=lambda e: e["nombre"].lower())
    return encontradas


# ---------- Capas tematicas KMZ locales ----------

def _kmz_es_numerico(valores):
    if not valores:
        return True
    ok = 0
    for v in valores[:60]:
        if re.fullmatch(r"[\d\s.,\-+]+", v):
            ok += 1
    return len(valores) and (ok / len(valores)) >= 0.8


def _kmz_detectar_campos(features):
    """Devuelve los campos no numericos con 2..80 valores distintos (candidatos a categoria)."""
    conteo = {}
    for ft in features:
        for k, v in (ft.get("properties") or {}).items():
            ks = (k or "").strip()
            if not ks or ks.upper() in _CAMPOS_KMZ_IGNORAR:
                continue
            vv = "" if v is None else str(v).strip()
            if vv:
                conteo.setdefault(ks, {})
                conteo[ks][vv] = conteo[ks].get(vv, 0) + 1
    campos = []
    for campo, vals in conteo.items():
        valores = sorted(vals.items(), key=lambda x: (-x[1], x[0]))
        if not (GIS_KMZ_MIN_CATEGORIA <= len(valores) <= GIS_KMZ_MAX_CATEGORIA):
            continue
        lista = [v for v, _ in valores]
        if campo.upper() not in _CAMPOS_KMZ_PRIORIDAD and _kmz_es_numerico(lista):
            continue
        campos.append({
            "campo": campo,
            "valores": lista,          # ordenado de mas a menos frecuente
            "conteos": [c for _, c in valores],
        })

    def rank(c):
        try:
            return _CAMPOS_KMZ_PRIORIDAD.index(c["campo"].upper())
        except ValueError:
            return len(_CAMPOS_KMZ_PRIORIDAD)
    campos.sort(key=lambda c: (rank(c), len(c["valores"])))
    return campos


def _redondear_coords(obj):
    if isinstance(obj, float):
        return round(obj, GIS_KMZ_COORD_DEC)
    if isinstance(obj, dict):
        return {k: _redondear_coords(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_redondear_coords(x) for x in obj]
    return obj


def _geom_n_vertices(geom):
    t = geom.get("type")
    c = geom.get("coordinates")
    if t == "Point":
        return 1 if c else 0
    if t == "LineString" or t == "MultiPoint":
        return len(c or [])
    if t == "Polygon":
        return sum(len(r) for r in (c or []))
    if t == "MultiLineString":
        return sum(len(l) for l in (c or []))
    if t == "MultiPolygon":
        return sum(len(r) for poly in (c or []) for r in poly)
    if t == "GeometryCollection":
        return sum(_geom_n_vertices(g) for g in (geom.get("geometries") or []))
    return 0


def _simplificar_geom_kmz(geom):
    """Simplifica la geometria (Douglas-Peucker en grados) con presupuesto de vertices y
    redondea coordenadas a 5 decimales para aligerar el GeoJSON sin deformar los bordes."""
    try:
        from shapely.geometry import shape, mapping
    except Exception:
        return _redondear_coords(geom)
    try:
        g = shape(geom)
    except Exception:
        return _redondear_coords(geom)
    if g.is_empty:
        return _redondear_coords(geom)
    tol = GIS_KMZ_SIMPLIFY
    for _ in range(7):
        try:
            s = g.simplify(tol, preserve_topology=True)
        except Exception:
            break
        g = s
        if _geom_n_vertices(mapping(g)) <= GIS_KMZ_VERTICES_MAX or tol >= 0.05:
            break
        tol *= 2
    try:
        return _redondear_coords(mapping(g))
    except Exception:
        return _redondear_coords(geom)


def _decodificar_kml(raw):
    for enc in ("utf-8", "cp1252", "latin-1"):
        try:
            return raw.decode(enc)
        except (UnicodeDecodeError, ValueError):
            continue
    return raw.decode("utf-8", errors="replace")


def _hash_ajustes_kmz():
    """Un digest de TODOS los parametros que afectan el GeoJSON. Si se cambia alguno (simplify,
    presupuesto de vertices, precision...), la cache KMZ se regenera automaticamente."""
    import hashlib
    s = "|".join([
        str(GIS_KMZ_SIMPLIFY), str(GIS_KMZ_VERTICES_MAX), str(GIS_KMZ_COORD_DEC),
        str(GIS_KMZ_MIN_CATEGORIA), str(GIS_KMZ_MAX_CATEGORIA),
    ])
    return hashlib.md5(s.encode("utf-8")).hexdigest()[:10]


def _clave_kmz(ruta):
    """Clave de caché basada en el CONTENIDO del KMZ (md5 del archivo), no en su ruta.
    Así la caché viaja dentro del paquete y sirve en cualquier computador, y si el
    KMZ cambia (otro contenido) la caché se regenera sola."""
    try:
        with open(ruta, "rb") as fh:
            return hashlib.md5(fh.read()).hexdigest()
    except OSError:
        return None


def _leer_kmz_por_ruta(ruta):
    """Abre un .kmz local, extrae su doc.kml, lo convierte a GeoJSON (con campos de la tabla
    HTML, simplify y coordenadas redondeadas). La 1ª vez se cachea en config/gis_cache/
    con clave por contenido (kmz_<md5 del archivo>.json)."""
    ruta = (ruta or "").strip()
    if not os.path.isabs(ruta):
        ruta = os.path.join(BASE_DIR, ruta)
    ruta = os.path.normpath(ruta)
    if not os.path.isfile(ruta) or not ruta.lower().endswith(".kmz"):
        return {"ok": False, "error": "La ruta no es un archivo .kmz válido."}
    nombre = os.path.splitext(os.path.basename(ruta))[0]
    clave = _clave_kmz(ruta)
    if not clave:
        return {"ok": False, "error": "No se pudo leer el archivo KMZ."}
    try:
        mtime = os.path.getmtime(ruta)
    except OSError:
        mtime = 0.0
    os.makedirs(GIS_CACHE_DIR, exist_ok=True)
    archivo_cache = os.path.join(GIS_CACHE_DIR, "kmz_" + clave + ".json")

    # La validez depende del contenido (md5), no de la fecha: al copiar el paquete a
    # otro computador la fecha cambia pero la caché sigue siendo válida.
    try:
        with open(archivo_cache, "r", encoding="utf-8") as fh:
            cc = json.load(fh)
        if (cc.get("version") == GIS_CACHE_VERSION
                and cc.get("ajustes") == _hash_ajustes_kmz()
                and cc.get("geojson")):
            cc["ok"] = True
            cc["de_cache"] = True
            cc["segundos"] = 0.01
            cams = cc.get("campos") or []
            cc["campo_categoria"] = cams[0]["campo"] if cams else ""
            cc["campo_subcategoria"] = cams[1]["campo"] if len(cams) > 1 else ""
            return cc
    except Exception:
        pass

    try:
        with zipfile.ZipFile(ruta) as zf:
            kml_nombre = next((n for n in zf.namelist() if n.lower().endswith(".kml")), None)
            if not kml_nombre:
                return {"ok": False, "error": "El KMZ no contiene un archivo .kml."}
            raw = zf.read(kml_nombre)
    except zipfile.BadZipFile:
        return {"ok": False, "error": "El archivo KMZ está dañado o no es válido."}
    except Exception as e:
        return {"ok": False, "error": "No se pudo leer el KMZ: " + str(e)}

    texto = _decodificar_kml(raw)
    fc, err = _kml_a_featurecollection(texto, nombre)
    if err:
        return {"ok": False, "error": err}
    for ft in fc["features"]:
        ft["geometry"] = _simplificar_geom_kmz(ft["geometry"])
    campos = _kmz_detectar_campos(fc["features"])
    resp = {
        "ok": True, "tipo": "kmz", "capa": nombre, "crs_original": "EPSG:4326",
        "features": len(fc["features"]),
        "geojson": fc, "campos": campos,
        "campo_categoria": campos[0]["campo"] if campos else "",
        "campo_subcategoria": campos[1]["campo"] if len(campos) > 1 else "",
        "ajustes": _hash_ajustes_kmz(),
        "mtime": mtime, "version": GIS_CACHE_VERSION,
    }
    try:
        with open(archivo_cache, "w", encoding="utf-8") as fh:
            json.dump(resp, fh, ensure_ascii=False)
    except Exception:
        pass
    return resp


def _descubrir_kmz():
    """Barre RUTAS_KMZ (y config/gis_kmz_paths.txt) listando archivos *.kmz locales.

    Deduplica por NOMBRE de archivo: si el mismo .kmz existe en varias rutas
    (p. ej. config/kmz portable y una ruta extra del equipo de origen en
    gis_kmz_paths.txt), se lista una sola vez; gana la primera ruta de
    RUTAS_KMZ (config/kmz, que es la que viaja con el paquete)."""
    rutas = list(RUTAS_KMZ) + _leer_rutas_extra("gis_kmz_paths.txt")
    encontradas, vistos, vistos_nombres = [], set(), set()
    for raiz in rutas:
        raiz = os.path.normpath(raiz)
        if os.path.isfile(raiz):
            archivos = [raiz] if raiz.lower().endswith(".kmz") else []
        elif os.path.isdir(raiz):
            archivos = []
            for p, subdirs, files in os.walk(raiz):
                if p[len(raiz):].count(os.sep) >= 2:
                    subdirs[:] = []
                    continue
                for f in files:
                    if f.lower().endswith(".kmz"):
                        archivos.append(os.path.join(p, f))
        else:
            continue
        for ruta in archivos:
            rn = os.path.normpath(ruta)
            bajo = rn.lower()
            if bajo in vistos:
                continue
            vistos.add(bajo)
            nombre_base = os.path.splitext(os.path.basename(rn))[0].lower()
            if nombre_base in vistos_nombres:
                continue
            vistos_nombres.add(nombre_base)
            try:
                tam = os.path.getsize(rn)
            except OSError:
                tam = 0
            info = {"ruta": rn, "nombre": os.path.splitext(os.path.basename(rn))[0],
                    "carpeta": os.path.dirname(rn), "bytes": tam}
            # Caché por contenido: la misma clave funciona en cualquier computador.
            clave = _clave_kmz(rn)
            cache = os.path.join(GIS_CACHE_DIR, "kmz_" + clave + ".json") if clave else None
            if cache:
                try:
                    with open(cache, "r", encoding="utf-8") as fh:
                        cc = json.load(fh)
                    if cc.get("version") == GIS_CACHE_VERSION:
                        info["features"] = cc.get("features")
                        # El panel KMZ espera la lista de campos (no el conteo).
                        info["campos"] = cc.get("campos") or []
                except Exception:
                    pass
            encontradas.append(info)
    encontradas.sort(key=lambda e: e["nombre"].lower())
    return encontradas


def _cache_gdb_por_id(gdb_id):
    """Devuelve el GeoJSON cacheado de una GDB (config/gis_cache/<id>.json) o None."""
    if not re.fullmatch(r"[0-9a-f]{32}", gdb_id or ""):
        return None
    archivo = os.path.join(GIS_CACHE_DIR, gdb_id + ".json")
    if not os.path.isfile(archivo):
        return None
    try:
        with open(archivo, "r", encoding="utf-8") as fh:
            cc = json.load(fh)
    except Exception:
        return None
    if not isinstance(cc, dict) or cc.get("tipo") != "gdb" or not cc.get("geojson"):
        return None
    cc["ok"] = True
    cc["de_cache"] = True
    cc["segundos"] = 0.01
    return cc


def _leer_gdb_por_ruta(ruta):
    """Lee las capas vectoriales de una geodatabase local y devuelve la respuesta GIS.
    La primera vez puede tardar; el resultado queda cacheado en config/gis_cache/.

    Si la carpeta .gdb no existe en este computador (p. ej. el paquete se copió a
    otro PC y el original estaba en D:), se devuelve el GeoJSON cacheado si existe.
    La pseudo-ruta 'cache://<id>' carga directamente ese caché."""
    ruta = (ruta or "").strip()
    if ruta.startswith("cache://"):
        cc = _cache_gdb_por_id(ruta[len("cache://"):].strip())
        return cc if cc else {"ok": False,
                              "error": "Esta capa no está en la caché integrada del servidor."}

    ruta = os.path.normpath(ruta)
    if not ruta.lower().endswith(".gdb"):
        return {"ok": False, "error": "La ruta no es una carpeta .gdb válida."}
    nombre_capa = os.path.basename(ruta).replace(".gdb", "")
    pesado = any(p in nombre_capa.lower() for p in _GDB_PESADO_PATTERNS)
    clave = hashlib.md5(ruta.lower().encode("utf-8")).hexdigest()
    mtime = 0.0
    try:
        mtime = os.path.getmtime(ruta)
    except OSError:
        pass
    archivo_cache = os.path.join(GIS_CACHE_DIR, clave + ".json")

    if not os.path.isdir(ruta):
        # La carpeta no viaja con el paquete: se usa el GeoJSON en caché (portable).
        cc = _cache_gdb_por_id(clave)
        if cc:
            return cc
        return {"ok": False, "error": (
            "La carpeta .gdb no existe en este computador y no hay una copia en caché. "
            "Copia la geodatabase aquí o agrégala en config/gis_paths.txt.")}

    if mtime:
        try:
            with open(archivo_cache, "r", encoding="utf-8") as fh:
                cc = json.load(fh)
            if (cc.get("mtime") == mtime and cc.get("limite") == GIS_LOCAL_FEATURES_MAX
                    and cc.get("pesado") == pesado
                    and cc.get("version") == GIS_CACHE_VERSION):
                cc["ok"] = True
                cc["de_cache"] = True
                cc["segundos"] = 0.01
                return cc
        except Exception:
            pass

    try:
        import fiona
    except ImportError:
        return {"ok": False, "error": "Falta instalar 'fiona' (pip install fiona)."}
    try:
        layers = fiona.listlayers(ruta)
    except Exception as e:
        return {"ok": False, "error": "No se pudo abrir la geodatabase: " + str(e)}
    if not layers:
        return {"ok": False, "error": "La geodatabase no tiene capas legibles."}

    geo_feats, errores, total, capas_nombres = [], [], 0, []
    for lay in layers:
        restante = GIS_LOCAL_FEATURES_MAX - total
        if restante <= 0:
            break
        bajo = (lay or "").lower()
        if any(s in bajo for s in _GDB_SKIP_PATTERNS):
            errores.append("Capas raster derivadas omitidas: {}".format(lay))
            continue
        limite = min(restante, GIS_LAYER_MAX)
        fc, err = _leer_features(ruta, layer=lay,
                                 nombre_capa="{} / {}".format(nombre_capa, lay),
                                 excluir_sin_geometria=True,
                                 limite=limite,
                                 simplificar_m=(GIS_SIMPLIFY_M_PESADO if pesado else GIS_SIMPLIFY_M),
                                 pesado=pesado)
        if err or fc is None:
            errores.append(err or "")
            continue
        if fc["features"]:
            capas_nombres.append(lay)
            geo_feats += fc["features"]
            total += len(fc["features"])
        if total >= GIS_LOCAL_FEATURES_MAX:
            break

    if not geo_feats:
        detalle = (" ({})".format("; ".join(errores[:3]))) if errores else ""
        return {"ok": False, "error": "No se encontraron geometrías para dibujar." + detalle}

    resp = {"ok": True, "tipo": "gdb", "capa": nombre_capa,
            "gdb_id": clave,
            "crs_original": "Reproyectado a WGS84 (EPSG:4326) autom.",
            "capas": capas_nombres,
            "features": total, "truncado": total >= GIS_LOCAL_FEATURES_MAX,
            "geojson": {"type": "FeatureCollection", "features": geo_feats}}

    try:
        import shapely.geometry as _shapely_geom
        xs, ys = [], []
        for _f in geo_feats:
            _b = _shapely_geom.shape(_f.get("geometry") or {}).bounds or (0, 0, 0, 0)
            if _b:
                xs += [_b[0], _b[2]]; ys += [_b[1], _b[3]]
        if xs:
            resp["extent"] = [min(xs), min(ys), max(xs), max(ys)]
    except Exception:
        pass

    try:
        os.makedirs(GIS_CACHE_DIR, exist_ok=True)
        guardar = dict(resp)
        guardar["mtime"] = mtime
        guardar["limite"] = GIS_LOCAL_FEATURES_MAX
        guardar["pesado"] = pesado
        guardar["version"] = GIS_CACHE_VERSION
        guardar["de_cache"] = False
        with open(archivo_cache, "w", encoding="utf-8") as fh:
            json.dump(guardar, fh, ensure_ascii=False)
    except Exception:
        pass
    return resp


# ==============================================
# VISTA DE PRESENTACION (ANLA): capas del proyecto + estadisticas
# Devuelve SOLO las capas que se presentan ante la ANLA, organizadas por temas:
#   1) Area de Desarrollo (bloque) Garcero C
#   2) Areas de influencia fisico-biotica y socioeconomica
#   3) Unidades territoriales mayores (municipios / departamento) y menores (veredas)
# NO incluye las areas de influencia INTERMEDIAS por componente (Flora, Fauna,
# Paisaje, Hidrologia...) para evitar ambiguedades en la presentacion.
# Para cada unidad territorial calcula: superficie total; superficie y % dentro del
# AI fisico-biotica; superficie y % dentro del AI socioeconomica; y superficie y %
# dentro del Area de Desarrollo Garcero C. El resultado se cachea en
# config/gis_cache/presentacion_<clave>.json (viaja con el proyecto) para que la
# vista cargue instantanea y funcione en otro PC aunque no este la GDB original.
# ==============================================

PRESENTACION_VERSION = 2
PRESENTACION_SIMPLIFY_M = 18.0
PRESENTACION_LAYERS = ("AreaProyecto", "AreaInfluencia", "UnidadTerritorial", "Municipio", "Departamento")
_PRESENTACION_MUNICIPIOS = {"85230": "Orocué", "85325": "San Luis de Palenque"}
_PRESENTACION_DEPARTAMENTOS = {"85": "Casanare"}
_PRESENTACION_GDB_MEMO = {"ruta": None, "at": 0.0}


def _pres_sin_tildes(texto):
    import unicodedata
    base = unicodedata.normalize("NFKD", str(texto or ""))
    return "".join(c for c in base if not unicodedata.combining(c)).lower()


def _pres_leer_capa(ruta, capa):
    """Lee UNA capa de la GDB con fiona y devuelve ([(props, geometria shapely)], crs)."""
    import fiona
    from shapely.geometry import shape as _shp_shape
    salida = []
    with fiona.open(ruta, layer=capa) as src:
        fcrs = src.crs
        for f in src:
            geom = f.get("geometry")
            if geom is None:
                continue
            try:
                g = _shp_shape(geom)
            except Exception:
                continue
            if g is None or g.is_empty:
                continue
            props = {k: _a_json_safe(v) for k, v in (f.get("properties") or {}).items()}
            salida.append((props, g))
    return salida, fcrs


def _pres_unir(geoms):
    from shapely.ops import unary_union
    geoms = [g for g in (geoms or []) if g is not None and not g.is_empty]
    if not geoms:
        return None
    try:
        return unary_union(geoms)
    except Exception:
        return None


def _pres_area_ha(geom):
    try:
        return float(geom.area) / 10000.0
    except Exception:
        return 0.0


def _pres_num(valor, dec=2):
    try:
        return round(float(valor), dec)
    except Exception:
        return 0.0


def _pres_stats(base, recortes):
    """Superficie total + superficie y % de cada recorte.

    base: geometria shapely de la unidad; recortes: [(clave, geometria)].
    Devuelve {total_ha, <clave>_ha, <clave>_pct, ...} redondeado a 2 decimales."""
    total = _pres_area_ha(base) if base is not None else 0.0
    salida = {"total_ha": _pres_num(total)}
    for clave, corte in (recortes or []):
        ha = 0.0
        if base is not None and corte is not None:
            try:
                if base.intersects(corte):
                    ha = _pres_area_ha(base.intersection(corte))
            except Exception:
                ha = 0.0
        pct = (ha / total * 100.0) if total > 0 else 0.0
        salida[clave + "_ha"] = _pres_num(ha)
        salida[clave + "_pct"] = _pres_num(pct)
    return salida


def _pres_geojson(feats, crs, props_fn, stats_fn=None):
    """FeatureCollection WGS84 (simplificada) con atributos curados y _stats opcional."""
    features = []
    for props, geom in feats:
        salida_props = props_fn(props)
        if stats_fn:
            salida_props["_stats"] = stats_fn(geom, props)
        geo = geom.__geo_interface__
        geo_wgs = _transformar_a_wgs84(geo, crs, simplificar_m=PRESENTACION_SIMPLIFY_M)
        features.append({"type": "Feature", "properties": salida_props, "geometry": geo_wgs})
    return {"type": "FeatureCollection", "features": features}


def _pres_props_proyecto(p):
    return {
        "Nombre": "Área de Desarrollo Garcero C",
        "Nomenclatura": p.get("NOMENCLAT") or "",
        "Descripción": p.get("DESCRIP") or "",
        "Proyecto": p.get("PROYECTO") or "",
        "Operador": p.get("OPERADOR") or "",
        "Contrato": p.get("CONTRATO") or "",
        "Área oficial (ha)": _pres_num(p.get("AREA_HA") or 0, 4),
    }


def _pres_props_influencia(p):
    tipo = p.get("_pres_tipo") or p.get("AREA_INFL") or p.get("OBSERV") or "Área de influencia"
    return {
        "Área de influencia": tipo,
        "Observaciones": p.get("OBSERV") or "",
        "Área oficial (ha)": _pres_num(p.get("AREA_HA") or 0, 2),
    }


def _pres_props_ut(p):
    mun = str(p.get("MUNICIPIO") or "").strip()
    dep = str(p.get("DEPTO") or "").strip()
    actividades = [p.get("DESC_ACT_1"), p.get("DESC_ACT_2"), p.get("DESC_ACT_3")]
    actividades = [a for a in actividades if a]
    return {
        "Unidad territorial": p.get("NOM_U_TERR") or p.get("VEREDA") or "",
        "Vereda / resguardo": p.get("VEREDA") or "",
        "Tipo": "Unidad territorial menor",
        "Municipio": _PRESENTACION_MUNICIPIOS.get(mun, mun),
        "Departamento": _PRESENTACION_DEPARTAMENTOS.get(dep, dep),
        "Habitantes": p.get("HABITANTES"),
        "Densidad (hab/ha)": p.get("DENSIDAD"),
        "PET": p.get("PET"),
        "Hogares": p.get("NUM_HOG"),
        "Viviendas": p.get("NUM_VIV"),
        "Población asentada": p.get("POBLA_ASEN") or "",
        "Actividades económicas": " · ".join(str(a) for a in actividades),
        "Área oficial (ha)": _pres_num(p.get("AREA_ha") or 0, 2),
    }


def _pres_props_municipio(p):
    cod = str(p.get("MUNICIPIO") or "").strip()
    dep = str(p.get("DEPTO") or "").strip()
    return {
        "Municipio": _PRESENTACION_MUNICIPIOS.get(cod, cod),
        "Código DANE": cod,
        "Departamento": _PRESENTACION_DEPARTAMENTOS.get(dep, dep),
        "Tipo": "Unidad territorial mayor",
        "Población": p.get("POBLA_ASEN") or "",
        "PEA": p.get("ML_PEA"),
        "Viviendas": p.get("NUM_VIVIEN"),
        "Área oficial (ha)": _pres_num(p.get("AREA_ha") or 0, 2),
    }


def _pres_props_departamento(p):
    cod = str(p.get("DEPTO") or "").strip()
    return {
        "Departamento": _PRESENTACION_DEPARTAMENTOS.get(cod, cod),
        "Código DANE": cod,
        "Tipo": "Unidad territorial mayor",
        "Población": p.get("POBLA_ASEN") or "",
        "PEA": p.get("ML_PEA"),
        "Área oficial (ha)": _pres_num(p.get("AREA_ha") or 0, 2),
    }


def _construir_presentacion(ruta_gdb, mtime=0.0, clave=""):
    """Arma la vista ANLA desde la GDB: capas filtradas, estilos y estadisticas."""
    import datetime as _dt
    t0 = time.time()
    leidas = {}
    crs = None
    for capa in PRESENTACION_LAYERS:
        try:
            feats, fcrs = _pres_leer_capa(ruta_gdb, capa)
        except Exception as e:
            return {"ok": False, "error": "No se pudo leer la capa {}: {}".format(capa, e)}
        if not feats and capa != "Departamento":
            return {"ok": False, "error": "La capa {} de la GDB está vacía.".format(capa)}
        leidas[capa] = feats
        crs = crs or fcrs

    # --- Areas de influencia: SOLO fisico-biotica (ID 1) y socioeconomica (ID 2).
    # Las intermedias por componente (ID 3..15) se descartan a proposito.
    infl_fb, infl_se, infl_extra = [], [], []
    for props, geom in leidas.get("AreaInfluencia") or []:
        ida = str(props.get("ID_AREAINF") or "").strip()
        texto = _pres_sin_tildes(str(props.get("AREA_INFL") or "") + " " + str(props.get("OBSERV") or ""))
        if ida == "1" or "fisicobiot" in texto:
            p = dict(props); p["_pres_tipo"] = "Fisicobiótica"
            infl_fb.append((p, geom))
        elif ida == "2" or "socioeconom" in texto:
            p = dict(props); p["_pres_tipo"] = "Socioeconómica"
            infl_se.append((p, geom))
        else:
            infl_extra.append((props, geom))
    if not infl_fb and not infl_se:
        return {"ok": False, "error": "La capa AreaInfluencia no trae el AI fisicobiótica ni la socioeconómica."}

    ad_u = _pres_unir([g for _p, g in leidas.get("AreaProyecto") or []])
    fb_u = _pres_unir([g for _p, g in infl_fb])
    se_u = _pres_unir([g for _p, g in infl_se])

    # --- Unidades territoriales: superficies y porcentajes dentro de las areas ---
    def stats_ut(geom, _props):
        return _pres_stats(geom, [("aifb", fb_u), ("aise", se_u), ("ad", ad_u)])

    def stats_proyecto(geom, _props):
        return _pres_stats(geom, [("aifb", fb_u), ("aise", se_u)])

    def stats_area(geom, _props):
        return {"total_ha": _pres_num(_pres_area_ha(geom))}

    capas = {}
    capas["proyecto"] = {
        "id": "proyecto",
        "nombre": "Área de Desarrollo Garcero C",
        "tema": "Área de Desarrollo",
        "features": len(leidas.get("AreaProyecto") or []),
        "geojson": _pres_geojson(leidas.get("AreaProyecto") or [], crs, _pres_props_proyecto, stats_proyecto),
    }
    capas["influencia"] = {
        "id": "influencia",
        "nombre": "Áreas de influencia",
        "tema": "Áreas de influencia",
        "features": len(infl_fb) + len(infl_se),
        "geojson": _pres_geojson(infl_fb + infl_se, crs, _pres_props_influencia, stats_area),
    }
    capas["ut_menores"] = {
        "id": "ut_menores",
        "nombre": "Unidades territoriales menores (veredas / resguardos)",
        "tema": "Unidades territoriales",
        "features": len(leidas.get("UnidadTerritorial") or []),
        "geojson": _pres_geojson(leidas.get("UnidadTerritorial") or [], crs, _pres_props_ut, stats_ut),
    }
    capas["municipios"] = {
        "id": "municipios",
        "nombre": "Unidades territoriales mayores (municipios)",
        "tema": "Unidades territoriales",
        "features": len(leidas.get("Municipio") or []),
        "geojson": _pres_geojson(leidas.get("Municipio") or [], crs, _pres_props_municipio, stats_ut),
    }
    capas["departamento"] = {
        "id": "departamento",
        "nombre": "Departamento (Casanare)",
        "tema": "Unidades territoriales",
        "features": len(leidas.get("Departamento") or []),
        "geojson": _pres_geojson(leidas.get("Departamento") or [], crs, _pres_props_departamento, stats_ut),
    }

    resp = {
        "ok": True,
        "tipo": "presentacion",
        "version": PRESENTACION_VERSION,
        "generado": _dt.datetime.now().isoformat(timespec="seconds"),
        "origen": "gdb",
        "parcial": False,
        "gdb": {"nombre": os.path.basename(ruta_gdb), "ruta": ruta_gdb},
        "capas": capas,
        "resumen": {
            "proyecto_ha": _pres_num(_pres_area_ha(ad_u)),
            "aifb_ha": _pres_num(_pres_area_ha(fb_u)),
            "aise_ha": _pres_num(_pres_area_ha(se_u)),
            "ai_intermedias_omitidas": len(infl_extra),
            "ut_menores": len(leidas.get("UnidadTerritorial") or []),
            "municipios": len(leidas.get("Municipio") or []),
            "departamento": len(leidas.get("Departamento") or []),
            "con_stats": True,
        },
        "segundos": round(time.time() - t0, 1),
    }

    # Cache que viaja con el proyecto (config/gis_cache): la proxima carga es instantanea
    try:
        if clave:
            os.makedirs(GIS_CACHE_DIR, exist_ok=True)
            archivo_cache = os.path.join(GIS_CACHE_DIR, "presentacion_" + clave + ".json")
            with open(archivo_cache, "w", encoding="utf-8") as fh:
                json.dump({"version": PRESENTACION_VERSION, "mtime": mtime,
                           "simplify": PRESENTACION_SIMPLIFY_M, "resp": resp},
                          fh, ensure_ascii=False, separators=(",", ":"))
    except Exception:
        pass
    return resp


def _pres_gdb_para_vista():
    """GDB con las capas de la presentación (memo 10 min para no barrer el disco cada vez)."""
    memo = _PRESENTACION_GDB_MEMO
    ahora = time.time()
    if memo["ruta"] and os.path.isdir(memo["ruta"]) and (ahora - memo["at"]) < 600:
        return memo["ruta"]
    necesarias = set(PRESENTACION_LAYERS)
    candidatas = []
    try:
        for gdb in _descubrir_gdb():
            ruta = gdb.get("ruta") or ""
            if not ruta or ruta.startswith("cache://"):
                continue
            nombre = (gdb.get("nombre") or "").lower()
            candidatas.append((0 if "garcero" in nombre else 1, ruta))
    except Exception:
        candidatas = []
    candidatas.sort(key=lambda c: c[0])
    for _prio, ruta in candidatas:
        if not os.path.isdir(ruta):
            continue
        try:
            import fiona
            capas = set(fiona.listlayers(ruta))
        except Exception:
            continue
        if necesarias.issubset(capas):
            memo["ruta"] = ruta
            memo["at"] = ahora
            return ruta
    memo["ruta"] = None
    memo["at"] = ahora
    return None


def _presentacion_desde_cache():
    """Copia de la presentación guardada en config/gis_cache (portabilidad a otro PC)."""
    mejor, mejor_mtime = None, -1.0
    try:
        nombres = os.listdir(GIS_CACHE_DIR)
    except OSError:
        return None
    for nombre in nombres:
        if not (nombre.startswith("presentacion_") and nombre.endswith(".json")):
            continue
        ruta = os.path.join(GIS_CACHE_DIR, nombre)
        try:
            with open(ruta, "r", encoding="utf-8") as fh:
                cc = json.load(fh)
        except Exception:
            continue
        if not isinstance(cc, dict) or cc.get("version") != PRESENTACION_VERSION or not cc.get("resp"):
            continue
        try:
            mt = os.path.getmtime(ruta)
        except OSError:
            mt = 0.0
        if mt > mejor_mtime:
            mejor, mejor_mtime = cc, mt
    if not mejor:
        return None
    resp = dict(mejor["resp"])
    resp["origen"] = "cache"
    return resp


def _presentacion_desde_kmz():
    """Respaldo parcial: si no hay GDB, arma la vista con los KMZ portables (sin UT)."""
    rutas = {}
    try:
        for kmz in _descubrir_kmz():
            nombre = _pres_sin_tildes(kmz.get("nombre") or "")
            if "areaproyecto" in nombre and "proyecto" not in rutas:
                rutas["proyecto"] = kmz.get("ruta")
            elif "areainfluencia" in nombre and "influencia" not in rutas:
                rutas["influencia"] = kmz.get("ruta")
    except Exception:
        return {"ok": False, "error": "No hay GDB ni KMZ de la presentación disponibles."}
    if not rutas:
        return {"ok": False, "error": "No se encontró la GDB ni los KMZ (AreaProyecto / AreaInfluencia)."}

    capas = {}
    for clave, nombre, ruta in (("proyecto", "Área de Desarrollo Garcero C", rutas.get("proyecto")),
                                ("influencia", "Áreas de influencia", rutas.get("influencia"))):
        if not ruta:
            continue
        data = _leer_kmz_por_ruta(ruta)
        if not data.get("ok"):
            continue
        feats = (data.get("geojson") or {}).get("features") or []
        salida = []
        for f in feats:
            props = dict(f.get("properties") or {})
            if clave == "influencia":
                ida = str(props.get("ID_AREAINF") or "").strip()
                texto = _pres_sin_tildes(str(props.get("AREA_INFL") or "") + " " + str(props.get("OBSERV") or ""))
                if ida not in ("1", "2") and "fisicobiot" not in texto and "socioeconom" not in texto:
                    continue
                props["_pres_tipo"] = "Fisicobiótica" if (ida == "1" or "fisicobiot" in texto) else "Socioeconómica"
                props = {"Área de influencia": props.get("_pres_tipo"),
                         "Área oficial (ha)": str(props.get("AREA_HA") or "").replace(",", ".")}
            else:
                props = {"Nombre": props.get("DESCRIP") or props.get("NOMENCLAT") or "Área de Desarrollo Garcero C",
                         "Nomenclatura": props.get("NOMENCLAT") or "",
                         "Operador": props.get("OPERADOR") or "",
                         "Área oficial (ha)": str(props.get("AREA_HA") or "").replace(",", ".")}
            salida.append({"type": "Feature", "properties": props, "geometry": f.get("geometry")})
        capas[clave] = {"id": clave, "nombre": nombre, "features": len(salida),
                        "geojson": {"type": "FeatureCollection", "features": salida}}

    if not capas:
        return {"ok": False, "error": "Los KMZ de la presentación no se pudieron leer."}
    return {
        "ok": True,
        "tipo": "presentacion",
        "version": PRESENTACION_VERSION,
        "origen": "kmz",
        "parcial": True,
        "aviso": "Vista parcial: falta la GDB (unidades territoriales y estadísticas). Copia GDB_EIA_GARCERO_C.gdb o su caché.",
        "gdb": None,
        "capas": capas,
        "resumen": {"con_stats": False},
    }


def _presentacion_anla():
    """Punto de entrada del endpoint: GDB en disco > caché que viaja > KMZ parcial."""
    ruta = _pres_gdb_para_vista()
    if ruta:
        try:
            mtime = os.path.getmtime(ruta)
        except OSError:
            mtime = 0.0
        clave = hashlib.md5(os.path.normpath(ruta).lower().encode("utf-8")).hexdigest()
        archivo_cache = os.path.join(GIS_CACHE_DIR, "presentacion_" + clave + ".json")
        try:
            with open(archivo_cache, "r", encoding="utf-8") as fh:
                cc = json.load(fh)
            if (cc.get("version") == PRESENTACION_VERSION and cc.get("mtime") == mtime
                    and cc.get("simplify") == PRESENTACION_SIMPLIFY_M and cc.get("resp")):
                resp = dict(cc["resp"])
                resp["origen"] = "cache"
                return resp
        except Exception:
            pass
        return _construir_presentacion(ruta, mtime, clave)

    resp = _presentacion_desde_cache()
    if resp:
        return resp
    return _presentacion_desde_kmz()


# ---------- Porcentajes de zonificación por area de referencia ----------
# Calcula, a partir de las capas ZonificacionAmbiental y ZonificacionManejo de la
# GDB del EIA, la superficie y el porcentaje de cada categoria dentro del Area de
# Influencia Fisico-biotica (AI FB) y dentro del Area de Desarrollo (bloque)
# Garcero C (AD). Asi la vista de Zonificacion muestra los mismos datos de los
# mapas, sin cifras escritas a mano. El resultado se cachea en
# config/gis_cache/zonificacion_<clave>.json (viaja con el proyecto).
#
# Los valores del AI fisico-biotica se comparan automaticamente con la tabla
# oficial del EIA que esta en los documentos del proyecto (D:\ASI.SAS):
# "9.14 Zonificacion del proyecto" de la presentacion "Tercer Proposito" de
# ASI S.A.S. (2026), diapositivas 52 y 53.

ZONIF_VERSION = 3
ZONIF_SENSIBILIDAD = (
    ("Muy Alta", "Muy Alta", "#FF0000"),
    ("Alta", "Alta", "#FFAA00"),
    ("Moderada", "Moderada", "#FFFF00"),
    ("Baja", "Baja", "#61C200"),
    ("Muy Baja", "Muy Baja", "#489C00"),
)
ZONIF_MANEJO = (
    ("AE", "Área de exclusión", "#FF0000"),
    ("AIR", "Intervención con restricción media", "#FFFF00"),
    ("AI", "Intervención", "#38A800"),
)

# Valores oficiales del EIA (ha) para el AI fisico-biotica, tomados de la tabla
# 9.14 de la presentacion "Tercer Proposito" (ASI S.A.S., 2026).
ZONIF_OFICIAL = {
    "sensibilidad": {"Muy Alta": 13830.10, "Alta": 8340.98, "Moderada": 546.23,
                     "Baja": 104789.31, "Muy Baja": 5.66},
    "manejo": {"AE": 13830.10, "AIR": 8887.21, "AI": 104794.97},
}
ZONIF_OFICIAL_TOLERANCIA_HA = 0.5

# Referencias documentales de los datos (se muestran en la vista Zonificacion).
ZONIF_FUENTES = (
    {"id": "tabla914_ambiental",
     "corto": "Tabla 9.14 «Zonificación ambiental»",
     "titulo": "Tabla 9.14 «Zonificación del proyecto — Zonificación ambiental»",
     "documento": "Presentación «Tercer Propósito» — ASI S.A.S., 2026 (diapositiva 52)",
     "detalle": "Categorías de sensibilidad con área (ha) y porcentaje del AI físico-biótica. Verificación automática contra el SIG."},
    {"id": "tabla914_manejo",
     "corto": "Tabla 9.14 «Zonificación de manejo»",
     "titulo": "Tabla 9.14 «Zonificación del proyecto — Zonificación de manejo»",
     "documento": "Presentación «Tercer Propósito» — ASI S.A.S., 2026 (diapositiva 53)",
     "detalle": "Áreas de exclusión, intervención con restricciones e intervención con área (ha) y porcentaje del AI físico-biótica. Verificación automática contra el SIG."},
    {"id": "capas",
     "corto": "Capas de la GDB EIA Garcero C (T_29_ZONIFICACIÓN)",
     "titulo": "Capas «ZonificacionAmbiental» y «ZonificacionManejo»",
     "documento": "GDB_EIA_GARCERO — carpeta T_29_ZONIFICACIÓN (insumo indicado en la presentación de la app, pestaña 5)",
     "detalle": "Geometrías oficiales del EIA con las que el servidor calcula la superficie de cada categoría."},
    {"id": "ad",
     "corto": "Área de Desarrollo Garcero C: 19.872,68 ha",
     "titulo": "Área de Desarrollo Garcero C: 19.872,68 ha",
     "documento": "CAP 1 «Generalidades» (pág. 10) y CAP 2 «Descripción del Proyecto» (pág. 12) — ASI S.A.S., 2026",
     "detalle": "Área del bloque objeto de la modificación de licencia; es el recorte para la columna «AD Garcero C»."},
)



def _zonif_gdb_para_vista():
    """GDB con las capas de zonificación (reutiliza la búsqueda de la presentación)."""
    necesarias = {"ZonificacionAmbiental", "ZonificacionManejo", "AreaInfluencia", "AreaProyecto"}
    ruta = _pres_gdb_para_vista()
    candidatas = []
    if ruta:
        candidatas.append(ruta)
    try:
        for gdb in _descubrir_gdb():
            r = gdb.get("ruta") or ""
            if not r or r.startswith("cache://") or r in candidatas:
                continue
            candidatas.append(r)
    except Exception:
        pass
    candidatas.sort(key=lambda r: (0 if "garcero" in os.path.basename(r).lower() else 1))
    for r in candidatas:
        if not os.path.isdir(r):
            continue
        try:
            import fiona
            capas = set(fiona.listlayers(r))
        except Exception:
            continue
        if necesarias.issubset(capas):
            return r
    return None


def _construir_zonificacion(ruta_gdb, mtime=0.0, clave=""):
    """Superficie y porcentaje de cada categoria de zonificacion en AI FB y AD."""
    import datetime as _dt
    t0 = time.time()
    try:
        infl, _ = _pres_leer_capa(ruta_gdb, "AreaInfluencia")
        proy, _ = _pres_leer_capa(ruta_gdb, "AreaProyecto")
        amb, _ = _pres_leer_capa(ruta_gdb, "ZonificacionAmbiental")
        man, _ = _pres_leer_capa(ruta_gdb, "ZonificacionManejo")
    except Exception as e:
        return {"ok": False, "error": "No se pudieron leer las capas de zonificación: " + str(e)}

    aifb_u = _pres_unir([g for p, g in infl if str(p.get("ID_AREAINF") or "").strip() == "1"])
    ad_u = _pres_unir([g for _p, g in proy])
    if aifb_u is None or ad_u is None:
        return {"ok": False, "error": "No se encontraron el AI físico-biótica ni el Área de Desarrollo Garcero C."}
    aifb_ha = _pres_area_ha(aifb_u)
    ad_ha = _pres_area_ha(ad_u)

    # Predicados preparados: casi todos los polígonos están enteros dentro del AI
    # físico-biótica o fuera del AD; la intersección (costosa) solo se calcula en
    # los polígonos que cruzan el borde del recorte.
    from shapely.prepared import prep
    prep_fb = prep(aifb_u)
    prep_ad = prep(ad_u)

    def _area_dentro(geom, contenedor, prep_cont):
        try:
            if prep_cont.contains(geom):
                return _pres_area_ha(geom)
            if not prep_cont.intersects(geom):
                return 0.0
            return _pres_area_ha(geom.intersection(contenedor))
        except Exception:
            return 0.0

    def acumular(feats, campo):
        # categoria -> [ha dentro de AIFB, ha dentro de AD, ha total]
        out = {}
        for props, geom in feats:
            cat = str(props.get(campo) or props.get("NOMENCLAT") or "").strip() or "(sin categoría)"
            reg = out.setdefault(cat, [0.0, 0.0, 0.0])
            reg[2] += _pres_area_ha(geom)
            reg[0] += _area_dentro(geom, aifb_u, prep_fb)
            reg[1] += _area_dentro(geom, ad_u, prep_ad)
        return out

    amb_acum = acumular(amb, "NOMENCLAT")
    man_acum = acumular(man, "NOMENCLAT")

    def fila(categoria, codigo, color, valores):
        ha_fb, ha_ad, total = valores
        return {
            "categoria": categoria,
            "codigo": codigo,
            "color": color,
            "total_ha": _pres_num(total),
            "aifb_ha": _pres_num(ha_fb),
            "aifb_pct": _pres_num(ha_fb / aifb_ha * 100.0 if aifb_ha else 0.0),
            "ad_ha": _pres_num(ha_ad),
            "ad_pct": _pres_num(ha_ad / ad_ha * 100.0 if ad_ha else 0.0),
        }

    sensibilidad = []
    for codigo, etiqueta, color in ZONIF_SENSIBILIDAD:
        match = next((c for c in amb_acum if _pres_sin_tildes(c) == _pres_sin_tildes(codigo)), None)
        datos = amb_acum.pop(match, [0.0, 0.0, 0.0]) if match else [0.0, 0.0, 0.0]
        sensibilidad.append(fila(etiqueta, codigo, color, datos))
    for cat in sorted(amb_acum):
        sensibilidad.append(fila(cat, cat, "#94A3B8", amb_acum[cat]))

    manejo = []
    for codigo, etiqueta, color in ZONIF_MANEJO:
        datos = man_acum.pop(codigo, [0.0, 0.0, 0.0])
        manejo.append(fila(etiqueta, codigo, color, datos))
    for cat in sorted(man_acum):
        manejo.append(fila(cat, cat, "#94A3B8", man_acum[cat]))

    def _validar(filas, oficial):
        """Compara los valores calculados (AI físico-biótica) con la tabla oficial del EIA."""
        detalles = []
        ok = True
        for f in filas:
            clave = f.get("codigo")
            if clave not in oficial:
                continue
            calc = float(f.get("aifb_ha") or 0.0)
            dif = round(calc - float(oficial[clave]), 2)
            coincide = abs(dif) <= ZONIF_OFICIAL_TOLERANCIA_HA
            ok = ok and coincide
            detalles.append({
                "categoria": f.get("categoria"),
                "codigo": clave,
                "oficial_ha": oficial[clave],
                "calculado_ha": calc,
                "diferencia_ha": dif,
                "coincide": coincide,
            })
        return {"ok": ok, "detalles": detalles}

    resp = {
        "ok": True,
        "tipo": "zonificacion",
        "version": ZONIF_VERSION,
        "generado": _dt.datetime.now().isoformat(timespec="seconds"),
        "origen": "gdb",
        "gdb": {"nombre": os.path.basename(ruta_gdb), "ruta": ruta_gdb},
        "referencias": {
            "aifb": {"clave": "aifb", "nombre": "Área de Influencia Físico-biótica", "ha": _pres_num(aifb_ha)},
            "ad": {"clave": "ad", "nombre": "Área de Desarrollo Garcero C", "ha": _pres_num(ad_ha)},
        },
        "sensibilidad": sensibilidad,
        "manejo": manejo,
        "nota": ("El porcentaje de cada categoría se calcula sobre el área total del recinto de "
                 "referencia (Área de Influencia Físico-biótica o Área de Desarrollo Garcero C)."),
        "fuentes": [dict(f) for f in ZONIF_FUENTES],
        "validacion": {
            "info": ("Los valores del AI físico-biótica se comparan con la tabla 9.14 «Zonificación del "
                     "proyecto» de la presentación «Tercer Propósito» (ASI S.A.S., 2026, diapositivas 52 y 53)."),
            "documento": "Presentacion Tercer Proposito.pptx — carpeta D:\\ASI.SAS\\Presentaciones de referencia",
            "sensibilidad": _validar(sensibilidad, ZONIF_OFICIAL["sensibilidad"]),
            "manejo": _validar(manejo, ZONIF_OFICIAL["manejo"]),
        },
        "segundos": round(time.time() - t0, 1),
    }

    try:
        if clave:
            os.makedirs(GIS_CACHE_DIR, exist_ok=True)
            archivo_cache = os.path.join(GIS_CACHE_DIR, "zonificacion_" + clave + ".json")
            with open(archivo_cache, "w", encoding="utf-8") as fh:
                json.dump({"version": ZONIF_VERSION, "mtime": mtime, "resp": resp},
                          fh, ensure_ascii=False, separators=(",", ":"))
    except Exception:
        pass
    return resp


def _zonificacion_desde_cache():
    """Copia de los porcentajes guardada en config/gis_cache (portabilidad a otro PC)."""
    mejor, mejor_mtime = None, -1.0
    try:
        nombres = os.listdir(GIS_CACHE_DIR)
    except OSError:
        return None
    for nombre in nombres:
        if not (nombre.startswith("zonificacion_") and nombre.endswith(".json")):
            continue
        ruta = os.path.join(GIS_CACHE_DIR, nombre)
        try:
            with open(ruta, "r", encoding="utf-8") as fh:
                cc = json.load(fh)
        except Exception:
            continue
        if not isinstance(cc, dict) or cc.get("version") != ZONIF_VERSION or not cc.get("resp"):
            continue
        try:
            mt = os.path.getmtime(ruta)
        except OSError:
            mt = 0.0
        if mt > mejor_mtime:
            mejor, mejor_mtime = cc, mt
    if not mejor:
        return None
    resp = dict(mejor["resp"])
    resp["origen"] = "cache"
    return resp


def _zonificacion_anla():
    """Punto de entrada del endpoint: GDB en disco > caché que viaja con el proyecto."""
    ruta = _zonif_gdb_para_vista()
    if ruta:
        try:
            mtime = os.path.getmtime(ruta)
        except OSError:
            mtime = 0.0
        clave = hashlib.md5(os.path.normpath(ruta).lower().encode("utf-8")).hexdigest()
        archivo_cache = os.path.join(GIS_CACHE_DIR, "zonificacion_" + clave + ".json")
        try:
            with open(archivo_cache, "r", encoding="utf-8") as fh:
                cc = json.load(fh)
            if (cc.get("version") == ZONIF_VERSION and cc.get("mtime") == mtime and cc.get("resp")):
                resp = dict(cc["resp"])
                resp["origen"] = "cache"
                return resp
        except Exception:
            pass
        return _construir_zonificacion(ruta, mtime, clave)
    resp = _zonificacion_desde_cache()
    if resp:
        return resp
    return {"ok": False, "error": ("No se encontró la GDB del EIA ni la caché de zonificación. "
                                   "Copia GDB_EIA_GARCERO_C.gdb al proyecto o revisa config/gis_paths.txt.")}


# ==============================================
# TILES RASTER (render tipo "Google Maps") + IDENTIFY
# El navegador ya no recibe geometría: PNG por recuadro y el popup se
# resuelve en el servidor (identify) con la geometría ORIGINAL.
# ==============================================
_TILE_RENDER_LOCK = threading.Lock()
_TILE_STATE_LOCK = threading.Lock()  # construye _TILE_STATE UNA sola vez (12.000 geometrías)
_TILE_STATE = {}     # gdb_id -> estado preparado en memoria (Mercator 3857)
_GDB_PATHS = {}      # gdb_id -> ruta (descubierta perezosamente)
_GDB_SIN_RUTA = set()  # ids que solo existen como caché (no hay .gdb en disco)
_GDB_SCAN_TTL = 30.0   # segundos entre barridos de descubrimiento de GDB
_GDB_SCAN_AT = 0.0
_EARTH_WORLD = 2.0 * math.pi * 6378137.0


def _transformer_merc():
    """Transformer cacheado EPSG:4326 -> EPSG:3857 (Web Mercator)."""
    from pyproj import CRS, Transformer
    clave = "merc-4326-3857"
    tr = _TRANSFORM_CACHE.get(clave)
    if tr is None:
        tr = Transformer.from_crs(CRS.from_epsg(4326), CRS.from_epsg(3857), always_xy=True)
        _TRANSFORM_CACHE[clave] = tr
    return tr


def _localizar_gdb(gdb_id):
    """Ruta en disco de una GDB descubierta (None si solo existe en caché o no está).

    El barrido de descubrimiento se hace como mucho cada _GDB_SCAN_TTL segundos:
    así los tiles/leyenda/puntos no re-buscan en config/gdb ni releen las
    cabeceras de la caché por cada imagen (en un PC distinto al de origen no
    hay .gdb en disco y todo se atiende desde la caché integrada)."""
    global _GDB_SCAN_AT, _GDB_SIN_RUTA
    if not re.fullmatch(r"[0-9a-f]{32}", gdb_id or ""):
        return None
    if gdb_id in _GDB_PATHS:
        return _GDB_PATHS[gdb_id]
    if gdb_id in _GDB_SIN_RUTA:
        return None
    ahora = time.time()
    if ahora - _GDB_SCAN_AT >= _GDB_SCAN_TTL:
        _GDB_SCAN_AT = ahora
        ids_json = set()
        try:
            for nombre in os.listdir(GIS_CACHE_DIR):
                m32 = re.fullmatch(r"([0-9a-f]{32})\.json", nombre)
                if m32:
                    ids_json.add(m32.group(1))
        except OSError:
            pass
        try:
            for e in _descubrir_gdb():
                if e["ruta"].startswith("cache://"):
                    continue
                k = hashlib.md5(os.path.normpath(e["ruta"]).lower().encode("utf-8")).hexdigest()
                _GDB_PATHS[k] = e["ruta"]
        except Exception:
            pass
        _GDB_SIN_RUTA = ids_json - set(_GDB_PATHS)
    return _GDB_PATHS.get(gdb_id)


def _geo_a_merc(g):
    tr = _transformer_merc()
    gg = dict(g)
    gg["coordinates"] = _walk_coords(gg.get("coordinates") or [], tr)
    return gg


def _nombre_prop(props):
    for k in ("NOMBRE", "nombre", "name", "NOMBRE_COMPLETO", "CODIGO", "codigo", "Label"):
        if props.get(k):
            return str(props[k])
    return None


_PALETA_POL = [
    ("#e7c98e", "#a5722a"), ("#bcd5ef", "#3f82b6"), ("#d6eac4", "#5f9c4e"),
    ("#ebd3f0", "#944d9e"), ("#f2cfc7", "#ab5543"), ("#cdebe2", "#3f9c8a"),
    ("#f0e6c0", "#a09040"), ("#c9cfe8", "#56679e"),
]
_PALETA_PTS = ["#d33b3b", "#0f8f5f", "#c2569f", "#e08a2e", "#2b6cb0", "#8a5cd6", "#0d9fb4"]


def _prio_capa(capa):
    low = (capa or "").lower()
    if "cartografia" in low:
        if any(s in low for s in ("mda", "depart", "pais")):
            return 1
        return 2
    if any(s in low for s in ("punto", "muestreo", "sondeo", "captacion", "sitio", "ocupacion")) or low.endswith("pt"):
        return 9
    return 5


def _colores_capa(capa, i):
    low = (capa or "").lower()
    if "mda" in low:
        return ("#b9d19b", "#5d7a43", None)
    if any(s in low for s in ("depart", "pais")):
        return ("#e8e2d5", "#8a8177", None)
    if any(s in low for s in ("drenaj", "dagua")):
        return ("#a5c9ea", "#2f6fae", None)
    if any(s in low for s in ("via", "camino", "constr")):
        return ("#e8c58e", "#a56f2c", None)
    if any(s in low for s in ("vulnera", "acuifer")):
        return ("#93c9b5", "#2a7058", "#0f7f5f")
    if "paisaje" in low:
        return ("#cfe3a0", "#6f9140", None)
    if "hidrogeolog" in low:
        return ("#aacdf0", "#3f7fb8", "#2b6cb0")
    if "geotec" in low:
        return ("#e3c69a", "#96682f", None)
    if any(s in low for s in ("cuenca", "recarga")):
        return ("#9fd4ea", "#33799e", "#1e6f9b")
    if any(s in low for s in ("ocupacion", "cauce")):
        return ("#e8837b", "#9e3a34", "#c0392b")
    if any(s in low for s in ("punto", "muestreo", "sondeo", "captacion", "sitio")) or low.endswith("pt"):
        return (None, None, _PALETA_PTS[i % len(_PALETA_PTS)])
    return _PALETA_POL[i % len(_PALETA_POL)]


def _cargar_estado(gdb_id, ruta):
    """Prepara en memoria las geometrías en Mercator por capa (+ índices) para tiles e identify.
    Funciona tanto si la GDB existe en disco como si solo está el GeoJSON en caché
    (config/gis_cache/<gdb_id>.json), que es el caso normal al abrir el paquete en otro PC."""
    if not re.fullmatch(r"[0-9a-f]{32}", gdb_id or ""):
        return None
    if gdb_id in _TILE_STATE:
        return _TILE_STATE[gdb_id]
    archivo = os.path.join(GIS_CACHE_DIR, gdb_id + ".json")
    if not os.path.isfile(archivo):
        return None
    try:
        with open(archivo, "r", encoding="utf-8") as fh:
            cc = json.load(fh)
        feats = (cc.get("geojson") or {}).get("features") or []
    except Exception:
        return None
    if not feats:
        return None

    # Construcción UNA sola vez: los primeros tiles + leyenda + puntos llegan
    # en paralelo y cada uno llamaba a esta función; sin candado, cada hilo
    # reconstruía las ~12.000 geometrías (reproyección + STRtree) por su lado,
    # saturando CPU y RAM (se vieron +2 GB) en el arranque. Con doble chequeo
    # solo el primer hilo construye y el resto espera y reutiliza.
    with _TILE_STATE_LOCK:
        if gdb_id in _TILE_STATE:
            return _TILE_STATE[gdb_id]

        from shapely.geometry import shape
        from shapely.ops import transform
        from shapely.strtree import STRtree

        tr = _transformer_merc()
        por_capa, orden = {}, []
        for f in feats:
            capa = f.get("properties", {}).get("_capa", "?")
            if capa not in por_capa:
                por_capa[capa] = []
                orden.append(capa)
            ga = f.get("geometry")
            if not ga:
                continue
            try:
                g = shape(_geo_a_merc(ga))
                if g is None or g.is_empty:
                    continue
                if not g.is_valid:
                    g = g.buffer(0)
            except Exception:
                continue
            por_capa[capa].append([g, f.get("properties", {})])

        merc = {}
        minx = miny = float("inf")
        maxx = maxy = float("-inf")
        for capa, arr in por_capa.items():
            arr2 = [x for x in arr if x[0] is not None]
            if not arr2:
                continue
            geoms = [x[0] for x in arr2]
            for g in geoms:
                b = g.bounds
                minx = min(minx, b[0]); miny = min(miny, b[1])
                maxx = max(maxx, b[2]); maxy = max(maxy, b[3])
            merc[capa] = {"arr": arr2, "tree": STRtree(geoms)}

        st = {
            "merc": merc,
            "extent": (minx, miny, maxx, maxy),
            "colores": {c: _colores_capa(c, i) for i, c in enumerate(merc)},
            "orden": sorted(merc.keys(), key=lambda c: _prio_capa(c)),
        }
        _TILE_STATE[gdb_id] = st
        return st


def _tile_bbox(z, x, y):
    n = 1 << z
    half = _EARTH_WORLD / 2.0
    w_tile = _EARTH_WORLD / n
    xmin = x * w_tile - half
    xmax = (x + 1) * w_tile - half
    ymax = half - y * w_tile
    ymin = half - (y + 1) * w_tile
    return xmin, ymin, xmax, ymax


def _tile_png(gdb_id, z, x, y):
    """Devuelve el PNG del tile (caché en disco o render bajo demanda).
    No exige que la .gdb exista: si hay GeoJSON en caché se dibuja igual."""
    ruta = _localizar_gdb(gdb_id)
    st = _cargar_estado(gdb_id, ruta)
    if not st:
        return None
    archivo = os.path.join(GIS_TILES_DIR, gdb_id, str(z), str(x), "{}.png".format(y))
    try:
        if os.path.isfile(archivo):
            with open(archivo, "rb") as fh:
                return fh.read()
    except Exception:
        pass

    minx, miny, maxx, maxy = _tile_bbox(z, x, y)
    ex = st["extent"]
    if ex is None or maxx < ex[0] or minx > ex[2] or maxy < ex[1] or miny > ex[3]:
        return None

    from shapely.geometry import box
    tb = box(minx, miny, maxx, maxy)
    px = (maxx - minx) / 256.0
    tol = px * 0.35
    pxv = px * 2.0    # mínimo tamaño (2 px) para dibujar un feature

    with _TILE_RENDER_LOCK:
        try:
            import matplotlib
            matplotlib.use("Agg")
            import matplotlib.pyplot as plt
            from matplotlib.collections import LineCollection, PatchCollection
            from matplotlib.patches import Polygon as MplPoly

            dpi = 100
            fig = plt.figure(figsize=(5.12, 5.12), dpi=dpi)
            fig.patch.set_alpha(0.0)
            ax = fig.add_axes([0, 0, 1, 1])
            ax.set_xlim(minx, maxx)
            ax.set_ylim(miny, maxy)
            ax.set_axis_off()
            ax.patch.set_alpha(0.0)

            for capa in st["orden"]:
                datos = st["merc"].get(capa)
                if not datos:
                    continue
                arr, tree = datos["arr"], datos["tree"]
                col = st["colores"].get(capa, ("#cccccc", "#999999"))
                fill = col[0]; edge = col[1]; pcol = col[2] if len(col) > 2 else None
                try:
                    idxs = tree.query(tb)
                except Exception:
                    idxs = []

                polys, line_pts, scatter_pts = [], [], []
                for i in idxs:
                    g, props = arr[i]
                    if len(g.bounds) == 4:
                        gw = g.bounds[2] - g.bounds[0]
                        gh = g.bounds[3] - g.bounds[1]
                        if max(gw, gh) < pxv and g.geom_type not in ("Point", "MultiPoint"):
                            continue
                    gg = None
                    try:
                        gg = tb.intersection(g.simplify(tol, preserve_topology=True))
                    except Exception:
                        gg = None
                    if gg is None or gg.is_empty:
                        continue
                    gt = gg.geom_type
                    if gt == "Polygon":
                        coords = list(gg.exterior.coords)
                        xs = [p[0] for p in coords]; ys = [p[1] for p in coords]
                        if len(xs) >= 3:
                            polys.append(MplPoly(list(zip(xs, ys))))
                    elif gt == "MultiPolygon":
                        for poly in gg.geoms:
                            coords = list(poly.exterior.coords)
                            xs = [p[0] for p in coords]
                            ys = [p[1] for p in coords]
                            if len(xs) >= 3:
                                polys.append(MplPoly(list(zip(xs, ys))))
                    elif gt == "LineString":
                        line_pts.append(list(gg.coords))
                    elif gt == "MultiLineString":
                        line_pts.extend([list(l.coords) for l in gg.geoms])
                    elif gt == "Point":
                        scatter_pts.append((gg.x, gg.y, props))
                    elif gt == "MultiPoint":
                        for pt in gg.geoms:
                            scatter_pts.append((pt.x, pt.y, props))
                    elif gt == "GeometryCollection":
                        for sub in gg.geoms:
                            if sub.geom_type == "Point":
                                scatter_pts.append((sub.x, sub.y, props))
                            elif sub.geom_type == "Polygon":
                                coords = list(sub.exterior.coords)
                                xs = [p[0] for p in coords]
                                ys = [p[1] for p in coords]
                                if len(xs) >= 3:
                                    polys.append(MplPoly(list(zip(xs, ys))))

                if polys and fill:
                    pc = PatchCollection(polys, facecolor=fill, edgecolor=edge,
                                         linewidths=0.5, alpha=0.9, zorder=3)
                    ax.add_collection(pc)
                if line_pts:
                    lc = LineCollection(line_pts, colors=edge or "#666666",
                                        linewidths=1.1, alpha=0.95, zorder=4)
                    ax.add_collection(lc)
                if scatter_pts:
                    xs = [p[0] for p in scatter_pts]
                    ys = [p[1] for p in scatter_pts]
                    col_pt = pcol or edge or "#d33b3b"
                    ax.scatter(xs, ys, s=30, color=col_pt, edgecolors="#0b1220",
                               linewidths=0.4, zorder=6)
                    if z >= 15 and len(scatter_pts) <= 60:
                        for sx, sy, props in scatter_pts:
                            nm = _nombre_prop(props)
                            if nm:
                                ax.annotate(nm, (sx, sy), xytext=(12, 12),
                                            textcoords="offset points",
                                            fontsize=11, color="#0b1220", zorder=7,
                                            bbox=dict(fc="white", alpha=0.65, lw=0, pad=1.5))
        except Exception:
            plt.close(fig)
            return None

        buf = io.BytesIO()
        try:
            fig.savefig(buf, format="png", dpi=dpi, transparent=True)
        finally:
            plt.close(fig)
        png = buf.getvalue()

    try:
        os.makedirs(os.path.join(GIS_TILES_DIR, gdb_id, str(z), str(x)), exist_ok=True)
        with open(archivo, "wb") as fh:
            fh.write(png)
    except Exception:
        pass
    return png


def _identificar(gdb_id, lat, lng, z):
    st = _cargar_estado(gdb_id, _localizar_gdb(gdb_id))
    if not st:
        return {"ok": False, "error": "La GDB no tiene datos preparados."}
    tr = _transformer_merc()
    px, py = tr.transform(lng, lat)
    n = 1 << max(0, int(z or 12))
    tol = (_EARTH_WORLD / n / 256.0) * 10.0
    from shapely.geometry import Point, box

    caja = box(px - tol, py - tol, px + tol, py + tol)
    mejor = None
    mejor_key = None
    for capa, datos in st["merc"].items():
        arr, tree = datos["arr"], datos["tree"]
        try:
            idxs = tree.query(caja)
        except Exception:
            continue
        for i in idxs:
            g, props = arr[i]
            gt = g.geom_type
            try:
                if gt in ("Point", "MultiPoint"):
                    dist = g.distance(Point(px, py))
                    if dist <= tol:
                        key = (_prio_capa(capa), 3, -dist)
                        if mejor_key is None or key > mejor_key:
                            mejor_key, mejor = key, (capa, props)
                elif gt in ("Polygon", "MultiPolygon"):
                    if g.contains(Point(px, py)):
                        area = abs(g.area)
                        key = (_prio_capa(capa), 2, -area)
                        if mejor_key is None or key > mejor_key:
                            mejor_key, mejor = key, (capa, props)
                elif gt in ("LineString", "MultiLineString"):
                    dist = g.distance(Point(px, py))
                    if dist <= tol:
                        key = (_prio_capa(capa), 1, -dist)
                        if mejor_key is None or key > mejor_key:
                            mejor_key, mejor = key, (capa, props)
            except Exception:
                continue
    if not mejor:
        return {"ok": False, "error": "No hay ninguna entidad en este punto."}
    capa, props = mejor
    props_out = {k: v for k, v in props.items() if k != "_capa"}
    return {"ok": True, "capa": capa, "layer": capa.split(" / ", 1)[-1],
            "propiedades": props_out}


def _transformer_merc_inv():
    """Transformer cacheado EPSG:3857 -> EPSG:4326 (para overlay de puntos en WGS84)."""
    from pyproj import CRS, Transformer
    clave = "merc-inv-3857-4326"
    tr = _TRANSFORM_CACHE.get(clave)
    if tr is None:
        tr = Transformer.from_crs(CRS.from_epsg(3857), CRS.from_epsg(4326), always_xy=True)
        _TRANSFORM_CACHE[clave] = tr
    return tr


def _tipo_geom(g):
    gt = g.geom_type
    if gt in ("Point", "MultiPoint"):
        return "punto"
    if gt in ("LineString", "MultiLineString"):
        return "linea"
    if gt in ("Polygon", "MultiPolygon"):
        return "area"
    return "mixto"


def _leyenda_gdb(gdb_id):
    """Resumen por capa (color de la paleta real, conteo y tipo) para la leyenda del mapa."""
    st = _cargar_estado(gdb_id, _localizar_gdb(gdb_id))
    if not st:
        return None
    salida = []
    for capa in st["orden"]:
        datos = st["merc"].get(capa)
        if not datos or not datos["arr"]:
            continue
        col = st["colores"].get(capa, ("#cccccc", "#999999"))
        fill = col[0]; edge = col[1]
        pcol = col[2] if len(col) > 2 else None
        tipo = _tipo_geom(datos["arr"][0][0])
        salida.append({
            "capa": capa,
            "layer": capa.split(" / ", 1)[-1],
            "tipo": tipo,
            "fill": fill, "edge": edge, "point": pcol or fill or edge,
            "count": len(datos["arr"]),
        })
    return salida


def _puntos_gdb(gdb_id):
    """Todos los puntos en WGS84 (overlay interactivo encima de los tiles)."""
    st = _cargar_estado(gdb_id, _localizar_gdb(gdb_id))
    if not st:
        return None
    inv = _transformer_merc_inv()
    feats = []
    for capa in st["orden"]:
        datos = st["merc"].get(capa)
        if not datos or not datos["arr"]:
            continue
        if _tipo_geom(datos["arr"][0][0]) != "punto":
            continue
        col = st["colores"].get(capa, ("#cccccc", "#999999"))
        pcol = col[2] if len(col) > 2 else (col[1] or col[0])
        for g, props in datos["arr"]:
            coords = []
            if g.geom_type == "Point":
                lng, lat = inv.transform(g.x, g.y)
                coords = [[lng, lat]]
            elif g.geom_type == "MultiPoint":
                for pt in g.geoms:
                    lng, lat = inv.transform(pt.x, pt.y)
                    coords.append([lng, lat])
            for lng, lat in coords:
                pop = dict(props)
                pop["_capa"] = capa
                feats.append({
                    "type": "Feature",
                    "geometry": {"type": "Point", "coordinates": [lng, lat]},
                    "properties": pop,
                })
    return {"features": feats, "count": len(feats)}


class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=BASE_DIR, **kwargs)

    # ------------------------------------------------------------------
    # Autenticacion basica opcional. Se activa solo si AMBAS variables
    # MAPA_AUTH_USER y MAPA_AUTH_PASSWORD estan definidas. El healthcheck
    # /api/ping queda exento para que Docker pueda verificar el servicio.
    # ------------------------------------------------------------------
    def _auth_configurada(self):
        return bool(
            os.environ.get("MAPA_AUTH_USER", "").strip()
            and os.environ.get("MAPA_AUTH_PASSWORD", "").strip()
        )

    def _autorizado(self):
        if not self._auth_configurada():
            return True
        cabecera = self.headers.get("Authorization", "")
        if not cabecera.startswith("Basic "):
            return False
        try:
            usuario, clave = base64.b64decode(cabecera[6:].strip()).decode("utf-8").split(":", 1)
        except Exception:
            return False
        return (
            hmac.compare_digest(usuario, os.environ.get("MAPA_AUTH_USER", "").strip())
            and hmac.compare_digest(clave, os.environ.get("MAPA_AUTH_PASSWORD", "").strip())
        )

    def _pedir_auth(self):
        self.send_response(401)
        self.send_header("WWW-Authenticate", 'Basic realm="Mapa Garcero C", charset="UTF-8"')
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(b"<h1>401</h1><p>Autenticacion requerida.</p>")

    def end_headers(self):
        if getattr(self, "_acepta_rangos", False):
            self._acepta_rangos = False
            self.send_header("Accept-Ranges", "bytes")
        self.send_header("Cache-Control", "no-cache, must-revalidate")
        super().end_headers()

    # ------------------------------------------------------------------
    # PETICIONES POR RANGOS (Range): imprescindible para que los videos se
    # reproduzcan de forma fluida (arranque inmediato, adelantar/retroceder
    # y no descargar archivos completos de una sola vez).
    # ------------------------------------------------------------------
    def send_head(self):
        if not self._autorizado():
            self._pedir_auth()
            return None
        self._rango = None
        ruta = self.translate_path(self.path)
        if os.path.isfile(ruta) and self.headers.get("Range"):
            archivo = self._send_head_rango(ruta)
            if archivo is not None:
                return archivo
        self._acepta_rangos = os.path.isfile(ruta)
        return super().send_head()

    def _send_head_rango(self, ruta):
        """Responde 206 Partial Content con el trozo pedido. Devuelve None si
        el rango no es válido (en ese caso se responde el archivo completo)."""
        try:
            tam = os.path.getsize(ruta)
            m = re.match(r"bytes=(\d*)-(\d*)\s*$", (self.headers.get("Range") or "").strip())
            if not m or tam <= 0:
                return None
            ini_s, fin_s = m.group(1), m.group(2)
            if ini_s == "":
                # "bytes=-N" significa: los últimos N bytes
                n = int(fin_s or 0)
                if n <= 0:
                    return None
                ini = max(0, tam - n)
                fin = tam - 1
            else:
                ini = int(ini_s)
                fin = int(fin_s) if fin_s else tam - 1
            fin = min(fin, tam - 1)
            if ini >= tam or ini > fin:
                return None
            archivo = open(ruta, "rb")
            archivo.seek(ini)
            self._rango = (ini, fin - ini + 1)
            self.send_response(206)
            self.send_header("Content-Type", self.guess_type(ruta))
            self.send_header("Accept-Ranges", "bytes")
            self.send_header("Content-Range", "bytes %d-%d/%d" % (ini, fin, tam))
            self.send_header("Content-Length", str(fin - ini + 1))
            self.send_header("Last-Modified", self.date_time_string(os.path.getmtime(ruta)))
            self.end_headers()
            return archivo
        except OSError:
            return None

    def copyfile(self, source, outputfile):
        """Copia el archivo al cliente; si es un rango, solo los bytes pedidos."""
        rango = getattr(self, "_rango", None)
        if rango is None:
            return super().copyfile(source, outputfile)
        self._rango = None
        restante = rango[1]
        while restante > 0:
            trozo = source.read(min(262144, restante))
            if not trozo:
                break
            outputfile.write(trozo)
            restante -= len(trozo)

    def _enviar_archivo(self, bytes_data, nombre, mime):
        self.send_response(200)
        self.send_header("Content-Type", mime)
        self.send_header("Content-Length", str(len(bytes_data)))
        self.send_header("Content-Disposition", 'attachment; filename="%s"' % nombre)
        self.end_headers()
        self.wfile.write(bytes_data)

    def _exportar_shp(self):
        try:
            length = int(self.headers.get("Content-Length") or 0)
            if length <= 0 or length > 64 * 1024 * 1024:
                send_json(self, {"ok": False, "error": "Cuerpo de petición inválido."}, 400)
                return
            payload = json.loads(self.rfile.read(length).decode("utf-8") or "{}")
            geojson = payload.get("geojson") or {}
            nombre = sanitize_name(payload.get("nombre") or "capa")
            features = (geojson.get("features") or []) if isinstance(geojson, dict) else []
            if not features:
                send_json(self, {"ok": False, "error": "No hay entidades que exportar."}, 400)
                return
            try:
                import fiona
            except Exception:
                send_json(self, {"ok": False, "error": "El servidor no tiene 'fiona' para SHP (pip install fiona)."}, 500)
                return

            def _normalizar_geom(tipo, coords):
                if tipo in ("Polygon", "MultiPolygon"):
                    polys = coords if tipo == "MultiPolygon" else [coords]
                    return {"type": "MultiPolygon", "coordinates": polys}
                if tipo in ("LineString", "MultiLineString"):
                    lines = coords if tipo == "MultiLineString" else [coords]
                    return {"type": "MultiLineString", "coordinates": lines}
                if tipo in ("Point", "MultiPoint"):
                    pts = coords if tipo == "MultiPoint" else [coords]
                    return {"type": "MultiPoint", "coordinates": pts}
                return None

            familias = {"MultiPolygon": "Polygon", "MultiLineString": "LineString", "MultiPoint": "Point"}
            por_familia = {"Polygon": [], "LineString": [], "Point": []}
            for f in features:
                g = f.get("geometry") or {}
                norm = _normalizar_geom(g.get("type"), g.get("coordinates"))
                if not norm:
                    continue
                props = {}
                for k, v in (f.get("properties") or {}).items():
                    if v is None:
                        continue
                    key = re.sub(r"[^A-Za-z0-9_]", "_", str(k))[:10] or "fld"
                    while key in props and props[key] != v:
                        key = key[:-1] + "x"
                    props[key] = float(v) if isinstance(v, (int, float)) else str(v)
                por_familia[familias[norm["type"]]].append({"properties": props, "geometry": norm})

            tmpdir = tempfile.mkdtemp(prefix="shp_")
            try:
                crs_wgs84 = "EPSG:4326"
                archivos = []
                for familia in ("Polygon", "LineString", "Point"):
                    items = por_familia[familia]
                    if not items:
                        continue
                    cols = {}
                    for it in items:
                        for k, v in it["properties"].items():
                            cols.setdefault(k, type(v).__name__)
                    schema_props = {}
                    for k, t in cols.items():
                        ft = "str"
                        if t == "float":
                            ft = "float"
                        elif t == "int":
                            ft = "int"
                        schema_props[k] = ft
                    shp_path = os.path.join(tmpdir, nombre + "_" + familia + ".shp")
                    multi_tipo = {"Polygon": "MultiPolygon", "LineString": "MultiLineString", "Point": "MultiPoint"}[familia]
                    with fiona.open(shp_path, "w", driver="ESRI Shapefile",
                                    schema={"geometry": multi_tipo, "properties": schema_props},
                                    crs=crs_wgs84) as dst:
                        for it in items:
                            rp = {k: (float(v) if schema_props[k] == "float" else v if schema_props[k] == "int" else str(v)) for k, v in it["properties"].items()}
                            dst.write({"properties": rp, "geometry": it["geometry"]})
                    for suf in (".shp", ".shx", ".dbf", ".prj", ".cpg"):
                        sf = shp_path[:-4] + suf
                        if os.path.exists(sf):
                            archivos.append(sf)
                if not archivos:
                    send_json(self, {"ok": False, "error": "Ninguna geometría válida para exportar."}, 400)
                    return
                buf = io.BytesIO()
                with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
                    for sf in archivos:
                        z.write(sf, os.path.basename(sf))
                self._enviar_archivo(buf.getvalue(), nombre + ".zip", "application/zip")
            finally:
                shutil.rmtree(tmpdir, ignore_errors=True)
        except Exception as e:
            send_json(self, {"ok": False, "error": "Error exportando SHP: %s" % e}, 500)

    def do_GET(self):
        ruta = self.path.split("?")[0].rstrip("/")

        if ruta == "/api/ping":
            send_json(self, {"ok": True, "app": "mapa-garcero-c", "version": 1, "sesion": SESION_ID})
            return

        if not self._autorizado():
            self._pedir_auth()
            return

        m = re.match(r"^/api/gis/tiles/([0-9a-f]{32})/(\d+)/(\d+)/(\d+)\.png$", ruta)
        if m:
            gdb_id = m.group(1)
            z = int(m.group(2)); x = int(m.group(3)); y = int(m.group(4))
            n = 1 << z
            if z < 0 or z > GIS_TILES_MAX_ZOOM or x < 0 or x >= n or y < 0 or y >= n:
                self.send_error(404)
                return
            png = _tile_png(gdb_id, z, x, y)
            if png is None:
                self.send_error(404)
                return
            self.send_response(200)
            self.send_header("Content-Type", "image/png")
            self.send_header("Content-Length", str(len(png)))
            self.send_header("Cache-Control", "public, max-age=604800")
            self.end_headers()
            self.wfile.write(png)
            return

        if ruta == "/api/gis/leyenda" or ruta.startswith("/api/gis/leyenda/"):
            gdb_id = ruta.rsplit("/", 1)[-1]
            ley = _leyenda_gdb(gdb_id)
            if not ley:
                send_json(self, {"ok": False, "error": "GDB no encontrada o sin datos."}, 404)
                return
            send_json(self, {"ok": True, "capas": ley})
            return

        if ruta == "/api/gis/puntos" or ruta.startswith("/api/gis/puntos/"):
            gdb_id = ruta.rsplit("/", 1)[-1]
            pts = _puntos_gdb(gdb_id)
            if not pts:
                send_json(self, {"ok": False, "error": "GDB no encontrada o sin datos."}, 404)
                return
            send_json(self, {"ok": True, "geojson": pts})
            return

        if ruta == "/api/gis/listar_gdb":
            try:
                send_json(self, {"ok": True, "gdb": _descubrir_gdb()})
            except Exception as e:
                send_json(self, {"ok": False, "error": str(e)}, 500)
            return

        if ruta == "/api/gis/listar_kmz":
            try:
                send_json(self, {"ok": True, "kmz": _descubrir_kmz()})
            except Exception as e:
                send_json(self, {"ok": False, "error": str(e)}, 500)
            return

        if ruta == "/api/gis/presentacion":
            try:
                resp = _presentacion_anla()
            except Exception as e:
                resp = {"ok": False, "error": "No se pudo preparar la presentación: " + str(e)}
            send_json(self, resp, 200 if resp.get("ok") else 404)
            return

        if ruta == "/api/gis/zonificacion":
            try:
                resp = _zonificacion_anla()
            except Exception as e:
                resp = {"ok": False, "error": "No se pudieron calcular los porcentajes de zonificación: " + str(e)}
            send_json(self, resp, 200 if resp.get("ok") else 404)
            return

        if ruta == "/api/data/estado":
            estado = _leer_estado()
            if not estado:
                send_json(self, {"ok": False, "error": "Sin datos guardados todavia."}, 404)
            else:
                send_json(self, {"ok": True, "data": estado})
            return
        super().do_GET()

    def do_POST(self):
        if not self._autorizado():
            self._pedir_auth()
            return
        ruta = self.path.split("?")[0].rstrip("/")

        if ruta == "/api/gis/loadpath":
            length = int(self.headers.get("Content-Length") or 0)
            if length <= 0 or length > 16384:
                send_json(self, {"ok": False, "error": "Cuerpo inválido."}, 400)
                return
            try:
                cuerpo = json.loads(self.rfile.read(length).decode("utf-8"))
            except (ValueError, UnicodeDecodeError):
                send_json(self, {"ok": False, "error": "JSON inválido."}, 400)
                return
            ruta_gdb = (cuerpo or {}).get("ruta") or ""
            t0 = time.time()
            try:
                resp = _leer_gdb_por_ruta(ruta_gdb)
            except Exception as e:
                send_json(self, {"ok": False, "error": "Error al leer la geodatabase: " + str(e)}, 500)
                return
            resp["segundos"] = round(time.time() - t0, 1)
            resp["ruta"] = ruta_gdb
            send_json(self, resp)
            return

        if ruta == "/api/gis/loadkmz":
            length = int(self.headers.get("Content-Length") or 0)
            if length <= 0 or length > 16384:
                send_json(self, {"ok": False, "error": "Cuerpo inválido."}, 400)
                return
            try:
                cuerpo = json.loads(self.rfile.read(length).decode("utf-8"))
            except (ValueError, UnicodeDecodeError):
                send_json(self, {"ok": False, "error": "JSON inválido."}, 400)
                return
            ruta_kmz = ((cuerpo or {}).get("ruta") or "").strip()
            t0 = time.time()
            try:
                resp = _leer_kmz_por_ruta(ruta_kmz)
            except Exception as e:
                send_json(self, {"ok": False, "error": "Error al leer el KMZ: " + str(e)}, 500)
                return
            resp["segundos"] = round(time.time() - t0, 1)
            resp["ruta"] = ruta_kmz
            send_json(self, resp)
            return

        if ruta == "/api/gis/identify":
            length = int(self.headers.get("Content-Length") or 0)
            if length <= 0 or length > 16384:
                send_json(self, {"ok": False, "error": "Cuerpo inválido."}, 400)
                return
            try:
                cuerpo = json.loads(self.rfile.read(length).decode("utf-8"))
            except (ValueError, UnicodeDecodeError):
                send_json(self, {"ok": False, "error": "JSON inválido."}, 400)
                return
            gdb_id = (cuerpo or {}).get("gdb_id") or ""
            try:
                lat = float((cuerpo or {}).get("lat"))
                lng = float((cuerpo or {}).get("lng"))
                z = int((cuerpo or {}).get("z") or 0)
            except (TypeError, ValueError):
                send_json(self, {"ok": False, "error": "Coordenadas inválidas."}, 400)
                return
            send_json(self, _identificar(gdb_id, lat, lng, z))
            return

        if ruta == "/api/gis/convert":
            length = int(self.headers.get("Content-Length") or 0)
            if length <= 0 or length > GIS_MAX_BYTES:
                send_json(self, {"ok": False, "error": "El archivo está vacío o supera el tamaño permitido (2 GB)."}, 400)
                return
            raw = self.rfile.read(length)
            qs = parse_qs(urlparse(self.path).query)
            nombre = (qs.get("nombre") or ["capa.zip"])[0]
            t0 = time.time()
            resp = convertir_capas_gis(nombre, raw)
            resp["segundos"] = round(time.time() - t0, 1)
            send_json(self, resp)
            return

        if ruta == "/api/gis/export_shp":
            self._exportar_shp()
            return

        if ruta == "/api/chat":
            length = int(self.headers.get("Content-Length") or 0)
            if length <= 0 or length > 102400:
                send_json(self, {"ok": False, "respuesta": "Cuerpo vacio o demasiado grande."}, 400)
                return
            raw = self.rfile.read(length)
            try:
                cuerpo = json.loads(raw.decode("utf-8"))
            except (ValueError, UnicodeDecodeError):
                send_json(self, {"ok": False, "respuesta": "JSON invalido."}, 400)
                return
            manejar_chat(self, cuerpo)
            return

        if ruta == "/api/data/estado":
            length = int(self.headers.get("Content-Length") or 0)
            if length <= 0 or length > (100 * 1024 * 1024):
                send_json(self, {"ok": False, "error": "Cuerpo invalido."}, 400)
                return
            try:
                cuerpo = json.loads(self.rfile.read(length).decode("utf-8"))
            except (ValueError, UnicodeDecodeError):
                send_json(self, {"ok": False, "error": "JSON invalido."}, 400)
                return
            if not isinstance(cuerpo, dict):
                send_json(self, {"ok": False, "error": "Se esperaba un objeto JSON."}, 400)
                return
            send_json(self, {"ok": True, "data": _fusionar_estado(cuerpo)})
            return

        if ruta != "/api/upload":
            send_json(self, {"ok": False, "error": "Ruta no encontrada"}, 404)
            return

        content_type = (self.headers.get("Content-Type") or "").lower()
        es_video = content_type in ALLOWED_VIDEO_MIME
        if content_type not in ALLOWED_MIME and not es_video:
            send_json(self, {"ok": False, "error": "Solo se permiten archivos de imagen o video (mp4, webm, ogv, mov)."}, 415)
            return

        length = int(self.headers.get("Content-Length") or 0)
        limite = MAX_VIDEO_SIZE if es_video else MAX_SIZE
        if length <= 0 or length > limite:
            max_mb = int(limite // (1024 * 1024))
            send_json(self, {"ok": False, "error": "El archivo supera el tamano permitido ({} MB).".format(max_mb)}, 400)
            return

        ext_map = {
            "image/png": ".png",
            "image/jpeg": ".jpg",
            "image/gif": ".gif",
            "image/webp": ".webp",
            "image/bmp": ".bmp",
            "video/mp4": ".mp4",
            "video/webm": ".webm",
            "video/ogg": ".ogv",
            "video/quicktime": ".mov",
            "application/ogg": ".ogg",
        }
        ext = ext_map.get(content_type, ".jpg" if not es_video else ".mp4")

        qs = parse_qs(urlparse(self.path).query)
        nombre_raw = (qs.get("nombre") or ["archivo"])[0]
        nombre = os.path.splitext(sanitize_name(nombre_raw))[0] + ext

        os.makedirs(UPLOAD_DIR, exist_ok=True)
        destino = os.path.join(UPLOAD_DIR, nombre)

        # Escritura por streaming: evita cargar archivos grandes (videos) en RAM.
        try:
            with open(destino, "wb") as f:
                restante = length
                while restante > 0:
                    chunk = self.rfile.read(min(1024 * 1024, restante))
                    if not chunk:
                        break
                    f.write(chunk)
                    restante -= len(chunk)
        except Exception:
            if os.path.exists(destino):
                try:
                    os.remove(destino)
                except OSError:
                    pass
            send_json(self, {"ok": False, "error": "Error al guardar el archivo."}, 500)
            return

        send_json(self, {"ok": True, "nombre": nombre, "ruta": "uploads/" + nombre})

    def log_message(self, fmt, *args):
        pass


# ==============================================
# ARRANQUE (consola + navegador)
# ==============================================

def _puerto_escuchando(puerto, timeout=0.2):
    """True si alguien está escuchando en 127.0.0.1:<puerto>."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(timeout)
        try:
            s.connect(("127.0.0.1", puerto))
            return True
        except OSError:
            return False


def _app_ya_corriendo(puerto):
    """True si en ese puerto responde esta misma app (evita abrir dos servidores)."""
    try:
        r = requests.get("http://127.0.0.1:{}/api/ping".format(puerto), timeout=1.0)
        return r.status_code == 200 and (r.json() or {}).get("app") == "mapa-garcero-c"
    except Exception:
        return False


def _elegir_puerto():
    """Recorre 8000..8010 en UNA pasada.

    Devuelve:
      ("app", puerto)  -> ya hay una instancia de la app corriendo en ese puerto
      ("libre", puerto)-> puerto disponible para arrancar
      (None, None)     -> no hay puertos libres
    """
    for puerto in range(8000, 8011):
        if _puerto_escuchando(puerto):
            if _app_ya_corriendo(puerto):
                return "app", puerto
            continue
        # Nadie responde: confirmar que se puede hacer bind en 127.0.0.1.
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                s.bind(("127.0.0.1", puerto))
            return "libre", puerto
        except OSError:
            continue
    return None, None


class ServidorSilencioso(http.server.ThreadingHTTPServer):
    """Servidor que no imprime tracebacks por desconexiones normales del navegador.

    Cuando el navegador cierra una pestana mientras se reproduce o descarga un
    video pesado, Windows reporta ConnectionResetError / ConnectionAbortedError.
    No es un fallo de la aplicacion: solo ruido en la consola. Aqui se silencia.
    """

    def handle_error(self, request, client_address):
        import sys as _sys
        exc = _sys.exc_info()[1]
        if isinstance(exc, (ConnectionResetError, ConnectionAbortedError, BrokenPipeError)):
            return
        super().handle_error(request, client_address)


def _log_inicio(mensaje):
    """Escribe una linea de diagnostico en inicio_log.txt (junto al ejecutable)."""
    try:
        ruta = os.path.join(BASE_DIR, "inicio_log.txt")
        try:
            if os.path.getsize(ruta) > 200 * 1024:
                os.remove(ruta)
        except OSError:
            pass
        with open(ruta, "a", encoding="utf-8") as fh:
            fh.write("[{}] {}\n".format(time.strftime("%Y-%m-%d %H:%M:%S"), mensaje))
    except Exception:
        pass


def _pausar(mensaje="\nPulsa ENTER para cerrar esta ventana..."):
    """Mantiene la consola abierta para poder leer el mensaje de error."""
    if os.environ.get("MAPA_NO_PAUSE") == "1":
        return
    try:
        if sys.stdin is not None and sys.stdin.isatty():
            input(mensaje)
    except Exception:
        pass


def _carpeta_escribible():
    """Comprueba que se pueda escribir junto al ejecutable (uploads, data...)."""
    prueba = os.path.join(BASE_DIR, ".prueba_escritura.tmp")
    try:
        with open(prueba, "w", encoding="utf-8") as fh:
            fh.write("ok")
        os.remove(prueba)
        return True
    except Exception:
        return False


def _verificar_paquete():
    """Devuelve la lista de archivos/carpetas clave que falten junto al ejecutable."""
    criticos = ["index.html", "sync_data.js", "estilos.css", "lib", "data", "config"]
    return [n for n in criticos if not os.path.exists(os.path.join(BASE_DIR, n))]


def _arrancar():
    """Arranque normal. Devuelve el codigo de salida."""
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    os.makedirs(GIS_TILES_DIR, exist_ok=True)
    os.makedirs(DATA_DIR, exist_ok=True)
    os.makedirs(CONFIG_DIR, exist_ok=True)

    # MAPA_NO_BROWSER=1 / MAPA_NO_PAUSE=1 se usan solo para pruebas automatizadas.
    abrir_navegador = os.environ.get("MAPA_NO_BROWSER", "") != "1"

    if os.name == "nt":
        try:
            os.system("title Mapa Garcero C - Servidor")
        except Exception:
            pass

    print("=" * 58, flush=True)
    print("  MAPA GARCERO C - Asistente IA incluido", flush=True)
    print("  Carpeta: {}".format(BASE_DIR), flush=True)
    print("=" * 58, flush=True)

    _log_inicio("Arranque. BASE_DIR={} frozen={} python={}".format(
        BASE_DIR, bool(getattr(sys, "frozen", False)), sys.version.split()[0]))

    # 1) La carpeta debe permitir escritura (si no, no se pueden guardar datos).
    if not _carpeta_escribible():
        print("[!] ESTA CARPETA NO PERMITE ESCRIBIR:", flush=True)
        print("    {}".format(BASE_DIR), flush=True)
        print("    Copia la carpeta MapaGarceroC a Documentos, Escritorio o una USB", flush=True)
        print("    (evita 'Archivos de programa') y vuelve a abrir el ejecutable.", flush=True)
        _log_inicio("ERROR: carpeta sin permiso de escritura")
        _pausar()
        return 1

    # 2) El paquete debe estar completo (no vale copiar solo el .exe).
    faltantes = _verificar_paquete()
    if faltantes:
        print("[!] FALTAN ARCHIVOS DEL PAQUETE: {}".format(", ".join(faltantes)), flush=True)
        print("    Copia la carpeta COMPLETA MapaGarceroC (con _internal, config,", flush=True)
        print("    data, uploads, lib, paginas .html...) y vuelve a intentarlo.", flush=True)
        _log_inicio("ERROR: faltan {}".format(", ".join(faltantes)))
        _pausar()
        return 1
    if not os.path.isdir(os.path.join(BASE_DIR, "uploads")):
        os.makedirs(os.path.join(BASE_DIR, "uploads"), exist_ok=True)

    # 3) Elegir host/puerto. En Docker se fijan con MAPA_HOST y MAPA_PORT.
    host = os.environ.get("MAPA_HOST", "127.0.0.1").strip() or "127.0.0.1"
    puerto_env = os.environ.get("MAPA_PORT", "").strip()
    if puerto_env:
        try:
            puerto = int(puerto_env)
        except ValueError:
            print("[!] MAPA_PORT no es un numero valido: {}".format(puerto_env), flush=True)
            _log_inicio("ERROR: MAPA_PORT invalido: {}".format(puerto_env))
            _pausar()
            return 1
        estado_puerto = "libre"
        print("Puerto fijado por MAPA_PORT: {}".format(puerto), flush=True)
        _log_inicio("Puerto fijado: {} host={}".format(puerto, host))
    else:
        print("Buscando puerto libre...", flush=True)
        estado_puerto, puerto = _elegir_puerto()
        _log_inicio("Puerto elegido: {} ({})".format(puerto, estado_puerto))

    if estado_puerto == "app":
        url = "http://localhost:{}/index.html".format(puerto)
        print("La aplicacion YA ESTABA ABIERTA en {}".format(url), flush=True)
        print("Se abre el navegador con la copia que ya esta activa.", flush=True)
        if abrir_navegador:
            webbrowser.open(url)
        print("Si el navegador no se abre, entra manualmente a esa direccion.", flush=True)
        _pausar("Pulsa ENTER para cerrar esta ventana (la aplicacion sigue activa en la otra).")
        return 0

    if estado_puerto != "libre":
        print("[!] No hay puertos libres entre 8000 y 8010.", flush=True)
        print("    Cierra otras aplicaciones e intentalo de nuevo.", flush=True)
        _log_inicio("ERROR: sin puertos libres")
        _pausar()
        return 1

    url = "http://localhost:{}/index.html".format(puerto)
    host_visible = "localhost" if host in ("0.0.0.0", "") else host
    try:
        httpd = ServidorSilencioso((host, puerto), Handler)
    except OSError as e:
        print("[!] No se pudo abrir {}:{}: {}".format(host, puerto, e), flush=True)
        print("    Cierra el programa que lo este usando o cambia MAPA_PORT.", flush=True)
        _log_inicio("ERROR bind {}:{}: {}".format(host, puerto, e))
        _pausar()
        return 1

    with httpd:
        print("Servidor listo en: http://{}:{}/index.html".format(host_visible, puerto), flush=True)
        print("Base de conocimiento EIA: {} trozos".format(len(_CONOCIMIENTO)), flush=True)
        print()
        print("Deja esta ventana abierta mientras usas la aplicacion.")
        print("Para detener el servidor: cierra esta ventana o pulsa Ctrl+C.")
        print()
        _log_inicio("Servidor escuchando en {}".format(url))

        if abrir_navegador:
            threading.Timer(1.2, lambda: webbrowser.open(url)).start()
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nServidor detenido.")
            _log_inicio("Servidor detenido por el usuario")
    return 0


def main():
    """Punto de entrada: si algo falla, deja el error visible y no cierra la consola."""
    try:
        return _arrancar()
    except Exception:
        import traceback
        tb = traceback.format_exc()
        print(tb, flush=True)
        print("[!] La aplicacion no pudo iniciar. El detalle quedo en:", flush=True)
        print("    {}".format(os.path.join(BASE_DIR, "error_inicio.txt")), flush=True)
        try:
            with open(os.path.join(BASE_DIR, "error_inicio.txt"), "w", encoding="utf-8") as fh:
                fh.write(tb)
        except Exception:
            pass
        _log_inicio("ERROR no controlado:\n" + tb)
        _pausar()
        return 1


if __name__ == "__main__":
    sys.exit(main())