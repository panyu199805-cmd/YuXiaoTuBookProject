from __future__ import annotations

import os
import uuid
from typing import List, Optional

from fastapi import APIRouter, Depends, File, UploadFile

from app.core.config import settings
from app.core.deps import get_admin_user
from app.core.response import fail, success
from datetime import date, datetime, time, timedelta

from app.models import (
    Book,
    BookVideo,
    Category,
    DailyBook,
    MemberOrder,
    MemberPackage,
    Order,
    OrderItem,
    SiteConfig,
    User,
    UserBookCollect,
    UserMember,
)
from app.schemas.requests import (
    BookCreateRequest,
    BookUpdateRequest,
    CategoryRequest,
    DailyBookRequest,
    DailyBookUpdateRequest,
    MemberPackageRequest,
    ShipOrderRequest,
    AdminOrderUpdateRequest,
    SiteConfigRequest,
    AdminUserUpdateRequest,
    VideoBindRequest,
    BookVideosUpdateRequest,
    AiGenerateRequest,
    AiItemUpdateRequest,
    AiItemAcceptRequest,
)
from app.services.book_service import book_to_dict, video_to_dict
from app.services.daily_service import daily_to_dict
from app.services.order_helpers import (
    STATUS_LABELS,
    filter_admin_orders,
    order_to_dict,
    summarize_book_names,
)
from app.services.order_service import OrderService
from app.services.home_page_video_service import (
    HOME_PAGE_URL_PREFIX,
    clear_home_page_videos,
    delete_home_page_video,
    home_page_dir,
    is_home_page_video_url,
    list_home_page_video_urls,
    merge_bg_videos_with_folder,
    normalize_home_page_url,
    purge_home_page_videos,
    save_home_page_video,
    url_to_path,
)
from app.services.book_review_video_service import (
    BOOK_REVIEW_URL_PREFIX,
    MAX_BOOK_REVIEW_VIDEOS,
    book_review_dir,
    delete_book_review_video,
    is_book_review_video_url,
    list_book_review_video_urls,
    normalize_book_review_url,
    normalize_book_video_url,
    is_valid_book_video_url,
    save_book_review_video,
    url_to_path as book_review_url_to_path,
)
from app.services.site_config_helpers import (
    MAX_BG_VIDEOS,
    normalize_bg_videos,
    site_config_to_dict,
)
from app.services.analytics_service import (
    build_order_stats,
    build_overview_stats,
    build_reading_stats,
    build_region_stats,
    build_system_stats,
)
from app.services.user_admin_service import build_user_region_tree, get_admin_user_detail
from app.services.ai_content_service import (
    accept_item,
    ai_runtime_config,
    create_and_run_task,
    discard_item,
    get_task_detail,
    list_tasks,
    update_item_text,
)

upload_router = APIRouter(tags=["Admin-上传"])
books_router = APIRouter(tags=["Admin-书籍"])
videos_router = APIRouter(tags=["Admin-视频"])
categories_router = APIRouter(tags=["Admin-分类"])
orders_router = APIRouter(tags=["Admin-订单"])
site_router = APIRouter(tags=["Admin-氛围配置"])
daily_router = APIRouter(tags=["Admin-每日读书"])
member_router = APIRouter(tags=["Admin-会员"])
users_router = APIRouter(tags=["Admin-用户"])
stats_router = APIRouter(tags=["Admin-数据统计"])
ai_router = APIRouter(tags=["Admin-AI内容"])

router = APIRouter()

REVENUE_STATUSES = ("paid", "shipped", "completed")

IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".webp"}
VIDEO_EXTS = {".mp4", ".webm"}
MAX_IMAGE_SIZE = 5 * 1024 * 1024
MAX_VIDEO_SIZE = 50 * 1024 * 1024
MAX_HOME_PAGE_VIDEO_SIZE = 100 * 1024 * 1024


