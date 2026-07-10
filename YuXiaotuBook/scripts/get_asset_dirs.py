"""输出素材目录 JSON，供 PowerShell 部署脚本读取（避免中文路径编码问题）。"""
from __future__ import annotations

import json

from book_video_asset import BOOK_REVIEW_SOURCE_DIR
from site_video_asset import HOME_EXHIBITION_SOURCE_DIR

print(
    json.dumps(
        {
            "home_exhibition": str(HOME_EXHIBITION_SOURCE_DIR),
            "book_review": str(BOOK_REVIEW_SOURCE_DIR),
        },
        ensure_ascii=False,
    )
)
