# Generate mkcert TLS certs for local HTTPS proxy (simulator + real device)
$ErrorActionPreference = "Stop"
Set-Location (Join-Path $PSScriptRoot "..")

$certDir = Join-Path $PWD ".local-certs"
$certFile = Join-Path $certDir "cert.pem"
$keyFile = Join-Path $certDir "key.pem"

$ip = (Get-NetIPAddress -AddressFamily IPv4 | Where-Object {
  $_.IPAddress -notlike '127.*' -and $_.IPAddress -notlike '169.254.*' -and
  $_.InterfaceAlias -notmatch 'Loopback|vEthernet|WSL|VMware|VirtualBox|Hyper-V'
} | Sort-Object @{
  Expression = { if ($_.IPAddress -like '192.168.*') { 0 } elseif ($_.IPAddress -like '10.*') { 1 } else { 9 } }
} | Select-Object -First 1).IPAddress
if (-not $ip) { $ip = "192.168.3.14" }

$mkcert = Get-Command mkcert -ErrorAction SilentlyContinue
if (-not $mkcert) {
  Write-Host "[FAIL] mkcert not installed." -ForegroundColor Red
  Write-Host "Install one of:" -ForegroundColor Yellow
  Write-Host "  winget install FiloSottile.mkcert"
  Write-Host "  choco install mkcert"
  Write-Host "  Or download: https://github.com/FiloSottile/mkcert/releases"
  Write-Host ""
  Write-Host "Without mkcert, real device gets ERR_CERT_AUTHORITY_INVALID."
  Write-Host "Use start-mp-simulator.bat on PC simulator instead."
  exit 1
}

Write-Host "Installing local CA (admin prompt may appear)..." -ForegroundColor Cyan
& mkcert -install

New-Item -ItemType Directory -Force -Path $certDir | Out-Null
Push-Location $certDir
& mkcert -cert-file cert.pem -key-file key.pem 127.0.0.1 localhost $ip
Pop-Location

$caRoot = & mkcert -CAROOT
Write-Host ""
Write-Host "[OK] Certs written to $certDir" -ForegroundColor Green
Write-Host "Restart dev-https-proxy.bat after this." -ForegroundColor Yellow
Write-Host ""
Write-Host "=== Real device (Android) ===" -ForegroundColor Cyan
Write-Host "Copy to phone and install as user CA certificate:"
Write-Host "  $caRoot\rootCA.pem"
Write-Host "Settings -> Security -> Encryption -> Install certificate -> CA certificate"
Write-Host ""
Write-Host "=== Real device (iOS) ===" -ForegroundColor Cyan
Write-Host "AirDrop/email rootCA.pem -> Install profile -> Settings -> General -> About -> Certificate Trust"
Write-Host ""
Write-Host "=== Or use PC simulator ===" -ForegroundColor Cyan
Write-Host "  .\start-mp-simulator.bat  (LAN IP + skip TLS in DevTools Details tab)"
Write-Host ""

exit 0
