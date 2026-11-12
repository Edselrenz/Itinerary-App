@echo off
title Nueva Ecija Travel Standalone Executable
cd /d "%~dp0"
echo Launching compiled standalone NuevaEcijaTravel.exe...
start "" "dist\NuevaEcijaTravel\NuevaEcijaTravel.exe"
exit
