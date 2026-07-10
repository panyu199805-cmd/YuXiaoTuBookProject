#!/usr/bin/env bash
# 宇小兔每日读书 — 生产部署脚本（Linux 云服务器）
# 默认布局：/usr/local/projects/yuxiaotu/{app,data,env,logs}
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

COMPOSE_FILE="docker-compose.prod.yml"

if [[ "$SCRIPT_DIR" == */app/YuXiaotuBook/deploy ]]; then
  PROJECT_ROOT="${PROJECT_ROOT:-$(cd "$SCRIPT_DIR/../../.." && pwd)}"
else
  PROJECT_ROOT="${PROJECT_ROOT:-/usr/local/projects/yuxiaotu}"
fi

export PROJECT_ROOT

log() { echo "[deploy] $*"; }

chmod +x scripts/setup-server-dirs.sh 2>/dev/null || true
PROJECT_ROOT="$PROJECT_ROOT" ./scripts/setup-server-dirs.sh

ENV_FILE="${ENV_FILE:-}"
if [[ -z "$ENV_FILE" ]]; then
  if [[ -f "$PROJECT_ROOT/env/prod.env" ]]; then
    ENV_FILE="$PROJECT_ROOT/env/prod.env"
  elif [[ -f "$PROJECT_ROOT/env/.env" ]]; then
    ENV_FILE="$PROJECT_ROOT/env/.env"
  else
    ENV_FILE="$PROJECT_ROOT/env/prod.env"
  fi
fi
if [[ ! -f "$ENV_FILE" ]] && [[ -f "$SCRIPT_DIR/.env" ]]; then
  ENV_FILE="$SCRIPT_DIR/.env"
fi

if [[ ! -f "$ENV_FILE" ]]; then
  log "未找到 $ENV_FILE"
  log "请运行 ./scripts/setup-server-dirs.sh 后编辑 env/prod.env"
  exit 1
fi

# shellcheck disable=SC1090
sed -i 's/\r$//' "$ENV_FILE" 2>/dev/null || true
set -a
source "$ENV_FILE"
set +a

# source 失败时的兜底（URL 含 & 等特殊字符时须加引号）
if [[ -z "${DATABASE_URL:-}" ]]; then
  DATABASE_URL="$(grep -E '^DATABASE_URL=' "$ENV_FILE" | head -1 | cut -d= -f2- | sed 's/^"//;s/"$//')"
  export DATABASE_URL
fi
if [[ -z "${JDBC_DATABASE_URL:-}" ]]; then
  JDBC_DATABASE_URL="$(grep -E '^JDBC_DATABASE_URL=' "$ENV_FILE" | head -1 | cut -d= -f2- | sed 's/^"//;s/"$//')"
  export JDBC_DATABASE_URL
fi

if [[ "${MYSQL_PASSWORD:-}" == "your_mysql_password" ]] \
  || [[ "${MYSQL_PASSWORD:-}" == "ChangeMe_Strong_Password_123!" ]] \
  || [[ "${DATABASE_URL:-}" == *"your_url_encoded_password"* ]] \
  || [[ "${JWT_SECRET:-}" == ChangeMe_* ]]; then
  log "请先在 $ENV_FILE 中修改 MYSQL_PASSWORD、DATABASE_URL 与 JWT_SECRET"
  exit 1
fi

if [[ -z "${DATABASE_URL:-}" ]] || [[ -z "${JDBC_DATABASE_URL:-}" ]]; then
  log "请在 $ENV_FILE 中设置 DATABASE_URL 与 JDBC_DATABASE_URL"
  exit 1
fi

UPLOAD_DATA_DIR="${UPLOAD_DATA_DIR:-$PROJECT_ROOT/data/uploads}"
mkdir -p "$UPLOAD_DATA_DIR"

if ! command -v docker >/dev/null 2>&1; then
  log "未安装 Docker，请运行：sudo ./ubuntu2404/01-install-docker.sh"
  exit 1
fi

if ! docker compose version >/dev/null 2>&1; then
  log "未找到 docker compose 插件，请安装 docker-compose-plugin 或 docker-compose-v2"
  exit 1
fi

FRONTEND_DIST="../frontend/dist"
if [[ -f "$FRONTEND_DIST/index.html" ]]; then
  log "使用已打包的前端 dist，跳过 npm 构建"
else
  if ! command -v npm >/dev/null 2>&1; then
    log "未安装 Node.js/npm，且无 frontend/dist，无法部署"
    exit 1
  fi

  log "构建前端..."
  cd ../frontend
  if [[ -f package-lock.json ]]; then
    npm ci --registry=https://registry.npmmirror.com
  else
    npm install --registry=https://registry.npmmirror.com
  fi
  if npm run build 2>/dev/null; then
    log "前端构建成功"
  else
    log "npm run build 失败，改用 npx vite build"
    npx vite build
  fi
  cd "$SCRIPT_DIR"
fi

if [[ ! -f "$FRONTEND_DIST/index.html" ]]; then
  log "前端构建失败：未生成 frontend/dist/index.html"
  exit 1
fi

log "启动 Docker 服务..."
docker compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" up -d --build

log "等待 API 健康检查..."
for i in $(seq 1 30); do
  if docker compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" exec -T api \
    python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/api/health')" 2>/dev/null; then
    break
  fi
  sleep 2
done

PORT="${HTTP_PORT:-80}"
log "部署完成。"
log "  项目根：$PROJECT_ROOT"
log "  上传目录：$UPLOAD_DATA_DIR"
log "  前台：http://${DOMAIN:-localhost}:${PORT}/"
log "  管理后台：http://${DOMAIN:-localhost}:${PORT}/admin/login"
log "  默认管理员（若已 seed）：admin / admin123456 — 上线后请立即修改"
log ""
log "首次部署初始化数据（宿主机 MySQL 已就绪后）："
log "  docker compose -f $COMPOSE_FILE --env-file $ENV_FILE --profile init run --rm seed"
log ""
log "MySQL 自动备份："
log "  ./scripts/backup-mysql.sh"
