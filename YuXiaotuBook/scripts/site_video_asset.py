"""首页展览视频素材 — 固定来源目录配置与同步。"""
from __future__ import annotations

import os
import shutil
from pathlib import Path
from typing import List, Tuple

from video_optimize import optimize_mp4_if_needed

# 仓库根目录（YuXiaoTuBook/scripts -> ../../..）
REPO_ROOT = Path(__file__).resolve().parent.parent.parent

# 首页展览视频唯一素材目录（相对仓库根）
HOME_EXHIBITION_SOURCE_DIR = REPO_ROOT / "网站素材" / "首页展览素材"

# 部署到 uploads 的子目录（生产：/usr/local/projects/yuxiaotu/data/uploads/homePage）
HOME_EXHIBITION_UPLOAD_SUBDIR = "homePage"
HOME_EXHIBITION_UPLOAD_URL_PREFIX = f"/uploads/{HOME_EXHIBITION_UPLOAD_SUBDIR}"


def resolve_upload_root(explicit: Path | str | None = None) -> Path:
    """解析 uploads 根目录（优先显式参数，其次 UPLOAD_DIR 环境变量）。"""
    if explicit:
        return Path(explicit)
    env = os.environ.get("UPLOAD_DIR")
    if env:
        return Path(env)
    backend_dir = Path(__file__).resolve().parent.parent / "backend"
    return backend_dir / "uploads"


def list_home_exhibition_source_files() -> List[Path]:
    """列出素材目录下全部 mp4（按文件名排序）。"""
    if not HOME_EXHIBITION_SOURCE_DIR.is_dir():
        return []
    return sorted(HOME_EXHIBITION_SOURCE_DIR.glob("*.mp4"), key=lambda p: p.name.lower())


def list_uploaded_exhibition_files(upload_root: Path | str) -> List[Path]:
    """列出 uploads/homePage 下已部署的 mp4。"""
    dest_dir = Path(upload_root) / HOME_EXHIBITION_UPLOAD_SUBDIR
    if not dest_dir.is_dir():
        return []
    return sorted(dest_dir.glob("*.mp4"), key=lambda p: p.name.lower())


def exhibition_urls_from_upload_root(upload_root: Path | str) -> List[str]:
    """根据 uploads 中已有文件生成 URL 列表。"""
    return [
        f"{HOME_EXHIBITION_UPLOAD_URL_PREFIX}/{path.name}"
        for path in list_uploaded_exhibition_files(upload_root)
    ]


def home_exhibition_upload_urls(upload_root: Path | str | None = None) -> List[str]:
    """返回首页展览视频 URL 列表（优先素材目录，否则读 uploads）。"""
    root = resolve_upload_root(upload_root)
    if list_home_exhibition_source_files():
        return [f"{HOME_EXHIBITION_UPLOAD_URL_PREFIX}/{path.name}" for path in list_home_exhibition_source_files()]
    return exhibition_urls_from_upload_root(root)


def sync_home_exhibition_to_uploads(upload_root: Path | str | None = None) -> Tuple[List[Path], List[str]]:
    """
    将 网站素材/首页展览素材 下 mp4 同步到 uploads/homePage/。
    若素材目录不存在，则仅返回 uploads 中已有文件的 URL。
    返回 (已复制/已有文件路径列表, URL 列表)。
    """
    root = resolve_upload_root(upload_root)
    sources = list_home_exhibition_source_files()
    if not sources:
        existing = list_uploaded_exhibition_files(root)
        return existing, exhibition_urls_from_upload_root(root)

    dest_dir = root / HOME_EXHIBITION_UPLOAD_SUBDIR
    try:
        if dest_dir.resolve() == HOME_EXHIBITION_SOURCE_DIR.resolve():
            return sources, home_exhibition_upload_urls(root)
    except OSError:
        pass

    dest_dir.mkdir(parents=True, exist_ok=True)

    copied: List[Path] = []
    for src in sources:
        dest = dest_dir / src.name
        if (not dest.exists()) or dest.stat().st_size != src.stat().st_size:
            shutil.copy2(src, dest)
        optimize_mp4_if_needed(dest)
        copied.append(dest)

    return copied, home_exhibition_upload_urls(root)
