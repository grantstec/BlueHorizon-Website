@echo off
REM ---------------------------------------------------------------------------
REM Build BlueHorizonDesktop.exe with PyInstaller.
REM
REM Why we build into %TEMP% instead of the current folder:
REM   This repo lives under OneDrive, and OneDrive's sync agent keeps files
REM   open during/after writes. PyInstaller cleans its own build/ folder on
REM   each run and the resulting locked-file race produces:
REM       PermissionError: [WinError 5] Access is denied: ...\build\...
REM   Building into %TEMP% bypasses OneDrive entirely, then we copy only the
REM   finished .exe back into desktop-app\dist\.
REM
REM Requires: Python 3.10+ on PATH. Run this from a normal Command Prompt.
REM ---------------------------------------------------------------------------

setlocal EnableDelayedExpansion
pushd "%~dp0"

set "BUILD_DIR=%TEMP%\BlueHorizonDesktop-build"
set "STAGE_DIR=%TEMP%\BlueHorizonDesktop-dist"
set "FINAL_DIR=%CD%\dist"

echo.
echo [1/5] Creating virtual environment (.venv) if needed...
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
echo [2/5] Installing PyInstaller...
python -m pip install --upgrade pip >nul
pip install -r requirements.txt
if errorlevel 1 (
    echo ERROR: Could not install dependencies.
    pause
    exit /b 1
)

echo.
echo [3/5] Closing any running BlueHorizonDesktop.exe so the file isn't locked...
taskkill /F /IM BlueHorizonDesktop.exe >nul 2>&1
REM Brief pause to let Windows release the handle
timeout /t 1 /nobreak >nul

echo.
echo [4/5] Cleaning previous build artifacts...
if exist "%BUILD_DIR%" rmdir /S /Q "%BUILD_DIR%" 2>nul
if exist "%STAGE_DIR%" rmdir /S /Q "%STAGE_DIR%" 2>nul
REM Also wipe any stale build/ and dist/ from previous in-tree runs
if exist build rmdir /S /Q build 2>nul
if exist dist rmdir /S /Q dist 2>nul

echo.
echo [5/5] Building BlueHorizonDesktop.exe (work dir: %BUILD_DIR%)...
pyinstaller --clean ^
    --workpath "%BUILD_DIR%" ^
    --distpath "%STAGE_DIR%" ^
    BlueHorizon.spec
if errorlevel 1 (
    echo.
    echo ERROR: PyInstaller failed. Common causes:
    echo   - Antivirus blocked the build. Add an exclusion for %BUILD_DIR%.
    echo   - The .exe is still running somewhere. Close it and rerun.
    pause
    exit /b 1
)

REM Copy the finished .exe back into the repo's dist\ folder
if not exist "%FINAL_DIR%" mkdir "%FINAL_DIR%"
copy /Y "%STAGE_DIR%\BlueHorizonDesktop.exe" "%FINAL_DIR%\" >nul
if errorlevel 1 (
    echo ERROR: Could not copy the finished .exe into %FINAL_DIR%.
    echo It is still available at: %STAGE_DIR%\BlueHorizonDesktop.exe
    pause
    exit /b 1
)

REM Clean up the temp staging area
rmdir /S /Q "%BUILD_DIR%" 2>nul
rmdir /S /Q "%STAGE_DIR%" 2>nul

echo.
echo ============================================================
echo Build complete!
echo Find the .exe at:  %FINAL_DIR%\BlueHorizonDesktop.exe
echo ============================================================
echo.

popd
endlocal
pause
