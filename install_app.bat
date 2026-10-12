@echo off
setlocal
title Installing Samlytics VoiceStudio...
cd /d "%~dp0"

echo ==========================================================
echo        SAMLYTICS DATA SERVICES - VOICE STUDIO
echo ==========================================================
echo.
echo Installing requirements...
python -m pip install -r requirements.txt
if %ERRORLEVEL% NEQ 0 (
    echo [WARNING] Some packages failed or are already installed. Continuing...
)

echo.
echo Generating ambient instrumentals and brand assets...
python tracks_generator.py

echo.
echo Creating Desktop shortcut...
python create_shortcut.py

echo.
echo ==========================================================
echo   INSTALLATION COMPLETE!
echo   A shortcut "Samlytics VoiceStudio" has been created
echo   on your Desktop. You can now launch it anytime!
echo ==========================================================
echo.
pause

