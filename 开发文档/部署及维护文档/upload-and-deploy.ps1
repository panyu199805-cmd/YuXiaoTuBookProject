# YuXiaoTu Book - pack, upload, deploy to Tencent Cloud
# Usage:
#   cd deploy docs folder
#   .\upload-and-deploy.ps1 -RebuildFrontend

param(
    [switch]$UploadOnly,
    [switch]$DeployOnly,
    [switch]$RebuildFrontend,
    [switch]$FixHomeVideo,
    [switch]$FixBookVideo
)

$ErrorActionPreference = 'Stop'
$Here = Split-Path -Parent $MyInvocation.MyCommand.Path
$RepoRoot = Resolve-Path (Join-Path $Here '..\..')
$DeployDir = Join-Path $RepoRoot 'YuXiaotuBook\deploy'
$EnvFile = Join-Path $Here 'server-deploy.env'
$DeployScript = Join-Path $Here 'server-deploy.sh'

function Read-EnvValue {
    param([string]$Key)
    if (-not (Test-Path $EnvFile)) { return $null }
    foreach ($line in Get-Content -LiteralPath $EnvFile -Encoding UTF8) {
        if ($line -notmatch '=') { continue }
        $name = $line.Split('=', 2)[0].Trim()
        if ($name -ne $Key) { continue }
        return $line.Split('=', 2)[1].Trim().Trim([char]34)
    }
    return $null
}

function Get-PythonExe {
    $venvPy = Join-Path $RepoRoot 'YuXiaotuBook\backend\.venv\Scripts\python.exe'
    if (Test-Path -LiteralPath $venvPy) { return $venvPy }
    return 'py'
}

function Get-AssetDirsFromPython {
    $scriptsDir = Join-Path $RepoRoot 'YuXiaotuBook\scripts'
    $getter = Join-Path $scriptsDir 'get_asset_dirs.py'
    if (-not (Test-Path -LiteralPath $getter)) { return $null }
    $output = & (Get-PythonExe) $getter 2>$null
    if ($LASTEXITCODE -ne 0 -or -not $output) { return $null }
    try {
        return ($output | ConvertFrom-Json)
    } catch {
        return $null
    }
}

function Resolve-HomeExhibitionDir {
    $fromEnv = Read-EnvValue -Key 'HOME_EXHIBITION_DIR'
    if ($fromEnv -and (Test-Path -LiteralPath $fromEnv)) {
        return (Resolve-Path -LiteralPath $fromEnv).Path
    }
    $dirs = Get-AssetDirsFromPython
    if ($dirs -and $dirs.home_exhibition -and (Test-Path -LiteralPath $dirs.home_exhibition)) {
        return (Resolve-Path -LiteralPath $dirs.home_exhibition).Path
    }
    $cached = Join-Path $RepoRoot 'YuXiaotuBook\backend\uploads\homePage'
    if ((Test-Path -LiteralPath $cached) -and (Get-ChildItem -LiteralPath $cached -Filter '*.mp4' -File -ErrorAction SilentlyContinue)) {
        return (Resolve-Path -LiteralPath $cached).Path
    }
    return $null
}

function Optimize-LocalVideos {
    param([string[]]$Dirs)
    $optimizer = Join-Path $RepoRoot 'YuXiaotuBook\scripts\optimize_all_videos.py'
    if (-not (Test-Path -LiteralPath $optimizer)) { return }
    Write-Host 'Optimizing videos for web playback (720p + faststart)...' -ForegroundColor Cyan
    $py = Get-PythonExe
    if ($Dirs -and $Dirs.Count -gt 0) {
        & $py $optimizer @Dirs
    } else {
        & $py $optimizer
    }
    if ($LASTEXITCODE -ne 0) {
        Write-Host 'Video optimize skipped or partial (install ffmpeg or: py -3 -m pip install imageio-ffmpeg)' -ForegroundColor Yellow
    }
}

