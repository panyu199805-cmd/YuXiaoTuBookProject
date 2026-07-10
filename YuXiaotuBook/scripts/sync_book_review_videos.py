"""同步图书解读视频到 uploads/bookReview，并更新 book_video 表。"""
from __future__ import annotations

import argparse
import asyncio
import os
import sys

BACKEND_DIR = os.path.join(os.path.dirname(__file__), "..", "backend")
sys.path.insert(0, os.path.abspath(BACKEND_DIR))
sys.path.insert(0, os.path.dirname(__file__))

from tortoise import Tortoise

from app.db.database import TORTOISE_ORM
from app.models import BookVideo
from book_video_asset import (
    BOOK_INTRO_VIDEO_INTRO,
    BOOK_REVIEW_SOURCE_DIR,
    book_intro_video_url,
    sync_book_review_to_uploads,
)
from site_video_asset import resolve_upload_root


async def update_book_videos(url: str) -> None:
    await Tortoise.init(config=TORTOISE_ORM)
    videos = await BookVideo.all()
    for video in videos:
        video.video_url = url
        video.video_intro = BOOK_INTRO_VIDEO_INTRO
        await video.save()
    print(f"已更新 {len(videos)} 条图书视频为: {url}")
    await Tortoise.close_connections()


def main() -> None:
    parser = argparse.ArgumentParser(description="同步图书解读视频素材")
    parser.add_argument(
        "--upload-dir",
        default=None,
        help="uploads 根目录，默认 UPLOAD_DIR 或 backend/uploads",
    )
    parser.add_argument(
        "--files-only",
        action="store_true",
        help="仅复制文件，不更新数据库",
    )
    args = parser.parse_args()

    upload_root = resolve_upload_root(args.upload_dir)
    copied, _ = sync_book_review_to_uploads(upload_root)
    url = book_intro_video_url(upload_root)
    print(f"素材来源: {BOOK_REVIEW_SOURCE_DIR}")
    print(f"已同步 {len(copied)} 个文件到 {upload_root / 'bookReview'}")
    print(f"默认解读视频 URL: {url}")

    if args.files_only:
        return

    asyncio.run(update_book_videos(url))


if __name__ == "__main__":
    main()
