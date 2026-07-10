#!/usr/bin/env bash
# 修复首页展览视频：同步 homePage 到 uploads 并更新站点 bg_videos
set -euo pipefail

UPLOAD_DIR="${UPLOAD_DIR:-/usr/local/projects/yuxiaotu/data/uploads}"
EXHIBITION_DIR="$UPLOAD_DIR/homePage"
SRC_DIR="${1:-$HOME/homePage}"

log() { echo "[fix-home-video] $*"; }
die() { echo "[fix-home-video] 错误: $*" >&2; exit 1; }

if [[ -d "$SRC_DIR" ]]; then
  mp4_count=$(find "$SRC_DIR" -maxdepth 1 -name '*.mp4' | wc -l)
  [[ "$mp4_count" -gt 0 ]] || die "素材目录无 mp4: $SRC_DIR"
  log "复制展览视频 ($mp4_count 个) -> $EXHIBITION_DIR"
  sudo mkdir -p "$EXHIBITION_DIR"
  sudo install -m 644 "$SRC_DIR"/*.mp4 "$EXHIBITION_DIR/"
else
  die "未找到展览素材目录: $SRC_DIR（请先 scp 到 ~/homePage/）"
fi

DEPLOY_DIR="${DEPLOY_DIR:-$HOME/app/YuXiaotuBook/deploy}"
PREP=""
for candidate in \
  "$HOME/prepare-web-videos.sh" \
  "$DEPLOY_DIR/scripts/prepare-web-videos.sh" \
  "/usr/local/projects/yuxiaotu/app/YuXiaotuBook/deploy/scripts/prepare-web-videos.sh"; do
  if [[ -f "$candidate" ]]; then
    PREP="$candidate"
    break
  fi
done
if [[ -n "$PREP" ]]; then
  log "优化视频体积（ffmpeg 720p + faststart）..."
  bash "$PREP" "$UPLOAD_DIR"
fi

if docker ps --format '{{.Names}}' | grep -q '^yuxiaotu-nginx-prod$'; then
  sample=$(find "$EXHIBITION_DIR" -maxdepth 1 -name '*.mp4' | head -1)
  sample_name=$(basename "$sample")
  if docker exec yuxiaotu-nginx-prod test -f "/var/www/uploads/homePage/$sample_name"; then
    log "Nginx 容器内已可见展览视频"
  else
    die "Nginx 容器内仍无 /var/www/uploads/homePage/，请检查 UPLOAD_DATA_DIR 挂载"
  fi
fi

PATCH_DIR="$HOME/patches"
for script in fix_site_bg_video.py site_video_asset.py sync_home_exhibition_videos.py; do
  if [[ -f "$PATCH_DIR/$script" ]]; then
    docker cp "$PATCH_DIR/$script" "yuxiaotu-api-prod:/scripts/$script"
  fi
done
docker exec yuxiaotu-api-prod python /scripts/fix_site_bg_video.py

first_url=$(find "$EXHIBITION_DIR" -maxdepth 1 -name '*.mp4' | head -1 | xargs -I{} basename {})
if curl -sfI "http://127.0.0.1/uploads/homePage/$first_url" | grep -qi '200\|206'; then
  log "HTTP 访问正常: /uploads/homePage/$first_url"
else
  die "HTTP 仍无法访问展览视频，请检查 docker logs yuxiaotu-nginx-prod"
fi

log "完成，请刷新首页"
