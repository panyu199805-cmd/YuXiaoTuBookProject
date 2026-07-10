from __future__ import annotations

from typing import Any, Dict, List, Optional

from app.models import SiteConfig
from app.services.home_page_video_service import home_page_dir, merge_bg_videos_with_folder

MAX_BG_VIDEOS = 6


def normalize_bg_videos(urls: Optional[List[str]] = None) -> List[str]:
    if not urls:
        return []
    if isinstance(urls, str):
        urls = [urls]
    cleaned: List[str] = []
    for item in urls:
        if not item or not isinstance(item, str):
            continue
        url = item.strip()
        if url and url not in cleaned:
            cleaned.append(url)
        if len(cleaned) >= MAX_BG_VIDEOS:
            break
    return cleaned


def site_config_to_dict(cfg: SiteConfig) -> Dict[str, Any]:
    raw_videos = getattr(cfg, "bg_videos", None)
    stored = normalize_bg_videos(raw_videos if isinstance(raw_videos, list) else None)
    if not stored and cfg.bg_type == "video" and cfg.bg_url:
        stored = normalize_bg_videos([cfg.bg_url])
    bg_videos = merge_bg_videos_with_folder(stored, MAX_BG_VIDEOS)
    bg_url = bg_videos[0] if bg_videos else cfg.bg_url
    return {
        "id": cfg.id,
        "bg_type": "video" if bg_videos else cfg.bg_type,
        "bg_url": bg_url,
        "bg_videos": bg_videos,
        "home_page_storage_dir": home_page_dir(),
        "bg_music": cfg.bg_music,
        "white_noise": cfg.white_noise,
        "music_enabled": cfg.music_enabled,
        "bg_enabled": cfg.bg_enabled,
        "featured_book_id": cfg.featured_book_id,
        "promo_title": cfg.promo_title,
        "daily_sentence": cfg.daily_sentence,
    }


def public_site_config_dict(cfg: SiteConfig) -> Dict[str, Any]:
    data = site_config_to_dict(cfg)
    return {
        "bg_type": data["bg_type"],
        "bg_url": data["bg_url"],
        "bg_videos": data["bg_videos"],
        "bg_music": data["bg_music"],
        "white_noise": data["white_noise"],
        "music_enabled": data["music_enabled"],
        "bg_enabled": data["bg_enabled"],
        "promo_title": data["promo_title"],
        "daily_sentence": data["daily_sentence"],
    }
