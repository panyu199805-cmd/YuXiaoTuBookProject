#!/usr/bin/env bash
# 宇小兔读书 — Ubuntu 24.04 一键自动化部署
# 适用：腾讯云 / 全新或重置后的服务器
#
# 用法：
#   1. 本机 pack-release.ps1 打部署包
#   2. 上传 server-deploy.sh、server-deploy.env、*.tar.gz 到服务器用户家目录 ~/
#   3. sudo bash ~/server-deploy.sh
#
# 更新代码（不装环境、不 seed）：
#   RUN_SEED=false INSTALL_ENV=false sudo bash ~/server-deploy.sh
set -euo pipefail

SCRIPT_VERSION="2026-07-09"

log()  { echo "[yuxiaotu-deploy] $*"; }
die()  { echo "[yuxiaotu-deploy] 错误: $*" >&2; exit 1; }

# ---------- 权限检查（非 root 时自动 sudo）----------
if [[ "${EUID:-$(id -u)}" -ne 0 ]]; then
  if command -v sudo >/dev/null 2>&1; then
    exec sudo bash "$0" "$@"
  fi
  die "请使用 sudo 执行：sudo bash $0"
fi

# ---------- 加载配置 ----------
SCRIPT_SELF_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DEPLOY_STAGING="${DEPLOY_STAGING:-$SCRIPT_SELF_DIR}"
CONFIG_FILE="${CONFIG_FILE:-$DEPLOY_STAGING/server-deploy.env}"
if [[ ! -f "$CONFIG_FILE" ]] && [[ -f "$SCRIPT_SELF_DIR/server-deploy.env" ]]; then
  CONFIG_FILE="$SCRIPT_SELF_DIR/server-deploy.env"
  DEPLOY_STAGING="$SCRIPT_SELF_DIR"
fi
if [[ ! -f "$CONFIG_FILE" ]] && [[ -f /root/server-deploy.env ]]; then
  CONFIG_FILE=/root/server-deploy.env
  DEPLOY_STAGING=/root
fi
if [[ ! -f "$CONFIG_FILE" ]]; then
  die "未找到配置文件 $CONFIG_FILE，请复制 server-deploy.env.example 为 server-deploy.env 并上传"
fi
# Windows 上传的 .env 可能带 CRLF
sed -i 's/\r$//' "$CONFIG_FILE" 2>/dev/null || true
# shellcheck disable=SC1090
source "$CONFIG_FILE"

PROJECT_ROOT="${PROJECT_ROOT:-/usr/local/projects/yuxiaotu}"
APP_DIR="$PROJECT_ROOT/app"
DEPLOY_DIR="$APP_DIR/YuXiaotuBook/deploy"
ENV_FILE="$PROJECT_ROOT/env/prod.env"
COMPOSE_FILE="$DEPLOY_DIR/docker-compose.prod.yml"

DOMAIN="${DOMAIN:?请在 server-deploy.env 中设置 DOMAIN}"
MYSQL_USER="${MYSQL_USER:-root}"
MYSQL_PASSWORD="${MYSQL_PASSWORD:?请在 server-deploy.env 中设置 MYSQL_PASSWORD}"
MYSQL_DATABASE="${MYSQL_DATABASE:-yuxiaotu_book}"
HTTP_PORT="${HTTP_PORT:-80}"
RUN_SEED="${RUN_SEED:-true}"
INSTALL_ENV="${INSTALL_ENV:-true}"
RUN_DATA_SCRIPTS="${RUN_DATA_SCRIPTS:-true}"
HOME_EXHIBITION_DIR="${HOME_EXHIBITION_DIR:-}"
BOOK_REVIEW_DIR="${BOOK_REVIEW_DIR:-}"
if [[ -z "$HOME_EXHIBITION_DIR" ]]; then
  for candidate in \
    "$HOME/homePage" \
    "$APP_DIR/YuXiaotuBook/backend/uploads/homePage"; do
    if [[ -d "$candidate" ]] && compgen -G "$candidate/*.mp4" > /dev/null; then
      HOME_EXHIBITION_DIR="$candidate"
      break
    fi
  done
fi
if [[ -z "$BOOK_REVIEW_DIR" ]]; then
  for candidate in \
    "$HOME/bookReview" \
    "$APP_DIR/YuXiaotuBook/backend/uploads/bookReview"; do
    if [[ -d "$candidate" ]] && compgen -G "$candidate/*.mp4" > /dev/null; then
      BOOK_REVIEW_DIR="$candidate"
      break
    fi
  done
fi

