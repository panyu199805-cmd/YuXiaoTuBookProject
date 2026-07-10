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

$expectedBase = "http://${ip}:8000/api/v1"
if ($currentBase -ne $expectedBase) {
  Write-Host ""
  Write-Host "[WARN] .env.development API mismatch" -ForegroundColor Yellow
  Write-Host "  current : $currentBase"
  Write-Host "  expected: $expectedBase"
  Write-Host "  Update .env.development then rebuild (build-mp-local.bat or dev-mp-weixin.bat)" -ForegroundColor Yellow
} else {
  Write-Host "[OK] .env.development matches LAN IP" -ForegroundColor Green
}

Write-Host ""
Write-Host "WeChat DevTools checklist:" -ForegroundColor Cyan
Write-Host "  [ ] Settings -> Security -> disable domain/TLS check"
Write-Host "  [ ] Allow WeChat DevTools through Windows Firewall (Private network)"
Write-Host "  [ ] Import: dist\dev\mp-weixin (watch) OR dist\build\mp-weixin (local build)"
Write-Host "  [ ] If still timeout: run scripts\dev-https-proxy.ps1 and switch .env to https://${ip}:8443"
Write-Host ""
