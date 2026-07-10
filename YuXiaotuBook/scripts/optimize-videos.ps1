# 压缩站点视频素材（需安装 ffmpeg 并加入 PATH）
# 用法：.\optimize-videos.ps1
# 输出到同目录下的 optimized/ 子文件夹，确认无误后手动替换原文件并重新部署

$ErrorActionPreference = "Stop"
$RepoRoot = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent

$Sources = @(
    Join-Path $RepoRoot "网站素材\首页展览素材"
    Join-Path $RepoRoot "网站素材\图书页面素材"
)

$ffmpeg = Get-Command ffmpeg -ErrorAction SilentlyContinue
if (-not $ffmpeg) {
    Write-Host "未找到 ffmpeg。请先安装：https://ffmpeg.org/download.html" -ForegroundColor Yellow
    Write-Host "Windows 可用：winget install Gyan.FFmpeg"
    exit 1
}

function Optimize-Video($InputPath, $OutputPath) {
    $dir = Split-Path $OutputPath -Parent
    if (-not (Test-Path $dir)) { New-Item -ItemType Directory -Path $dir -Force | Out-Null }

    $args = @(
        "-y", "-i", $InputPath,
        "-c:v", "libx264", "-preset", "medium", "-crf", "24",
        "-vf", "scale='min(1280,iw)':-2",
        "-movflags", "+faststart",
        "-c:a", "aac", "-b:a", "128k",
        "-pix_fmt", "yuv420p",
        $OutputPath
    )
    Write-Host "压缩: $InputPath"
    & ffmpeg @args
    if ($LASTEXITCODE -ne 0) { throw "ffmpeg 失败: $InputPath" }
}

foreach ($srcDir in $Sources) {
    if (-not (Test-Path -LiteralPath $srcDir)) {
        Write-Host "跳过（目录不存在）: $srcDir"
        continue
    }
    $outDir = Join-Path $srcDir "optimized"
    Get-ChildItem -LiteralPath $srcDir -Filter *.mp4 | ForEach-Object {
        $outFile = Join-Path $outDir $_.Name
        Optimize-Video -InputPath $_.FullName -OutputPath $outFile
        $origMb = [math]::Round($_.Length / 1MB, 2)
        $newMb = [math]::Round((Get-Item -LiteralPath $outFile).Length / 1MB, 2)
        Write-Host "  $($_.Name): ${origMb}MB -> ${newMb}MB" -ForegroundColor Green
    }
}

Write-Host "`n完成。请将 optimized 目录中的文件替换原素材后执行部署。" -ForegroundColor Cyan
