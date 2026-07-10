from __future__ import annotations

import os

from starlette.staticfiles import StaticFiles
from starlette.types import Scope

# python:3.8-slim 默认无 /etc/mime.types，.mp4 会变成 application/octet-stream 导致浏览器下载而非播放
MIME_BY_EXT = {
    ".mp4": "video/mp4",
    ".webm": "video/webm",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
    ".webp": "image/webp",
    ".svg": "image/svg+xml",
}


class CachedStaticFiles(StaticFiles):
    """静态资源长缓存，减少视频/图片重复加载。"""

    async def get_response(self, path: str, scope: Scope):
        response = await super().get_response(path, scope)
        if response.status_code == 200:
            ext = os.path.splitext(path)[1].lower()
            mime = MIME_BY_EXT.get(ext)
            if mime:
                response.headers["Content-Type"] = mime
            if ext in (".mp4", ".webm"):
                response.headers["Content-Disposition"] = "inline"
                response.headers["Accept-Ranges"] = "bytes"
            if self._should_cache(path):
                response.headers["Cache-Control"] = "public, max-age=31536000, immutable"
        return response

    @staticmethod
    def _should_cache(path: str) -> bool:
        lower = path.lower()
        return lower.endswith((".mp4", ".webm", ".jpg", ".jpeg", ".png", ".webp", ".svg"))
