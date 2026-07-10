# Local WeChat preview build (uses .env.development API, not production)
$ErrorActionPreference = "Stop"
Set-Location (Join-Path $PSScriptRoot "..")

$envFile = Join-Path $PWD ".env.development"
if (Test-Path $envFile) {
  Get-Content $envFile | ForEach-Object {
    if ($_ -match '^\s*VITE_API_BASE=(.+)$') { $env:VITE_API_BASE = $matches[1].Trim() }
    if ($_ -match '^\s*VITE_MEDIA_ORIGIN=(.+)$') { $env:VITE_MEDIA_ORIGIN = $matches[1].Trim() }
    if ($_ -match '^\s*VITE_TRADE_API_BASE=(.+)$') { $env:VITE_TRADE_API_BASE = $matches[1].Trim() }
  }
}

if (-not $env:VITE_API_BASE) {
  $env:VITE_API_BASE = "http://192.168.3.14:8000/api/v1"
  $env:VITE_MEDIA_ORIGIN = "http://192.168.3.14:8000"
  $env:VITE_TRADE_API_BASE = "http://192.168.3.14:8081/api/v1"
}

Write-Host "Building mp-weixin with API: $env:VITE_API_BASE" -ForegroundColor Cyan
npx uni build -p mp-weixin

Write-Host ""
Write-Host "Import in WeChat DevTools:" -ForegroundColor Green
Write-Host "  $(Join-Path $PWD 'dist\build\mp-weixin')"