function Upload-HomeExhibitionVideos {
    param(
        [string]$TargetHost,
        [switch]$Required
    )
    $srcDir = Resolve-HomeExhibitionDir
    if (-not $srcDir) {
        if ($Required) {
            throw 'Home exhibition videos not found. Set HOME_EXHIBITION_DIR or run sync_home_exhibition_videos.py first.'
        }
        Write-Host 'Home exhibition videos not found, skipped.' -ForegroundColor Yellow
        return $false
    }
    Optimize-LocalVideos -Dirs @($srcDir)
    $mp4s = Get-ChildItem -LiteralPath $srcDir -Filter '*.mp4' -File
    if (-not $mp4s) {
        if ($Required) { throw "No mp4 in: $srcDir" }
        Write-Host 'No mp4 in exhibition dir, skipped.' -ForegroundColor Yellow
        return $false
    }
    $totalMb = [math]::Round(($mp4s | Measure-Object -Property Length -Sum).Sum / 1MB, 1)
    Write-Host ("Uploading {0} exhibition videos ({1} MB) from: {2}" -f $mp4s.Count, $totalMb, $srcDir) -ForegroundColor Cyan
    $opts = Get-SshOpts
    & ssh.exe -T @opts $TargetHost 'mkdir -p ~/homePage'
    Assert-LastExitCode -Step 'ssh mkdir homePage'
    foreach ($mp4 in $mp4s) {
        Invoke-ScpUpload -LocalPath $mp4.FullName -RemotePath ([string]::Concat($TargetHost, ':~/homePage/', $mp4.Name))
    }
    return $true
}

function Resolve-BookReviewDir {
    $fromEnv = Read-EnvValue -Key 'BOOK_REVIEW_DIR'
    if ($fromEnv -and (Test-Path -LiteralPath $fromEnv)) {
        return (Resolve-Path -LiteralPath $fromEnv).Path
    }
    $dirs = Get-AssetDirsFromPython
    if ($dirs -and $dirs.book_review -and (Test-Path -LiteralPath $dirs.book_review)) {
        return (Resolve-Path -LiteralPath $dirs.book_review).Path
    }
    $cached = Join-Path $RepoRoot 'YuXiaotuBook\backend\uploads\bookReview'
    if ((Test-Path -LiteralPath $cached) -and (Get-ChildItem -LiteralPath $cached -Filter '*.mp4' -File -ErrorAction SilentlyContinue)) {
        return (Resolve-Path -LiteralPath $cached).Path
    }
    return $null
}

function Upload-BookReviewVideos {
    param(
        [string]$TargetHost,
        [switch]$Required
    )
    $srcDir = Resolve-BookReviewDir
    if (-not $srcDir) {
        if ($Required) {
            throw 'Book review videos not found. Set BOOK_REVIEW_DIR or run sync_book_review_videos.py first.'
        }
        Write-Host 'Book review videos not found, skipped.' -ForegroundColor Yellow
        return $false
    }
    Optimize-LocalVideos -Dirs @($srcDir)
    $mp4s = Get-ChildItem -LiteralPath $srcDir -Filter '*.mp4' -File
    if (-not $mp4s) {
        if ($Required) { throw "No mp4 in: $srcDir" }
        Write-Host 'No mp4 in book review dir, skipped.' -ForegroundColor Yellow
        return $false
    }
    $totalMb = [math]::Round(($mp4s | Measure-Object -Property Length -Sum).Sum / 1MB, 1)
    Write-Host ("Uploading {0} book review videos ({1} MB) from: {2}" -f $mp4s.Count, $totalMb, $srcDir) -ForegroundColor Cyan
    $opts = Get-SshOpts
    & ssh.exe -T @opts $TargetHost 'mkdir -p ~/bookReview'
    Assert-LastExitCode -Step 'ssh mkdir bookReview'
    foreach ($mp4 in $mp4s) {
        Invoke-ScpUpload -LocalPath $mp4.FullName -RemotePath ([string]::Concat($TargetHost, ':~/bookReview/', $mp4.Name))
    }
    return $true
}

function Get-SshFailureHint {
    param([string]$Step)
    $key = $Script:SshKeyPath
    $lines = @(
        ($Step + ' failed (exit code 255).'),
        'SSH login failed. Try:',
        '  1) Reset ubuntu password in Tencent Cloud console',
        '  2) Run setup-ssh-key.ps1 to bind public key',
        '  3) Use user ubuntu (not root)'
    )
    if ($key) {
        $lines += ('  Current key: ' + $key)
    }
    return ($lines -join [Environment]::NewLine)
}

function Assert-LastExitCode {
    param(
        [string]$Step,
        [string]$Hint = ''
    )
    if ($LASTEXITCODE -ne 0) {
        if ($Hint) {
            Write-Host $Hint -ForegroundColor Yellow
        }
        if ($LASTEXITCODE -eq 255) {
            throw (Get-SshFailureHint -Step $Step)
        }
        throw ($Step + ' failed (exit code ' + $LASTEXITCODE + ')')
    }
}

