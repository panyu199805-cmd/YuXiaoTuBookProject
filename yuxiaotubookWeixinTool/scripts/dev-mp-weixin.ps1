# WeChat mini program dev build (uni-app watch mode)
$ErrorActionPreference = "Stop"
Set-Location (Join-Path $PSScriptRoot "..")

& (Join-Path $PSScriptRoot "check-mp-api.ps1")
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host "=== YuXiaoTu WeChat Mini Program Dev Build ===" -ForegroundColor Cyan
Write-Host ""
Write-Host "Close WeChat DevTools for this project, then press Enter..." -ForegroundColor Yellow
Read-Host | Out-Null

$outDir = Join-Path $PWD "dist\dev\mp-weixin"
if (Test-Path $outDir) {
  try {
    Remove-Item -Recurse -Force $outDir
    Write-Host "Cleaned old build output." -ForegroundColor Green
  } catch {
    Write-Host "Cannot delete: $outDir" -ForegroundColor Red
    Write-Host "Close WeChat DevTools completely and retry." -ForegroundColor Red
    exit 1
  }
}

Write-Host "Building mp-weixin (dev watch)..." -ForegroundColor Cyan
npx uni -p mp-weixin

Write-Host ""
Write-Host "=== Build started (watch mode) ===" -ForegroundColor Green
Write-Host "Import this folder in WeChat DevTools:" -ForegroundColor Yellow
Write-Host "  $outDir" -ForegroundColor White
Write-Host ""
Write-Host "Checklist:" -ForegroundColor Yellow
Write-Host '  1. Import dist/dev/mp-weixin (NOT src, NOT dist/build)'
Write-Host '  2. Settings -> disable urlCheck / allow local domain'
Write-Host '  3. If "Page has not been registered": Tools -> Clear cache -> Recompile'
Write-Host '  4. Keep this terminal running; do not enable auto-compile in DevTools'
Write-Host ""
