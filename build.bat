@echo off
REM ============================================================================
REM build.bat - Packages Relay Controller Studio into a single Windows .exe
REM using PyInstaller.
REM
REM Produces:
REM   build\dist\RelayControllerStudio.exe
REM
REM Requires the virtual environment created by run.bat to already exist
REM (run.bat at least once before running this script), or a system Python
REM with the packages in requirements.txt + pyinstaller installed.
REM ============================================================================

setlocal

set VENV_DIR=%~dp0.venv
set PY=%VENV_DIR%\Scripts\python.exe

if not exist "%PY%" (
    echo [build.bat] No virtual environment found at %VENV_DIR%.
    echo [build.bat] Run run.bat first, or edit this script to point at your Python install.
    pause
    exit /b 1
)

echo [build.bat] Ensuring PyInstaller is installed...
"%PY%" -m pip install --upgrade pyinstaller

echo [build.bat] Building single-file executable...
"%PY%" -m PyInstaller ^
    --name RelayControllerStudio ^
    --onefile ^
    --windowed ^
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
echo [build.bat] Done. If successful, the executable is at:
echo     build\dist\RelayControllerStudio.exe
echo.
echo NOTE: --add-data uses Windows-style ';' separators (this script is
echo Windows-only). See README.md "Building a Windows executable" for the
echo macOS/Linux equivalent (':' separator) if building from source there.

endlocal
