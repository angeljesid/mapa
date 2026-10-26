# -*- coding: utf-8 -*-
"""Genera garcero_geo.js: la geometria REAL del AD Garcero C (poligono del AD,
area de influencia, rios/canos con nombres, vias, municipios, cuencas, coberturas
y puntos reales de infraestructura) extrayendo y simplificando las cachés GIS del
proyecto (config/gis_cache). La pagina index4.html usa este archivo para dibujar
los mini mapas de las tarjetas como una miniatura fiel del mapa principal.

Uso:
    python build_garcero_geo.py
"""
import json
import math
import random

from shapely.geometry import shape, box, LineString
from shapely.ops import unary_union

CACHE = r"C:\mapa\config\gis_cache"
SALIDA = r"C:\mapa\garcero_geo.js"

# ------------------- Cargas -------------------

def cargar(nombre):
    with open("{}\\{}".format(CACHE, nombre), "r", encoding="utf-8") as fh:
        return json.load(fh)

def feats_de(d, sufijo_capa):
    out = []
    for f in (d.get("geojson") or {}).get("features") or []:
        if str(f.get("properties", {}).get("_capa", "")).endswith(sufijo_capa):
            g = shape(f.get("geometry") or {})
            if g and not g.is_empty:
                out.append((f.get("properties", {}), g))
    return out

CART = cargar("c9faabce823dacabb440711ed924b49d.json")          # Cartografia_Basica
GDB = cargar("3a8791214e8f1311c80ac92671503c06.json")           # GDB_EIA_GARCERO_C
K_AD = cargar("kmz_38b4db03a33678de5acd046ae7fe86e7.json")      # AreaProyecto
K_AIS = cargar("kmz_57ef4b58567f3ba5b78263bf74630464.json")     # AreaInfluencia
K_COB = cargar("kmz_77bae5be8f8c3712c610b469dae6c629.json")     # CoberturaTierra

ad_pol = shape(K_AD["geojson"]["features"][0]["geometry"])
ais_pols = [shape(f["geometry"]) for f in K_AIS["geojson"]["features"]]

# Marco = AD Garcero C ampliado moderadamente (como la vista inicial del mapa
# principal: el AD centrado con sus ríos, caños y municipios alrededor).
w0, s0, e0, n0 = ad_pol.bounds
FRAME = box(w0 - 0.06, s0 - 0.07, e0 + 0.08, n0 + 0.05)
bbox = [round(FRAME.bounds[0], 5), round(FRAME.bounds[1], 5),
        round(FRAME.bounds[2], 5), round(FRAME.bounds[3], 5)]

rng = random.Random(42)

def simpl(g, tol):
    return g.simplify(tol, preserve_topology=True)

def round_ring(g, tol):
    g = simpl(g, tol)
    if g.geom_type == "Polygon":
        return [[[round(c[0], 5), round(c[1], 5)] for c in g.exterior.coords]]
    if g.geom_type == "MultiPolygon":
        return [[[round(c[0], 5), round(c[1], 5)] for c in p.exterior.coords] for p in g.geoms]
    return []

def round_line(g, tol):
    g = simpl(g, tol)
    if g.geom_type == "LineString":
        return [[[round(c[0], 5), round(c[1], 5)] for c in g.coords]]
    if g.geom_type == "MultiLineString":
        return [[[round(c[0], 5), round(c[1], 5)] for c in ln.coords]
                for ln in sorted(g.geoms, key=lambda l: -l.length)]
    return []

# ------------------- AD y AIS -------------------

ad_ring = round_ring(ad_pol, 0.0008)[0]
ad_cent = [round(ad_pol.representative_point().x, 5), round(ad_pol.representative_point().y, 5)]

# AIS: contorno ÚNICO (unión de los 14 polígonos) para no dibujar un enredo
ais_union = unary_union([simpl(g, 0.0012) for g in ais_pols])
if ais_union.geom_type == "Polygon":
    ais_rings = [[[round(c[0], 5), round(c[1], 5)] for c in ais_union.exterior.coords]]
elif ais_union.geom_type == "MultiPolygon":
    ais_rings = []
    for p in sorted(ais_union.geoms, key=lambda g: -g.area):
        ais_rings.append([[round(c[0], 5), round(c[1], 5)] for c in p.exterior.coords])

