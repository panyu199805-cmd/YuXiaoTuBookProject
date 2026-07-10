"""同步首页展览视频到 uploads，并更新站点 bg_videos 配置。"""
from __future__ import annotations

import argparse
import asyncio
import os
import sys
from pathlib import Path

BACKEND_DIR = os.path.join(os.path.dirname(__file__), "..", "backend")
sys.path.insert(0, os.path.abspath(BACKEND_DIR))
sys.path.insert(0, os.path.dirname(__file__))

from tortoise import Tortoise

from app.db.database import TORTOISE_ORM
from app.models import SiteConfig
from site_video_asset import (
    HOME_EXHIBITION_SOURCE_DIR,
    resolve_upload_root,
    sync_home_exhibition_to_uploads,
)


async def update_site_config(urls: list[str]) -> None:
    if not urls:
        print(f"警告: 素材目录为空或无 mp4: {HOME_EXHIBITION_SOURCE_DIR}")
        return
    await Tortoise.init(config=TORTOISE_ORM)
    cfg, created = await SiteConfig.get_or_create(id=1)
    cfg.bg_type = "video"
    cfg.bg_enabled = True
    cfg.bg_url = urls[0]
    cfg.bg_videos = urls
    await cfg.save()
    action = "创建" if created else "更新"
    print(f"已{action}首页展览视频 ({len(urls)} 个):")
    for url in urls:
        print(f"  - {url}")
    await Tortoise.close_connections()


def main() -> None:
    parser = argparse.ArgumentParser(description="同步首页展览视频素材")
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
    copied, urls = sync_home_exhibition_to_uploads(upload_root)
    print(f"素材来源: {HOME_EXHIBITION_SOURCE_DIR}")
    print(f"已同步 {len(copied)} 个文件到 {upload_root / 'homePage'}")

    if args.files_only:
        return

    asyncio.run(update_site_config(urls))


if __name__ == "__main__":
    main()