@upload_router.post("/upload", summary="上传图片或视频")
async def upload_file(
    file: UploadFile = File(...),
    user: User = Depends(get_admin_user),
):
    ext = os.path.splitext(file.filename or "")[1].lower()
    if ext in IMAGE_EXTS:
        media_type = "image"
        max_size = MAX_IMAGE_SIZE
    elif ext in VIDEO_EXTS:
        media_type = "video"
        max_size = MAX_VIDEO_SIZE
    else:
        return fail("仅支持 jpg/png/webp/mp4/webm", 400)
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    name = f"{uuid.uuid4().hex}{ext}"
    path = os.path.join(settings.UPLOAD_DIR, name)
    content = await file.read()
    if len(content) > max_size:
        limit_mb = max_size // (1024 * 1024)
        return fail(f"文件不能超过{limit_mb}MB", 400)
    with open(path, "wb") as f:
        f.write(content)
    url = f"/uploads/{name}"
    return success({"url": url, "media_type": media_type})


@upload_router.post("/home-page-videos/upload", summary="上传首页背景视频到 homePage 目录")
async def upload_home_page_video(
    file: UploadFile = File(...),
    user: User = Depends(get_admin_user),
):
    ext = os.path.splitext(file.filename or "")[1].lower()
    if ext not in VIDEO_EXTS:
        return fail("首页背景仅支持 mp4/webm", 400)
    content = await file.read()
    if len(content) > MAX_HOME_PAGE_VIDEO_SIZE:
        return fail("视频不能超过100MB", 400)
    url = save_home_page_video(file.filename or "video.mp4", content)
    return success({"url": url, "media_type": "video"})


@upload_router.delete("/home-page-videos", summary="删除 homePage 目录中的背景视频")
async def delete_home_page_video_file(
    url: str,
    user: User = Depends(get_admin_user),
):
    if not is_home_page_video_url(url):
        return fail(f"仅允许删除 {HOME_PAGE_URL_PREFIX}/ 下的视频", 400)
    if not url_to_path(url):
        return fail("无效的视频路径", 400)
    if not delete_home_page_video(url):
        return fail("视频不存在或已删除", 404)
    return success(None, "已删除")


@upload_router.post("/book-review-videos/upload", summary="上传图书解读视频到 bookReview 目录")
async def upload_book_review_video(
    file: UploadFile = File(...),
    user: User = Depends(get_admin_user),
):
    ext = os.path.splitext(file.filename or "")[1].lower()
    if ext not in VIDEO_EXTS:
        return fail("解读视频仅支持 mp4/webm", 400)
    content = await file.read()
    if len(content) > MAX_HOME_PAGE_VIDEO_SIZE:
        return fail("视频不能超过100MB", 400)
    url = save_book_review_video(file.filename or "video.mp4", content)
    return success({"url": url, "media_type": "video"})


@upload_router.delete("/book-review-videos", summary="删除 bookReview 目录中的解读视频")
async def delete_book_review_video_file(
    url: str,
    user: User = Depends(get_admin_user),
):
    if not is_book_review_video_url(url):
        return fail(f"仅允许删除 {BOOK_REVIEW_URL_PREFIX}/ 下的视频", 400)
    if not book_review_url_to_path(url):
        return fail("无效的视频路径", 400)
    if not delete_book_review_video(url):
        return fail("视频不存在或已删除", 404)
    return success(None, "已删除")


@upload_router.get("/book-review-videos", summary="列出 bookReview 目录中的解读视频")
async def list_book_review_videos(user: User = Depends(get_admin_user)):
    return success(
        {
            "storage_dir": book_review_dir(),
            "urls": list_book_review_video_urls(),
        }
    )


@upload_router.get("/home-page-videos", summary="列出 homePage 目录中的背景视频")
async def list_home_page_videos(user: User = Depends(get_admin_user)):
    return success(
        {
            "storage_dir": home_page_dir(),
            "urls": list_home_page_video_urls(),
        }
    )


@books_router.get("/books", summary="书籍列表")
async def admin_list_books(user: User = Depends(get_admin_user)):
    books = await Book.all().order_by("-id")
    result = []
    for b in books:
        d = await book_to_dict(b)
        d["status"] = b.status
        d["stock"] = b.stock
        result.append(d)
    return success(result)


