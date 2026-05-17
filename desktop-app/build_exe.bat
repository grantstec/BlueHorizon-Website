@echo off
REM ---------------------------------------------------------------------------
REM Build BlueHorizonDesktop.exe with PyInstaller.
REM Requires: Python 3.10+ on PATH. Run this from a normal Command Prompt.
REM ---------------------------------------------------------------------------

setlocal
pushd "%~dp0"

echo.
echo [1/3] Creating virtual environment (.venv) if needed...
if not exist .venv (
    python -m venv .venv
    if errorlevel 1 (
        echo ERROR: Could not create virtual environment. Is Python installed?
        echo Download Python from https://www.python.org/downloads/ and try again.
        pause
        exit /b 1
    )
)

call .venv\Scripts\activate.bat

echo.
echo [2/3] Installing PyInstaller...
python -m pip install --upgrade pip
pip install -r requirements.txt
if errorlevel 1 (
    echo ERROR: Could not install dependencies.
    pause
    exit /b 1
)

echo.
echo [3/3] Building BlueHorizonDesktop.exe ...
pyinstaller --clean BlueHorizon.spec
if errorlevel 1 (
    echo ERROR: PyInstaller failed.
    pause
    exit /b 1
)

echo.
echo ============================================================
echo Build complete!
echo Find the .exe at:  desktop-app\dist\BlueHorizonDesktop.exe
echo ============================================================
echo.

popd
endlocal
pause
