@echo off
setlocal
title Installing Samlytics VoiceStudio...
cd /d "%~dp0"

echo ==========================================================
echo        SAMLYTICS DATA SERVICES - VOICE STUDIO
echo ==========================================================
echo.

where python >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    set PY_CMD=python
) else (
    where py >nul 2>&1
    if %ERRORLEVEL% EQU 0 (
        set PY_CMD=py
    ) else (
        echo [ERROR] Python is not installed or not in your system PATH.
        echo Please download and install Python 3.10+ from https://www.python.org/downloads/
        echo Make sure to check the box "Add Python to PATH" during installation.
        echo.
        pause
        exit /b 1
    )
)

echo [1/3] Installing Python dependencies from requirements.txt...
%PY_CMD% -m pip install -r requirements.txt
if %ERRORLEVEL% NEQ 0 (
    echo [WARNING] Some optional packages may have failed, proceeding...
)

echo.
echo [2/3] Generating ambient storytelling instrumentals...
%PY_CMD% tracks_generator.py

echo.
echo [3/3] Creating Windows Desktop shortcut with brand icon...
%PY_CMD% create_shortcut.py

echo.
echo ==========================================================
echo   INSTALLATION COMPLETE!
echo   A shortcut "Samlytics VoiceStudio" has been placed on
echo   your Desktop. You can now launch and use it anytime!
echo ==========================================================
echo.
pause