@books_router.post("/books", summary="新增书籍")
async def admin_create_book(body: BookCreateRequest, user: User = Depends(get_admin_user)):
    book = await Book.create(**body.model_dump())
    return success(await book_to_dict(book))


@books_router.put("/books/{book_id}", summary="更新书籍")
async def admin_update_book(
    book_id: int, body: BookUpdateRequest, user: User = Depends(get_admin_user)
):
    book = await Book.get_or_none(id=book_id)
    if not book:
        return fail("书籍不存在", 404)
    data = body.model_dump(exclude_unset=True)
    for k, v in data.items():
        setattr(book, k, v)
    await book.save()
    return success(await book_to_dict(book))


@books_router.delete("/books/{book_id}", summary="删除书籍")
async def admin_delete_book(book_id: int, user: User = Depends(get_admin_user)):
    await Book.filter(id=book_id).delete()
    await BookVideo.filter(book_id=book_id).delete()
    return success(None, "已删除")


@videos_router.get("/videos", summary="视频列表")
async def admin_list_videos(user: User = Depends(get_admin_user)):
    videos = await BookVideo.all().order_by("book_id", "sort_order", "id")
    book_titles = {
        b.id: b.title
        for b in await Book.filter(id__in=[v.book_id for v in videos] or [-1])
    }
    grouped: dict[int, dict] = {}
    for v in videos:
        item = video_to_dict(v)
        item["book_title"] = book_titles.get(v.book_id, "")
        bucket = grouped.setdefault(
            v.book_id,
            {
                "book_id": v.book_id,
                "book_title": item["book_title"],
                "videos": [],
                "play_count": 0,
                "status": 1,
            },
        )
        bucket["videos"].append(item)
        bucket["play_count"] += v.play_count or 0
        if v.status != 1:
            bucket["status"] = 0
    rows = []
    for bucket in grouped.values():
        first_url = bucket["videos"][0]["video_url"] if bucket["videos"] else ""
        rows.append(
            {
                **bucket,
                "video_count": len(bucket["videos"]),
                "video_url": first_url,
            }
        )
    rows.sort(key=lambda row: row["book_id"], reverse=True)
    return success(rows)


@videos_router.get("/videos/by-book/{book_id}", summary="按书籍获取解读视频列表")
async def admin_list_videos_by_book(book_id: int, user: User = Depends(get_admin_user)):
    book = await Book.get_or_none(id=book_id)
    if not book:
        return fail("书籍不存在", 404)
    videos = await BookVideo.filter(book_id=book_id).order_by("sort_order", "id")
    return success([video_to_dict(v) for v in videos])


@videos_router.put("/videos/by-book/{book_id}", summary="批量保存某书籍的解读视频")
async def admin_update_videos_by_book(
    book_id: int,
    body: BookVideosUpdateRequest,
    user: User = Depends(get_admin_user),
):
    book = await Book.get_or_none(id=book_id)
    if not book:
        return fail("书籍不存在", 404)
    if len(body.videos) > MAX_BOOK_REVIEW_VIDEOS:
        return fail(f"每本书最多绑定 {MAX_BOOK_REVIEW_VIDEOS} 个解读视频", 400)

    existing = await BookVideo.filter(book_id=book_id).order_by("sort_order", "id")
    preserved_explain = next((v.explain_content for v in existing if v.explain_content), None)
    await BookVideo.filter(book_id=book_id).delete()

    default_cover = book.cover or ""
    created_ids: List[int] = []
    for index, item in enumerate(body.videos):
        url = normalize_book_video_url(item.video_url.strip())
        if not is_valid_book_video_url(url):
            return fail(f"无效解读视频地址：{item.video_url}", 400)
        video = await BookVideo.create(
            book_id=book_id,
            sort_order=index,
            video_cover=item.video_cover or default_cover,
            video_url=url,
            video_duration=item.video_duration,
            video_intro=item.video_intro,
            explain_content=preserved_explain if index == 0 else None,
            status=item.status,
        )
        created_ids.append(video.id)

    return success({"book_id": book_id, "video_ids": created_ids, "count": len(created_ids)})


