@echo off
REM ============================================================================
REM run.bat - Launches Relay Controller Studio from source on Windows.
REM
REM Assumes Python 3.10+ is installed and on PATH. Creates/uses a local
REM virtual environment (.venv) so dependencies never pollute the system
REM Python installation.
REM ============================================================================

setlocal

set VENV_DIR=%~dp0.venv

if not exist "%VENV_DIR%\Scripts\python.exe" (
    echo [run.bat] No virtual environment found - creating one at %VENV_DIR%
    python -m venv "%VENV_DIR%"
    if errorlevel 1 (
        echo [run.bat] ERROR: Failed to create virtual environment. Is Python installed and on PATH?
        pause
        exit /b 1
    )

    echo [run.bat] Installing dependencies from requirements.txt...
    "%VENV_DIR%\Scripts\python.exe" -m pip install --upgrade pip
    "%VENV_DIR%\Scripts\python.exe" -m pip install -r "%~dp0requirements.txt"
    if errorlevel 1 (
        echo [run.bat] ERROR: Dependency installation failed.
        pause
        exit /b 1
    )
)

echo [run.bat] Launching Relay Controller Studio...
"%VENV_DIR%\Scripts\python.exe" "%~dp0main.py"

endlocal
