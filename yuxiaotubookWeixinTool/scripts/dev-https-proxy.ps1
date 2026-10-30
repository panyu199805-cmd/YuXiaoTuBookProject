# Local HTTPS proxy for WeChat mini program (8443->8000, 8444->8081)
# Requires: Python API :8000, Java trade :8081 already running
# WeChat DevTools: disable domain check + disable TLS certificate check

$ErrorActionPreference = "Stop"

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

if (-not $ip) { $ip = "127.0.0.1" }

Write-Host "LAN IP: $ip" -ForegroundColor Cyan
Write-Host "HTTPS proxy:" -ForegroundColor Green
Write-Host "  https://${ip}:8443  ->  http://127.0.0.1:8000  (Python API)"
Write-Host "  https://${ip}:8444  ->  http://127.0.0.1:8081  (Java trade)"
Write-Host ""
Write-Host ".env.development (simulator):" -ForegroundColor Yellow
Write-Host "  VITE_API_BASE=https://127.0.0.1:8443/api/v1"
Write-Host "  VITE_MEDIA_ORIGIN=https://127.0.0.1:8443"
Write-Host "  VITE_TRADE_API_BASE=https://127.0.0.1:8444/api/v1"
Write-Host ""
Write-Host ".env.development (real device on phone):" -ForegroundColor Yellow
Write-Host "  VITE_API_BASE=https://${ip}:8443/api/v1"
Write-Host "  VITE_MEDIA_ORIGIN=https://${ip}:8443"
Write-Host "  VITE_TRADE_API_BASE=https://${ip}:8444/api/v1"
Write-Host ""

$port8443 = Get-NetTCPConnection -LocalPort 8443 -State Listen -ErrorAction SilentlyContinue
if ($port8443) {
  Write-Host "[OK] Port 8443 already in use (proxy running). Keep this window open or Ctrl+C to stop." -ForegroundColor Green
  Write-Host "  WeChat DevTools: Settings -> Proxy -> NO PROXY" -ForegroundColor Cyan
  try {
    while ($true) { Start-Sleep -Seconds 60 }
  } finally {
    exit 0
  }
}

$npx = if (Test-Path "C:\Program Files\nodejs\npx.cmd") {
  "C:\Program Files\nodejs\npx.cmd"
} else {
  (Get-Command npx.cmd -ErrorAction SilentlyContinue).Source
}
if (-not $npx) {
  Write-Host "[FAIL] npx.cmd not found. Install Node.js first." -ForegroundColor Red
  exit 1
}

$certDir = Join-Path (Split-Path $PSScriptRoot -Parent) ".local-certs"
$certFile = Join-Path $certDir "cert.pem"
$keyFile = Join-Path $certDir "key.pem"
$certArgs = @()
if ((Test-Path $certFile) -and (Test-Path $keyFile)) {
  Write-Host "[OK] Using mkcert certs from .local-certs" -ForegroundColor Green
  $certArgs = @("--cert", $certFile, "--key", $keyFile)
} else {
  Write-Host "[WARN] No mkcert certs. Real device may show ERR_CERT_AUTHORITY_INVALID." -ForegroundColor Yellow
  Write-Host "       Run setup-mkcert.bat OR use start-mp-simulator.bat on PC simulator." -ForegroundColor Yellow
}

$job1 = Start-Process -FilePath $npx -ArgumentList @(
  "--yes", "local-ssl-proxy", "--source", "8443", "--target", "8000", "--hostname", "0.0.0.0"
) + $certArgs -PassThru -WindowStyle Hidden
Start-Sleep -Seconds 2
$job2 = Start-Process -FilePath $npx -ArgumentList @(
  "--yes", "local-ssl-proxy", "--source", "8444", "--target", "8081", "--hostname", "0.0.0.0"
) + $certArgs -PassThru -WindowStyle Hidden

Write-Host "HTTPS proxy started (Ctrl+C to stop)..." -ForegroundColor Green
Write-Host "  PID api=$($job1.Id) trade=$($job2.Id)" -ForegroundColor DarkGray

try {
  while ($true) {
    if ($job1.HasExited -or $job2.HasExited) {
      Write-Host "[WARN] Proxy process exited. Check ports 8000 and 8081." -ForegroundColor Yellow
      break
    }
    Start-Sleep -Seconds 3
  }
} finally {
  if (-not $job1.HasExited) { Stop-Process -Id $job1.Id -Force -ErrorAction SilentlyContinue }
  if (-not $job2.HasExited) { Stop-Process -Id $job2.Id -Force -ErrorAction SilentlyContinue }
}
