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
  $env:VITE_API_BASE = "http://127.0.0.1:8000/api/v1"
  $env:VITE_MEDIA_ORIGIN = "http://127.0.0.1:8000"
  $env:VITE_TRADE_API_BASE = "http://127.0.0.1:8081/api/v1"
}

Write-Host "Building mp-weixin with API: $env:VITE_API_BASE" -ForegroundColor Cyan
npx uni build -p mp-weixin --mode development

$buildRoot = Join-Path $PWD "dist\build\mp-weixin"
$devRoot = Join-Path $PWD "dist\dev\mp-weixin"
if (Test-Path $buildRoot) {
  if (Test-Path $devRoot) {
    Remove-Item $devRoot -Recurse -Force
  }
  New-Item -ItemType Directory -Force -Path (Split-Path $devRoot -Parent) | Out-Null
  Copy-Item $buildRoot $devRoot -Recurse -Force
  Write-Host "Synced dist/build -> dist/dev (WeChat miniprogramRoot uses dist/dev)" -ForegroundColor Green
}

$staticSrc = Join-Path $PWD "src\static"
foreach ($target in @("dist\build\mp-weixin\static", "dist\dev\mp-weixin\static")) {
  $targetPath = Join-Path $PWD $target
  if (Test-Path (Split-Path $targetPath -Parent)) {
    New-Item -ItemType Directory -Force -Path $targetPath | Out-Null
    Copy-Item (Join-Path $staticSrc "tab-*.png") $targetPath -Force -ErrorAction SilentlyContinue
  }
}
Write-Host "Synced tab icons to build/dev output" -ForegroundColor Green

Write-Host ""
Write-Host "Built API (verify in WeChat after recompile):" -ForegroundColor Cyan
$builtEnv = Join-Path $devRoot "config\env.js"
if (Test-Path $builtEnv) { Get-Content $builtEnv }
Write-Host ""
Write-Host "WeChat DevTools MUST:" -ForegroundColor Yellow
Write-Host "  1. Import THIS folder as project: $PWD"
Write-Host "  2. Settings -> Proxy -> NO PROXY"
Write-Host "  3. Clear ALL cache -> Recompile"
Write-Host "  4. Home page yellow bar should show 127.0.0.1 (simulator)"
Write-Host ""
Write-Host "Import in WeChat DevTools (project root or dist/build/mp-weixin):" -ForegroundColor Green
Write-Host "  $(Join-Path $PWD 'dist\build\mp-weixin')"