# ------------------- Agua (cuerpos Drenaj_R) -------------------

WHITELIST_AGUA = {"R\xedo Meta", "Ca\xf1o Tuj\xeda", "Ca\xf1o Guirripa", "Ca\xf1o El Espinero (Garcero)",
                  "Ca\xf1o Duya", "R\xedo Guanapalo", "Ca\xf1o Paravare", "Ca\xf1o Madrevieja"}

agua_pols = []
for props, g in feats_de(CART, "/ Drenaj_R"):
    gi = g.intersection(FRAME)
    if gi.is_empty:
        continue
    if gi.area < 0.000004:
        continue
    agua_pols.append((props.get("DNombre"), gi))

nombrados = {}
agua_rings = []
total_pts = 0
mw, ms, me, mn = FRAME.bounds
for nombre, gi in sorted(agua_pols, key=lambda t: -t[1].area):
    rings = round_ring(gi, 0.0009)
    pts = sum(len(r) for r in rings)
    if total_pts + pts > 2400:
        continue
    agua_rings.extend(rings)
    total_pts += pts
    if nombre in WHITELIST_AGUA and nombre not in nombrados:
        rp = simpl(gi, 0.0015).representative_point()
        # meter el rótulo dentro del marco (los cuerpos cortados por el borde)
        px = min(max(rp.x, mw + 0.012), me - 0.012)
        py = min(max(rp.y, ms + 0.012), mn - 0.012)
        nombrados[nombre] = [round(px, 5), round(py, 5)]

# ------------------- Ríos (líneas Drenaj_L) -------------------

rios = []
for props, g in feats_de(CART, "/ Drenaj_L"):
    gi = g.intersection(FRAME)
    if gi.is_empty or gi.length < 0.004:
        continue
    rios.append((props.get("DNombre"), gi))

rios_rings = []
for nombre, gi in sorted(rios, key=lambda t: -t[1].length):
    for pts in round_line(gi, 0.0006):
        if len(pts) >= 4 and len(rios_rings) < 26:
            rios_rings.append(pts)

# ------------------- Vías (Via) -------------------

vias_pols = []
for props, g in feats_de(CART, "/ Via"):
    gi = g.intersection(FRAME)
    if gi.is_empty or gi.length < 0.005:
        continue
    vias_pols.append(gi)

vias_rings = []
for gi in sorted(vias_pols, key=lambda g: -g.length):
    for pts in round_line(gi, 0.0006):
        if len(pts) >= 4 and len(vias_rings) < 15:
            vias_rings.append(pts)

# ------------------- Límites municipales -------------------

muni_candidates = []
for props, g in feats_de(CART, "/ MDANMu"):
    gi = g.intersection(FRAME)
    if gi.is_empty:
        continue
    muni_candidates.append((props.get("MDANMNombr"), gi))

union_muni = unary_union([g for _, g in muni_candidates])
bordes = []
fronteras = union_muni.boundary
if fronteras.geom_type == "MultiLineString":
    for ln in sorted(fronteras.geoms, key=lambda l: -l.length):
        if ln.length > 0.012:
            bordes.extend(round_line(ln, 0.0008))
elif fronteras.geom_type == "LineString" and fronteras.length > 0.012:
    bordes.extend(round_line(fronteras, 0.0008))

# Ciudades: represent point del municipio dentro del frame
ciudades = []
for nombre_buscado in ("Orocu\xe9", "San Luis De Palenque"):
    mejor = None
    for nombre, g in muni_candidates:
        if str(nombre).lower() == nombre_buscado.lower():
            rp = g.representative_point()
            mejor = [round(rp.x, 5), round(rp.y, 5)]
            break
    if mejor:
        # si quedó pegado al borde del frame, alejarlo un poco hacia adentro
        mw, ms, me, mn = FRAME.bounds
        mejor[0] = min(max(mejor[0], mw + 0.02), me - 0.02)
        mejor[1] = min(max(mejor[1], ms + 0.02), mn - 0.02)
        ciudades.append({"n": nombre_buscado, "c": mejor})

# ------------------- Cuencas (5 subzonas reales) -------------------

cuen = []
for props, g in feats_de(GDB, "/ CuencaHidrografica"):
    gi = g.intersection(FRAME)
    if gi.is_empty:
        continue
    cuen.append((props.get("N_NV_SUB"), gi))

