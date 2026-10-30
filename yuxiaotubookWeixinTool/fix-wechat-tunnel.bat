@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo.
echo ========================================
echo  Fix WeChat -111 (ERR_TUNNEL_CONNECTION_FAILED)
echo ========================================
echo.
echo Root cause: Clash proxy 7890 + WeChat DevTools using proxy tunnel.
echo API https://127.0.0.1:8443 is OK when connecting directly.
echo.
powershell -ExecutionPolicy Bypass -File "%~dp0scripts\check-wechat-proxy.ps1"
echo.
echo ----------------------------------------
echo  REQUIRED: WeChat DevTools proxy setting
echo ----------------------------------------
echo  Top-right Settings ^> Proxy ^> select:
echo    "Do not use any proxy" (NOT system proxy)
echo  Then FULLY QUIT and reopen WeChat DevTools.
echo.
echo Optional: run pause-clash-for-wechat.bat to stop Clash temporarily.
echo.
pause