@videos_router.post("/videos", summary="绑定/更新单条视频（兼容旧接口）")
async def admin_bind_video(body: VideoBindRequest, user: User = Depends(get_admin_user)):
    book = await Book.get_or_none(id=body.book_id)
    if not book:
        return fail("书籍不存在", 404)
    url = normalize_book_video_url(body.video_url.strip())
    if not is_valid_book_video_url(url):
        return fail(f"无效解读视频地址：{body.video_url}", 400)
    payload = body.model_dump()
    payload["video_url"] = url
    existing = await BookVideo.filter(book_id=body.book_id, video_url=url).first()
    if existing:
        for k, v in payload.items():
            setattr(existing, k, v)
        await existing.save()
        return success({"id": existing.id})
    count = await BookVideo.filter(book_id=body.book_id).count()
    if count >= MAX_BOOK_REVIEW_VIDEOS:
        return fail(f"每本书最多绑定 {MAX_BOOK_REVIEW_VIDEOS} 个解读视频", 400)
    payload["sort_order"] = count
    video = await BookVideo.create(**payload)
    return success({"id": video.id})


@videos_router.delete("/videos/{video_id}", summary="删除视频")
async def admin_delete_video(video_id: int, user: User = Depends(get_admin_user)):
    if not await BookVideo.filter(id=video_id).exists():
        return fail("视频不存在", 404)
    await BookVideo.filter(id=video_id).delete()
    return success(None, "已删除")


@categories_router.get("/categories", summary="分类列表")
async def admin_categories(user: User = Depends(get_admin_user)):
    cats = await Category.all().order_by("sort_order")
    return success([{"id": c.id, "name": c.name, "slug": c.slug, "sort_order": c.sort_order} for c in cats])


@categories_router.post("/categories", summary="新增分类")
async def admin_create_category(body: CategoryRequest, user: User = Depends(get_admin_user)):
    cat = await Category.create(**body.model_dump())
    return success({"id": cat.id})


@categories_router.delete("/categories/{cat_id}", summary="删除分类")
async def admin_delete_category(cat_id: int, user: User = Depends(get_admin_user)):
    await Category.filter(id=cat_id).delete()
    return success(None)


@orders_router.get("/orders", summary="订单列表")
async def admin_orders(
    page: int = 1,
    page_size: int = 10,
    order_no: Optional[str] = None,
    book_name: Optional[str] = None,
    user_nickname: Optional[str] = None,
    receiver_phone: Optional[str] = None,
    ship_tracking_no: Optional[str] = None,
    status: Optional[str] = None,
    created_start: Optional[str] = None,
    created_end: Optional[str] = None,
    pay_start: Optional[str] = None,
    pay_end: Optional[str] = None,
    user: User = Depends(get_admin_user),
):
    allowed_sizes = {10, 20, 30, 40, 50}
    page = max(1, page)
    if page_size not in allowed_sizes:
        page_size = 10

    qs = await filter_admin_orders(
        order_no=order_no,
        book_name=book_name,
        user_nickname=user_nickname,
        receiver_phone=receiver_phone,
        ship_tracking_no=ship_tracking_no,
        status=status,
        created_start=created_start,
        created_end=created_end,
        pay_start=pay_start,
        pay_end=pay_end,
    )
    total = await qs.count()
    if total == 0:
        return success({"list": [], "total": 0, "page": page, "page_size": page_size})

    orders = await qs.order_by("-created_at").offset((page - 1) * page_size).limit(page_size)
    user_map = {
        u.id: u for u in await User.filter(id__in=list({o.user_id for o in orders}))
    }
    items = [await order_to_dict(o, user=user_map.get(o.user_id)) for o in orders]
    return success({"list": items, "total": total, "page": page, "page_size": page_size})


