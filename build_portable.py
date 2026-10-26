# -*- coding: utf-8 -*-
"""Genera la carpeta PORTABLE MapaGarceroC (EXE + datos) lista para copiar a
cualquier PC Windows sin instalar Python ni dependencias.

Uso:
    python build_portable.py

Resultado:
    dist/MapaGarceroC/
        MapaGarceroC.exe        <- doble clic y listo
        _internal/              <- runtime de Python incluido
        index.html, lib/, data/, config/, uploads/, assets/...

El script:
  1) Pre-siembra las cache de los KMZ (clave por CONTENIDO, sirven en cualquier PC).
  2) Compila el EXE con PyInstaller (modo carpeta, arranque rapido).
  3) Copia los datos del proyecto (paginas, estado, imagenes, cache GIS, KMZ).
  4) Deja archivos de configuracion portables y un LEEME.txt.
"""
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import time

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DIST_ROOT = os.path.join(BASE_DIR, "dist")
DIST_APP = os.path.join(DIST_ROOT, "MapaGarceroC")
BUILD_TMP = os.path.join(BASE_DIR, "build_tmp")
SERVER_PY = os.path.join(BASE_DIR, "server.py")
CONFIG_DIR = os.path.join(BASE_DIR, "config")
CACHE_DIR = os.path.join(CONFIG_DIR, "gis_cache")
GIS_TILES = os.path.join(CONFIG_DIR, "gis_tiles")

# Carpetas donde se buscan los .kmz originales para pre-sembrar las cache.
# config/kmz es la copia local portable; D:\INSUMOS KML es la fuente original del equipo.
KMZ_SOURCE_DIRS = [
    os.path.join(CONFIG_DIR, "kmz"),
    r"D:\INSUMOS KML",
]

# Archivos/carpetas del proyecto que se copian junto al EXE.
# iniciar.bat + server.py + requirements.txt se incluyen para que el paquete
# también pueda arrancar con un Python del sistema si el usuario lo prefiere;
# si NO hay Python instalado, iniciar.bat lanza directo MapaGarceroC.exe.
COPIAR = [
    "index.html", "index2.html", "index3.html", "index4.html",
    "index5.html", "index6.html", "index7.html",
    "estilos.css", "sync_data.js", "garcero_geo.js", "fondo_scenic.webp",
    "VERIFICACION_FUENTES.md",
    "iniciar.bat", "server.py", "requirements.txt",
    "assets", "lib", "data", "uploads",
]

