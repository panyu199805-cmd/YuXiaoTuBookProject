"""修复站点首页背景视频（同步 网站素材/首页展览素材 并写入 bg_videos）。"""
from __future__ import annotations

import asyncio
import os
import sys

BACKEND_DIR = os.path.join(os.path.dirname(__file__), "..", "backend")
sys.path.insert(0, os.path.abspath(BACKEND_DIR))
sys.path.insert(0, os.path.dirname(__file__))

from sync_home_exhibition_videos import update_site_config
from site_video_asset import resolve_upload_root, sync_home_exhibition_to_uploads


async def main() -> None:
    upload_root = resolve_upload_root()
    _, urls = sync_home_exhibition_to_uploads(upload_root)
    await update_site_config(urls)


if __name__ == "__main__":
    asyncio.run(main())
