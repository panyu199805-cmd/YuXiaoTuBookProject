# Build Ubuntu 24.04 deployment tarball
# Usage: cd YuXiaotuBook\deploy ; .\pack-release.ps1

param(
    [switch]$RebuildFrontend
)

$ErrorActionPreference = "Stop"
$DeployDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RepoRoot = Resolve-Path (Join-Path $DeployDir "..\..")
$ReleaseDir = Join-Path $DeployDir "release"
$FrontendDir = Join-Path $RepoRoot "YuXiaotuBook\frontend"
$TradeDir = Join-Path $RepoRoot "yuxiaotu-trade-service"
$Stamp = Get-Date -Format "yyyyMMdd"
$ArchiveName = "yuxiaotu-book-ubuntu2404-$Stamp.tar.gz"
$ArchivePath = Join-Path $ReleaseDir $ArchiveName
$ManifestPath = Join-Path $ReleaseDir "MANIFEST-$Stamp.txt"

if (-not (Test-Path $ReleaseDir)) {
    New-Item -ItemType Directory -Path $ReleaseDir | Out-Null
}

$DistDir = Join-Path $FrontendDir "dist"
if ((Test-Path $DistDir) -and -not $RebuildFrontend) {
    Write-Host "[pack] use existing frontend/dist (pass -RebuildFrontend to rebuild)" -ForegroundColor Yellow
} else {
    Write-Host "[pack] building frontend..." -ForegroundColor Cyan
    Push-Location $FrontendDir
    if (-not (Test-Path "node_modules\vite")) { npm install }
    npm run build
    if ($LASTEXITCODE -ne 0) {
        Write-Host "[pack] fallback: npx vite build" -ForegroundColor Yellow
        npx vite build
        if ($LASTEXITCODE -ne 0) { throw "frontend build failed" }
    }
    Pop-Location
}

if (-not (Test-Path $DistDir)) {
    throw "frontend/dist not found"
}

Write-Host "[pack] staging files..." -ForegroundColor Cyan
$TempDir = Join-Path $env:TEMP "yuxiaotu-pack-$Stamp"
if (Test-Path $TempDir) { Remove-Item $TempDir -Recurse -Force }
New-Item -ItemType Directory -Path $TempDir | Out-Null

$CopyItems = @(
    "YuXiaotuBook\backend",
    "YuXiaotuBook\frontend",
    "YuXiaotuBook\deploy",
    "YuXiaotuBook\scripts"
)
foreach ($item in $CopyItems) {
    $src = Join-Path $RepoRoot $item
    $dst = Join-Path $TempDir $item
    robocopy $src $dst /E /XD node_modules .venv uploads __pycache__ target release /NFL /NDL /NJH /NJS /nc /ns /np | Out-Null
}
robocopy $TradeDir (Join-Path $TempDir "yuxiaotu-trade-service") /E /XD target .git /NFL /NDL /NJH /NJS /nc /ns /np | Out-Null

$ExhibitionSrc = $null
$BookReviewSrc = $null
$assetJson = & (Join-Path $RepoRoot 'YuXiaotuBook\backend\.venv\Scripts\python.exe') (Join-Path $RepoRoot 'YuXiaotuBook\scripts\get_asset_dirs.py') 2>$null
if (-not $assetJson) {
    $assetJson = & py -3 (Join-Path $RepoRoot 'YuXiaotuBook\scripts\get_asset_dirs.py') 2>$null
}
if ($assetJson) {
    $assetDirs = $assetJson | ConvertFrom-Json
    $ExhibitionSrc = $assetDirs.home_exhibition
    $BookReviewSrc = $assetDirs.book_review
}
$ExhibitionDst = Join-Path $TempDir "YuXiaotuBook\backend\uploads\homePage"
if (Test-Path -LiteralPath $ExhibitionSrc) {
    Write-Host "[pack] copying home exhibition videos..." -ForegroundColor Cyan
    New-Item -ItemType Directory -Path $ExhibitionDst -Force | Out-Null
    Copy-Item -Path (Join-Path $ExhibitionSrc "*.mp4") -Destination $ExhibitionDst -Force
} else {
    Write-Host "[pack] warning: exhibition source not found: $ExhibitionSrc" -ForegroundColor Yellow
}

$BookReviewDst = Join-Path $TempDir "YuXiaotuBook\backend\uploads\bookReview"
if ($BookReviewSrc -and (Test-Path -LiteralPath $BookReviewSrc)) {
    Write-Host "[pack] copying book review videos..." -ForegroundColor Cyan
    New-Item -ItemType Directory -Path $BookReviewDst -Force | Out-Null
    Copy-Item -Path (Join-Path $BookReviewSrc "*.mp4") -Destination $BookReviewDst -Force
} else {
    Write-Host "[pack] warning: book review source not found: $BookReviewSrc" -ForegroundColor Yellow
}

# Windows 打包的 .sh 默认 CRLF 且无 +x，Linux 上 ./xxx.sh 会报 command not found
Write-Host "[pack] normalizing shell scripts (LF + executable)..." -ForegroundColor Cyan
Get-ChildItem -Path $TempDir -Recurse -Filter *.sh -File | ForEach-Object {
    $bytes = [System.IO.File]::ReadAllBytes($_.FullName)
    $text = [System.Text.Encoding]::UTF8.GetString($bytes)
    $text = $text -replace "`r`n", "`n" -replace "`r", "`n"
    [System.IO.File]::WriteAllText($_.FullName, $text, [System.Text.UTF8Encoding]::new($false))
}

Write-Host "[pack] creating $ArchiveName ..." -ForegroundColor Cyan
if (Test-Path $ArchivePath) { Remove-Item $ArchivePath -Force }
tar -czf $ArchivePath -C $TempDir YuXiaotuBook yuxiaotu-trade-service
Remove-Item $TempDir -Recurse -Force

@(
    "YuXiaoTuBook Ubuntu 24.04.4 deployment package"
    "Built: $(Get-Date -Format o)"
    "Archive: $ArchiveName"
    "Project root: /usr/local/projects/yuxiaotu"
    ""
    "1. Create dirs:"
    "  sudo mkdir -p /usr/local/projects/yuxiaotu/{app,data/uploads,data/mysql-backup,env,logs}"
    "  sudo mkdir -p /var/backups/yuxiaotu/mysql"
    ""
    "2. Extract:"
    "  sudo tar -xzf $ArchiveName -C /usr/local/projects/yuxiaotu/app"
    ""
    "2b. Fix shell scripts (if ./install-all.sh says command not found):"
    "  bash /usr/local/projects/yuxiaotu/app/YuXiaotuBook/deploy/scripts/fix-shell-scripts.sh"
    ""
    "3. Install env:"
    "  cd /usr/local/projects/yuxiaotu/app/YuXiaotuBook/deploy/ubuntu2404"
    "  sudo MYSQL_PASSWORD=your_password ./install-all.sh"
    ""
    "4. Setup dirs and .env:"
    "  cd /usr/local/projects/yuxiaotu/app/YuXiaotuBook/deploy"
    "  ./scripts/setup-server-dirs.sh"
    "  nano /usr/local/projects/yuxiaotu/env/.env"
    ""
    "5. Deploy:"
    "  ./deploy.sh"
) | Set-Content -Path $ManifestPath -Encoding UTF8

$sizeMb = [math]::Round((Get-Item $ArchivePath).Length / 1MB, 2)
Write-Host ""
Write-Host "[pack] done" -ForegroundColor Green
Write-Host "  archive: $ArchivePath ($sizeMb MB)"
Write-Host "  manifest: $ManifestPath"