LEEME = """\
==============================================================
 MAPA GARCERO C - Aplicacion portable (EXE incluido)
==============================================================

COMO USARLA EN CUALQUIER COMPUTADOR WINDOWS
-------------------------------------------
1. Copia TODA esta carpeta (MapaGarceroC) al PC destino
   (USB, escritorio, Documentos...). No hace falta instalar
   Python ni ningun programa.

2. Haz doble clic en INICIAR.bat  (recomendado)
   - Si el PC NO tiene Python: abrira automaticamente
     MapaGarceroC.exe (version portable incluida).
   - Si el PC SI tiene Python: arrancara con ese Python
     (instala las dependencias la primera vez, con internet).
   Tambien puedes abrir directamente MapaGarceroC.exe.

3. Se abrira una ventana negra (servidor) y luego el navegador
   con la aplicacion. Deja la ventana negra abierta mientras
   usas el mapa; para cerrar la aplicacion, cierra esa ventana.

NOTAS IMPORTANTES
-----------------
* PARA PASAR LA APP A OTRO PC usa SIEMPRE este paquete (la carpeta
  MapaGarceroC que sale de este ZIP), que incluye MapaGarceroC.exe.
  NO lleves la carpeta del proyecto fuente (C:\mapa sin el .exe):
  esa version no es portable y su iniciador pide instalar Python.
* No muevas solo el .exe: tiene que ir acompanado de las
  carpetas que estan a su lado (config, data, uploads, lib...).
* Copia la carpeta a Documentos, Escritorio o USB. Evita
  "Archivos de programa" (Windows bloquea la escritura ahi).
* Para guardarlo en la NUBE (OneDrive/Drive), sube SIEMPRE el
  ZIP completo (un solo archivo), nunca la carpeta descomprimida
  (tiene 843 archivos y la nube puede dejar algunos a medio
  subir). En OneDrive usa la APP de escritorio (no el navegador)
  y espera el checqueo verde de sincronizacion; el ZIP pesa
  ~454 MB por los videos de drone y las imagenes incluidas.
* Quien lo reciba: con OneDrive en "archivos bajo demanda",
  clic derecho sobre el ZIP -> "Mantener siempre en este
  dispositivo" antes de descomprimir (asi baja completo).
* Si Windows muestra "Windows protegio tu PC" al abrir el .exe
  por primera vez, pulsa "Mas informacion" -> "Ejecutar de
  todas formas" (el archivo no esta firmado digitalmente).
  INICIAR.bat intenta quitar esa marca automaticamente.
* Los datos editables (estrategias, permisos, imagenes, videos,
  anotaciones) viajan en data/estado_app.json y en uploads/:
  si los cambias en un PC y quieres llevarlos a otro, copia
  de nuevo toda la carpeta.
* Las capas GIS (GDB EIA Garcero C y Cartografia Basica) y los
  KMZ EIA (AreaProyecto, AreaInfluencia, CoberturaTierra,
  ZonificacionAmbiental, ZonificacionManejo) se cargan al
  abrirlas en el mapa. Viajan como cache dentro de config/;
  no necesitas las geodatabases originales de 850 MB.
* El asistente IA necesita internet y la clave configurada en
  config/ia_config.json.

SI LA CONSOLA SE ABRE Y SE CIERRA SOLA
--------------------------------------
* Vuelve a abrir INICIAR.bat (o MapaGarceroC.exe) y mira los
  archivos que quedan junto al ejecutable: "inicio_log.txt" y
  "error_inicio.txt" (abrelos con el Bloc de notas). Ahi dice
  exactamente que paso.
* Causa mas comun: se copio SOLO el archivo .exe. Hay que copiar
  TODA la carpeta MapaGarceroC, incluida la carpeta "_internal".
* Otra causa: la carpeta esta en un lugar sin permiso de escritura
  (p. ej. "Archivos de programa"). Copiala a Documentos/Escritorio.
* Si Windows bloquea el archivo (antivirus), desbloquealo:
  clic derecho en el .exe > Propiedades > marcar "Desbloquear".
* Si desempaquetaste el ZIP y la extraccion fallo a mitad,
  borra la carpeta y extrae de nuevo (usa 7-Zip si hace falta).

ESTRUCTURA
----------
INICIAR.bat          Arranque recomendado (Python o EXE portable)
MapaGarceroC.exe     Programa (servidor + app) - no necesita Python
server.py            Codigo fuente (solo si hay Python instalado)
config/              Capas GIS en cache, KMZ EIA, clave IA
data/                Estado portable (cambios guardados) + base EIA
uploads/             Imagenes y videos subidos
lib/                 Librerias del mapa (Leaflet) para uso sin internet
index*.html          Paginas de la aplicacion
"""


def log(msg):
    print("[build] " + msg, flush=True)


def md5_file(ruta):
    h = hashlib.md5()
    try:
        with open(ruta, "rb") as fh:
            for trozo in iter(lambda: fh.read(1024 * 1024), b""):
                h.update(trozo)
        return h.hexdigest()
    except OSError:
        return None


def sembrar_cache_kmz():
    """Copia las cache KMZ existentes (clave por ruta) a claves por CONTENIDO, para que
    funcionen en cualquier PC. Devuelve cuantas sembró."""
    if not os.path.isdir(CACHE_DIR):
        return 0
    sembradas = 0
    # Mapa capa -> ruta del kmz original
    por_nombre = {}
    for carpeta in KMZ_SOURCE_DIRS:
        if os.path.isdir(carpeta):
            for f in os.listdir(carpeta):
                if f.lower().endswith(".kmz"):
                    por_nombre[os.path.splitext(f)[0].lower()] = os.path.join(carpeta, f)

    for nombre_json in os.listdir(CACHE_DIR):
        if not (nombre_json.startswith("kmz_") and nombre_json.endswith(".json")):
            continue
        ruta_json = os.path.join(CACHE_DIR, nombre_json)
        try:
            with open(ruta_json, "r", encoding="utf-8") as fh:
                cc = json.load(fh)
        except Exception:
            continue
        capa = str(cc.get("capa") or "").strip().lower()
        origen = por_nombre.get(capa)
        if not origen:
            continue
        clave = md5_file(origen)
        if not clave:
            continue
        destino = os.path.join(CACHE_DIR, "kmz_" + clave + ".json")
        if os.path.isfile(destino):
            continue
        try:
            cc["mtime"] = os.path.getmtime(origen)
            with open(destino, "w", encoding="utf-8") as fh:
                json.dump(cc, fh, ensure_ascii=False)
            sembradas += 1
            log("cache KMZ sembrada por contenido: {} -> kmz_{}.json".format(capa, clave[:8]))
        except Exception as e:
            log("aviso: no se pudo sembrar la cache de {}: {}".format(capa, e))
    return sembradas


