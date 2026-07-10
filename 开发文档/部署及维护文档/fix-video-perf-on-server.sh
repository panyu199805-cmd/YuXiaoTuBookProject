#!/usr/bin/env bash
# 在服务器上直接执行（腾讯云 Web 终端），一键压缩视频并刷新缓存
set -euo pipefail

UPLOAD_DIR="${UPLOAD_DIR:-/usr/local/projects/yuxiaotu/data/uploads}"

echo "[fix-video-perf] 安装 ffmpeg（如未安装）..."
if ! command -v ffmpeg >/dev/null 2>&1; then
  sudo apt-get update -qq
  sudo apt-get install -y ffmpeg
fi

SCRIPT="/usr/local/projects/yuxiaotu/app/YuXiaotuBook/deploy/scripts/prepare-web-videos.sh"
if [[ ! -f "$SCRIPT" ]]; then
  SCRIPT="$HOME/app/YuXiaotuBook/deploy/scripts/prepare-web-videos.sh"
fi
if [[ ! -f "$SCRIPT" ]]; then
  echo "[fix-video-perf] 未找到 prepare-web-videos.sh，请先部署最新代码"
  exit 1
fi

bash "$SCRIPT" "$UPLOAD_DIR"

echo "[fix-video-perf] 当前视频体积："
find "$UPLOAD_DIR/homePage" "$UPLOAD_DIR/bookReview" -name '*.mp4' -exec ls -lh {} \; 2>/dev/null || true

echo "[fix-video-perf] 完成。请 Ctrl+F5 刷新网站。"
