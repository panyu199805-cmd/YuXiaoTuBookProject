# Clear stale Windows proxy registry left by Clash (ProxyEnable=0 but ProxyServer still set).
# Safe: only runs when system proxy is already disabled.
param([switch]$Force)

$ErrorActionPreference = "Stop"
$path = 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Internet Settings'

$ie = Get-ItemProperty -Path $path
if ($ie.ProxyEnable -eq 1) {
  Write-Host "[SKIP] System proxy is ON. Turn it off in Windows Settings first." -ForegroundColor Yellow
  exit 1
}

if (-not $ie.ProxyServer) {
  Write-Host "[OK] No stale ProxyServer in registry." -ForegroundColor Green
  exit 0
}

Write-Host "Found stale proxy registry (ProxyEnable=0 but ProxyServer=$($ie.ProxyServer))" -ForegroundColor Yellow
Write-Host "WeChat cronet may still try this address -> ERR_TUNNEL_CONNECTION_FAILED (-111)" -ForegroundColor Yellow

if (-not $Force) {
  $ans = Read-Host "Clear ProxyServer and AutoConfigURL? [y/N]"
  if ($ans -notmatch '^[yY]') { exit 0 }
}

Remove-ItemProperty -Path $path -Name ProxyServer -ErrorAction SilentlyContinue
Remove-ItemProperty -Path $path -Name AutoConfigURL -ErrorAction SilentlyContinue
Write-Host "[OK] Cleared stale proxy registry keys." -ForegroundColor Green
Write-Host "Next: quit WeChat DevTools completely, run pause-clash-for-wechat.bat if Clash is on, reopen DevTools." -ForegroundColor Cyan
