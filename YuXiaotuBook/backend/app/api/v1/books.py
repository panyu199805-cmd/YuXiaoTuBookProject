from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends
from tortoise.expressions import Q

from app.core.config import settings
from app.core.deps import get_current_user_optional
from app.core.response import fail, success
from app.models import Book, BookVideo, User, UserBookCollect
from app.schemas.requests import PlayReportRequest
from app.services.book_service import book_list_item, book_to_dict
from app.services.member_service import is_vip
from app.services.video_url_service import to_protected_video_url

router = APIRouter()

_play_reported: set = set()


@router.get("")
async def list_books(
    category_id: Optional[int] = None,
    sort: str = "hot",
    keyword: Optional[str] = None,
    page: int = 1,
    page_size: int = 12,
):
    qs = Book.filter(status="published")
    if category_id:
        qs = qs.filter(category_id=category_id)
    if keyword:
        qs = qs.filter(Q(title__icontains=keyword) | Q(author__icontains=keyword))

    if sort == "new":
        qs = qs.order_by("-created_at", "-id")
    else:
        qs = qs.order_by("-view_count", "-id")

    all_books = await qs
    # has_video 优先（内存排序，一期数据量小）
    async def has_video(b: Book) -> bool:
        return await BookVideo.filter(book_id=b.id, status=1).exists()

    enriched = []
    for b in all_books:
        enriched.append((await has_video(b), b))
    enriched.sort(key=lambda x: (-int(x[0]), -x[1].view_count, -x[1].id))

    total = len(enriched)
    start = (page - 1) * page_size
    page_items = enriched[start : start + page_size]
    items = [await book_list_item(b) for _, b in page_items]
    return success({"list": items, "total": total, "page": page, "page_size": page_size})


@router.get("/{book_id}")
async def book_detail(
    book_id: int,
    user: Optional[User] = Depends(get_current_user_optional),
):
    book = await Book.get_or_none(id=book_id, status="published")
    if not book:
        return fail("书籍不存在", 404)
    book.view_count += 1
    await book.save()
    if user:
        exists = await UserBookCollect.filter(
            user_id=user.id, book_id=book.id, collect_type=2
        ).exists()
        if not exists:
            await UserBookCollect.create(
                user_id=user.id, book_id=book.id, collect_type=2
            )
    return success(await book_to_dict(book))


@router.get("/{book_id}/play-auth", tags=["书籍"], summary="获取播放地址")
async def play_auth(
    book_id: int,
    user: Optional[User] = Depends(get_current_user_optional),
):
    book = await Book.get_or_none(id=book_id, status="published")
    if not book:
        return fail("书籍不存在", 404)
    video = await BookVideo.get_or_none(book_id=book_id, status=1)
    if not video:
        return fail("暂无解读视频", 404)

    full_access = user is not None
    max_duration = None
    if not full_access and settings.GUEST_VIDEO_PREVIEW_SECONDS > 0:
        max_duration = settings.GUEST_VIDEO_PREVIEW_SECONDS

    vip = await is_vip(user.id) if user else False
    return success(
        {
            "video_url": to_protected_video_url(video.video_url),
            "poster": video.video_cover,
            "duration": video.video_duration,
            "full_access": full_access,
            "max_duration": max_duration,
            "is_vip": vip,
        }
    )


@router.post("/{book_id}/play-report")
async def play_report(book_id: int, body: PlayReportRequest):
    if body.position < 30:
        return success(None)
    key = (book_id,)
    if key in _play_reported:
        return success(None)
    video = await BookVideo.get_or_none(book_id=book_id, status=1)
    if video:
        video.play_count += 1
        await video.save()
        _play_reported.add(key)
    return success(None)


@router.get("/{book_id}/similar")
async def similar(book_id: int):
    book = await Book.get_or_none(id=book_id, status="published")
    if not book:
        return fail("书籍不存在", 404)
    others = (
        await Book.filter(status="published", category_id=book.category_id)
        .exclude(id=book_id)
        .order_by("-view_count")
        .limit(6)
    )
    return success([await book_list_item(b) for b in others])
