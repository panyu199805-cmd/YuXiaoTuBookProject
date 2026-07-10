#!/usr/bin/env bash
# 热修复 API 崩溃（home_page_video_service.py Docker 路径 IndexError）
set -euo pipefail

PATCH="${1:-$HOME/patches/home_page_video_service.py}"
API="yuxiaotu-api-prod"

log() { echo "[fix-api-homepage] $*"; }
die() { echo "[fix-api-homepage] 错误: $*" >&2; exit 1; }

[[ -f "$PATCH" ]] || die "未找到补丁: $PATCH"

docker ps -a --format '{{.Names}}' | grep -q "^${API}$" || die "容器 $API 不存在"
docker cp "$PATCH" "${API}:/app/app/services/home_page_video_service.py"
log "已复制补丁到容器，重启 API..."
docker restart "$API"

for i in $(seq 1 30); do
  if docker exec "$API" python -c "from app.main import app" >/dev/null 2>&1; then
    log "API 已恢复"
    curl -sf "http://127.0.0.1/api/health" && echo && exit 0
  fi
  sleep 2
done

die "API 仍未就绪，请执行: docker logs $API"
