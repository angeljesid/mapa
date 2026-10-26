# -*- coding: utf-8 -*-
"""Extrae el texto de los PDFs del EIA (CAP 1 y CAP 2) y genera una base de
conocimiento reutilizable por el asistente IA: data/conocimiento_eia.json

Uso:
    python extraer_eia.py
"""
import os
import json
import re

try:
    import fitz  # PyMuPDF
except ImportError:
    quit("PyMuPDF no está instalado. Ejecuta: pip install --user pymupdf")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT = os.path.join(BASE_DIR, "data", "conocimiento_eia.json")

FUENTES = [
    (r"D:\ASI.SAS\CAP 1 GENERALIDADES.pdf", "CAP 1 - Generalidades"),
    (r"D:\ASI.SAS\CAP 2 DESCRIPCION DEL PROYECTO.pdf", "CAP 2 - Descripción del Proyecto"),
]

MIN_CHARS = 60       # párrafos más cortos se descartan
MAX_CHARS = 2200     # tamaño máximo por trozo


def limpiar(texto):
    texto = texto.replace("\xa0", " ").replace("\u2011", "-")
    texto = re.sub(r"[ \t]+", " ", texto)
    texto = re.sub(r" ?\n ?", "\n", texto)
    texto = re.sub(r"\n{3,}", "\n\n", texto)
    return texto.strip()


def dividir_parrafos(texto, fuente, pagina):
    trozos = []
    parrafos = [p.strip() for p in re.split(r"\n\s*\n", texto) if p.strip()]
    buffer = ""
    for parrafo in parrafos:
        if len(parrafo) < MIN_CHARS:
            continue
        if len(buffer) + len(parrafo) > MAX_CHARS and buffer:
            trozos.append((buffer, fuente, pagina))
            buffer = parrafo
        else:
            buffer = (buffer + "\n\n" + parrafo).strip() if buffer else parrafo
    if buffer:
        trozos.append((buffer, fuente, pagina))
    return trozos


def extraer_pdf(ruta, nombre):
    doc = fitz.open(ruta)
    trozos = []
    for num, page in enumerate(doc, start=1):
        texto = limpiar(page.get_text("text"))
        if not texto:
            continue
        trozos.extend(dividir_parrafos(texto, nombre, num))
    doc.close()
    return trozos


def main():
    todos = []
    for ruta, nombre in FUENTES:
        if not os.path.exists(ruta):
            print(f"[AVISO] No existe: {ruta}")
            continue
        trozos = extraer_pdf(ruta, nombre)
        print(f"{nombre}: {len(trozos)} trozos extraídos")
        for texto, fuente, pagina in trozos:
            todos.append({
                "fuente": fuente,
                "pagina": pagina,
                "titulo": texto[:90].replace("\n", " "),
                "texto": texto,
            })

    os.makedirs(os.path.dirname(OUTPUT), exist_ok=True)
    with open(OUTPUT, "w", encoding="utf-8") as f:
        json.dump(todos, f, ensure_ascii=False, indent=1)
    print(f"Base de conocimiento generada: {OUTPUT} ({len(todos)} trozos)")


if __name__ == "__main__":
    main()