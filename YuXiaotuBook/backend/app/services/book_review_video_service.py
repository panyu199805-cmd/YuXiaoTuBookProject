"""图书解读视频 — 读写 uploads/bookReview 或本地 网站素材/图书页面素材。"""
from __future__ import annotations

import os
import re
from pathlib import Path
from typing import List, Optional, Set

from app.core.config import settings

BOOK_REVIEW_SUBDIR = "bookReview"
BOOK_REVIEW_URL_PREFIX = f"/uploads/{BOOK_REVIEW_SUBDIR}"
VIDEO_EXTS = {".mp4", ".webm"}
MAX_BOOK_REVIEW_VIDEOS = 20


def local_book_review_source_dir() -> Optional[Path]:
    here = Path(__file__).resolve()
    seen: Set[str] = set()
    for depth in range(2, min(len(here.parents), 7)):
        for base in (here.parents[depth], here.parents[depth].parent):
            key = str(base)
            if key in seen:
                continue
            seen.add(key)
            candidate = base / "网站素材" / "图书页面素材"
            if candidate.is_dir():
                return candidate
    return None


def resolve_book_review_storage_dir() -> str:
    env_dir = (getattr(settings, "BOOK_REVIEW_VIDEO_DIR", None) or "").strip()
    if env_dir:
        target = env_dir
    else:
        local_dir = local_book_review_source_dir()
        if local_dir is not None:
            target = str(local_dir)
        else:
            target = os.path.join(settings.UPLOAD_DIR, BOOK_REVIEW_SUBDIR)
    os.makedirs(target, exist_ok=True)
    return target


def book_review_dir() -> str:
    return resolve_book_review_storage_dir()


def sanitize_filename(name: str) -> str:
    base = os.path.basename(name or "video.mp4")
    base = re.sub(r"[^\w.\-()\u4e00-\u9fff]", "_", base)
    if not base or base.startswith("."):
        base = "video.mp4"
    ext = os.path.splitext(base)[1].lower()
    if ext not in VIDEO_EXTS:
        base = f"{os.path.splitext(base)[0] or 'video'}.mp4"
    return base


def unique_filename(name: str) -> str:
    safe = sanitize_filename(name)
    directory = book_review_dir()
    candidate = safe
    stem, ext = os.path.splitext(safe)
    index = 1
    while os.path.exists(os.path.join(directory, candidate)):
        candidate = f"{stem}_{index}{ext}"
        index += 1
    return candidate


def is_book_review_video_url(url: str) -> bool:
    if not isinstance(url, str):
        return False
    if url.startswith(f"{BOOK_REVIEW_URL_PREFIX}/"):
        return True
    filename = os.path.basename(url.split("?", 1)[0])
    if filename and re.search(r"\.(mp4|webm)$", filename, re.I):
        return os.path.isfile(os.path.join(book_review_dir(), filename))
    return False


def url_to_path(url: str) -> Optional[str]:
    if not url or not isinstance(url, str):
        return None
    url = url.strip()
    if url.startswith(f"{BOOK_REVIEW_URL_PREFIX}/"):
        filename = url[len(BOOK_REVIEW_URL_PREFIX) + 1 :]
    elif url.startswith("/uploads/"):
        filename = url[len("/uploads/") :].split("?", 1)[0]
    else:
        return None
    if not filename or ".." in filename:
        return None
    filename = filename.replace("\\", "/").strip("/")
    if not filename:
        return None
    if "/" in filename:
        nested = os.path.join(settings.UPLOAD_DIR, filename)
        if os.path.isfile(nested):
            return nested
    basename = os.path.basename(filename)
    if not basename:
        return None
    review_path = os.path.join(book_review_dir(), basename)
    if os.path.isfile(review_path):
        return review_path
    legacy_path = os.path.join(settings.UPLOAD_DIR, basename)
    if os.path.isfile(legacy_path):
        return legacy_path
    return None


def normalize_book_review_url(url: str) -> str:
    path = url_to_path(url)
    if not path:
        return url
    return f"{BOOK_REVIEW_URL_PREFIX}/{os.path.basename(path)}"


def list_book_review_video_urls() -> List[str]:
    directory = book_review_dir()
    if not os.path.isdir(directory):
        return []
    names = [
        name
        for name in os.listdir(directory)
        if os.path.isfile(os.path.join(directory, name))
        and os.path.splitext(name)[1].lower() in VIDEO_EXTS
    ]
    names.sort(key=str.lower)
    return [f"{BOOK_REVIEW_URL_PREFIX}/{name}" for name in names]


def save_book_review_video(filename: str, content: bytes) -> str:
    final_name = unique_filename(filename)
    path = os.path.join(book_review_dir(), final_name)
    with open(path, "wb") as handle:
        handle.write(content)
    return f"{BOOK_REVIEW_URL_PREFIX}/{final_name}"


def delete_book_review_video(url: str) -> bool:
    path = url_to_path(url)
    if path and os.path.isfile(path):
        os.remove(path)
        return True
    return False


def is_external_video_url(url: str) -> bool:
    if not isinstance(url, str):
        return False
    lowered = url.strip().lower()
    return lowered.startswith("http://") or lowered.startswith("https://")


def is_valid_book_video_url(url: str) -> bool:
    if not url or not isinstance(url, str):
        return False
    raw = url.strip()
    if is_external_video_url(raw):
        return True
    if is_book_review_video_url(raw):
        return True
    if raw.startswith("/uploads/"):
        return True
    return False


def normalize_book_video_url(url: str) -> str:
    raw = (url or "").strip()
    if not raw:
        return raw
    if is_external_video_url(raw):
        return raw
    return normalize_book_review_url(raw)