@orders_router.put("/orders/{order_id}", summary="编辑订单")
async def admin_update_order(
    order_id: int,
    body: AdminOrderUpdateRequest,
    user: User = Depends(get_admin_user),
):
    try:
        order = await OrderService.update_order(
            order_id,
            body.receiver_name,
            body.receiver_phone,
            body.receiver_address,
            body.ship_company,
            body.ship_tracking_no,
        )
    except ValueError as e:
        return fail(str(e), 400)
    return success(await order_to_dict(order), "保存成功")


@orders_router.put("/orders/{order_id}/ship", summary="订单发货")
async def admin_ship_order(
    order_id: int, body: ShipOrderRequest, user: User = Depends(get_admin_user)
):
    try:
        order = await OrderService.ship_order(
            order_id, body.ship_company, body.ship_tracking_no
        )
    except ValueError as e:
        return fail(str(e), 400)
    return success(await order_to_dict(order), "发货成功")


@orders_router.put("/orders/{order_id}/status", summary="更新订单状态")
async def admin_update_order_status(
    order_id: int,
    status: str,
    cancel_reason: Optional[str] = None,
    user: User = Depends(get_admin_user),
):
    order = await Order.get_or_none(id=order_id)
    if not order:
        return fail("订单不存在", 404)
    if status == "cancelled":
        try:
            order = await OrderService.cancel(
                order_id,
                None,
                is_admin=True,
                cancel_reason=cancel_reason,
            )
        except ValueError as e:
            return fail(str(e), 400)
    else:
        order.status = status
        if status == "completed" and not order.completed_at:
            from datetime import datetime

            order.completed_at = datetime.utcnow()
        await order.save()
    return success(await order_to_dict(order))


@site_router.get("/site-config", summary="获取氛围配置")
async def admin_get_site_config(user: User = Depends(get_admin_user)):
    cfg = await SiteConfig.all().order_by("-id").first()
    if not cfg:
        return success(None)
    return success(site_config_to_dict(cfg))


@site_router.put("/site-config", summary="保存氛围配置")
async def admin_save_site_config(
    body: SiteConfigRequest, user: User = Depends(get_admin_user)
):
    payload = body.model_dump()
    requested = normalize_bg_videos(payload.get("bg_videos"))
    if len(requested) > MAX_BG_VIDEOS:
        return fail(f"背景视频最多 {MAX_BG_VIDEOS} 个", 400)

    cfg = await SiteConfig.all().order_by("-id").first()

    if not requested:
        removed = clear_home_page_videos()
        bg_videos: List[str] = []
        payload["bg_videos"] = None
        payload["bg_url"] = ""
        payload["bg_type"] = "image"
        payload["bg_enabled"] = False
    else:
        bg_videos = []
        for url in requested:
            if not is_home_page_video_url(url):
                continue
            path = url_to_path(url)
            if path and os.path.isfile(path):
                bg_videos.append(normalize_home_page_url(url))
        if len(bg_videos) > MAX_BG_VIDEOS:
            return fail(f"背景视频最多 {MAX_BG_VIDEOS} 个", 400)
        removed = purge_home_page_videos(bg_videos)
        payload["bg_videos"] = bg_videos or None
        if bg_videos:
            payload["bg_type"] = "video"
            payload["bg_url"] = bg_videos[0]
            payload["bg_enabled"] = True
        else:
            payload["bg_url"] = ""
            payload["bg_type"] = "image"
            payload["bg_enabled"] = False

    if cfg:
        for k, v in payload.items():
            setattr(cfg, k, v)
        await cfg.save()
    else:
        cfg = await SiteConfig.create(**payload)
    data = site_config_to_dict(cfg)
    data["purged_videos"] = removed
    return success(data)


@daily_router.get("/daily", summary="每日读书列表")
async def admin_list_daily(user: User = Depends(get_admin_user)):
    items = await DailyBook.all().order_by("-publish_date")
    return success([await daily_to_dict(d) for d in items])