function Get-SshBaseOpts {
    $opts = @(
        '-o', 'ServerAliveInterval=30',
        '-o', 'ServerAliveCountMax=120',
        '-o', 'ConnectTimeout=15',
        '-o', 'RequestTTY=no',
        '-o', 'StrictHostKeyChecking=accept-new',
        '-o', 'PreferredAuthentications=publickey,password',
        '-o', 'PubkeyAuthentication=yes'
    )
    $keyPath = $Script:SshKeyPath
    if ($keyPath -and (Test-Path -LiteralPath $keyPath)) {
        $opts += @('-i', (Resolve-Path -LiteralPath $keyPath).Path)
    }
    return $opts
}

function Get-SshControlPath {
    if (-not $Script:SshControlPath -and $Script:RemoteHostForSsh) {
        $safe = ($Script:RemoteHostForSsh -replace '[^a-zA-Z0-9._-]', '_')
        $Script:SshControlPath = Join-Path $env:TEMP ("yuxiaotu-ssh-$safe.ctrl")
    }
    return $Script:SshControlPath
}

function Test-SshMultiplexActive {
    param([string]$TargetHost)
    $controlPath = Get-SshControlPath
    if (-not $controlPath -or -not (Test-Path -LiteralPath $controlPath)) {
        return $false
    }
    $checkOpts = Get-SshOpts + @('-O', 'check', '-o', 'BatchMode=yes')
    & ssh.exe @checkOpts $TargetHost 2>$null
    return ($LASTEXITCODE -eq 0)
}

function Initialize-SshMultiplex {
    param([string]$TargetHost)
    $Script:RemoteHostForSsh = $TargetHost

    if (-not $Script:UseSshMultiplex) {
        Write-Host 'Windows 部署模式：不使用 SSH 连接复用（避免 scp 异常跳转 shell）' -ForegroundColor Yellow
        Write-Host '每次 scp/ssh 可能提示输入密码；运行 setup-ssh-key.ps1 配置公钥后可免密' -ForegroundColor Yellow
        return
    }

    $null = Get-SshControlPath
    if (Test-SshMultiplexActive -TargetHost $TargetHost) {
        Write-Host 'SSH 连接已复用（免重复输入密码）' -ForegroundColor Green
        return
    }

    Write-Host 'SSH 复用已启用：首次 scp 上传时会提示输入密码一次，后续自动复用' -ForegroundColor Cyan
}

function Ensure-SshControlMaster {
    param(
        [string]$TargetHost,
        [switch]$Reconnect
    )
    if (Test-SshMultiplexActive -TargetHost $TargetHost) { return }
    if ($Reconnect) {
        Write-Host 'SSH 连接已断开，下一步操作会再次提示输入密码...' -ForegroundColor Yellow
    }
}

function Stop-SshControlMaster {
    param([string]$TargetHost)
    if (-not $Script:UseSshMultiplex) { return }
    $controlPath = Get-SshControlPath
    if (-not $controlPath) { return }
    $opts = Get-SshBaseOpts + @('-o', "ControlPath=$controlPath", '-o', 'ControlMaster=auto', '-O', 'exit', '-o', 'BatchMode=yes')
    & ssh.exe @opts $TargetHost 2>$null
    $Script:SshControlPath = $null
}

function Get-SshOpts {
    $opts = Get-SshBaseOpts
    if (-not $Script:UseSshMultiplex) {
        return $opts
    }
    $controlPath = Get-SshControlPath
    if ($controlPath) {
        $opts += @(
            '-o', "ControlPath=$controlPath",
            '-o', 'ControlMaster=auto',
            '-o', 'ControlPersist=900'
        )
    }
    return $opts
}

function Resolve-SshKeyPath {
    $fromEnv = Read-EnvValue -Key 'SSH_KEY_PATH'
    if ($fromEnv -and (Test-Path -LiteralPath $fromEnv)) {
        return (Resolve-Path -LiteralPath $fromEnv).Path
    }
    foreach ($candidate in @(
        (Join-Path $env:USERPROFILE '.ssh\id_ed25519'),
        (Join-Path $env:USERPROFILE '.ssh\id_rsa')
    )) {
        if (Test-Path -LiteralPath $candidate) {
            return (Resolve-Path -LiteralPath $candidate).Path
        }
    }
    return $null
}

