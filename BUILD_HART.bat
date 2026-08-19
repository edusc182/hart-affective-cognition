@echo off
setlocal enabledelayedexpansion

REM Simple build script
set "SCRIPT_DIR=%~dp0"
cd /d "%SCRIPT_DIR%"

set "LIBCLANG_PATH=C:\Program Files\Microsoft Visual Studio\2022\Community\VC\Tools\Llvm\x64\bin"
set "CMAKE_BIN_DIR=C:\Program Files\CMake\bin"

set "PATH=%LIBCLANG_PATH%;%CMAKE_BIN_DIR%;%PATH%"

cd /d "%SCRIPT_DIR%hart_agent"
echo Compilando hart_agent en modo release...
cargo build --release

if !errorlevel! equ 0 (
    echo.
    echo [OK] Compilacion exitosa!
    echo Ejecutable: %SCRIPT_DIR%hart_agent\target\release\hart_agent.exe
) else (
    echo.
    echo [ERROR] Fallo en la compilacion. Codigo: !errorlevel!
)

pause