mejores_cuencas = {}
for nombre, g in sorted(cuen, key=lambda t: -t[1].area):
    if nombre in mejores_cuencas:
        continue
    mejores_cuencas[nombre] = g
    if len(mejores_cuencas) >= 5:
        break

cuencas = []
for nombre, g in mejores_cuencas.items():
    gi = simpl(g.intersection(FRAME), 0.001)
    rings = round_ring(gi, 0.001)
    if rings:
        rp = simpl(gi, 0.0015).representative_point()
        cuencas.append({"n": str(nombre or ""), "c": rings,
                        "cent": [round(rp.x, 5), round(rp.y, 5)]})

# ------------------- Unidades geológicas (AD partido /4) -------------------

def partidas_ad(valores):
    """Divide el AD en franjas verticales con ancho proporcional a sqrt(valor)."""
    ad_x0, ad_y0, ad_x1, ad_y1 = ad_pol.bounds
    total = sum(math.sqrt(max(v, 1e-6)) for v in valores) or 1
    salida, x = [], ad_x0
    for i, v in enumerate(valores):
        frac = math.sqrt(max(v, 1e-6)) / total
        x1 = ad_x1 if i == len(valores) - 1 else x + (ad_x1 - ad_x0) * frac
        franja = ad_pol.intersection(box(x, ad_y0, x1, ad_y1))
        rings = round_ring(franja, 0.0008)
        salida.append(rings)
        x = x1
    return salida

# ------------------- Coberturas reales (4 clases de la tarjeta) -------------------

# (KMZ no marca _capa; se lee directo)
cob_parts = {"herbazal": [], "pastos": [], "arroz": [], "bosque": []}
for f in K_COB["geojson"]["features"]:
    props = f.get("properties", {})
    n3 = props.get("N3_COBERT")
    n4 = props.get("N4_COBERT")
    g = shape(f.get("geometry") or {})
    if g.is_empty or not g.intersects(ad_pol):
        continue
    gi = g.intersection(ad_pol)
    if gi.is_empty:
        continue
    if n3 == "Herbazal":
        cob_parts["herbazal"].append(gi)
    elif n3 == "Pastos limpios":
        cob_parts["pastos"].append(gi)
    elif n3 == "Cereales" and n4 == "Arroz":
        cob_parts["arroz"].append(gi)
    elif n3 == "Bosque de galer\xeda y/o ripario":
        cob_parts["bosque"].append(gi)

cob = []
for clave in ("herbazal", "pastos", "arroz", "bosque"):
    if not cob_parts[clave]:
        continue
    uni = unary_union(cob_parts[clave])
    uni = simpl(uni, 0.0012)
    rings = round_ring(uni, 0.0012)
    if rings:
        cob.append({"k": clave, "c": rings})

# ------------------- Transectos de flora (3 líneas dentro del AD) -------------------

transectos = []
ad_x0, ad_y0, ad_x1, ad_y1 = ad_pol.bounds
for frac in (0.30, 0.55, 0.80):
    y = ad_y0 + (ad_y1 - ad_y0) * frac
    linea = LineString([(ad_x0 - 0.002, y), (ad_x1 + 0.002, y)]).intersection(ad_pol)
    if linea.is_empty:
        continue
    mejor = max(linea.geoms, key=lambda l: l.length) if linea.geom_type == "MultiLineString" else linea
    pts = round_line(mejor, 0.0006)
    if pts:
        transectos.append(pts[0])

# ------------------- Puntos reales / anclas -------------------

def puntos_en(geom, lista, n, semilla, dentro_de=True):
    rng2 = random.Random(semilla)
    pts = [g for _, g in lista]
    dentro = [p for p in pts if (p.within(geom) if dentro_de else p.intersects(geom))]
    if not dentro:
        dentro = pts
    salida = []
    if len(dentro) <= n:
        salida = dentro
    else:
        paso = len(dentro) / n
        for i in range(n):
            salida.append(dentro[int(i * paso)])
    # jitter fino
    return [[round(p.x + (rng2.random() - 0.5) * 0.0015, 5),
             round(p.y + (rng2.random() - 0.5) * 0.0015, 5)] for p in salida]

