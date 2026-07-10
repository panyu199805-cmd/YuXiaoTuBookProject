from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Literal, Optional
from urllib.parse import quote, unquote

from app.core.config import settings
from app.services.home_page_video_service import home_page_dir

VideoCategory = Literal["homePage", "bookReview"]

_UPLOAD_VIDEO_RE = re.compile(
    r"^/uploads/(homePage|bookReview)/(.+)\.(mp4|webm)$",
    re.IGNORECASE,
)


def to_protected_video_url(url: str) -> str:
    """将 /uploads/.../*.mp4 转为 /media/v/...（无扩展名，减少浏览器注入下载按钮）。"""
    if not url:
        return url
    path = url.split("?", 1)[0]
    match = _UPLOAD_VIDEO_RE.match(path)
    if not match:
        return url
    category, basename, _ext = match.groups()
    name = unquote(basename)
    return f"/media/v/{category}/{quote(name, safe='')}"


def resolve_video_file(category: VideoCategory, name: str) -> Optional[Path]:
    """根据分类与文件名（无扩展名）解析磁盘上的 mp4/webm 路径。"""
    safe_name = unquote(name).strip().strip("/")
    if not safe_name or ".." in safe_name or "/" in safe_name or "\\" in safe_name:
        return None

    base_dir = Path(home_page_dir()) if category == "homePage" else Path(settings.UPLOAD_DIR) / "bookReview"
    for ext in (".mp4", ".webm", ".MP4", ".WEBM"):
        candidate = base_dir / f"{safe_name}{ext}"
        if candidate.is_file():
            return candidate.resolve()
    return None
