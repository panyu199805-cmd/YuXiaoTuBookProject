#!/usr/bin/env bash
# 将 uploads 下体积过大的 MP4 转为 Web 友好格式（部署后自动执行）
set -euo pipefail

WEB_MAX_BYTES=$((12 * 1024 * 1024))

install_optimized_video() {
  local tmp="$1"
  local dest="$2"
  if [[ -w "$dest" ]] 2>/dev/null && [[ -w "$(dirname "$dest")" ]] 2>/dev/null; then
    mv -f "$tmp" "$dest"
  else
    sudo install -m 644 "$tmp" "$dest"
    rm -f "$tmp"
  fi
}

optimize_mp4() {
  local file="$1"
  [[ -f "$file" ]] || return 0
  local size
  size=$(stat -c%s "$file" 2>/dev/null || stat -f%z "$file")
  if (( size <= WEB_MAX_BYTES )); then
    return 0
  fi
  if ! command -v ffmpeg >/dev/null 2>&1; then
    echo "[video] ffmpeg 未安装，跳过 ${file} (${size} bytes)"
    echo "[video] 可执行: sudo apt-get install -y ffmpeg"
    return 0
  fi

  local tmp
  tmp=$(mktemp /tmp/yuxiaotu-video-opt.XXXXXX.mp4)
  echo "[video] 转码 ${file} (${size} bytes) ..."
  ffmpeg -y -hide_banner -loglevel error -i "$file" \
    -c:v libx264 -preset fast -crf 24 \
    -vf "scale='min(1280,iw)':-2" \
    -movflags +faststart \
    -c:a aac -b:a 96k -ac 2 \
    -pix_fmt yuv420p \
    "$tmp"
  install_optimized_video "$tmp" "$file"

  local new_size
  new_size=$(stat -c%s "$file" 2>/dev/null || stat -f%z "$file")
  echo "[video] 完成 ${file} -> ${new_size} bytes"
}

UPLOAD_BASE="${1:-${PROJECT_ROOT:-/usr/local/projects/yuxiaotu}/data/uploads}"
for sub in homePage bookReview; do
  dir="${UPLOAD_BASE}/${sub}"
  [[ -d "$dir" ]] || continue
  shopt -s nullglob
  for f in "$dir"/*.mp4; do
    optimize_mp4 "$f"
  done
done
