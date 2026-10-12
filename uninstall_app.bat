@echo off
setlocal
title Uninstalling Samlytics VoiceStudio...
cd /d "%~dp0"

echo ==========================================================
echo       SAMLYTICS DATA SERVICES - VOICE STUDIO
echo                   UNINSTALLER
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
        echo [ERROR] Python not found. Removing desktop shortcuts directly via PowerShell...
        powershell -NoProfile -Command "Remove-Item -Path \"$([Environment]::GetFolderPath('Desktop'))\Samlytics VoiceStudio.lnk\" -ErrorAction SilentlyContinue"
        powershell -NoProfile -Command "Remove-Item -Path \"$env:APPDATA\Microsoft\Windows\Start Menu\Programs\Samlytics VoiceStudio.lnk\" -ErrorAction SilentlyContinue"
        echo Done.
        pause
        exit /b 0
    )
)

%PY_CMD% uninstall_app.py %*

if "%1" NEQ "/quiet" (
    echo.
    pause
)
