from __future__ import annotations

from typing import Any, Dict, List, Optional

from app.models import Book, BookVideo, Category


async def list_active_book_videos(book_id: int) -> List[BookVideo]:
    return await BookVideo.filter(book_id=book_id, status=1).order_by("sort_order", "id")


async def book_to_dict(book: Book, with_video_meta: bool = True) -> Dict[str, Any]:
    category = await Category.get_or_none(id=book.category_id)
    videos = await list_active_book_videos(book.id) if with_video_meta else []
    first = videos[0] if videos else None
    data: Dict[str, Any] = {
        "id": book.id,
        "title": book.title,
        "author": book.author,
        "cover": book.cover,
        "category": {"id": category.id, "name": category.name} if category else None,
        "price": float(book.price),
        "stock": book.stock,
        "summary": book.summary,
        "highlight": book.highlight,
        "target_audience": book.target_audience,
        "status": book.status,
        "view_count": book.view_count,
        "has_video": first is not None,
        "video_count": len(videos),
    }
    if with_video_meta and first:
        data["video"] = {
            "duration": first.video_duration,
            "cover": first.video_cover,
            "intro": first.video_intro,
        }
        if first.explain_content:
            raw = first.explain_content.strip()
            if "---\n" in raw:
                title, body = raw.split("---\n", 1)
                data["ebook_title"] = title.strip()
                data["ebook_content"] = body.strip()
            else:
                data["ebook_content"] = raw
    return data


async def book_list_item(book: Book) -> Dict[str, Any]:
    has_video = await BookVideo.filter(book_id=book.id, status=1).exists()
    category = await Category.get_or_none(id=book.category_id)
    return {
        "id": book.id,
        "title": book.title,
        "author": book.author,
        "cover": book.cover,
        "highlight": book.highlight,
        "category": {"id": category.id, "name": category.name} if category else None,
        "price": float(book.price),
        "has_video": has_video,
        "view_count": book.view_count,
    }


def video_to_dict(video: BookVideo) -> Dict[str, Any]:
    return {
        "id": video.id,
        "book_id": video.book_id,
        "sort_order": video.sort_order,
        "video_cover": video.video_cover,
        "video_url": video.video_url,
        "video_duration": video.video_duration,
        "video_intro": video.video_intro,
        "status": video.status,
        "play_count": video.play_count,
    }
