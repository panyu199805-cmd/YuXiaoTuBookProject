#!/usr/bin/env bash
# Ubuntu 24.04.4 LTS 首次环境安装：Docker + Node.js + MySQL
# 用法：sudo MYSQL_PASSWORD='你的密码' ./install-all.sh
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if [[ "${EUID:-$(id -u)}" -ne 0 ]]; then
  echo "[install-all] 请使用：sudo MYSQL_PASSWORD='...' $0"
  exit 1
fi

bash "$SCRIPT_DIR/01-install-docker.sh"

if [[ "${SKIP_NODE_INSTALL:-false}" == "true" ]]; then
  echo "[install-all] 跳过 Node.js（使用预构建 frontend/dist）"
else
  bash "$SCRIPT_DIR/02-install-nodejs.sh"
fi

if [[ -n "${MYSQL_PASSWORD:-}" ]]; then
  bash "$SCRIPT_DIR/03-install-mysql.sh"
else
  echo "[install-all] 未设置 MYSQL_PASSWORD，跳过 MySQL 安装"
  echo "  稍后执行：sudo MYSQL_PASSWORD='...' $SCRIPT_DIR/03-install-mysql.sh"
fi

echo ""
echo "[install-all] 环境就绪。下一步："
echo "  1. cd /usr/local/projects/yuxiaotu/app/YuXiaotuBook/deploy"
echo "  2. ./scripts/setup-server-dirs.sh && nano /usr/local/projects/yuxiaotu/env/.env"
echo "  3. ./deploy.sh"
echo "  4. docker compose -f docker-compose.prod.yml --env-file /usr/local/projects/yuxiaotu/env/.env --profile init run --rm seed"
