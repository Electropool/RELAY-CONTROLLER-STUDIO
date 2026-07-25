@echo off
REM ============================================================================
REM build_release.bat - Packaging Relay Controller Studio (Release Build)
REM Creates a clean GUI-only executable without console window.
REM ============================================================================

setlocal enabledelayedexpansion

set VENV_DIR=%~dp0.venv
set PY=%VENV_DIR%\Scripts\python.exe

if not exist "%PY%" (
    set PY=python
)

echo [build_release.bat] Ensuring PyInstaller is installed...
"%PY%" -m pip install --upgrade pyinstaller

echo [build_release.bat] Building Release Executable (No Console)...
"%PY%" -m PyInstaller ^
    --name RelayControllerStudio_Release ^
    --onefile ^
    --windowed ^
    --clean ^
    --icon "assets\icons\icon.ico" ^
    --add-data "src;src" ^
    --add-data "firmware;firmware" ^
    --add-data "config;config" ^
    --add-data "assets;assets" ^
    --add-data "docs;docs" ^
    --paths "src" ^
    --distpath "build\dist" ^
    --workpath "build\work" ^
    --specpath "build" ^
    main.py

echo.
echo [build_release.bat] Release build complete!
echo Output: build\dist\RelayControllerStudio_Release.exe
echo.
endlocal
