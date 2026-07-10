$dir = Join-Path $PSScriptRoot "..\src\static"
$logo = Join-Path $dir "logo.png"
if (-not (Test-Path $logo)) { Write-Error "logo.png not found"; exit 1 }
@(
  "tab-home.png", "tab-home-active.png",
  "tab-books.png", "tab-books-active.png",
  "tab-daily.png", "tab-daily-active.png",
  "tab-user.png", "tab-user-active.png"
) | ForEach-Object {
  Copy-Item -Force $logo (Join-Path $dir $_)
}
Write-Host "Tab icons updated from logo.png"