@daily_router.post("/daily", summary="新增每日读书")
async def admin_create_daily(body: DailyBookRequest, user: User = Depends(get_admin_user)):
    book = await Book.get_or_none(id=body.book_id)
    if not book:
        return fail("书籍不存在", 404)
    try:
        pub = date.fromisoformat(body.publish_date)
    except ValueError:
        return fail("日期格式错误", 400)
    if await DailyBook.filter(publish_date=pub).exists():
        return fail("该日期已有内容", 400)
    daily = await DailyBook.create(
        book_id=body.book_id,
        daily_sentence=body.daily_sentence,
        daily_intro=body.daily_intro,
        publish_date=pub,
        is_top=body.is_top,
        status=body.status,
    )
    return success(await daily_to_dict(daily))


@daily_router.put("/daily/{daily_id}", summary="更新每日读书")
async def admin_update_daily(
    daily_id: int, body: DailyBookUpdateRequest, user: User = Depends(get_admin_user)
):
    daily = await DailyBook.get_or_none(id=daily_id)
    if not daily:
        return fail("内容不存在", 404)
    data = body.model_dump(exclude_unset=True)
    if "publish_date" in data and data["publish_date"]:
        try:
            data["publish_date"] = date.fromisoformat(data["publish_date"])
        except ValueError:
            return fail("日期格式错误", 400)
    for k, v in data.items():
        setattr(daily, k, v)
    await daily.save()
    return success(await daily_to_dict(daily))


@daily_router.delete("/daily/{daily_id}", summary="删除每日读书")
async def admin_delete_daily(daily_id: int, user: User = Depends(get_admin_user)):
    await DailyBook.filter(id=daily_id).delete()
    return success(None, "已删除")


@member_router.get("/member/packages", summary="会员套餐列表")
async def admin_list_packages(user: User = Depends(get_admin_user)):
    packages = await MemberPackage.all().order_by("price")
    return success(
        [
            {
                "id": p.id,
                "package_name": p.package_name,
                "price": p.price,
                "valid_day": p.valid_day,
                "rights": p.rights,
                "status": p.status,
            }
            for p in packages
        ]
    )


@member_router.post("/member/packages", summary="新增会员套餐")
async def admin_create_package(body: MemberPackageRequest, user: User = Depends(get_admin_user)):
    pkg = await MemberPackage.create(**body.model_dump())
    return success({"id": pkg.id})


@member_router.put("/member/packages/{package_id}", summary="更新会员套餐")
async def admin_update_package(
    package_id: int, body: MemberPackageRequest, user: User = Depends(get_admin_user)
):
    pkg = await MemberPackage.get_or_none(id=package_id)
    if not pkg:
        return fail("套餐不存在", 404)
    for k, v in body.model_dump().items():
        setattr(pkg, k, v)
    await pkg.save()
    return success({"id": pkg.id})


@member_router.delete("/member/packages/{package_id}", summary="删除会员套餐")
async def admin_delete_package(package_id: int, user: User = Depends(get_admin_user)):
    await MemberPackage.filter(id=package_id).delete()
    return success(None, "已删除")


@users_router.get("/users/tree", summary="用户地区树")
async def admin_users_tree(user: User = Depends(get_admin_user)):
    tree = await build_user_region_tree()
    total = await User.filter(role="user").count()
    return success({"tree": tree, "total": total})


@users_router.get("/users/{user_id}", summary="用户详情")
async def admin_user_detail(user_id: int, user: User = Depends(get_admin_user)):
    try:
        data = await get_admin_user_detail(user_id)
    except ValueError as e:
        return fail(str(e), 404)
    return success(data)


@users_router.put("/users/{user_id}", summary="更新用户信息")
async def admin_update_user(
    user_id: int, body: AdminUserUpdateRequest, admin: User = Depends(get_admin_user)
):
    target = await User.get_or_none(id=user_id)
    if not target:
        return fail("用户不存在", 404)
    data = body.model_dump(exclude_unset=True)
    for k, v in data.items():
        if k in ("province", "city") and v is not None:
            v = v.strip() or None
        setattr(target, k, v)
    await target.save()
    try:
        detail = await get_admin_user_detail(user_id)
    except ValueError as e:
        return fail(str(e), 404)
    return success(detail, "更新成功")


