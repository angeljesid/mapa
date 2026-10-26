# -*- coding: utf-8 -*-
"""Portada del instructivo: degradado azul oscuro -> verde oscuro con acento."""
from PIL import Image, ImageDraw, ImageFont

ANCHO, ALTO = 1600, 900
img = Image.new('RGB', (ANCHO, ALTO))
d = ImageDraw.Draw(img)

# degradado vertical
for y in range(ALTO):
    t = y / ALTO
    r = int(11 + (0 - 11) * t)
    g = int(18 + (80 - 18) * t)
    b = int(32 + (50 - 32) * t)
    d.line([(0, y), (ANCHO, y)], fill=(r, g, b))

# franja de acento
d.rectangle([0, ALTO - 14, ANCHO, ALTO], fill=(0, 176, 80))
d.rectangle([0, ALTO - 14, ANCHO, ALTO - 7], fill=(0, 138, 62))

def fuente(tam, bold=True):
    ruta = r"C:\Windows\Fonts\segoeuib.ttf" if bold else r"C:\Windows\Fonts\segoeui.ttf"
    try:
        return ImageFont.truetype(ruta, tam)
    except Exception:
        return ImageFont.load_default()

# linea verde decorativa superior
d.rectangle([0, 0, ANCHO, 10], fill=(0, 176, 80))

f_tit = fuente(96)
f_sub = fuente(40)
f_pie = fuente(24)

titulo = "INSTRUCTIVO"
d.text((ANCHO // 2, 300), titulo, font=f_tit, fill=(255, 255, 255), anchor="mm")

sub = "Mapa Garcero C"
d.text((ANCHO // 2, 430), sub, font=fuente(58), fill=(110, 226, 158), anchor="mm")

d.text((ANCHO // 2, 530), "SIG del Estudio de Impacto Ambiental", font=f_sub, fill=(203, 213, 225), anchor="mm")
d.text((ANCHO // 2, 590), "Area de Desarrollo Garcero C · Perenco Colombia Limited", font=f_sub, fill=(148, 163, 184), anchor="mm")
d.text((ANCHO // 2, 660), "Guía rápida: iniciar, cargar capas y funcionalidades", font=f_pie, fill=(148, 163, 184), anchor="mm")

d.rectangle([ANCHO // 2 - 180, 720, ANCHO // 2 + 180, 726], fill=(0, 176, 80))

ruta = r"C:\Users\Angel\AppData\Local\Temp\opencode\cap_instructivo\0_portada.png"
img.save(ruta)
print("portada -> " + ruta)