function Normalize-UnixTextFile {
    param([string]$SourcePath)
    if (-not (Test-Path $SourcePath)) { return $SourcePath }
    $bytes = [System.IO.File]::ReadAllBytes($SourcePath)
    $text = [System.Text.Encoding]::UTF8.GetString($bytes)
    $text = $text.Replace([char]13 + [string][char]10, [string][char]10)
    $text = $text.Replace([string][char]13, [string][char]10)
    $tempName = 'yuxiaotu-upload-' + [IO.Path]::GetFileName($SourcePath)
    $tempPath = Join-Path $env:TEMP $tempName
    [System.IO.File]::WriteAllText($tempPath, $text, [System.Text.UTF8Encoding]::new($false))
    return $tempPath
}

function Invoke-ScpUpload {
    param(
        [string]$LocalPath,
        [string]$RemotePath
    )
    $uploadPath = $LocalPath
    $tempPath = $null
    if ($LocalPath -match '\.(sh|env)$') {
        $tempPath = Normalize-UnixTextFile -SourcePath $LocalPath
        $uploadPath = $tempPath
    }
    try {
        $opts = Get-SshOpts
        if (Test-Path -LiteralPath $LocalPath) {
            $sizeMb = [math]::Round((Get-Item -LiteralPath $LocalPath).Length / 1MB, 1)
            Write-Host ("Uploading ${sizeMb} MB -> $RemotePath") -ForegroundColor Cyan
        }
        & scp.exe @opts $uploadPath $RemotePath
        Assert-LastExitCode -Step ('scp ' + $LocalPath)
    } finally {
        if ($tempPath -and (Test-Path $tempPath)) {
            Remove-Item $tempPath -Force -ErrorAction SilentlyContinue
        }
    }
}

function Invoke-SshCommand {
    param(
        [string]$TargetHost,
        [string]$Command
    )
    $opts = Get-SshOpts
    & ssh.exe -T @opts $TargetHost $Command
    Assert-LastExitCode -Step ('ssh ' + $TargetHost)
}

