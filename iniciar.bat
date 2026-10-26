@echo off
setlocal EnableExtensions
title Mapa Garcero C - Iniciador
cd /d "%~dp0"

echo.
echo   ============================================
echo     MAPA GARCERO C - Asistente IA incluido
echo   ============================================
echo.

rem --- Quitar la marca "descargado de internet" (SmartScreen) de los .exe ---
powershell -NoProfile -Command "Get-ChildItem -Path '%~dp0' -Recurse -Filter *.exe -ErrorAction SilentlyContinue | Unblock-File -ErrorAction SilentlyContinue" >nul 2>nul

set "PYEXE="

rem ============================================================
rem  1) VERSION PORTABLE (EXE) dentro de esta misma carpeta.
rem     Es la PRIMERA opcion: no necesita Python, no necesita
rem     internet y no instala nada en el computador destino.
rem ============================================================
if exist "%~dp0MapaGarceroC.exe" goto lanzar_portable
if exist "%~dp0dist\MapaGarceroC\MapaGarceroC.exe" (
    start "" "%~dp0dist\MapaGarceroC\MapaGarceroC.exe"
    exit /b 0
)

rem ============================================================
rem  2) PYTHON PORTABLE LOCAL (opcional, dentro del proyecto)
rem     Si existe la carpeta python_portable\python.exe se usa
rem     ese Python sin instalar nada en el equipo.
rem ============================================================
if exist "%~dp0python_portable\python.exe" set "PYEXE=%~dp0python_portable\python.exe"
if defined PYEXE goto verificar_deps

rem ============================================================
rem  3) PYTHON DEL SISTEMA (se prefiere 3.13; se descartan 3.14+)
rem ============================================================
for /f "delims=" %%P in ('py -3.13 -c "import sys; print(sys.executable)" 2^>nul') do set "PYEXE=%%P"
if defined PYEXE goto verificar_deps

for /f "delims=" %%P in ('py -3 -c "import sys; v=sys.version_info; print(sys.executable if v[:2] <= (3,13) else '')" 2^>nul') do set "PYEXE=%%P"
if defined PYEXE goto verificar_deps

for /f "delims=" %%P in ('python -c "import sys; v=sys.version_info; print(sys.executable if v[:2] <= (3,13) else '')" 2^>nul') do set "PYEXE=%%P"
if defined PYEXE goto verificar_deps

rem ============================================================
rem  4) SIN PYTHON Y SIN EXE: SE INSTALA PYTHON 3.13
rem     (solo como respaldo; este caso requiere internet)
rem     Primero con winget; si no esta, con el instalador oficial
rem     de python.org (solo para este usuario, sin permisos admin).
rem ============================================================
echo   [!] Este equipo no tiene Python 3.13.
echo       Se instalara automaticamente (solo para este usuario).
echo       Requiere conexion a internet.
echo.
if "%MAPA_DRY_RUN%"=="1" (
    echo   [PRUEBA] Aqui se instalaria Python 3.13 ^(winget o python.org^) y luego las dependencias.
    exit /b 0
)

where winget >nul 2>nul
if errorlevel 1 goto instalar_instalador
echo   Intentando instalar Python con winget...
winget install --id Python.Python.3.13 -e --scope user --silent --accept-package-agreements --accept-source-agreements
set "PYINST=%LocalAppData%\Programs\Python\Python313\python.exe"
if exist "%PYINST%" goto usar_instalado

:instalar_instalador
echo   Descargando el instalador oficial de Python (una sola vez)...
set "INST=%TEMP%\python-313-instalador.exe"
if exist "%INST%" del /q "%INST%" >nul 2>nul
call :descargar_python 3.13.13
if not exist "%INST%" call :descargar_python 3.13.12
if not exist "%INST%" call :descargar_python 3.13.11
if not exist "%INST%" call :descargar_python 3.13.10
if not exist "%INST%" call :descargar_python 3.13.9
if not exist "%INST%" call :descargar_python 3.13.8
if not exist "%INST%" call :descargar_python 3.13.7
if not exist "%INST%" goto error_sin_python
echo   Instalando Python 3.13 (silencioso)...
"%INST%" /quiet InstallAllUsers=0 PrependPath=1 Include_launcher=1 InstallLauncherAllUsers=0 Include_pip=1
ping -n 4 127.0.0.1 >nul
set "PYINST=%LocalAppData%\Programs\Python\Python313\python.exe"
if not exist "%PYINST%" goto error_sin_python

:usar_instalado
echo   Python instalado correctamente: %PYINST%
set "PYEXE=%PYINST%"

rem ============================================================
rem  5) DEPENDENCIAS (solo la primera vez; requieren internet)
rem ============================================================
:verificar_deps
"%PYEXE%" -c "import fiona, pyproj, shapely, requests, matplotlib" >nul 2>nul
if errorlevel 1 goto instalar_deps
goto ejecutar

:instalar_deps
echo   Instalando dependencias: fiona, pyproj, shapely, requests, matplotlib...
"%PYEXE%" -m pip --version >nul 2>nul
if errorlevel 1 "%PYEXE%" -m ensurepip --default-pip >nul 2>nul
"%PYEXE%" -m pip install --only-binary :all: --disable-pip-version-check -r requirements.txt
if errorlevel 1 goto error_instalacion

:ejecutar
echo   Iniciando servidor... (esta ventana debe quedar abierta)
echo.
"%PYEXE%" server.py
echo.
echo   El servidor se detuvo.
if not "%MAPA_NO_PAUSE%"=="1" pause
exit /b 0

rem ------------------------------------------------------------
rem  Subrutinas
rem ------------------------------------------------------------
:descargar_python
if exist "%INST%" exit /b 0
echo     intentando version %1...
powershell -NoProfile -Command "try { Invoke-WebRequest -Uri 'https://www.python.org/ftp/python/%1/python-%1-amd64.exe' -OutFile '%INST%' -UseBasicParsing -TimeoutSec 240 } catch { exit 1 }"
exit /b 0

:lanzar_portable
echo   No hace falta instalar nada: se abre la version PORTABLE
echo   incluida en este paquete (lleva su propio Python interno).
echo.
echo   Si Windows pregunta "Windows protegio tu PC":
echo   pulsa "Mas informacion" -^> "Ejecutar de todas formas".
echo.
start "" "%~dp0MapaGarceroC.exe"
exit /b 0

:error_sin_python
echo.
echo   [!] No se pudo instalar Python automaticamente.
echo       Revisa la conexion a internet e intentalo de nuevo, o
echo       instala Python 3.13 manualmente desde:
echo       https://www.python.org/downloads/
echo       (marca la casilla "Add python.exe to PATH" al instalar)
echo       y vuelve a ejecutar este INICIAR.bat.
if not "%MAPA_NO_PAUSE%"=="1" pause
exit /b 1

:error_instalacion
echo.
echo   [!] Fallo la instalacion de dependencias. Revisa tu conexion a internet.
if not "%MAPA_NO_PAUSE%"=="1" pause
exit /b 1
