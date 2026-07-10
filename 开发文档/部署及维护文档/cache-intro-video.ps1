$RepoRoot = Resolve-Path (Join-Path $PSScriptRoot '..\..')
$ReleaseDir = Join-Path $RepoRoot 'YuXiaotuBook\deploy\release'
$Target = Join-Path $ReleaseDir 'yuxiaotu-intro.mp4'

$source = Get-ChildItem -Path $RepoRoot -Recurse -Filter '*.mp4' -ErrorAction SilentlyContinue |
    Where-Object { $_.Length -gt 50MB } |
    Sort-Object Length -Descending |
    Select-Object -First 1

if (-not $source) {
    Write-Error 'No intro mp4 (>50MB) found under repo root'
    exit 1
}

New-Item -ItemType Directory -Path $ReleaseDir -Force | Out-Null
if ((Test-Path -LiteralPath $Target) -and ((Get-Item -LiteralPath $Target).Length -eq $source.Length)) {
    Write-Output "Already cached: $Target"
    exit 0
}

Write-Output ("Copying {0} -> {1}" -f $source.FullName, $Target)
Copy-Item -LiteralPath $source.FullName -Destination $Target -Force
Write-Output 'Done'
