# Delegate to scripts/setup-mkcert.ps1
$ErrorActionPreference = "Stop"
& (Join-Path $PSScriptRoot "scripts\setup-mkcert.ps1")