if [[ "$MYSQL_PASSWORD" == "ChangeMe_Strong_Password_123!" ]] || [[ "$MYSQL_PASSWORD" == "your_mysql_password" ]]; then
  die "请修改 server-deploy.env 中的 MYSQL_PASSWORD"
fi

# ---------- 工具函数 ----------
urlencode() {
  python3 - <<PY
import urllib.parse
print(urllib.parse.quote("""${1}""", safe=""))
PY
}

find_tarball() {
  if [[ -n "${TAR_PATH:-}" ]]; then
    [[ -f "$TAR_PATH" ]] || die "TAR_PATH 不存在: $TAR_PATH"
    echo "$TAR_PATH"
    return
  fi
  local latest dir
  for dir in "$DEPLOY_STAGING" "$SCRIPT_SELF_DIR" /root /home/ubuntu; do
    [[ -d "$dir" ]] || continue
    latest=$(ls -t "$dir"/yuxiaotu-book-ubuntu2404-*.tar.gz 2>/dev/null | head -1 || true)
    if [[ -n "$latest" ]]; then
      echo "$latest"
      return
    fi
  done
  die "未找到部署包，请上传 yuxiaotu-book-ubuntu2404-*.tar.gz 到 ~/ 或设置 TAR_PATH"
}

write_prod_env() {
  local jwt="${JWT_SECRET:-}"
  if [[ -z "$jwt" ]]; then
    jwt=$(openssl rand -hex 24)
    log "已自动生成 JWT_SECRET"
  fi
  local enc_pw
  enc_pw=$(urlencode "$MYSQL_PASSWORD")
  local cors="${CORS_ORIGINS:-}"
  if [[ -z "$cors" ]]; then
    cors="http://${DOMAIN}"
    [[ "$DOMAIN" != *"localhost"* ]] && cors="${cors},https://${DOMAIN}"
  fi

  mkdir -p "$PROJECT_ROOT/env"
  cat > "$ENV_FILE" <<EOF
# 由 server-deploy.sh 自动生成 — $(date -Iseconds)
PROJECT_ROOT=$PROJECT_ROOT
UPLOAD_DATA_DIR=$PROJECT_ROOT/data/uploads
BACKUP_DIR=/var/backups/yuxiaotu/mysql

DOMAIN=$DOMAIN
HTTP_PORT=$HTTP_PORT

MYSQL_USER=$MYSQL_USER
MYSQL_PASSWORD=$MYSQL_PASSWORD
MYSQL_HOST=host.docker.internal
MYSQL_PORT=3306
MYSQL_DATABASE=$MYSQL_DATABASE

DATABASE_URL="mysql://${MYSQL_USER}:${enc_pw}@host.docker.internal:3306/${MYSQL_DATABASE}"
JDBC_DATABASE_URL="jdbc:mysql://host.docker.internal:3306/${MYSQL_DATABASE}?useUnicode=true&characterEncoding=utf8&serverTimezone=UTC"

JWT_SECRET=$jwt
CORS_ORIGINS="$cors"
DEBUG=${DEBUG:-false}
MOCK_PAY_ENABLED=${MOCK_PAY_ENABLED:-false}
MEMBER_MOCK_PAY_ENABLED=${MEMBER_MOCK_PAY_ENABLED:-false}
PAYMENT_PROVIDER=mock
JWT_EXPIRE_HOURS=168
GUEST_VIDEO_PREVIEW_SECONDS=180
ORDER_TIMEOUT_MINUTES=30
JAVA_OPTS="-Xms256m -Xmx512m"

# AI 内容生成（OpenAI 兼容；不填 Key 则 Mock，后台页面仍可用）
AI_API_KEY=${AI_API_KEY:-}
AI_BASE_URL=${AI_BASE_URL:-https://api.deepseek.com/v1}
AI_MODEL=${AI_MODEL:-deepseek-chat}
AI_TIMEOUT_SECONDS=${AI_TIMEOUT_SECONDS:-60}
AI_MOCK_ENABLED=${AI_MOCK_ENABLED:-true}
EOF
  chmod 600 "$ENV_FILE"
  log "已写入 $ENV_FILE"
}

fix_mysql_docker_access() {
  local user="$MYSQL_USER"
  log "配置 MySQL 用户 ${user}（供 Docker 连接）..."
  local -a mysql_cmd=(mysql -uroot)
  if ! "${mysql_cmd[@]}" -e "SELECT 1" >/dev/null 2>&1; then
    mysql_cmd=(mysql)
  fi
  "${mysql_cmd[@]}" <<SQL
CREATE DATABASE IF NOT EXISTS \`${MYSQL_DATABASE}\` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER IF NOT EXISTS '${user}'@'localhost' IDENTIFIED BY '${MYSQL_PASSWORD}';
CREATE USER IF NOT EXISTS '${user}'@'127.0.0.1' IDENTIFIED BY '${MYSQL_PASSWORD}';
CREATE USER IF NOT EXISTS '${user}'@'172.%' IDENTIFIED BY '${MYSQL_PASSWORD}';
GRANT ALL PRIVILEGES ON \`${MYSQL_DATABASE}\`.* TO '${user}'@'localhost';
GRANT ALL PRIVILEGES ON \`${MYSQL_DATABASE}\`.* TO '${user}'@'127.0.0.1';
GRANT ALL PRIVILEGES ON \`${MYSQL_DATABASE}\`.* TO '${user}'@'172.%';
FLUSH PRIVILEGES;
SQL
}

wait_health() {
  local i
  for i in $(seq 1 40); do
    if curl -sf "http://127.0.0.1/api/health" >/dev/null 2>&1; then
      log "健康检查通过"
      curl -s "http://127.0.0.1/api/health"
      echo
      return 0
    fi
    sleep 2
  done
  die "健康检查失败，请执行: docker logs yuxiaotu-api-prod"
}

wait_api_running() {
  local api="yuxiaotu-api-prod"
  log "等待 API 容器就绪..."
  local i status
  for i in $(seq 1 60); do
    status=$(docker inspect -f '{{.State.Status}}' "$api" 2>/dev/null || echo "missing")
    if [[ "$status" == "running" ]]; then
      if docker exec "$api" python -c "from app.main import app" >/dev/null 2>&1; then
        log "API 容器已就绪"
        return 0
      fi
    fi
    sleep 3
  done
  log "警告: API 容器未就绪，跳过数据脚本"
  return 1
}

run_data_scripts() {
  [[ "$RUN_DATA_SCRIPTS" == "true" ]] || { log "跳过数据脚本 (RUN_DATA_SCRIPTS=false)"; return; }
  local api="yuxiaotu-api-prod"
  wait_api_running || return
  docker ps --format '{{.Names}}' | grep -q "^${api}$" || die "容器 $api 未运行"

  log "复制并执行数据更新脚本..."
  docker cp "$APP_DIR/YuXiaotuBook/scripts/." "${api}:/scripts/"

  if [[ -f "$APP_DIR/YuXiaotuBook/scripts/update_book_videos.py" ]]; then
    docker exec "$api" python /scripts/update_book_videos.py || log "警告: update_book_videos 失败"
  fi
  if [[ -f "$APP_DIR/YuXiaotuBook/scripts/update_all_ebooks.py" ]]; then
    docker exec "$api" python /scripts/update_all_ebooks.py || log "警告: update_all_ebooks 失败"
  fi
  if [[ -f "$APP_DIR/YuXiaotuBook/scripts/fix_site_bg_video.py" ]]; then
    docker exec "$api" python /scripts/fix_site_bg_video.py || log "警告: fix_site_bg_video 失败"
  fi
}

# ---------- 主流程 ----------
log "版本 $SCRIPT_VERSION | DOMAIN=$DOMAIN | MYSQL_USER=$MYSQL_USER | PROJECT_ROOT=$PROJECT_ROOT"

TAR_FILE=$(find_tarball)
log "使用部署包: $TAR_FILE"

log "=== 1/8 创建目录 ==="
mkdir -p "$APP_DIR" "$PROJECT_ROOT/data/uploads" "$PROJECT_ROOT/logs"
mkdir -p /var/backups/yuxiaotu/mysql

apply_deploy_patches() {
  local patch_dir="$SCRIPT_SELF_DIR/patches"
  [[ -d "$patch_dir" ]] || return 0
  if [[ -f "$patch_dir/01-install-docker.sh" ]]; then
    cp "$patch_dir/01-install-docker.sh" "$DEPLOY_DIR/ubuntu2404/01-install-docker.sh"
    log "已应用补丁: 01-install-docker.sh"
  fi
  if [[ -f "$patch_dir/install-all.sh" ]]; then
    cp "$patch_dir/install-all.sh" "$DEPLOY_DIR/ubuntu2404/install-all.sh"
    log "已应用补丁: install-all.sh"
  fi
  if [[ -f "$patch_dir/deploy.sh" ]]; then
    cp "$patch_dir/deploy.sh" "$DEPLOY_DIR/deploy.sh"
    log "已应用补丁: deploy.sh"
  fi
}

log "=== 2/8 解压代码 ==="
tar -xzf "$TAR_FILE" -C "$APP_DIR"
[[ -f "$DEPLOY_DIR/deploy.sh" ]] || die "解压后未找到 $DEPLOY_DIR/deploy.sh"
apply_deploy_patches

if [[ -f "$DEPLOY_DIR/scripts/fix-shell-scripts.sh" ]]; then
  bash "$DEPLOY_DIR/scripts/fix-shell-scripts.sh" || true
fi
chmod +x "$DEPLOY_DIR/deploy.sh" "$DEPLOY_DIR/scripts/"*.sh "$DEPLOY_DIR/ubuntu2404/"*.sh 2>/dev/null || true

log "=== 3/8 安装运行环境 ==="
if [[ "$INSTALL_ENV" == "true" ]]; then
  export MYSQL_PASSWORD MYSQL_USER MYSQL_DATABASE SKIP_NODE_INSTALL=true
  bash "$DEPLOY_DIR/ubuntu2404/install-all.sh"
  fix_mysql_docker_access
else
  log "跳过环境安装 (INSTALL_ENV=false)"
  fix_mysql_docker_access
fi

log "=== 4/8 生成生产配置 ==="
write_prod_env
export PROJECT_ROOT
bash "$DEPLOY_DIR/scripts/setup-server-dirs.sh"

log "=== 5/8 部署应用 ==="
bash "$DEPLOY_DIR/deploy.sh"

log "=== 6/8 重建 Nginx（避免 502）==="
docker compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" up -d --force-recreate nginx api trade
wait_api_running || log "警告: API 尚未就绪，后续步骤可能失败"

log "=== 7/8 初始化数据 ==="
if [[ "$RUN_SEED" == "true" ]]; then
  docker compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" --profile init run --rm seed
  log "默认管理员: admin / admin123456 （请尽快修改）"
else
  log "跳过 seed (RUN_SEED=false)"
fi

if [[ -n "$HOME_EXHIBITION_DIR" && -d "$HOME_EXHIBITION_DIR" ]]; then
  log "复制首页展览视频到 uploads/homePage..."
  mkdir -p "$PROJECT_ROOT/data/uploads/homePage"
  install -m 644 "$HOME_EXHIBITION_DIR"/*.mp4 "$PROJECT_ROOT/data/uploads/homePage/"
  log "展览视频已就位: $(find "$PROJECT_ROOT/data/uploads/homePage" -name '*.mp4' | wc -l) 个"
elif [[ -d "$APP_DIR/YuXiaotuBook/backend/uploads/homePage" ]]; then
  log "从部署包复制展览视频..."
  mkdir -p "$PROJECT_ROOT/data/uploads/homePage"
  install -m 644 "$APP_DIR/YuXiaotuBook/backend/uploads/homePage"/*.mp4 "$PROJECT_ROOT/data/uploads/homePage/" 2>/dev/null || true
fi

if [[ -n "$BOOK_REVIEW_DIR" && -d "$BOOK_REVIEW_DIR" ]]; then
  log "复制图书解读视频到 uploads/bookReview..."
  mkdir -p "$PROJECT_ROOT/data/uploads/bookReview"
  install -m 644 "$BOOK_REVIEW_DIR"/*.mp4 "$PROJECT_ROOT/data/uploads/bookReview/"
  log "解读视频已就位: $(find "$PROJECT_ROOT/data/uploads/bookReview" -name '*.mp4' | wc -l) 个"
elif [[ -d "$APP_DIR/YuXiaotuBook/backend/uploads/bookReview" ]]; then
  log "从部署包复制图书解读视频..."
  mkdir -p "$PROJECT_ROOT/data/uploads/bookReview"
  install -m 644 "$APP_DIR/YuXiaotuBook/backend/uploads/bookReview"/*.mp4 "$PROJECT_ROOT/data/uploads/bookReview/" 2>/dev/null || true
fi

if [[ -f "$DEPLOY_DIR/scripts/prepare-web-videos.sh" ]]; then
  log "优化 Web 播放视频（ffmpeg 转码 + faststart）..."
  bash "$DEPLOY_DIR/scripts/prepare-web-videos.sh" "$PROJECT_ROOT/data/uploads"
fi

run_data_scripts

log "=== 8/8 验证 ==="
wait_health

log ""
log "=========================================="
log " 部署完成"
log " 前台:     http://${DOMAIN}/"
log " 管理后台: http://${DOMAIN}/admin/login"
log " 项目目录: $PROJECT_ROOT"
log " 环境配置: $ENV_FILE"
log "=========================================="
