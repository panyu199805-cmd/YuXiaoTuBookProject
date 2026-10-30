@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo Phone hotspot mode: HTTP LAN (no HTTPS, no cert)
powershell -ExecutionPolicy Bypass -File "%~dp0scripts\start-mp-simulator.ps1"
pause
