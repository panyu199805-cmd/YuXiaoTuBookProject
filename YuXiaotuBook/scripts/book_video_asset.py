"""图书详情页解读视频素材 — 固定来源目录配置与同步。"""
from __future__ import annotations

import shutil
from pathlib import Path
from typing import List, Tuple

from site_video_asset import REPO_ROOT, resolve_upload_root
from video_optimize import optimize_mp4_if_needed

# 图书解读视频唯一素材目录（相对仓库根）
BOOK_REVIEW_SOURCE_DIR = REPO_ROOT / "网站素材" / "图书页面素材"

# 部署到 uploads 的子目录（生产：/usr/local/projects/yuxiaotu/data/uploads/bookReview）
BOOK_REVIEW_UPLOAD_SUBDIR = "bookReview"
BOOK_REVIEW_UPLOAD_URL_PREFIX = f"/uploads/{BOOK_REVIEW_UPLOAD_SUBDIR}"

# 默认解读视频文件名
BOOK_REVIEW_DEFAULT_FILENAME = "宇小兔自我介绍视频2.mp4"
BOOK_INTRO_VIDEO_INTRO = "宇小兔为你介绍本书"
BOOK_INTRO_VIDEO_URL = f"{BOOK_REVIEW_UPLOAD_URL_PREFIX}/{BOOK_REVIEW_DEFAULT_FILENAME}"


def list_book_review_source_files() -> List[Path]:
    """列出素材目录下全部 mp4（按文件名排序）。"""
    if not BOOK_REVIEW_SOURCE_DIR.is_dir():
        return []
    return sorted(BOOK_REVIEW_SOURCE_DIR.glob("*.mp4"), key=lambda p: p.name.lower())


def list_uploaded_book_review_files(upload_root: Path | str) -> List[Path]:
    """列出 uploads/bookReview 下已部署的 mp4。"""
    dest_dir = Path(upload_root) / BOOK_REVIEW_UPLOAD_SUBDIR
    if not dest_dir.is_dir():
        return []
    return sorted(dest_dir.glob("*.mp4"), key=lambda p: p.name.lower())


def book_review_upload_urls(upload_root: Path | str | None = None) -> List[str]:
    """返回图书解读视频 URL 列表。"""
    root = resolve_upload_root(upload_root)
    if list_book_review_source_files():
        return [
            f"{BOOK_REVIEW_UPLOAD_URL_PREFIX}/{path.name}"
            for path in list_book_review_source_files()
        ]
    return [
        f"{BOOK_REVIEW_UPLOAD_URL_PREFIX}/{path.name}"
        for path in list_uploaded_book_review_files(root)
    ]


def book_intro_video_url(upload_root: Path | str | None = None) -> str:
    """返回默认图书解读视频 URL（优先默认文件名，否则取第一个）。"""
    root = resolve_upload_root(upload_root)
    preferred = root / BOOK_REVIEW_UPLOAD_SUBDIR / BOOK_REVIEW_DEFAULT_FILENAME
    if preferred.exists():
        return BOOK_INTRO_VIDEO_URL
    uploaded = list_uploaded_book_review_files(root)
    if uploaded:
        return f"{BOOK_REVIEW_UPLOAD_URL_PREFIX}/{uploaded[0].name}"
    for src in list_book_review_source_files():
        if src.name == BOOK_REVIEW_DEFAULT_FILENAME:
            return BOOK_INTRO_VIDEO_URL
    sources = list_book_review_source_files()
    if sources:
        return f"{BOOK_REVIEW_UPLOAD_URL_PREFIX}/{sources[0].name}"
    return BOOK_INTRO_VIDEO_URL


def sync_book_review_to_uploads(upload_root: Path | str | None = None) -> Tuple[List[Path], List[str]]:
    """
    将 网站素材/图书页面素材 下 mp4 同步到 uploads/bookReview/。
    若素材目录不存在，则仅返回 uploads 中已有文件的 URL。
    """
    root = resolve_upload_root(upload_root)
    sources = list_book_review_source_files()
    if not sources:
        existing = list_uploaded_book_review_files(root)
        return existing, book_review_upload_urls(root)

    dest_dir = root / BOOK_REVIEW_UPLOAD_SUBDIR
    dest_dir.mkdir(parents=True, exist_ok=True)

    copied: List[Path] = []
    for src in sources:
        dest = dest_dir / src.name
        if (not dest.exists()) or dest.stat().st_size != src.stat().st_size:
            shutil.copy2(src, dest)
        optimize_mp4_if_needed(dest)
        copied.append(dest)

    return copied, book_review_upload_urls(root)
