"""将所有图书解读视频 URL 更新为 bookReview 目录下的默认视频。"""
from __future__ import annotations

import asyncio
import os
import sys

BACKEND_DIR = os.path.join(os.path.dirname(__file__), "..", "backend")
sys.path.insert(0, os.path.abspath(BACKEND_DIR))
sys.path.insert(0, os.path.dirname(__file__))

from sync_book_review_videos import update_book_videos
from book_video_asset import book_intro_video_url, sync_book_review_to_uploads
from site_video_asset import resolve_upload_root


async def main() -> None:
    upload_root = resolve_upload_root()
    sync_book_review_to_uploads(upload_root)
    url = book_intro_video_url(upload_root)
    await update_book_videos(url)


if __name__ == "__main__":
    asyncio.run(main())