# 13 plataformas sobre las 3 vías más largas dentro del AD
vias_en_ad = []
for props, g in feats_de(CART, "/ Via"):
    gi = g.intersection(ad_pol)
    if not gi.is_empty and gi.length > 0.008:
        vias_en_ad.append(gi)
vias_en_ad.sort(key=lambda g: -g.length)
p_civil = []
reparto = (5, 4, 4)
for vi, via in enumerate(vias_en_ad[:3]):
    if via.geom_type == "MultiLineString":
        ln = max(via.geoms, key=lambda l: l.length)
    else:
        ln = via
    coords = list(ln.coords)
    k = reparto[vi] if vi < len(reparto) else 3
    for i in range(k):
        t = (i + 0.5) / k
        pos = ln.interpolate(t, normalized=True)
        p_civil.append([round(pos.x + (rng.random() - 0.5) * 0.0012, 5),
                        round(pos.y + (rng.random() - 0.5) * 0.0012, 5)])

# 3 pozos de captación reales dentro del AD
p_sub = puntos_en(ad_pol, feats_de(GDB, "/ PuntoMuestreoAguaSubter"), 3, 5)
if len(p_sub) < 3:
    p_sub = puntos_en(ad_pol, feats_de(GDB, "/ PuntoHidrogeologico"), 3, 5)
p_sub = p_sub[:3]

# 3 estaciones (anclas interiores deterministas) y 2 sitios culturales
ad_x0, ad_y0, ad_x1, ad_y1 = ad_pol.bounds
def interior(fx, fy, semilla, rr=0.0015):
    rng2 = random.Random(semilla)
    return [round(ad_x0 + (ad_x1 - ad_x0) * fx + (rng2.random() - 0.5) * rr, 5),
            round(ad_y0 + (ad_y1 - ad_y0) * fy + (rng2.random() - 0.5) * rr, 5)]

p_est = [interior(0.28, 0.62, 7), interior(0.55, 0.38, 8), interior(0.80, 0.66, 9)]
p_sitio = [interior(0.30, 0.45, 11), interior(0.72, 0.60, 12)]

# 150 construcciones reales (Constr_P) dentro del marco
casas_tmp = [g for _, g in feats_de(CART, "/ Constr_P") if g.within(FRAME)]
casas_tmp.sort(key=lambda g: (g.x, g.y))
paso = max(1, len(casas_tmp) // 150) if len(casas_tmp) > 150 else 1
casas = [[round(g.x, 5), round(g.y, 5)] for g in casas_tmp[::paso]][:150]

# ------------------- Salida -------------------

salida = {
    "bbox": bbox,
    "ad": ad_ring,
    "adCent": ad_cent,
    "ais": ais_rings,
    "agua": agua_rings,
    "rios": rios_rings,
    "aguasNombradas": [{"n": n, "c": c} for n, c in nombrados.items()],
    "vias": vias_rings,
    "muni": bordes,
    "ciudades": ciudades,
    "cuencas": cuencas,
    "unidades": partidas_ad([3629.70, 12585.66, 13800.43, 97496.49]),
    "cob": cob,
    "transectos": [t for t in transectos if t],
    "pCivil": p_civil,
    "pSub": p_sub,
    "pEst": p_est,
    "pSitio": p_sitio,
    "casas": casas,
}

texto = "// Geometría REAL del AD Garcero C extraída de las cachés GIS del proyecto\n" \
        "// (generado por build_garcero_geo.py). Coordenadas WGS84, simplificadas.\n" \
        "window.GARCERO_C_GEO = " + json.dumps(salida, ensure_ascii=False, separators=(",", ":")) + ";\n"

with open(SALIDA, "w", encoding="utf-8") as fh:
    fh.write(texto)

print("OK ->", SALIDA, "{:.0f} KB".format(len(texto) / 1024))
print("ad pts:", len(ad_ring), "| ais:", len(ais_rings), "| agua rings:", len(agua_rings),
      "| rios:", len(rios_rings), "| vias:", len(vias_rings), "| muni:", len(bordes))
print("ciudades:", ciudades)
print("aguas nombradas:", list(nombrados.items()))
print("cuencas:", [c["n"] for c in cuencas])
print("cob:", [(c["k"], len(c["c"])) for c in cob])
print("transectos:", len([t for t in transectos if t]))
print("pCivil:", len(p_civil), "| pSub:", len(p_sub), "| casas:", len(casas))