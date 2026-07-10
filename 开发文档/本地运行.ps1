# 宇小兔读书 — 本地开发一键启动
# 用法：.\本地运行.ps1

$ErrorActionPreference = 'Stop'
$RepoRoot = Resolve-Path (Join-Path $PSScriptRoot '..\..')
$DeployDir = Join-Path $RepoRoot 'YuXiaotuBook\deploy'
$BackendDir = Join-Path $RepoRoot 'YuXiaotuBook\backend'
$FrontendDir = Join-Path $RepoRoot 'YuXiaotuBook\frontend'
$ScriptsDir = Join-Path $RepoRoot 'YuXiaotuBook\scripts'

function Wait-DockerReady {
    param([int]$TimeoutSec = 120)
    $deadline = (Get-Date).AddSeconds($TimeoutSec)
    while ((Get-Date) -lt $deadline) {
        docker info *> $null
        if ($LASTEXITCODE -eq 0) { return $true }
        Start-Sleep -Seconds 3
    }
    return $false
}

function Test-ApiHealth {
    try {
        $r = Invoke-WebRequest -Uri 'http://127.0.0.1:8000/api/health' -UseBasicParsing -TimeoutSec 5
        return $r.StatusCode -eq 200
    } catch { return $false }
}

Write-Host '[1/6] 检查 Docker...' -ForegroundColor Cyan
docker info *> $null
if ($LASTEXITCODE -ne 0) {
    $dockerExe = 'C:\Program Files\Docker\Docker\Docker Desktop.exe'
    if (Test-Path $dockerExe) {
        Write-Host '正在启动 Docker Desktop，请稍候...' -ForegroundColor Yellow
        Start-Process $dockerExe | Out-Null
        if (-not (Wait-DockerReady)) {
            throw 'Docker 未就绪，请手动打开 Docker Desktop 后重试'
        }
    } else {
        throw '未安装 Docker Desktop，请先安装并启动'
    }
}

Write-Host '[2/6] 启动 MySQL + API + Trade...' -ForegroundColor Cyan
docker volume create deploy_mysql_data 2>$null | Out-Null
Push-Location $DeployDir
docker compose up -d mysql api trade
Pop-Location

Write-Host '[3/6] 等待 API 就绪...' -ForegroundColor Cyan
$ready = $false
for ($i = 0; $i -lt 40; $i++) {
    if (Test-ApiHealth) { $ready = $true; break }
    Start-Sleep -Seconds 3
}
if (-not $ready) { throw 'API 启动超时，请执行: docker logs YuXiaotuBook' }

Write-Host '[4/7] 同步首页展览与图书解读视频...' -ForegroundColor Cyan
$uploadsDir = Join-Path $BackendDir 'uploads'
New-Item -ItemType Directory -Path $uploadsDir -Force | Out-Null
$venvPython = Join-Path $BackendDir '.venv\Scripts\python.exe'
if (-not (Test-Path $venvPython)) {
    Push-Location $BackendDir
    py -3.8 -m venv .venv
    & .\.venv\Scripts\pip.exe install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
    Pop-Location
}
& $venvPython (Join-Path $ScriptsDir 'sync_home_exhibition_videos.py') --files-only 2>&1 | Out-Null
& $venvPython (Join-Path $ScriptsDir 'sync_book_review_videos.py') --files-only 2>&1 | Out-Null

Write-Host '[5/7] 初始化数据库（seed）...' -ForegroundColor Cyan
$envFile = Join-Path $BackendDir '.env'
$envExample = Join-Path $BackendDir '.env.example'
if (-not (Test-Path $envFile) -and (Test-Path $envExample)) {
    Copy-Item $envExample $envFile
}
& $venvPython (Join-Path $ScriptsDir 'seed.py') 2>&1 | Out-Null
& $venvPython (Join-Path $ScriptsDir 'fix_site_bg_video.py') 2>$null
& $venvPython (Join-Path $ScriptsDir 'update_book_videos.py') 2>$null

Write-Host '[6/7] 启动前端 dev server...' -ForegroundColor Cyan
Push-Location $FrontendDir
if (-not (Test-Path 'node_modules\vite')) { npm install }
Write-Host ''
Write-Host '========================================' -ForegroundColor Green
Write-Host ' 本地开发已就绪' -ForegroundColor Green
Write-Host ' 前台:     http://localhost:5188/' -ForegroundColor Green
Write-Host ' 管理后台: http://localhost:5188/admin/login' -ForegroundColor Green
Write-Host ' API 文档: http://127.0.0.1:8000/docs' -ForegroundColor Green
Write-Host ' 管理员:   admin / admin123456' -ForegroundColor Green
Write-Host '========================================' -ForegroundColor Green
Write-Host '按 Ctrl+C 停止前端；Docker 服务仍在后台运行' -ForegroundColor Yellow
npm run dev
