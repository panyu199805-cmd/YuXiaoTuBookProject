@echo off
chcp 65001 >nul
cd /d "%~dp0.."
echo === WeChat Mini Program Dev Build ===
echo.
echo Close WeChat DevTools first, then press any key...
pause >nul

if exist "dist\dev\mp-weixin" (
  rmdir /s /q "dist\dev\mp-weixin" 2>nul
)

echo Building...
call npx uni -p mp-weixin

echo.
echo === Done ===
echo Import in WeChat DevTools:
echo   %CD%\dist\dev\mp-weixin
echo.
echo Or import project root (uses miniprogramRoot in project.config.json):
echo   %CD%
echo.
pause
