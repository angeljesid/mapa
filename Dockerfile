FROM python:3.12-slim

# Configuración pensada para contenedor: sin consola interactiva, sin navegador
# y escuchando en todas las interfaces para que Docker pueda publicar el puerto.
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    MAPA_HOST=0.0.0.0 \
    MAPA_PORT=8000 \
    MAPA_NO_BROWSER=1 \
    MAPA_NO_PAUSE=1

WORKDIR /app

# Librerías base que necesitan algunas ruedas de Fiona/Matplotlib.
RUN apt-get update && apt-get install -y --no-install-recommends \
        libexpat1 \
        libfreetype6 \
        libpng16-16 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./
RUN pip install --upgrade pip \
    && pip install -r requirements.txt

COPY . .

# Carpetas que la aplicación escribe en tiempo de ejecución.
RUN mkdir -p /app/uploads /app/data /app/config/gis_cache /app/config/gis_tiles

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/api/ping', timeout=3)" || exit 1

CMD ["python", "server.py"]
