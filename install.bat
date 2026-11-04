@echo off
title ForgeArtisan Installer Setup
color 0B
echo Launching ForgeArtisan Windows Installer with PATH configuration...
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0packaging\Install-ForgeArtisan.ps1"
pause
