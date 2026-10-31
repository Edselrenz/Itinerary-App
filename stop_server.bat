@echo off
title Nueva Ecija Travel App - Server Shutdown
cd /d "%~dp0"
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\stop_server.ps1"
pause
