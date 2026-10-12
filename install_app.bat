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

echo [1/4] Installing Python dependencies from requirements.txt...
%PY_CMD% -m pip install -r requirements.txt
if %ERRORLEVEL% NEQ 0 (
    echo [WARNING] Some optional packages may have failed, proceeding...
)

echo.
echo [2/4] Generating ambient storytelling instrumentals...
%PY_CMD% tracks_generator.py

echo.
echo [3/4] Creating Windows Desktop and Start Menu shortcuts...
%PY_CMD% create_shortcut.py

echo.
echo [4/4] Registering in Windows Installed Programs (Add or Remove Programs)...
%PY_CMD% register_app.py

echo.
echo ==========================================================
echo   INSTALLATION COMPLETE!
echo   * Desktop shortcut "Samlytics VoiceStudio" created
echo   * Start Menu shortcut created
echo   * Registered in Windows Settings (Installed Apps)
echo.
echo   To uninstall in the future:
echo   - Use Windows Settings ^> Apps ^> Installed apps, OR
echo   - Double-click uninstall_app.bat
echo ==========================================================
echo.
pause
