@echo off
title Nueva Ecija Travel App - Server Launcher
cd /d "%~dp0"
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\start_server.ps1"
pause

