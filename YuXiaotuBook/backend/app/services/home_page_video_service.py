"""首页背景视频 — 本地读写 网站素材/首页展览素材，生产读写 uploads/homePage。"""
from __future__ import annotations

import os
import re
from pathlib import Path
from typing import List, Optional, Set

from app.core.config import settings

HOME_PAGE_SUBDIR = "homePage"
HOME_PAGE_URL_PREFIX = f"/uploads/{HOME_PAGE_SUBDIR}"
VIDEO_EXTS = {".mp4", ".webm"}


def local_exhibition_source_dir() -> Optional[Path]:
    """查找本地素材目录 网站素材/首页展览素材（Docker 内通常不存在）。"""
    here = Path(__file__).resolve()
    seen: Set[str] = set()
    for depth in range(2, min(len(here.parents), 7)):
        for base in (here.parents[depth], here.parents[depth].parent):
            key = str(base)
            if key in seen:
                continue
            seen.add(key)
            candidate = base / "网站素材" / "首页展览素材"
            if candidate.is_dir():
                return candidate
    return None


def resolve_home_page_storage_dir() -> str:
    """
    解析首页视频物理存储目录：
    - HOME_PAGE_VIDEO_DIR 环境变量（最高优先级）
    - 本地开发：网站素材/首页展览素材（若存在）
    - 生产环境：UPLOAD_DIR/homePage（即 /usr/local/projects/yuxiaotu/data/uploads/homePage）
    """
    env_dir = (settings.HOME_PAGE_VIDEO_DIR or "").strip()
    if env_dir:
        target = env_dir
    else:
        local_dir = local_exhibition_source_dir()
        if local_dir is not None:
            target = str(local_dir)
        else:
            target = os.path.join(settings.UPLOAD_DIR, HOME_PAGE_SUBDIR)
    os.makedirs(target, exist_ok=True)
    return target


def home_page_dir() -> str:
    return resolve_home_page_storage_dir()


def is_local_exhibition_storage() -> bool:
    local_dir = local_exhibition_source_dir()
    if not local_dir:
        return False
    try:
        return Path(home_page_dir()).resolve() == local_dir.resolve()
    except OSError:
        return False


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
    directory = home_page_dir()
    candidate = safe
    stem, ext = os.path.splitext(safe)
    index = 1
    while os.path.exists(os.path.join(directory, candidate)):
        candidate = f"{stem}_{index}{ext}"
        index += 1
    return candidate


def is_home_page_video_url(url: str) -> bool:
    if not isinstance(url, str):
        return False
    if url.startswith(f"{HOME_PAGE_URL_PREFIX}/"):
        return True
    # 兼容旧配置：/uploads/xxx.mp4 且文件实际在 homePage 目录
    filename = os.path.basename(url.split("?", 1)[0])
    if filename and re.search(r"\.(mp4|webm)$", filename, re.I):
        return os.path.isfile(os.path.join(home_page_dir(), filename))
    return False


def url_to_path(url: str) -> Optional[str]:
    if not url or not isinstance(url, str):
        return None
    url = url.strip()
    if url.startswith(f"{HOME_PAGE_URL_PREFIX}/"):
        filename = url[len(HOME_PAGE_URL_PREFIX) + 1 :]
    elif url.startswith("/uploads/"):
        filename = url[len("/uploads/") :].split("?", 1)[0]
    else:
        return None
    if not filename or ".." in filename:
        return None
    filename = filename.replace("\\", "/").strip("/")
    if not filename:
        return None
    # /uploads/homePage/foo.mp4
    if "/" in filename:
        nested = os.path.join(settings.UPLOAD_DIR, filename)
        if os.path.isfile(nested):
            return nested
    basename = os.path.basename(filename)
    if not basename:
        return None
    home_path = os.path.join(home_page_dir(), basename)
    if os.path.isfile(home_path):
        return home_path
    # 兼容旧配置：/uploads/foo.mp4 直接位于 uploads 根目录
    legacy_path = os.path.join(settings.UPLOAD_DIR, basename)
    if os.path.isfile(legacy_path):
        return legacy_path
    return None


def normalize_home_page_url(url: str) -> str:
    path = url_to_path(url)
    if not path:
        return url
    return f"{HOME_PAGE_URL_PREFIX}/{os.path.basename(path)}"


def list_home_page_video_urls() -> List[str]:
    directory = home_page_dir()
    if not os.path.isdir(directory):
        return []
    names = [
        name
        for name in os.listdir(directory)
        if os.path.isfile(os.path.join(directory, name))
        and os.path.splitext(name)[1].lower() in VIDEO_EXTS
    ]
    names.sort(key=str.lower)
    return [f"{HOME_PAGE_URL_PREFIX}/{name}" for name in names]


def save_home_page_video(filename: str, content: bytes) -> str:
    final_name = unique_filename(filename)
    path = os.path.join(home_page_dir(), final_name)
    with open(path, "wb") as handle:
        handle.write(content)
    return f"{HOME_PAGE_URL_PREFIX}/{final_name}"


def delete_home_page_file(filename: str) -> bool:
    if not filename or ".." in filename or "/" in filename or "\\" in filename:
        return False
    path = os.path.join(home_page_dir(), filename)
    if os.path.isfile(path):
        os.remove(path)
        return True
    return False


def delete_home_page_video(url: str) -> bool:
    path = url_to_path(url)
    if path and os.path.isfile(path):
        os.remove(path)
        return True
    return False


def purge_home_page_videos(exclude_urls: Optional[List[str]] = None) -> List[str]:
    """删除存储目录中不在保留列表内的视频。"""
    exclude_urls = exclude_urls or []
    keep_names: Set[str] = set()
    for url in exclude_urls:
        path = url_to_path(url)
        if path:
            keep_names.add(os.path.basename(path))

    removed: List[str] = []
    directory = home_page_dir()
    if not os.path.isdir(directory):
        return removed

    for name in os.listdir(directory):
        full_path = os.path.join(directory, name)
        if not os.path.isfile(full_path):
            continue
        if os.path.splitext(name)[1].lower() not in VIDEO_EXTS:
            continue
        if name in keep_names:
            continue
        os.remove(full_path)
        removed.append(f"{HOME_PAGE_URL_PREFIX}/{name}")
    return removed


def clear_home_page_videos() -> List[str]:
    """清空存储目录内全部视频。"""
    return purge_home_page_videos([])


def merge_bg_videos_with_folder(stored_urls: Optional[List[str]], limit: int = 6) -> List[str]:
    """按 DB 顺序合并目录内实际存在的视频。"""
    existing = list_home_page_video_urls()
    existing_set = set(existing)
    ordered: List[str] = []

    if stored_urls:
        for item in stored_urls:
            if not item or not isinstance(item, str):
                continue
            raw = item.strip()
            if not url_to_path(raw):
                continue
            normalized = normalize_home_page_url(raw)
            candidate = normalized if normalized in existing_set else raw
            if candidate not in ordered:
                ordered.append(candidate)

    for url in existing:
        if url not in ordered:
            ordered.append(url)

    return ordered[:limit]
