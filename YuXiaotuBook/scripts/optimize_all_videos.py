#!/usr/bin/env python3
"""批量将素材目录中的 MP4 转为 Web 播放友好格式。"""
from __future__ import annotations

import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from book_video_asset import BOOK_REVIEW_SOURCE_DIR
from site_video_asset import HOME_EXHIBITION_SOURCE_DIR, resolve_upload_root
from video_optimize import optimize_directory


def main() -> None:
    targets: list[Path] = []
    if len(sys.argv) > 1:
        targets = [Path(p) for p in sys.argv[1:]]
    else:
        upload_root = resolve_upload_root()
        for candidate in (
            HOME_EXHIBITION_SOURCE_DIR,
            BOOK_REVIEW_SOURCE_DIR,
            upload_root / "homePage",
            upload_root / "bookReview",
        ):
            if candidate.is_dir():
                targets.append(candidate)

    if not targets:
        print("未找到可优化的视频目录")
        sys.exit(1)

    total = 0
    for directory in targets:
        print(f"\n=== {directory} ===")
        total += optimize_directory(directory)
    print(f"\n共优化 {total} 个文件")


if __name__ == "__main__":
    main()
