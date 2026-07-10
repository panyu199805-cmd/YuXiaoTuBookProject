#!/usr/bin/env bash
# 修复图书解读视频：同步 bookReview 到 uploads 并更新 book_video 表
set -euo pipefail

UPLOAD_DIR="${UPLOAD_DIR:-/usr/local/projects/yuxiaotu/data/uploads}"
REVIEW_DIR="$UPLOAD_DIR/bookReview"
SRC_DIR="${1:-$HOME/bookReview}"

log() { echo "[fix-book-video] $*"; }
die() { echo "[fix-book-video] 错误: $*" >&2; exit 1; }

if [[ -d "$SRC_DIR" ]]; then
  mp4_count=$(find "$SRC_DIR" -maxdepth 1 -name '*.mp4' | wc -l)
  [[ "$mp4_count" -gt 0 ]] || die "素材目录无 mp4: $SRC_DIR"
  log "复制解读视频 ($mp4_count 个) -> $REVIEW_DIR"
  sudo mkdir -p "$REVIEW_DIR"
  sudo install -m 644 "$SRC_DIR"/*.mp4 "$REVIEW_DIR/"
else
  die "未找到解读素材目录: $SRC_DIR（请先 scp 到 ~/bookReview/）"
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
elif command -v ffmpeg >/dev/null 2>&1; then
  log "优化视频（内联 ffmpeg）..."
  for f in "$REVIEW_DIR"/*.mp4; do
    [[ -f "$f" ]] || continue
    size=$(stat -c%s "$f" 2>/dev/null || stat -f%z "$f")
    (( size <= 12582912 )) && continue
    tmp=$(mktemp /tmp/yuxiaotu-video-opt.XXXXXX.mp4)
    ffmpeg -y -hide_banner -loglevel error -i "$f" \
      -c:v libx264 -preset fast -crf 24 \
      -vf "scale='min(1280,iw)':-2" \
      -movflags +faststart -c:a aac -b:a 96k -pix_fmt yuv420p "$tmp"
    sudo install -m 644 "$tmp" "$f"
    rm -f "$tmp"
  done
else
  log "警告: 未找到 ffmpeg，视频仍为原始体积，播放可能卡顿"
  log "请执行: sudo apt-get install -y ffmpeg && bash ~/prepare-web-videos.sh $UPLOAD_DIR"
fi

PATCH_DIR="$HOME/patches"
for script in update_book_videos.py book_video_asset.py sync_book_review_videos.py site_video_asset.py; do
  if [[ -f "$PATCH_DIR/$script" ]]; then
    docker cp "$PATCH_DIR/$script" "yuxiaotu-api-prod:/scripts/$script"
  fi
done
docker exec yuxiaotu-api-prod python /scripts/update_book_videos.py

sample=$(find "$REVIEW_DIR" -maxdepth 1 -name '*.mp4' | head -1)
sample_name=$(basename "$sample")
if curl -sfI "http://127.0.0.1/uploads/bookReview/$sample_name" | grep -qi '200\|206'; then
  log "HTTP 访问正常: /uploads/bookReview/$sample_name"
else
  die "HTTP 仍无法访问解读视频，请检查 docker logs yuxiaotu-nginx-prod"
fi

log "完成，请刷新图书详情页"