@stats_router.get("/stats/overview", summary="全站总览仪表盘")
async def admin_stats_overview(user: User = Depends(get_admin_user)):
    return success(await build_overview_stats())


@stats_router.get("/stats/reading", summary="用户阅读行为分析")
async def admin_stats_reading(user: User = Depends(get_admin_user)):
    return success(await build_reading_stats())


@stats_router.get("/stats/orders", summary="交易订单数据统计")
async def admin_stats_orders(
    days: int = 30,
    user: User = Depends(get_admin_user),
):
    safe_days = 30 if days not in (7, 30, 90) else days
    return success(await build_order_stats(days=safe_days))


@stats_router.get("/stats/region", summary="用户地域分布分析")
async def admin_stats_region(user: User = Depends(get_admin_user)):
    return success(await build_region_stats())


@stats_router.get("/stats/system", summary="系统性能监控面板")
async def admin_stats_system(user: User = Depends(get_admin_user)):
    return success(await build_system_stats())


@ai_router.get("/ai/config", summary="AI 内容生成配置状态")
async def admin_ai_config(user: User = Depends(get_admin_user)):
    return success(ai_runtime_config())


@ai_router.post("/ai/generate", summary="创建并执行 AI 内容生成任务")
async def admin_ai_generate(body: AiGenerateRequest, user: User = Depends(get_admin_user)):
    try:
        data = await create_and_run_task(
            operator_id=user.id,
            book_ids=body.book_ids,
            content_types=body.content_types,
            tone=body.tone,
            length=body.length,
            extra_prompt=body.extra_prompt,
            write_mode=body.write_mode,
        )
    except ValueError as e:
        return fail(str(e), 400)
    except Exception as e:  # noqa: BLE001
        return fail(f"生成失败: {e}", 500)
    return success(data, "生成完成")


@ai_router.get("/ai/tasks", summary="AI 生成任务列表")
async def admin_ai_tasks(limit: int = 20, user: User = Depends(get_admin_user)):
    return success(await list_tasks(limit=limit))


@ai_router.get("/ai/tasks/{task_id}", summary="AI 生成任务详情")
async def admin_ai_task_detail(task_id: int, user: User = Depends(get_admin_user)):
    try:
        data = await get_task_detail(task_id)
    except ValueError as e:
        return fail(str(e), 404)
    return success(data)


@ai_router.put("/ai/items/{item_id}", summary="编辑 AI 生成文案")
async def admin_ai_item_update(
    item_id: int, body: AiItemUpdateRequest, user: User = Depends(get_admin_user)
):
    try:
        data = await update_item_text(item_id, body.text)
    except ValueError as e:
        return fail(str(e), 400)
    return success(data, "已保存")


@ai_router.post("/ai/items/{item_id}/accept", summary="采纳 AI 文案并写入业务表")
async def admin_ai_item_accept(
    item_id: int, body: AiItemAcceptRequest, user: User = Depends(get_admin_user)
):
    publish_date = None
    if body.publish_date:
        try:
            publish_date = date.fromisoformat(body.publish_date)
        except ValueError:
            return fail("publish_date 格式应为 YYYY-MM-DD", 400)
    try:
        data = await accept_item(
            item_id,
            write_mode=body.write_mode,
            publish_date=publish_date,
            text=body.text,
        )
    except ValueError as e:
        return fail(str(e), 400)
    return success(data, "已采纳入库")


@ai_router.post("/ai/items/{item_id}/discard", summary="丢弃 AI 生成文案")
async def admin_ai_item_discard(item_id: int, user: User = Depends(get_admin_user)):
    try:
        data = await discard_item(item_id)
    except ValueError as e:
        return fail(str(e), 400)
    return success(data, "已丢弃")


router.include_router(upload_router)
router.include_router(books_router)
router.include_router(videos_router)
router.include_router(categories_router)
router.include_router(orders_router)
router.include_router(site_router)
router.include_router(daily_router)
router.include_router(member_router)
router.include_router(users_router)
router.include_router(stats_router)
router.include_router(ai_router)
