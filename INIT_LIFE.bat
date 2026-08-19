@echo off
setlocal enabledelayedexpansion

REM ============================================================
REM INIT_LIFE: Inicializador del Sistema Hart Consciousness
REM Inicia Java y Python en el orden correcto con doble clic
REM ============================================================

cd /d "%~dp0"

set "PORT=5050"
call :find_free_port

echo.
echo ============================================================
echo          INIT_LIFE: HART CONSCIOUSNESS MODEL
echo ============================================================
echo.
echo [1/3] Compilando agente Java...
javac -cp ".;lib\gson-2.13.1.jar" CharacterBody.java CognitiveSocketBridge.java SensoryData.java FeedbackData.java

if errorlevel 1 (
    echo.
    echo [ERROR] Compilacion fallida. Verifica los archivos .java
    echo Presiona cualquier tecla para salir...
    pause
    exit /b 1
)

echo [OK] Compilacion exitosa.
echo [INFO] Puerto seleccionado: !PORT!
echo.
echo [2/3] Iniciando CharacterBody (agente fisico)...
start "HART CharacterBody" cmd /k java -cp ".;lib\gson-2.13.1.jar" CharacterBody !PORT!

echo [INFO] Esperando a que Java esté listo (3 segundos)...
timeout /t 3 /nobreak

echo.
echo [3/3] Iniciando orquestador cognitivo Python...
start "HART Python Orchestrator" cmd /k py Untitled-1.py --port !PORT!

echo.
echo ============================================================
echo [DONE] Ambos procesos iniciados exitosamente.
echo.
echo - CharacterBody en ventana: HART CharacterBody
echo - Python Orchestrator en ventana: HART Python Orchestrator
echo.
echo Usa Ctrl+C en cada ventana para detener los procesos.
echo ============================================================
echo.
echo Presiona cualquier tecla para cerrar esta ventana de control...
pause
exit /b 0

:find_free_port
set "CHECK_RESULT="
for /l %%P in (!PORT!,1,5100) do (
    set "CHECK_RESULT="
    for /f "delims=" %%L in ('netstat -ano ^| findstr /R /C:":%%P .*LISTENING"') do set "CHECK_RESULT=busy"
    if not defined CHECK_RESULT (
        set "PORT=%%P"
        goto :eof
    )
)

echo [ERROR] No se encontro un puerto libre en el rango 5050-5100.
echo Presiona cualquier tecla para salir...
pause
exit /b 1
