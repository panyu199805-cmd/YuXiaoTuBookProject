# Detect proxy settings that cause WeChat ERR_TUNNEL_CONNECTION_FAILED (-111)
$ErrorActionPreference = "SilentlyContinue"

$warn = $false
$root = Split-Path $PSScriptRoot -Parent

Write-Host "=== WeChat DevTools proxy check ===" -ForegroundColor Cyan

try {
  $ie = Get-ItemProperty -Path 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Internet Settings'
  if ($ie.ProxyEnable -eq 1) {
    $warn = $true
    Write-Host "[WARN] Windows system proxy ON: $($ie.ProxyServer)" -ForegroundColor Yellow
  } elseif ($ie.ProxyServer -match '7890|7891|1080|10808') {
    $warn = $true
    Write-Host "[WARN] Stale proxy server in registry (ProxyEnable=0 but ProxyServer=$($ie.ProxyServer))" -ForegroundColor Yellow
    Write-Host "       WeChat cronet may still use 7890 even when DevTools proxy = NO PROXY" -ForegroundColor Yellow
    Write-Host "       Fix: run clear-stale-proxy.bat AND pause-clash-for-wechat.bat" -ForegroundColor Yellow
  }
  if ($ie.AutoConfigURL) {
    $warn = $true
    Write-Host "[WARN] PAC script enabled: $($ie.AutoConfigURL)" -ForegroundColor Yellow
  }
} catch {}

try {
  $winhttp = netsh winhttp show proxy 2>$null | Out-String
  if ($winhttp -notmatch 'Direct access|direct access|直接访问') {
    $warn = $true
    Write-Host "[WARN] WinHTTP proxy configured:" -ForegroundColor Yellow
    Write-Host $winhttp
  }
} catch {}

$clashPort = Get-NetTCPConnection -LocalPort 7890 -State Listen -ErrorAction SilentlyContinue
if ($clashPort) {
  $warn = $true
  Write-Host "[WARN] Clash/V2Ray likely listening on 127.0.0.1:7890 (PID $($clashPort.OwningProcess))" -ForegroundColor Yellow
  $viaProxy = & curl.exe -k -x "http://127.0.0.1:7890" -s -o NUL -w "%{http_code}" "https://127.0.0.1:8443/api/v1/site/config" 2>$null
  if ($viaProxy -ne "200") {
    Write-Host "[FAIL] https://127.0.0.1:8443 via proxy 7890 -> HTTP $viaProxy (same as WeChat -111)" -ForegroundColor Red
  }
}

$direct = & curl.exe -k -s -o NUL -w "%{http_code}" "https://127.0.0.1:8443/api/v1/site/config" 2>$null
if ($direct -eq "200") {
  Write-Host "[OK] https://127.0.0.1:8443 direct -> HTTP 200" -ForegroundColor Green
} else {
  $warn = $true
  Write-Host "[FAIL] https://127.0.0.1:8443 direct -> HTTP $direct (run dev-https-proxy.bat)" -ForegroundColor Red
}

if (-not $warn) {
  Write-Host "[OK] No obvious Windows proxy conflict" -ForegroundColor Green
}

Write-Host ""
Write-Host "Fix ERR_TUNNEL_CONNECTION_FAILED (-111):" -ForegroundColor Yellow
Write-Host "  1. DevTools proxy = NO PROXY (you already did this)"
Write-Host "  2. Run clear-stale-proxy.bat (remove leftover 127.0.0.1:7890 in registry)"
Write-Host "  3. Run pause-clash-for-wechat.bat (stop Clash on 7890)"
Write-Host "  4. Fully QUIT WeChat DevTools -> reopen -> clear cache -> recompile"
Write-Host ""
Write-Host "Run: $root\fix-wechat-tunnel.bat" -ForegroundColor Cyan
