# 一键检测：本机 API 是否可被小程序访问
# 用法：powershell -ExecutionPolicy Bypass -File scripts\check-mp-api.ps1

$ErrorActionPreference = "Stop"
Set-Location (Join-Path $PSScriptRoot "..")

$ip = (Get-NetIPAddress -AddressFamily IPv4 | Where-Object {
  $_.IPAddress -notlike '127.*' `
    -and $_.IPAddress -notlike '169.254.*' `
    -and $_.InterfaceAlias -notmatch 'Loopback|vEthernet|WSL|VMware|VirtualBox|Hyper-V'
} | Sort-Object @{
  Expression = {
    if ($_.IPAddress -like '192.168.*') { 0 }
    elseif ($_.IPAddress -like '10.*') { 1 }
    elseif ($_.IPAddress -match '^172\.(1[6-9]|2\d|3[01])\.') { 2 }
    else { 9 }
  }
} | Select-Object -First 1).IPAddress

if (-not $ip) {
  Write-Host "[FAIL] No LAN IPv4 found. Connect Wi-Fi/Ethernet first." -ForegroundColor Red
  exit 1
}

$apiUrl = "http://${ip}:8000/api/v1/site/config"
Write-Host "LAN IP: $ip" -ForegroundColor Cyan
Write-Host "Testing: $apiUrl" -ForegroundColor Cyan

try {
  $r = Invoke-WebRequest -Uri $apiUrl -UseBasicParsing -TimeoutSec 8
  if ($r.StatusCode -eq 200) {
    Write-Host "[OK] API reachable (HTTP $($r.StatusCode))" -ForegroundColor Green
  } else {
    Write-Host "[WARN] HTTP $($r.StatusCode)" -ForegroundColor Yellow
  }
} catch {
  Write-Host "[FAIL] API not reachable: $($_.Exception.Message)" -ForegroundColor Red
  Write-Host "  1. Run: ..\开发文档\本地运行.ps1" -ForegroundColor Yellow
  Write-Host "  2. Check Docker: docker ps" -ForegroundColor Yellow
  exit 1
}

$tradeUrl = "http://${ip}:8081/api/v1/member/packages"
Write-Host "Testing trade: $tradeUrl" -ForegroundColor Cyan
try {
  $tr = Invoke-WebRequest -Uri $tradeUrl -UseBasicParsing -TimeoutSec 8
  if ($tr.StatusCode -eq 200) {
    Write-Host "[OK] Trade service reachable (HTTP $($tr.StatusCode))" -ForegroundColor Green
  } else {
    Write-Host "[WARN] Trade HTTP $($tr.StatusCode)" -ForegroundColor Yellow
  }
} catch {
  Write-Host "[FAIL] Trade service not reachable: $($_.Exception.Message)" -ForegroundColor Red
  Write-Host "  Run: ..\开发文档\本地运行.ps1  (starts trade on :8081)" -ForegroundColor Yellow
}

$envFile = Join-Path $PWD ".env.development"
$currentBase = $null
if (Test-Path $envFile) {
  Select-String -Path $envFile -Pattern '^\s*VITE_API_BASE=(.+)$' | ForEach-Object {
    $currentBase = $_.Matches[0].Groups[1].Value.Trim()
  }
}

$expectedBaseHttp = "http://${ip}:8000/api/v1"
$expectedBaseHttps = "https://${ip}:8443/api/v1"
$expectedBaseLocal = "https://127.0.0.1:8443/api/v1"

if ($currentBase -match '127\.0\.0\.1') {
  Write-Host "[WARN] .env uses 127.0.0.1 — wx.request will fail. Use start-mp-simulator.bat (LAN HTTP)." -ForegroundColor Yellow
} elseif ($currentBase -match '8443') {
  Write-Host "[WARN] .env uses HTTPS 8443 — may hit -202 cert error. Simulator: use start-mp-simulator.bat (HTTP)." -ForegroundColor Yellow
} elseif ($currentBase -ne $expectedBaseHttp -and $currentBase -ne $expectedBaseHttps) {
  Write-Host ""
  Write-Host "[WARN] .env.development API mismatch" -ForegroundColor Yellow
  Write-Host "  current : $currentBase"
  Write-Host "  expected: $expectedBaseHttps (real device) or $expectedBaseLocal (simulator)"
  $content = Get-Content $envFile -Raw -Encoding UTF8
  if ($content -match '8443') {
    $content = $content -replace 'VITE_API_BASE=.*', "VITE_API_BASE=https://${ip}:8443/api/v1"
    $content = $content -replace 'VITE_MEDIA_ORIGIN=.*', "VITE_MEDIA_ORIGIN=https://${ip}:8443"
    $content = $content -replace 'VITE_TRADE_API_BASE=.*', "VITE_TRADE_API_BASE=https://${ip}:8444/api/v1"
  } else {
    $content = $content -replace 'VITE_API_BASE=.*', "VITE_API_BASE=$expectedBaseHttp"
    $content = $content -replace 'VITE_MEDIA_ORIGIN=.*', "VITE_MEDIA_ORIGIN=http://${ip}:8000"
    $content = $content -replace 'VITE_TRADE_API_BASE=.*', "VITE_TRADE_API_BASE=http://${ip}:8081/api/v1"
  }
  Set-Content -Path $envFile -Value $content -Encoding UTF8 -NoNewline
  Write-Host "[FIX] Updated .env.development to LAN IP $ip" -ForegroundColor Green
  Write-Host "  Rebuild: build-mp-local.bat" -ForegroundColor Yellow
} else {
  Write-Host "[OK] .env.development matches LAN IP" -ForegroundColor Green
}

Write-Host "WeChat DevTools checklist:" -ForegroundColor Cyan
Write-Host "  [ ] Settings -> Proxy -> NO PROXY (fix ERR_TUNNEL_CONNECTION_FAILED)"
Write-Host "  [ ] Settings -> disable domain check AND TLS check"
Write-Host "  [ ] Simulator: LAN HTTP http://${ip}:8000 (start-mp-simulator.bat)"
Write-Host "  [ ] Real device: start-mp-real-device.bat (HTTPS, same Wi-Fi)"
Write-Host "  [ ] Rebuild: build-mp-local.bat then recompile"
Write-Host ""

exit 0
