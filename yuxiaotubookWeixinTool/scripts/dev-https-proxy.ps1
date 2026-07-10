# 本地 HTTPS 代理：解决小程序基础库 3.15+ 禁止 HTTP 图片/视频
# 用法：先启动 本地运行.ps1，再运行本脚本，然后 .env 使用 8443 端口
#
# 前置：Python :8000、Java :8081 已启动
# 微信开发者工具：勾选「不校验合法域名」+「不校验 TLS 证书」

$ErrorActionPreference = "Stop"
$ip = (Get-NetIPAddress -AddressFamily IPv4 | Where-Object {
  $_.IPAddress -notlike '127.*' `
    -and $_.IPAddress -notlike '169.254.*' `
    -and $_.InterfaceAlias -notmatch 'Loopback|vEthernet|WSL|VMware|VirtualBox|Hyper-V'
} | Sort-Object @{
  Expression = {
    if ($_.IPAddress -like '192.168.*') { 0 }
    elseif ($_.IPAddress -like '10.*') { 1 }
    elseif ($_.IPAddress -match '^172\.(1[6-9]|2\d|3[01])\.') { 2 }
    else { 9 }
  }
} | Select-Object -First 1).IPAddress

if (-not $ip) { $ip = "127.0.0.1" }

Write-Host "本机 IP: $ip" -ForegroundColor Cyan
Write-Host "HTTPS 代理：" -ForegroundColor Green
Write-Host "  https://${ip}:8443  ->  http://127.0.0.1:8000  (Python API + 静态资源)"
Write-Host "  https://${ip}:8444  ->  http://127.0.0.1:8081  (Java 订单/会员)"
Write-Host ""
Write-Host "请在 .env.development 中设置：" -ForegroundColor Yellow
Write-Host "  VITE_API_BASE=https://${ip}:8443/api/v1"
Write-Host "  VITE_MEDIA_ORIGIN=https://${ip}:8443"
Write-Host "  VITE_TRADE_API_BASE=https://${ip}:8444/api/v1"
Write-Host ""

$job1 = Start-Job -ScriptBlock {
  param($hostName)
  npx --yes local-ssl-proxy --source 8443 --target 8000 --hostname $hostName 2>&1
} -ArgumentList $ip

$job2 = Start-Job -ScriptBlock {
  param($hostName)
  npx --yes local-ssl-proxy --source 8444 --target 8081 --hostname $hostName 2>&1
} -ArgumentList $ip

Write-Host "HTTPS 代理已启动（Ctrl+C 停止）..." -ForegroundColor Green
try {
  while ($true) {
    Receive-Job $job1, $job2 -ErrorAction SilentlyContinue | Write-Host
    Start-Sleep -Seconds 2
  }
} finally {
  Stop-Job $job1, $job2 -ErrorAction SilentlyContinue
  Remove-Job $job1, $job2 -ErrorAction SilentlyContinue
}
