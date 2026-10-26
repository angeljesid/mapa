@echo off
title Empaquetar Mapa Garcero C para Drive
cd /d "%~dp0"

echo.
echo   ================================================
echo     EMPAQUETAR MAPA GARCERO C PARA GOOGLE DRIVE
echo   ================================================
echo.

rem --- Carpeta portable generada por build_portable.py ---
set "ORIGEN=%~dp0dist\MapaGarceroC"
if not exist "%ORIGEN%\MapaGarceroC.exe" (
    echo   [!] No se encontro la version portable en "%ORIGEN%".
    echo       Ejecuta primero:  py -3.13 build_portable.py
    echo.
    pause
    exit /b 1
)

echo   Se encontro la version portable: %ORIGEN%
echo.

rem --- Ofrecer recompilar el EXE (solo si cambiaste el codigo) ---
choice /c SN /n /t 15 /d N /m "Recompilar el EXE con el codigo actual antes de empaquetar? (S) Si / (N) No [15 s]: "
if errorlevel 2 goto empaquetar
echo   Recompilando...
py -3.13 build_portable.py
if errorlevel 1 (
    echo   [!] Fallo la recompilacion. Revisa el mensaje anterior.
    pause
    exit /b 1
)

:empaquetar
echo.
echo   Comprimiendo (puede tardar unos minutos)...
for /f %%i in ('powershell -NoProfile -Command "(Get-Date).ToString('yyyy-MM-dd')"') do set "FECHA=%%i"
set "SALIDA=%~dp0ENTREGA\MapaGarceroC_Portable_%FECHA%.zip"
if not exist "%~dp0ENTREGA" mkdir "%~dp0ENTREGA"
if exist "%SALIDA%" del /q "%SALIDA%"

rem --- ZIP con tar.exe (viene con Windows 10/11) o .NET como respaldo ---
set "TAR=tar.exe"
where tar.exe >nul 2>nul
if errorlevel 1 goto zip_dotnet
cd /d "%~dp0dist"
"%TAR%" -a -c -f "%SALIDA%" MapaGarceroC
if errorlevel 1 goto zip_dotnet
goto zip_listo

:zip_dotnet
echo   tar no disponible; usando compresion .NET (mas lenta)...
powershell -NoProfile -Command "Add-Type -AssemblyName System.IO.Compression.FileSystem; [System.IO.Compression.ZipFile]::CreateFromDirectory('%ORIGEN%', '%SALIDA%', [System.IO.Compression.CompressionLevel]::Optimal, $true)"
if errorlevel 1 (
    echo   [!] Fallo al crear el ZIP.
    pause
    exit /b 1
)

:zip_listo
cd /d "%~dp0"
echo.
echo   ================================================
for %%A in ("%SALIDA%") do echo   ZIP CREADO: %%A
for /f %%s in ('powershell -NoProfile -Command "[math]::Round((Get-Item -LiteralPath '%SALIDA%').Length/1MB)"') do set "SIZE_MB=%%s"
echo   Tamano: %SIZE_MB% MB (aprox.)
echo   ================================================
echo.
echo   Pasos para enviarlo por Drive/WhatsApp/USB:
echo     1. Sube este ZIP a Google Drive (o copialo a una USB).
echo     2. Quien lo reciba debe DESCOMPRIMIRLO ENTERO
echo        (clic derecho -^> Extraer todo...).
echo     3. Dentro queda la carpeta MapaGarceroC con
echo        INICIAR.bat: doble clic y listo, sin instalar nada.
echo.
pause