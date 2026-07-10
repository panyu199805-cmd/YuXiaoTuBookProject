# 配置本机 SSH 公钥到腾讯云服务器（解决 Permission denied）
# 用法：
#   cd 开发文档\部署及维护文档
#   .\setup-ssh-key.ps1

$ErrorActionPreference = 'Stop'
$Here = Split-Path -Parent $MyInvocation.MyCommand.Path
$EnvFile = Join-Path $Here 'server-deploy.env'

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

$keyCandidates = @(
    (Join-Path $env:USERPROFILE '.ssh\id_ed25519'),
    (Join-Path $env:USERPROFILE '.ssh\id_rsa')
)
$privateKey = $null
$publicKey = $null
foreach ($candidate in $keyCandidates) {
    if (Test-Path -LiteralPath $candidate) {
        $privateKey = $candidate
        $publicKey = "$candidate.pub"
        break
    }
}

if (-not $privateKey) {
    Write-Host '未找到 SSH 密钥，正在生成 id_ed25519 ...' -ForegroundColor Yellow
    $sshDir = Join-Path $env:USERPROFILE '.ssh'
    New-Item -ItemType Directory -Path $sshDir -Force | Out-Null
    ssh-keygen -t ed25519 -C 'yuxiaotu-deploy' -f (Join-Path $sshDir 'id_ed25519') -N '""'
    $privateKey = Join-Path $sshDir 'id_ed25519'
    $publicKey = "$privateKey.pub"
}

$ServerIp = Read-EnvValue -Key 'SERVER_IP'
if (-not $ServerIp) { $ServerIp = '175.178.119.166' }
$RemoteUser = Read-EnvValue -Key 'SERVER_USER'
if (-not $RemoteUser) { $RemoteUser = 'ubuntu' }

$pubLine = (Get-Content -LiteralPath $publicKey -Raw).Trim()
$remoteHost = "$RemoteUser@$ServerIp"

Write-Host ''
Write-Host '========================================' -ForegroundColor Cyan
Write-Host ' 宇小兔部署 SSH 公钥配置' -ForegroundColor Cyan
Write-Host '========================================' -ForegroundColor Cyan
Write-Host ("服务器: {0}" -f $remoteHost)
Write-Host ("私钥:   {0}" -f $privateKey)
Write-Host ''
Write-Host '你的公钥（复制整行）:' -ForegroundColor Green
Write-Host $pubLine -ForegroundColor Yellow
Write-Host ''

Write-Host '方式 A（推荐）：腾讯云控制台 → 登录实例 → 密钥/密码 → 绑定 SSH 公钥' -ForegroundColor White
Write-Host '方式 B：用 VNC 登录服务器后执行:' -ForegroundColor White
Write-Host ("  mkdir -p ~/.ssh && echo '{0}' >> ~/.ssh/authorized_keys && chmod 600 ~/.ssh/authorized_keys" -f $pubLine) -ForegroundColor Gray
Write-Host ''

$envPath = $EnvFile
if (Test-Path $envPath) {
    $content = Get-Content -LiteralPath $envPath -Encoding UTF8 -Raw
    if ($content -notmatch '(?m)^SSH_KEY_PATH=') {
        Add-Content -LiteralPath $envPath -Value ("SSH_KEY_PATH={0}" -f $privateKey) -Encoding UTF8
        Write-Host ("已写入 server-deploy.env: SSH_KEY_PATH={0}" -f $privateKey) -ForegroundColor Green
    }
}

Write-Host ''
Write-Host '配置完成后测试连接:' -ForegroundColor Cyan
Write-Host ("  ssh -i `"$privateKey`" $remoteHost `"echo ok`"") -ForegroundColor Gray
Write-Host ''

$test = Read-Host '公钥已绑定到服务器了吗？输入 y 立即测试 SSH (y/N)'
if ($test -eq 'y' -or $test -eq 'Y') {
    ssh -i $privateKey -o StrictHostKeyChecking=accept-new $remoteHost 'echo SSH OK'
    if ($LASTEXITCODE -eq 0) {
        Write-Host 'SSH 连接成功，可重新运行 upload-and-deploy.ps1' -ForegroundColor Green
    } else {
        Write-Host '仍无法连接：请在腾讯云控制台重置 ubuntu 密码，或确认公钥已写入 authorized_keys' -ForegroundColor Red
    }
}
