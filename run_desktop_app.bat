@echo off
title Nueva Ecija Travel - Desktop Application
cd /d "%~dp0"
echo Starting Nueva Ecija Travel Desktop Client...
python desktop_client\main.py
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo Desktop application exited with error code %ERRORLEVEL%.
    pause
)
