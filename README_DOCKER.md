# Despliegue con Docker — Mapa Garcero C

Esta carpeta ya incluye `Dockerfile`, `docker-compose.yml`, `.dockerignore` y este instructivo.
La aplicación se sirve en el puerto **8000** dentro del contenedor y se publica en el puerto
**8000** del equipo anfitrión (configurable).

## 1. Requisitos

- Docker Desktop (Windows/macOS) o Docker Engine + Docker Compose (Linux).
- En Windows, Docker Desktop debe estar iniciado y usando contenedores Linux (WSL2).
- Para Geo-IA: salida a internet y la clave de Gemini en `config/ia_config.json`
  o en la variable `GEMINI_API_KEY`.
- El mapa base (ArcGIS) y Geo-IA necesitan internet. Las capas GIS/KMZ, los videos
  y las imágenes viajan dentro del proyecto.

## 2. Arranque rápido (recomendado)

Desde la carpeta del proyecto:

```powershell
cd C:\mapa
docker compose up -d --build
```

Abrir en el navegador:

```text
http://localhost:8000
```

En un servidor, reemplazar `localhost` por la IP o el dominio del servidor.

## 3. Comandos útiles

```powershell
# Ver estado y salud del contenedor
docker compose ps

# Ver logs en vivo
docker compose logs -f

# Detener sin borrar datos
docker compose down

# Volver a construir después de cambiar archivos
docker compose up -d --build

# Reiniciar
docker compose restart
```

Los datos **no se pierden** con `docker compose down`: `uploads`, `data` y `config`
están montados desde la carpeta del proyecto.

## 4. Cambiar el puerto

Por defecto se publica en `8000`. Si está ocupado:

**PowerShell:**

```powershell
$env:MAPA_PUERTO=8080
docker compose up -d
```

**Linux/macOS:**

```bash
MAPA_PUERTO=8080 docker compose up -d
```

Luego abrir `http://localhost:8080`.

También puedes copiar `.env.example` a `.env` y editar `MAPA_PUERTO`.

## 5. Persistencia y respaldo

El contenedor monta estas carpetas del proyecto:

| Carpeta | Contenido |
|---|---|
| `uploads/` | Videos, imágenes y archivos subidos |
| `data/` | `estado_app.json`, base de conocimiento y datos editables |
| `config/` | `ia_config.json`, caché GIS, GDB/KMZ y configuración |

Para respaldar, copia esas tres carpetas. Para mover la app a otro servidor,
copia el proyecto completo (incluidas esas carpetas) y ejecuta de nuevo
`docker compose up -d --build`.

## 6. Geo-IA (Gemini)

La app necesita internet para el asistente. La clave se puede dejar en:

1. `config/ia_config.json` (viene con el proyecto), o
2. la variable de entorno `GEMINI_API_KEY`.

Para usar `.env`:

```powershell
Copy-Item .env.example .env
notepad .env
# Escribir: GEMINI_API_KEY=tu_clave
docker compose up -d
```

No subas `.env` a repositorios públicos.

## 6.1 Enlace público temporal (Cloudflare Tunnel)

Si los otros dispositivos no están en la misma red, puedes publicar un enlace
temporal sin abrir puertos en el router:

```powershell
docker compose --profile tunnel up -d
docker compose logs -f cloudflared
```

En los logs aparece una URL parecida a:

```text
https://algo-aleatorio.trycloudflare.com
```

Ese es el enlace que puedes abrir desde cualquier celular, tablet u otro PC.
La URL cambia cada vez que reinicies el túnel.

Para detenerlo:

```powershell
docker compose --profile tunnel down
```

**Importante:** el túnel es público. Antes de usarlo, define un usuario y una
contraseña en `.env`:

```text
MAPA_AUTH_USER=garcero
MAPA_AUTH_PASSWORD=una-clave-larga-y-dificil
```

Luego reinicia:

```powershell
docker compose --profile tunnel up -d
```

El navegador pedirá esas credenciales al abrir el enlace.

## 7. Ejecución sin Docker Compose

```powershell
cd C:\mapa
docker build -t mapa-garcero-c:latest .
docker run -d --name mapa-garcero-c -p 8000:8000 `
  -e MAPA_HOST=0.0.0.0 -e MAPA_PORT=8000 -e MAPA_NO_BROWSER=1 -e MAPA_NO_PAUSE=1 `
  -v "${PWD}\uploads:/app/uploads" `
  -v "${PWD}\data:/app/data" `
  -v "${PWD}\config:/app/config" `
  mapa-garcero-c:latest
```

En Linux/macOS:

```bash
docker build -t mapa-garcero-c:latest .
docker run -d --name mapa-garcero-c -p 8000:8000 \
  -e MAPA_HOST=0.0.0.0 -e MAPA_PORT=8000 -e MAPA_NO_BROWSER=1 -e MAPA_NO_PAUSE=1 \
  -v "$PWD/uploads:/app/uploads" \
  -v "$PWD/data:/app/data" \
  -v "$PWD/config:/app/config" \
  mapa-garcero-c:latest
```

## 8. Seguridad

La aplicación **no tiene autenticación propia**. Para publicarla en internet:

- Déjala detrás de una VPN, red interna o un proxy inverso con autenticación.
- Publica solo el puerto necesario.
- No expongas `config/`, `data/` ni `uploads/` por otros medios.
- La imagen contiene `config/ia_config.json`; trátala como un artefacto sensible.

## 9. Solución de problemas

- **`port is already allocated`**: cambia `MAPA_PUERTO` o detén el proceso que usa el 8000
  (por ejemplo, el servidor local de Python).
- **El contenedor no arranca**: revisa `docker compose logs -f`; los errores también quedan
  en `inicio_log.txt` dentro del contenedor.
- **No cargan videos o mapas**: verifica que `uploads/` y `config/gdb`, `config/kmz`,
  `config/gis_cache` existan en la carpeta del proyecto y tengan permisos de lectura.
- **Geo-IA no responde**: revisa internet, la clave en `config/ia_config.json` o
  `GEMINI_API_KEY`, y los logs.