function Upload-DeployPatches {
    param([string]$TargetHost)
    $opts = Get-SshOpts
    & ssh.exe -T @opts $TargetHost 'mkdir -p ~/patches'
    Assert-LastExitCode -Step 'ssh mkdir patches'
    Invoke-ScpUpload -LocalPath $DeployScript -RemotePath ([string]::Concat($TargetHost, ':~/server-deploy.sh'))
    Invoke-ScpUpload -LocalPath $EnvFile -RemotePath ([string]::Concat($TargetHost, ':~/server-deploy.env'))
    $patchFiles = @(
        @{ Local = Join-Path $DeployDir 'ubuntu2404\01-install-docker.sh'; Remote = '01-install-docker.sh' },
        @{ Local = Join-Path $DeployDir 'ubuntu2404\install-all.sh'; Remote = 'install-all.sh' },
        @{ Local = Join-Path $DeployDir 'deploy.sh'; Remote = 'deploy.sh' }
    )
    foreach ($pf in $patchFiles) {
        if (Test-Path $pf.Local) {
            Invoke-ScpUpload -LocalPath $pf.Local -RemotePath ([string]::Concat($TargetHost, ':~/patches/', $pf.Remote))
        }
    }
    $scriptPatches = @(
        'fix_site_bg_video.py',
        'site_video_asset.py',
        'sync_home_exhibition_videos.py',
        'book_video_asset.py',
        'sync_book_review_videos.py',
        'update_book_videos.py'
    )
    foreach ($name in $scriptPatches) {
        $local = Join-Path $RepoRoot ('YuXiaotuBook\scripts\' + $name)
        if (Test-Path $local) {
            Invoke-ScpUpload -LocalPath $local -RemotePath ([string]::Concat($TargetHost, ':~/patches/', $name))
        }
    }
    $servicePatch = Join-Path $RepoRoot 'YuXiaotuBook\backend\app\services\home_page_video_service.py'
    if (Test-Path $servicePatch) {
        Invoke-ScpUpload -LocalPath $servicePatch -RemotePath ([string]::Concat($TargetHost, ':~/patches/home_page_video_service.py'))
    }
    $fixApiSh = Join-Path $Here 'fix-api-homepage.sh'
    if (Test-Path $fixApiSh) {
        Invoke-ScpUpload -LocalPath $fixApiSh -RemotePath ([string]::Concat($TargetHost, ':~/fix-api-homepage.sh'))
    }
}

function Build-RemoteDeployCommand {
    $parts = @(
        'mkdir -p ~/patches'
        'chmod +x ~/server-deploy.sh ~/patches/*.sh 2>/dev/null || true'
        'bash ~/server-deploy.sh 2>&1 | tee ~/server-deploy.log'
    )
    return ($parts -join '; ')
}

if (-not (Test-Path $EnvFile)) {
    Write-Host 'Missing server-deploy.env' -ForegroundColor Red
    exit 1
}

$ServerIp = Read-EnvValue -Key 'SERVER_IP'
if (-not $ServerIp) {
    Write-Host 'Set SERVER_IP in server-deploy.env' -ForegroundColor Red
    exit 1
}

$RemoteUser = Read-EnvValue -Key 'SERVER_USER'
if (-not $RemoteUser) { $RemoteUser = 'ubuntu' }

$Script:SshKeyPath = Resolve-SshKeyPath
$Script:SshControlPath = $null
$Script:RemoteHostForSsh = $null
# Windows OpenSSH 的 ControlMaster 与 scp 不兼容，会导致 getsockname failed 并误入交互 shell
$Script:UseSshMultiplex = $false
Get-ChildItem -LiteralPath $env:TEMP -Filter 'yuxiaotu-ssh-*.ctrl' -ErrorAction SilentlyContinue |
    Remove-Item -Force -Recurse -ErrorAction SilentlyContinue
if ($Script:SshKeyPath) {
    Write-Host ('SSH key: ' + $Script:SshKeyPath) -ForegroundColor Cyan
} else {
    Write-Host 'SSH key: not found (will use password). Run setup-ssh-key.ps1' -ForegroundColor Yellow
}

$RemoteHost = [string]::Concat($RemoteUser, '@', $ServerIp)
$RemoteHome = [string]::Concat($RemoteHost, ':~/')

$PrevEap = $ErrorActionPreference
$ErrorActionPreference = 'SilentlyContinue'
ssh-keygen -R $ServerIp 2>$null | Out-Null
ssh-keygen -R ('[' + $ServerIp + ']:22') 2>$null | Out-Null
$ErrorActionPreference = $PrevEap

Write-Host ('SSH user: ' + $RemoteUser + ' (Tencent Cloud default: ubuntu)') -ForegroundColor Cyan

try {
Initialize-SshMultiplex -TargetHost $RemoteHost

if ($DeployOnly) {
    Write-Host '[upload] DeployOnly: prepare release and upload...' -ForegroundColor Cyan
}

if ($FixHomeVideo) {
    Write-Host '[fix] Upload exhibition videos and patch site config...' -ForegroundColor Cyan
    $fixSh = Join-Path $Here 'fix-home-video.sh'
    Upload-HomeExhibitionVideos -TargetHost $RemoteHost -Required | Out-Null
    $opts = Get-SshOpts
    & ssh.exe -T @opts $RemoteHost 'mkdir -p ~/patches'
    Assert-LastExitCode -Step 'ssh mkdir patches'
    Invoke-ScpUpload -LocalPath $fixSh -RemotePath ([string]::Concat($RemoteHost, ':~/fix-home-video.sh'))
    $prepSh = Join-Path $RepoRoot 'YuXiaotuBook\deploy\scripts\prepare-web-videos.sh'
    if (Test-Path -LiteralPath $prepSh) {
        Invoke-ScpUpload -LocalPath $prepSh -RemotePath ([string]::Concat($RemoteHost, ':~/prepare-web-videos.sh'))
    }
    foreach ($name in @('fix_site_bg_video.py', 'site_video_asset.py', 'sync_home_exhibition_videos.py', 'video_optimize.py')) {
        $local = Join-Path $RepoRoot ('YuXiaotuBook\scripts\' + $name)
        if (Test-Path $local) {
            Invoke-ScpUpload -LocalPath $local -RemotePath ([string]::Concat($RemoteHost, ':~/patches/', $name))
        }
    }
    $remoteFix = 'sed -i ''s/\r$//'' ~/fix-home-video.sh; chmod +x ~/fix-home-video.sh; bash ~/fix-home-video.sh'
    Invoke-SshCommand -TargetHost $RemoteHost -Command $remoteFix
    Write-Host 'Home video fix done. Refresh http://www.yuxiaotubook.com/ (Ctrl+F5)' -ForegroundColor Green
    exit 0
}

if ($FixBookVideo) {
    Write-Host '[fix] Upload book review videos and patch book_video...' -ForegroundColor Cyan
    $fixSh = Join-Path $Here 'fix-book-video.sh'
    Upload-BookReviewVideos -TargetHost $RemoteHost -Required | Out-Null
    $opts = Get-SshOpts
    & ssh.exe -T @opts $RemoteHost 'mkdir -p ~/patches'
    Assert-LastExitCode -Step 'ssh mkdir patches'
    Invoke-ScpUpload -LocalPath $fixSh -RemotePath ([string]::Concat($RemoteHost, ':~/fix-book-video.sh'))
    $prepSh = Join-Path $RepoRoot 'YuXiaotuBook\deploy\scripts\prepare-web-videos.sh'
    if (Test-Path -LiteralPath $prepSh) {
        Invoke-ScpUpload -LocalPath $prepSh -RemotePath ([string]::Concat($RemoteHost, ':~/prepare-web-videos.sh'))
    }
    foreach ($name in @('update_book_videos.py', 'book_video_asset.py', 'sync_book_review_videos.py', 'site_video_asset.py', 'video_optimize.py')) {
        $local = Join-Path $RepoRoot ('YuXiaotuBook\scripts\' + $name)
        if (Test-Path $local) {
            Invoke-ScpUpload -LocalPath $local -RemotePath ([string]::Concat($RemoteHost, ':~/patches/', $name))
        }
    }
    $remoteFix = 'sed -i ''s/\r$//'' ~/fix-book-video.sh; chmod +x ~/fix-book-video.sh; bash ~/fix-book-video.sh'
    Invoke-SshCommand -TargetHost $RemoteHost -Command $remoteFix
    Write-Host 'Book video fix done. Refresh book detail pages (Ctrl+F5)' -ForegroundColor Green
    exit 0
}

if (-not $DeployOnly) {
    Write-Host '[1/3] Packing release...' -ForegroundColor Cyan
    $packArgs = @()
    if ($RebuildFrontend) { $packArgs += '-RebuildFrontend' }
    & (Join-Path $DeployDir 'pack-release.ps1') @packArgs

    $releaseGlob = Join-Path $DeployDir 'release\yuxiaotu-book-ubuntu2404-*.tar.gz'
    $tar = Get-ChildItem $releaseGlob | Sort-Object LastWriteTime -Descending | Select-Object -First 1
    if (-not $tar) { throw 'Release tar.gz not found' }

    Write-Host '[2/3] Uploading to server home (~/)...' -ForegroundColor Cyan
    Invoke-ScpUpload -LocalPath $tar.FullName -RemotePath $RemoteHome
    Upload-DeployPatches -TargetHost $RemoteHost
    Upload-HomeExhibitionVideos -TargetHost $RemoteHost | Out-Null
    Upload-BookReviewVideos -TargetHost $RemoteHost | Out-Null

    Write-Host ('Upload done: ' + $tar.Name) -ForegroundColor Green
}

if ($DeployOnly) {
    Write-Host '[upload] DeployOnly: uploading scripts and patches...' -ForegroundColor Cyan
    if ($RebuildFrontend) {
        Write-Host '[pack] RebuildFrontend requested...' -ForegroundColor Cyan
        & (Join-Path $DeployDir 'pack-release.ps1') -RebuildFrontend
        $releaseGlob = Join-Path $DeployDir 'release\yuxiaotu-book-ubuntu2404-*.tar.gz'
        $tar = Get-ChildItem $releaseGlob | Sort-Object LastWriteTime -Descending | Select-Object -First 1
        if ($tar) {
            Invoke-ScpUpload -LocalPath $tar.FullName -RemotePath $RemoteHome
        }
    }
    Upload-DeployPatches -TargetHost $RemoteHost
    Upload-HomeExhibitionVideos -TargetHost $RemoteHost | Out-Null
    Upload-BookReviewVideos -TargetHost $RemoteHost | Out-Null
}

if ($UploadOnly) {
    Write-Host 'Upload only. Run on server: sudo bash ~/server-deploy.sh' -ForegroundColor Yellow
    exit 0
}

Write-Host '[3/3] Running remote deploy (may take 10-20 min)...' -ForegroundColor Cyan
$confirm = Read-Host '确认在服务器执行部署？(Y/n)'
if ($confirm -match '^[Nn]') {
    Write-Host '已取消部署。' -ForegroundColor Yellow
    exit 0
}
Ensure-SshControlMaster -TargetHost $RemoteHost -Reconnect
$RemoteCmd = Build-RemoteDeployCommand
Invoke-SshCommand -TargetHost $RemoteHost -Command $RemoteCmd

Write-Host 'Done.' -ForegroundColor Green
} finally {
    Stop-SshControlMaster -TargetHost $RemoteHost
}
