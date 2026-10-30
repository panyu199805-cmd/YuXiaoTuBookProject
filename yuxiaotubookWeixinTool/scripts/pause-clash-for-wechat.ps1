# Temporarily stop Clash/V2Ray so WeChat DevTools can reach https://127.0.0.1:8443
param(
  [switch]$Force
)

$ErrorActionPreference = "SilentlyContinue"

Write-Host "=== Pause Clash for WeChat mini program dev ===" -ForegroundColor Cyan

$clashProcs = Get-Process -Name "clash-win64", "Clash for Windows" -ErrorAction SilentlyContinue
$port7890 = Get-NetTCPConnection -LocalPort 7890 -State Listen -ErrorAction SilentlyContinue

if (-not $clashProcs -and -not $port7890) {
  Write-Host "[OK] Clash/V2Ray not detected on 7890" -ForegroundColor Green
  & (Join-Path $PSScriptRoot "check-wechat-proxy.ps1")
  exit 0
}

Write-Host "[WARN] Clash is running. WeChat DevTools will fail with -111 if it uses proxy 7890." -ForegroundColor Yellow
Write-Host ""
Write-Host "Choose ONE fix:" -ForegroundColor Yellow
Write-Host "  A) WeChat DevTools -> Settings -> Proxy -> NO PROXY, then fully restart DevTools"
Write-Host "  B) Stop Clash now (this script), debug mini program, restart Clash later"
Write-Host ""

if (-not $Force) {
  $ans = Read-Host "Stop Clash processes now? [y/N]"
  if ($ans -notmatch '^[yY]') {
    Write-Host "Skipped. Fix WeChat proxy setting instead, then restart DevTools." -ForegroundColor Cyan
    exit 0
  }
}

foreach ($p in $clashProcs) {
  Write-Host "Stopping $($p.ProcessName) (PID $($p.Id))..." -ForegroundColor Yellow
  Stop-Process -Id $p.Id -Force -ErrorAction SilentlyContinue
}

Start-Sleep -Seconds 2
$still = Get-NetTCPConnection -LocalPort 7890 -State Listen -ErrorAction SilentlyContinue
if ($still) {
  Write-Host "[FAIL] Port 7890 still in use (PID $($still.OwningProcess)). Quit Clash from tray manually." -ForegroundColor Red
  exit 1
}

Write-Host "[OK] Clash stopped. Port 7890 is free." -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Cyan
Write-Host "  1. Fully QUIT WeChat DevTools (all wechatdevtools processes)"
Write-Host "  2. Reopen project -> Clear cache -> Recompile"
Write-Host "  3. When done debugging, start Clash for Windows again"
Write-Host ""

& (Join-Path $PSScriptRoot "check-wechat-proxy.ps1")
