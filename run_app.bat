@echo off
setlocal
title Samlytics VoiceStudio Launcher
cd /d "%~dp0"

where python >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    set PY_CMD=python
) else (
    where py >nul 2>&1
    if %ERRORLEVEL% EQU 0 (
        set PY_CMD=py
    ) else (
        echo.
        echo [ERROR] Python was not found on this computer.
        echo Please install Python 3.10 or higher from: https://www.python.org/downloads/
        echo Be sure to check the box "Add Python to PATH" during setup.
        echo.
        pause
        exit /b 1
    )
)

%PY_CMD% app.py
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo Application exited with an error code.
    pause
)
