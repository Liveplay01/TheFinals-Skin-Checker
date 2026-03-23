@echo off
title TheFinalsStats — Build
echo.
echo  ================================================
echo   TheFinalsStats ^| Build Script
echo  ================================================
echo.

:: Step 1 — Prepare Tesseract vendor files
echo [1/3] Preparing Tesseract vendor files...
python prepare_vendor.py
if errorlevel 1 (
    echo.
    echo  [FAILED] Could not prepare Tesseract. See error above.
    echo  Install Tesseract from: https://github.com/UB-Mannheim/tesseract/wiki
    echo.
    pause
    exit /b 1
)

echo.

:: Step 2 — Install / update Python dependencies
echo [2/3] Installing Python dependencies...
pip install -r requirements.txt --quiet
if errorlevel 1 (
    echo  [FAILED] pip install failed.
    pause
    exit /b 1
)

echo.

:: Step 3 — Build with PyInstaller
echo [3/3] Building .exe with PyInstaller...
pyinstaller TheFinalsStats.spec --clean --noconfirm
if errorlevel 1 (
    echo.
    echo  [FAILED] PyInstaller build failed. Check output above.
    pause
    exit /b 1
)

echo.
echo  ================================================
echo   BUILD COMPLETE
echo   Output: dist\TheFinalsStats\TheFinalsStats.exe
echo  ================================================
echo.
pause