def copiar_kmz():
    """Copia los .kmz originales a config/kmz de la distribucion (44 MB)."""
    destino = os.path.join(DIST_APP, "config", "kmz")
    os.makedirs(destino, exist_ok=True)
    n = 0
    for carpeta in KMZ_SOURCE_DIRS:
        if os.path.isdir(carpeta):
            for f in os.listdir(carpeta):
                if f.lower().endswith(".kmz"):
                    shutil.copy2(os.path.join(carpeta, f), os.path.join(destino, f))
                    n += 1
    return n


def compilar_exe():
    args = [sys.executable, "-m", "PyInstaller",
            "--noconfirm", "--onedir", "--console",
            "--name", "MapaGarceroC",
            "--distpath", DIST_ROOT,
            "--workpath", BUILD_TMP,
            "--specpath", BUILD_TMP,
            SERVER_PY]
    if not os.path.isdir(os.path.join(BUILD_TMP, "MapaGarceroC")):
        args.insert(3, "--clean")
    log("compilando EXE (PyInstaller)... puede tardar varios minutos")
    r = subprocess.run(args, cwd=BASE_DIR)
    if r.returncode != 0:
        raise SystemExit("Fallo PyInstaller (codigo {}).".format(r.returncode))


def copiar_datos():
    for nombre in COPIAR:
        origen = os.path.join(BASE_DIR, nombre)
        destino = os.path.join(DIST_APP, nombre)
        if not os.path.exists(origen):
            log("aviso: no existe {} (se omite)".format(nombre))
            continue
        if os.path.isdir(origen):
            if os.path.isdir(destino):
                shutil.rmtree(destino)
            shutil.copytree(origen, destino)
        else:
            shutil.copy2(origen, destino)
    # config completo (cache GIS, tiles, clave IA, KMZ)
    cfg_origen = CONFIG_DIR
    cfg_destino = os.path.join(DIST_APP, "config")
    # gdb: solo un LEEME (las GDB originales pesan cientos de MB y no viajan)
    gdb_destino = os.path.join(cfg_destino, "gdb")
    for nombre in ("gis_cache", "gis_tiles", "ia_config.json"):
        o = os.path.join(cfg_origen, nombre)
        d = os.path.join(cfg_destino, nombre)
        if os.path.isdir(o):
            if os.path.isdir(d):
                shutil.rmtree(d)
            shutil.copytree(o, d)
        elif os.path.isfile(o):
            shutil.copy2(o, d)
    os.makedirs(gdb_destino, exist_ok=True)
    with open(os.path.join(gdb_destino, "LEEME.txt"), "w", encoding="utf-8") as fh:
        fh.write("Copia aqui carpetas .gdb (geodatabases de ArcGIS) si quieres abrirlas\n"
                 "en este equipo. Tambien puedes usar el campo de ruta del panel\n"
                 "'GDB locales' del mapa o agregar rutas en config/gis_paths.txt.\n")
    # Archivos de rutas PORTABLES (solo comentarios: usan config/gdb y config/kmz)
    with open(os.path.join(cfg_destino, "gis_paths.txt"), "w", encoding="utf-8") as fh:
        fh.write("# Rutas adicionales donde buscar carpetas *.gdb (una por linea).\n"
                 "# Las rutas relativas se resuelven junto al ejecutable.\n"
                 "# La carpeta config/gdb se revisa siempre automaticamente.\n")
    with open(os.path.join(cfg_destino, "gis_kmz_paths.txt"), "w", encoding="utf-8") as fh:
        fh.write("# Rutas adicionales donde buscar capas *.kmz (una por linea).\n"
                 "# Las rutas relativas se resuelven junto al ejecutable.\n"
                 "# La carpeta config/kmz (KMZ EIA incluidos) se revisa automaticamente.\n")


def resumen():
    total = 0
    for p, _dirs, files in os.walk(DIST_APP):
        for f in files:
            try:
                total += os.path.getsize(os.path.join(p, f))
            except OSError:
                pass
    log("LISTO: {}".format(DIST_APP))
    log("Tamano total: {:.0f} MB".format(total / (1024 * 1024)))
    log("Ejecutable: {}".format(os.path.join(DIST_APP, "MapaGarceroC.exe")))


def main():
    t0 = time.time()
    log("1/5 sembrando cache KMZ por contenido...")
    log("     {} sembradas".format(sembrar_cache_kmz()))
    log("2/5 compilando el ejecutable...")
    compilar_exe()
    log("3/5 copiando paginas, datos, uploads y cache GIS...")
    copiar_datos()
    log("4/5 copiando KMZ EIA...")
    log("     {} archivos .kmz".format(copiar_kmz()))
    with open(os.path.join(DIST_APP, "LEEME.txt"), "w", encoding="utf-8") as fh:
        fh.write(LEEME)
    log("5/5 resumen")
    resumen()
    log("Completado en {:.0f} s".format(time.time() - t0))


if __name__ == "__main__":
    main()
