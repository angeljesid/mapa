# -*- coding: utf-8 -*-
"""Copia el LEEME.txt (con la sección de nube) a dist desde build_portable.py."""
import re

src = open(r"C:\mapa\build_portable.py", encoding="utf-8").read()
m = re.search(r'LEEME = """\\(.*?)"""', src, re.S)
if not m:
    raise SystemExit("no encontre LEEME en build_portable.py")
leeme = m.group(1)
destino = r"C:\mapa\dist\MapaGarceroC\LEEME.txt"
open(destino, "w", encoding="utf-8").write(leeme)
print("LEEME copiado a dist:", len(leeme), "chars, incluye seccion nube:", "524 MB" in leeme)