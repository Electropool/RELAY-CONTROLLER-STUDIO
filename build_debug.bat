@echo off
REM ============================================================================
REM build_debug.bat - Packaging Relay Controller Studio (Debug Build)
REM Creates an executable with console output enabled for debugging.
REM ============================================================================

setlocal enabledelayedexpansion

set VENV_DIR=%~dp0.venv
set PY=%VENV_DIR%\Scripts\python.exe

if not exist "%PY%" (
    set PY=python
)

echo [build_debug.bat] Ensuring PyInstaller is installed...
"%PY%" -m pip install --upgrade pyinstaller

echo [build_debug.bat] Building Debug Executable (With Console Output)...
"%PY%" -m PyInstaller ^
    --name RelayControllerStudio_Debug ^
    --onefile ^
    --console ^
    --clean ^
    --add-data "src;src" ^
    --add-data "firmware;firmware" ^
    --add-data "config;config" ^
    --paths "src" ^
    --distpath "build\dist" ^
    --workpath "build\work" ^
    --specpath "build" ^
    main.py

echo.
echo [build_debug.bat] Debug build complete!
echo Output: build\dist\RelayControllerStudio_Debug.exe
echo.
endlocal
