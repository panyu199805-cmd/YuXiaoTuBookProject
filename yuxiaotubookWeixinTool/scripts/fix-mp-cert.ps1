# Fix WeChat MP ERR_CERT_AUTHORITY_INVALID (-202) for LAN HTTPS
$ErrorActionPreference = "SilentlyContinue"
$root = Split-Path $PSScriptRoot -Parent
$certDir = Join-Path $root ".local-certs"
$ip = (Get-NetIPAddress -AddressFamily IPv4 | Where-Object {
  $_.IPAddress -notlike '127.*' -and $_.IPAddress -notlike '169.254.*' -and
  $_.InterfaceAlias -notmatch 'Loopback|vEthernet|WSL|VMware|VirtualBox|Hyper-V'
} | Sort-Object @{ Expression = { if ($_.IPAddress -like '192.168.*') { 0 } else { 9 } } } |
  Select-Object -First 1).IPAddress

Write-Host "=== Fix WeChat -202 (ERR_CERT_AUTHORITY_INVALID) ===" -ForegroundColor Cyan
Write-Host "API uses https://${ip}:8443 with self-signed cert." -ForegroundColor Yellow
Write-Host ""

if ((Test-Path (Join-Path $certDir "cert.pem")) -and (Test-Path (Join-Path $certDir "key.pem"))) {
  Write-Host "[OK] mkcert files found in .local-certs" -ForegroundColor Green
  Write-Host "Restart dev-https-proxy.bat then recompile WeChat project." -ForegroundColor Cyan
} else {
  Write-Host "[INFO] No mkcert certs yet (.local-certs/cert.pem missing)" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "=== Fix A (fastest, PC simulator) ===" -ForegroundColor Green
Write-Host "In WeChat DevTools, open project then:"
Write-Host "  Top toolbar -> Details (详情) -> Local Settings (本地设置)"
Write-Host "  CHECK: Do not verify legal domain / TLS / HTTPS certificate"
Write-Host "       (不校验合法域名、web-view、TLS 版本以及 HTTPS 证书)"
Write-Host ""
Write-Host "NOTE: This is NOT the same as Settings(设置)->Proxy(代理)."
Write-Host "Clear cache -> Recompile after checking."
Write-Host ""
Write-Host "=== Fix B (stable, also for real device) ===" -ForegroundColor Green
Write-Host "1. Install mkcert: winget install FiloSottile.mkcert"
Write-Host "2. Run: setup-mkcert.bat"
Write-Host "3. Restart: dev-https-proxy.bat"
Write-Host "4. Recompile WeChat project"
Write-Host ""

$code = & curl.exe -k -s -o NUL -w "%{http_code}" "https://${ip}:8443/api/v1/site/config" 2>$null
Write-Host "curl -k https://${ip}:8443 -> HTTP $code (ignore cert)" -ForegroundColor DarkGray
