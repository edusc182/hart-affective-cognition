@echo off
setlocal

REM ============================================================
REM INIT_LIFE2.bat
REM Arranca el agente Rust con GGUF en CPU y prepara libclang.
REM ============================================================

set "SCRIPT_DIR=%~dp0"
cd /d "%SCRIPT_DIR%"

title HART Rust Bootstrap (INIT_LIFE2)

REM Ruta por defecto a LLVM (requerido por bindgen / llama-cpp-sys-2)
set "LIBCLANG_PATH="

REM Permitir override externo si ya existe variable del sistema
if defined LIBCLANG_PATH (
    set "LIBCLANG_PATH=%LIBCLANG_PATH%"
)
if defined USER_LIBCLANG_PATH (
    set "LIBCLANG_PATH=%USER_LIBCLANG_PATH%"
)

if defined LIBCLANG_PATH (
    if exist "%LIBCLANG_PATH%\libclang.dll" goto :libclang_ok
    if exist "%LIBCLANG_PATH%\clang.dll" goto :libclang_ok
)

for %%D in (
    "C:\Program Files\LLVM\bin"
    "C:\Program Files (x86)\LLVM\bin"
    "C:\msys64\clang64\bin"
    "C:\msys64\ucrt64\bin"
    "C:\msys64\mingw64\bin"
    "C:\Program Files\Microsoft Visual Studio\2022\Community\VC\Tools\Llvm\x64\bin"
    "C:\Program Files\Microsoft Visual Studio\2022\BuildTools\VC\Tools\Llvm\x64\bin"
    "C:\Program Files\Microsoft Visual Studio\2022\Professional\VC\Tools\Llvm\x64\bin"
    "C:\Program Files\Microsoft Visual Studio\2022\Enterprise\VC\Tools\Llvm\x64\bin"
    "%LocalAppData%\Programs\LLVM\bin"
    "%SCRIPT_DIR%tools\llvm\bin"
) do (
    if exist "%%~D\libclang.dll" (
        set "LIBCLANG_PATH=%%~D"
        goto :libclang_ok
    )
    if exist "%%~D\clang.dll" (
        set "LIBCLANG_PATH=%%~D"
        goto :libclang_ok
    )
)

if not defined LIBCLANG_PATH (
    echo.
    echo [ERROR] No se encontro libclang.dll ni clang.dll.
    echo.
    echo Rutas revisadas:
    echo   C:\Program Files\LLVM\bin
    echo   C:\Program Files ^(x86^)\LLVM\bin
    echo   C:\msys64\clang64\bin
    echo   C:\msys64\ucrt64\bin
    echo   C:\msys64\mingw64\bin
    echo   C:\Program Files\Microsoft Visual Studio\2022\...\VC\Tools\Llvm\x64\bin
    echo   %%LocalAppData%%\Programs\LLVM\bin
    echo   %SCRIPT_DIR%tools\llvm\bin
    echo.
    echo Instala LLVM y verifica alguno de estos archivos:
    echo   libclang.dll  o  clang.dll
    echo.
    echo Luego puedes fijarlo temporalmente en cmd:
    echo   set "LIBCLANG_PATH=C:\Ruta\A\LLVM\bin"
    echo.
    echo O persistente:
    echo   setx LIBCLANG_PATH "C:\Ruta\A\LLVM\bin"
    echo.
    set /p "MANUAL_LIBCLANG_PATH=Ingresa ahora la ruta de LLVM\bin (ENTER para cancelar): "
    if "%MANUAL_LIBCLANG_PATH%"=="" (
        echo.
        echo [CANCELADO] No se proporciono ruta manual de LLVM.
        pause
        exit /b 1
    )

    if exist "%MANUAL_LIBCLANG_PATH%\libclang.dll" (
        set "LIBCLANG_PATH=%MANUAL_LIBCLANG_PATH%"
        goto :libclang_ok
    )
    if exist "%MANUAL_LIBCLANG_PATH%\clang.dll" (
        set "LIBCLANG_PATH=%MANUAL_LIBCLANG_PATH%"
        goto :libclang_ok
    )

    echo.
    echo [ERROR] En esa ruta no existe libclang.dll ni clang.dll:
    echo         "%MANUAL_LIBCLANG_PATH%"
    echo.
    pause
    exit /b 1
)

:libclang_ok
set "PATH=%LIBCLANG_PATH%;%PATH%"

REM Detectar CMake requerido por llama-cpp-sys-2
set "CMAKE_BIN_DIR="
for %%D in (
    "C:\Program Files\CMake\bin"
    "C:\Program Files (x86)\CMake\bin"
    "C:\Program Files\Microsoft Visual Studio\2022\Community\Common7\IDE\CommonExtensions\Microsoft\CMake\CMake\bin"
    "C:\Program Files\Microsoft Visual Studio\2022\BuildTools\Common7\IDE\CommonExtensions\Microsoft\CMake\CMake\bin"
    "C:\Program Files\Microsoft Visual Studio\2022\Professional\Common7\IDE\CommonExtensions\Microsoft\CMake\CMake\bin"
    "C:\Program Files\Microsoft Visual Studio\2022\Enterprise\Common7\IDE\CommonExtensions\Microsoft\CMake\CMake\bin"
) do (
    if exist "%%~D\cmake.exe" (
        set "CMAKE_BIN_DIR=%%~D"
        goto :cmake_ok
    )
)

for %%I in (cmake.exe) do (
    if not "%%~$PATH:I"=="" (
        set "CMAKE_BIN_DIR=%%~dp$PATH:I"
        goto :cmake_ok
    )
)

echo.
echo [ERROR] No se encontro cmake.exe.
echo.
echo Instala CMake y verifica uno de estos caminos:
echo   C:\Program Files\CMake\bin\cmake.exe
echo   C:\Program Files\Microsoft Visual Studio\2022\...\CMake\bin\cmake.exe
echo.
echo Luego vuelve a ejecutar INIT_LIFE2.bat.
echo.
pause
exit /b 1

:cmake_ok
set "PATH=%CMAKE_BIN_DIR%;%PATH%"

REM Carpeta del modelo GGUF
set "MODEL_DIR=%SCRIPT_DIR%Modelo GGUF"
set "MODEL_PATH="

for %%F in ("%MODEL_DIR%\*.gguf") do (
    set "MODEL_PATH=%%~fF"
    goto :model_found
)

:model_found

if not exist "%MODEL_PATH%" (
    echo.
    echo [ERROR] No se encontro ningun modelo GGUF en:
    echo         "%MODEL_DIR%"
    echo.
    echo Copia un archivo .gguf a esa carpeta o ajusta MODEL_DIR.
    echo.
    pause
    exit /b 1
)

set "HART_GGUF_PATH=%MODEL_PATH%"

echo.
echo [OK] LIBCLANG_PATH = %LIBCLANG_PATH%
echo [OK] CMAKE_BIN_DIR = %CMAKE_BIN_DIR%
echo [OK] HART_GGUF_PATH = %HART_GGUF_PATH%
echo [INFO] Iniciando hart_agent en modo release...
echo.

if not exist "hart_agent\Cargo.toml" (
    echo [ERROR] No se encontro hart_agent\Cargo.toml en esta carpeta.
    pause
    exit /b 1
)

pushd "hart_agent"
cargo run --release -- "%HART_GGUF_PATH%"
set "EXITCODE=%ERRORLEVEL%"
popd

echo.
if not "%EXITCODE%"=="0" (
    echo [ERROR] El proceso termino con codigo %EXITCODE%.
) else (
    echo [OK] Proceso finalizado correctamente.
)

echo.
pause
exit /b %EXITCODE%
