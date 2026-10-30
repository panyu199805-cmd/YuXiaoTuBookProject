# One-shot fix for WeChat MP -111: clear stale proxy + stop Clash + verify 8443
param([switch]$SkipClash)

$ErrorActionPreference = "SilentlyContinue"
$root = Split-Path $PSScriptRoot -Parent

Write-Host "=== Fix WeChat MP network (-111) ===" -ForegroundColor Cyan

# 1. Clear stale registry proxy (ProxyEnable=0 but ProxyServer still 7890)
$path = 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Internet Settings'
$ie = Get-ItemProperty -Path $path
if ($ie.ProxyEnable -eq 0 -and $ie.ProxyServer) {
  Write-Host "[FIX] Clearing stale ProxyServer=$($ie.ProxyServer)" -ForegroundColor Yellow
  Remove-ItemProperty -Path $path -Name ProxyServer -ErrorAction SilentlyContinue
  Remove-ItemProperty -Path $path -Name AutoConfigURL -ErrorAction SilentlyContinue
}

# 2. Stop Clash
if (-not $SkipClash) {
  $clash = Get-Process -Name "clash-win64", "Clash for Windows" -ErrorAction SilentlyContinue
  if ($clash) {
    Write-Host "[FIX] Stopping Clash (required for WeChat local HTTPS)..." -ForegroundColor Yellow
    $clash | ForEach-Object { Stop-Process -Id $_.Id -Force -ErrorAction SilentlyContinue }
    Start-Sleep -Seconds 2
  }
  $p7890 = Get-NetTCPConnection -LocalPort 7890 -State Listen -ErrorAction SilentlyContinue
  if ($p7890) {
    Write-Host "[FAIL] Port 7890 still in use. Quit Clash from system tray manually." -ForegroundColor Red
    exit 1
  }
  Write-Host "[OK] Clash stopped, port 7890 free" -ForegroundColor Green
}

# 3. Ensure HTTPS proxy (8443/8444)
$code = & curl.exe -k -s -o NUL -w "%{http_code}" "https://127.0.0.1:8443/api/v1/site/config" 2>$null
if ($code -ne "200") {
  Write-Host "[FIX] HTTPS proxy not reachable. Starting dev-https-proxy..." -ForegroundColor Yellow
  Start-Process powershell -ArgumentList @(
    '-ExecutionPolicy', 'Bypass', '-NoExit', '-File', (Join-Path $PSScriptRoot 'dev-https-proxy.ps1')
  ) -WindowStyle Minimized
  Start-Sleep -Seconds 6
  $code = & curl.exe -k -s -o NUL -w "%{http_code}" "https://127.0.0.1:8443/api/v1/site/config" 2>$null
}
if ($code -ne "200") {
  Write-Host "[FAIL] https://127.0.0.1:8443 -> HTTP $code. Run dev-https-proxy.bat manually." -ForegroundColor Red
  Write-Host "       Also confirm Python :8000 and Java :8081 are running." -ForegroundColor Red
  exit 1
}
Write-Host "[OK] https://127.0.0.1:8443 -> HTTP 200" -ForegroundColor Green

Write-Host ""
Write-Host "=== YOU MUST DO THIS NOW ===" -ForegroundColor Yellow
Write-Host "1. Task Manager -> end ALL wechatdevtools processes"
Write-Host "2. Reopen WeChat DevTools -> import project"
Write-Host "3. Settings -> Proxy -> NO PROXY (already set)"
Write-Host "4. Clear cache -> Recompile"
Write-Host ""
Write-Host "When done debugging, restart Clash for Windows." -ForegroundColor Cyan
