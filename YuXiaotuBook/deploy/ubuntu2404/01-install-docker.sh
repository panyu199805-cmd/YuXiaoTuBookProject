#!/usr/bin/env bash
# Ubuntu 24.04 LTS — 安装 Docker Engine + Compose 插件（国内镜像优先）
set -euo pipefail

if [[ "${EUID:-$(id -u)}" -ne 0 ]]; then
  echo "[docker] 请使用 root 或 sudo 运行"
  exit 1
fi

if command -v docker >/dev/null 2>&1; then
  echo "[docker] 已安装：$(docker --version)"
  docker compose version 2>/dev/null || true
else
  . /etc/os-release
  if [[ "${ID:-}" != "ubuntu" ]]; then
    echo "[docker] 警告：此脚本针对 Ubuntu，当前系统 ID=${ID:-unknown}"
  fi

  echo "[docker] 安装依赖..."
  apt-get update
  apt-get install -y ca-certificates curl gnupg

  install -m 0755 -d /etc/apt/keyrings

  install_docker_io() {
    echo "[docker] 使用 Ubuntu 官方 docker.io 包..."
    apt-get update
    apt-get install -y docker.io docker-compose-v2
  }

  install_docker_ce_mirror() {
    local mirror="${DOCKER_APT_MIRROR:-https://mirrors.aliyun.com/docker-ce/linux/ubuntu}"
    local codename="${VERSION_CODENAME:-noble}"
    local arch
    arch="$(dpkg --print-architecture)"
    local gpg_urls=(
      "${mirror}/gpg"
      "https://download.docker.com/linux/ubuntu/gpg"
    )
    local gpg_ok=false
    for url in "${gpg_urls[@]}"; do
      echo "[docker] 下载 GPG: $url"
      if curl -fsSL --connect-timeout 20 --retry 3 "$url" -o /etc/apt/keyrings/docker.asc; then
        gpg_ok=true
        break
      fi
    done
    if [[ "$gpg_ok" != "true" ]]; then
      echo "[docker] GPG 下载失败，改用 docker.io"
      install_docker_io
      return
    fi
    chmod a+r /etc/apt/keyrings/docker.asc
    echo "deb [arch=${arch} signed-by=/etc/apt/keyrings/docker.asc] ${mirror} ${codename} stable" \
      > /etc/apt/sources.list.d/docker.list
    apt-get update
    apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
  }

  install_docker_ce_mirror || install_docker_io

  systemctl enable docker
  systemctl start docker
fi

mkdir -p /etc/docker
if [[ ! -f /etc/docker/daemon.json ]]; then
  cat > /etc/docker/daemon.json <<'JSON'
{
  "registry-mirrors": [
    "https://mirror.ccs.tencentyun.com",
    "https://docker.m.daocloud.io"
  ]
}
JSON
  systemctl restart docker
fi

echo "[docker] 版本："
docker --version
docker compose version 2>/dev/null || docker-compose --version 2>/dev/null || true

if [[ -n "${SUDO_USER:-}" ]]; then
  usermod -aG docker "$SUDO_USER" 2>/dev/null || true
  echo "[docker] 已将用户 ${SUDO_USER} 加入 docker 组，重新登录 SSH 后生效"
fi

echo "[docker] 安装完成"
