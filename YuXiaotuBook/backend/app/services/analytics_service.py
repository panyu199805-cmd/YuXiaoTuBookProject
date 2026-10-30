from __future__ import annotations

import json
import os
import time
from collections import Counter, defaultdict
from datetime import date, datetime, time as dt_time, timedelta
from typing import Any, Dict, List, Optional

from tortoise import Tortoise

from app.models import (
    Book,
    BookVideo,
    Category,
    DailyBook,
    MemberOrder,
    MemberPackage,
    Order,
    OrderItem,
    User,
    UserBookCollect,
    UserMember,
    UserPreference,
)
from app.services.order_helpers import STATUS_LABELS
from app.services.user_admin_service import UNKNOWN_CITY, UNKNOWN_PROVINCE, _region
from app.utils.timezone import to_beijing_str

REVENUE_STATUSES = ("paid", "shipped", "completed")
_PROCESS_START = time.time()


def _naive_dt(value: datetime) -> datetime:
    return value.replace(tzinfo=None) if value.tzinfo is not None else value


def _day_bounds(day: date) -> tuple[datetime, datetime]:
    start = datetime.combine(day, dt_time.min)
    end = datetime.combine(day, dt_time.max)
    return start, end


def _iter_days(days: int) -> List[date]:
    today = date.today()
    return [today - timedelta(days=offset) for offset in range(days - 1, -1, -1)]


async def build_overview_stats() -> Dict[str, Any]:
    today = date.today()
    today_start = datetime.combine(today, dt_time.min)
    now = datetime.now()

    book_total = await Book.all().count()
    book_published = await Book.filter(status="published").count()
    book_draft = book_total - book_published

    user_total = await User.filter(role="user").count()
    user_today = await User.filter(role="user", created_at__gte=today_start).count()

    videos = await BookVideo.all()
    video_total = len(videos)
    video_play_count = sum(video.play_count or 0 for video in videos)

    collect_total = await UserBookCollect.all().count()
    collect_today = await UserBookCollect.filter(created_at__gte=today_start).count()

    vip_active = await UserMember.filter(is_vip=True, expire_time__gte=now).count()
    member_package_count = await MemberPackage.filter(status=1).count()

    orders_today = await Order.filter(created_at__gte=today_start).count()
    order_total = await Order.all().count()

    paid_orders = await Order.filter(status__in=REVENUE_STATUSES).all()
    order_total_amount = float(sum(order.total_amount for order in paid_orders))
    order_today_amount = float(
        sum(
            order.total_amount
            for order in paid_orders
            if order.pay_time and _naive_dt(order.pay_time) >= today_start
        )
    )

    member_orders_today = await MemberOrder.filter(created_at__gte=today_start).count()
    member_paid_orders = await MemberOrder.filter(status="paid").all()
    member_total_amount = float(sum(order.amount for order in member_paid_orders))
    member_today_amount = float(
        sum(
            order.amount
            for order in member_paid_orders
            if order.pay_time and _naive_dt(order.pay_time) >= today_start
        )
    )

    order_trend: List[Dict[str, Any]] = []
    user_trend: List[Dict[str, Any]] = []
    for day in _iter_days(7):
        day_start, day_end = _day_bounds(day)
        day_orders = await Order.filter(
            created_at__gte=day_start, created_at__lte=day_end
        ).count()
        day_paid = await Order.filter(
            created_at__gte=day_start,
            created_at__lte=day_end,
            status__in=REVENUE_STATUSES,
        ).all()
        day_amount = float(sum(order.total_amount for order in day_paid))
        order_trend.append(
            {"date": day.isoformat(), "count": day_orders, "amount": day_amount}
        )
        day_users = await User.filter(
            role="user", created_at__gte=day_start, created_at__lte=day_end
        ).count()
        user_trend.append({"date": day.isoformat(), "count": day_users})

    categories = await Category.all().order_by("sort_order", "id")
    category_distribution = []
    for category in categories:
        count = await Book.filter(category_id=category.id).count()
        if count > 0:
            category_distribution.append({"name": category.name, "count": count})

    top_books_raw = await Book.all().order_by("-view_count", "-id").limit(5)
    video_map = {
        video.book_id: video
        for video in await BookVideo.filter(
            book_id__in=[book.id for book in top_books_raw]
        )
    }
    top_books = [
        {
            "id": book.id,
            "title": book.title,
            "cover": book.cover,
            "view_count": book.view_count or 0,
            "play_count": (video_map.get(book.id).play_count or 0)
            if video_map.get(book.id)
            else 0,
        }
        for book in top_books_raw
    ]

    recent_orders_raw = await Order.all().order_by("-created_at").limit(5)
    recent_user_map = {
        item.id: item
        for item in await User.filter(
            id__in=list({order.user_id for order in recent_orders_raw})
        )
    }
    recent_orders = []
    for order in recent_orders_raw:
        items = await OrderItem.filter(order_id=order.id)
        order_user = recent_user_map.get(order.user_id)
        from app.services.order_helpers import summarize_book_names

        recent_orders.append(
            {
                "id": order.id,
                "order_no": order.order_no,
                "user_nickname": order_user.nickname if order_user else "—",
                "total_amount": float(order.total_amount),
                "status": order.status,
                "status_label": STATUS_LABELS.get(order.status, order.status),
                "created_at": to_beijing_str(order.created_at),
                "book_summary": summarize_book_names(items),
            }
        )

    order_status = []
    for status, label in STATUS_LABELS.items():
        count = await Order.filter(status=status).count()
        if count > 0:
            order_status.append({"status": status, "label": label, "count": count})

    daily_total = await DailyBook.all().count()

    return {
        "summary": {
            "books": {
                "total": book_total,
                "published": book_published,
                "draft": book_draft,
            },
            "users": {"total": user_total, "today": user_today},
            "orders": {
                "today_count": orders_today,
                "today_amount": round(order_today_amount + member_today_amount, 2),
                "total_count": order_total,
                "total_amount": round(order_total_amount + member_total_amount, 2),
            },
            "videos": {"total": video_total, "play_count": video_play_count},
            "collects": {"total": collect_total, "today": collect_today},
            "members": {
                "vip_active": vip_active,
                "package_count": member_package_count,
                "orders_today": member_orders_today,
            },
            "daily": {"total": daily_total},
        },
        "book_status": {"published": book_published, "draft": book_draft},
        "category_distribution": category_distribution,
        "order_trend": order_trend,
        "user_trend": user_trend,
        "top_books": top_books,
        "recent_orders": recent_orders,
        "order_status": order_status,
    }


async def build_reading_stats() -> Dict[str, Any]:
    books = await Book.filter(status="published").order_by("-view_count", "-id")
    book_ids = [book.id for book in books]
    videos = {
        video.book_id: video
        for video in await BookVideo.filter(book_id__in=book_ids or [-1])
    }
    collects = await UserBookCollect.all()
    collect_by_book: Counter[int] = Counter()
    history_by_book: Counter[int] = Counter()
    hour_counter: Counter[int] = Counter()
    for item in collects:
        if item.collect_type == 1:
            collect_by_book[item.book_id] += 1
        elif item.collect_type == 2:
            history_by_book[item.book_id] += 1
        if item.created_at:
            hour_counter[item.created_at.hour] += 1

    video_ranking = []
    for book in books[:10]:
        video = videos.get(book.id)
        video_ranking.append(
            {
                "id": book.id,
                "title": book.title,
                "cover": book.cover,
                "view_count": book.view_count or 0,
                "play_count": (video.play_count or 0) if video else 0,
                "favorite_count": collect_by_book.get(book.id, 0),
                "history_count": history_by_book.get(book.id, 0),
            }
        )

    categories = {cat.id: cat.name for cat in await Category.all()}
    preference_counter: Counter[str] = Counter()
    for pref in await UserPreference.all():
        try:
            category_ids = json.loads(pref.category_ids or "[]")
        except json.JSONDecodeError:
            category_ids = []
        if not isinstance(category_ids, list):
            continue
        for category_id in category_ids:
            name = categories.get(int(category_id))
            if name:
                preference_counter[name] += 1

    preference_stats = [
        {"name": name, "count": count}
        for name, count in preference_counter.most_common(8)
    ]

    daily_books = await DailyBook.filter(status=1).order_by("-publish_date").limit(8)
    daily_book_ids = [item.book_id for item in daily_books]
    daily_title_map = {
        book.id: book.title
        for book in await Book.filter(id__in=daily_book_ids)
    }
    daily_stats = [
        {
            "id": item.id,
            "title": daily_title_map.get(item.book_id, f"书籍#{item.book_id}"),
            "publish_date": item.publish_date.isoformat(),
            "like_count": item.like_count or 0,
            "is_top": item.is_top,
        }
        for item in daily_books
    ]

    hour_distribution = [
        {"hour": hour, "count": hour_counter.get(hour, 0)} for hour in range(24)
    ]

    return {
        "summary": {
            "total_views": sum(book.view_count or 0 for book in books),
            "total_plays": sum((videos.get(book.id).play_count or 0) if videos.get(book.id) else 0 for book in books),
            "favorite_total": sum(collect_by_book.values()),
            "history_total": sum(history_by_book.values()),
            "daily_total": await DailyBook.filter(status=1).count(),
        },
        "video_ranking": video_ranking,
        "preference_stats": preference_stats,
        "daily_stats": daily_stats,
        "hour_distribution": hour_distribution,
    }


async def build_order_stats(days: int = 30) -> Dict[str, Any]:
    today = date.today()
    day_list = _iter_days(days)

    order_trend = []
    amount_trend = []
    for day in day_list:
        day_start, day_end = _day_bounds(day)
        day_orders = await Order.filter(
            created_at__gte=day_start, created_at__lte=day_end
        ).all()
        paid_amount = float(
            sum(
                order.total_amount
                for order in day_orders
                if order.status in REVENUE_STATUSES
            )
        )
        order_trend.append({"date": day.isoformat(), "count": len(day_orders)})
        amount_trend.append({"date": day.isoformat(), "amount": paid_amount})

    member_trend = []
    for day in day_list[-7:]:
        day_start, day_end = _day_bounds(day)
        member_count = await MemberOrder.filter(
            created_at__gte=day_start, created_at__lte=day_end
        ).count()
        member_paid = await MemberOrder.filter(
            created_at__gte=day_start,
            created_at__lte=day_end,
            status="paid",
        ).all()
        member_amount = float(sum(order.amount for order in member_paid))
        member_trend.append(
            {
                "date": day.isoformat(),
                "count": member_count,
                "amount": member_amount,
            }
        )

    status_stats = []
    for status, label in STATUS_LABELS.items():
        count = await Order.filter(status=status).count()
        status_stats.append({"status": status, "label": label, "count": count})

    member_status_stats = []
    for status in ("pending_payment", "paid", "cancelled"):
        count = await MemberOrder.filter(status=status).count()
        if count:
            member_status_stats.append({"status": status, "count": count})

    items = await OrderItem.all()
    sales_counter: Counter[int] = Counter()
    revenue_counter: defaultdict[int, float] = defaultdict(float)
    for item in items:
        sales_counter[item.book_id] += item.quantity
        revenue_counter[item.book_id] += float(item.price) * item.quantity

    top_ids = [book_id for book_id, _ in sales_counter.most_common(8)]
    book_map = {book.id: book for book in await Book.filter(id__in=top_ids)}
    top_sales = [
        {
            "id": book_id,
            "title": book_map[book_id].title if book_id in book_map else f"书籍#{book_id}",
            "quantity": sales_counter[book_id],
            "amount": round(revenue_counter[book_id], 2),
        }
        for book_id in top_ids
    ]

    hour_counter: Counter[int] = Counter()
    for order in await Order.all():
        if order.created_at:
            hour_counter[order.created_at.hour] += 1
    hour_distribution = [
        {"hour": hour, "count": hour_counter.get(hour, 0)} for hour in range(24)
    ]

    paid_orders = await Order.filter(status__in=REVENUE_STATUSES).all()
    member_paid = await MemberOrder.filter(status="paid").all()

    return {
        "summary": {
            "book_order_total": await Order.all().count(),
            "book_revenue": round(float(sum(order.total_amount for order in paid_orders)), 2),
            "member_order_total": await MemberOrder.all().count(),
            "member_revenue": round(float(sum(order.amount for order in member_paid)), 2),
            "cancelled_total": await Order.filter(status="cancelled").count(),
        },
        "order_trend": order_trend,
        "amount_trend": amount_trend,
        "member_trend": member_trend,
        "status_stats": status_stats,
        "member_status_stats": member_status_stats,
        "top_sales": top_sales,
        "hour_distribution": hour_distribution,
    }


async def build_region_stats() -> Dict[str, Any]:
    users = await User.filter(role="user")
    orders = await Order.all()
    user_map = {user.id: user for user in users}

    province_users: Counter[str] = Counter()
    city_users: Counter[str] = Counter()
    province_orders: Counter[str] = Counter()
    province_amount: defaultdict[str, float] = defaultdict(float)
    category_by_province: defaultdict[str, Counter[str]] = defaultdict(Counter)

    categories = {cat.id: cat.name for cat in await Category.all()}
    for user in users:
        province = _region(user.province, UNKNOWN_PROVINCE)
        city = _region(user.city, UNKNOWN_CITY)
        province_users[province] += 1
        city_users[f"{province}·{city}"] += 1

    for order in orders:
        user = user_map.get(order.user_id)
        if not user:
            continue
        province = _region(user.province, UNKNOWN_PROVINCE)
        province_orders[province] += 1
        if order.status in REVENUE_STATUSES:
            province_amount[province] += float(order.total_amount)

    for pref in await UserPreference.all():
        user = user_map.get(pref.user_id)
        if not user:
            continue
        province = _region(user.province, UNKNOWN_PROVINCE)
        try:
            category_ids = json.loads(pref.category_ids or "[]")
        except json.JSONDecodeError:
            category_ids = []
        if not isinstance(category_ids, list):
            continue
        for category_id in category_ids:
            name = categories.get(int(category_id))
            if name:
                category_by_province[province][name] += 1

    province_stats = []
    for province, count in province_users.most_common():
        top_categories = category_by_province.get(province, Counter()).most_common(2)
        province_stats.append(
            {
                "province": province,
                "user_count": count,
                "order_count": province_orders.get(province, 0),
                "order_amount": round(province_amount.get(province, 0.0), 2),
                "top_categories": [
                    {"name": name, "count": value} for name, value in top_categories
                ],
            }
        )

    city_stats = [
        {"city": city, "user_count": count}
        for city, count in city_users.most_common(10)
    ]

    return {
        "summary": {
            "province_count": len(province_stats),
            "user_total": sum(province_users.values()),
            "filled_region_users": sum(
                count
                for province, count in province_users.items()
                if province != UNKNOWN_PROVINCE
            ),
        },
        "province_stats": province_stats,
        "city_stats": city_stats,
    }


def _read_meminfo() -> Dict[str, Any]:
    result: Dict[str, Any] = {}
    try:
        with open("/proc/meminfo", encoding="utf-8") as file:
            lines = file.readlines()
        mem_total_kb = 0
        mem_available_kb = 0
        for line in lines:
            if line.startswith("MemTotal:"):
                mem_total_kb = int(line.split()[1])
            elif line.startswith("MemAvailable:"):
                mem_available_kb = int(line.split()[1])
        if mem_total_kb:
            used_percent = round((1 - mem_available_kb / mem_total_kb) * 100, 1)
            result["memory_total_mb"] = round(mem_total_kb / 1024, 1)
            result["memory_used_percent"] = used_percent
    except OSError:
        pass
    return result


def _read_loadavg() -> Optional[List[str]]:
    try:
        with open("/proc/loadavg", encoding="utf-8") as file:
            return file.read().strip().split()[:3]
    except OSError:
        return None


def _read_disk_usage() -> Optional[Dict[str, Any]]:
    try:
        usage = os.statvfs("/")
        total = usage.f_frsize * usage.f_blocks
        free = usage.f_frsize * usage.f_bavail
        used_percent = round((1 - free / total) * 100, 1) if total else 0
        return {
            "total_gb": round(total / (1024 ** 3), 2),
            "used_percent": used_percent,
        }
    except OSError:
        return None


async def build_system_stats() -> Dict[str, Any]:
    started = time.perf_counter()
    await Book.all().count()
    db_latency_ms = round((time.perf_counter() - started) * 1000, 2)

    table_counts = {
        "users": await User.filter(role="user").count(),
        "books": await Book.all().count(),
        "orders": await Order.all().count(),
        "member_orders": await MemberOrder.all().count(),
        "collects": await UserBookCollect.all().count(),
    }

    conn = Tortoise.get_connection("default")
    db_status = "ok"
    try:
        await conn.execute_query("SELECT 1")
    except Exception:
        db_status = "error"

    meminfo = _read_meminfo()
    disk = _read_disk_usage()
    load_avg = _read_loadavg()

    return {
        "summary": {
            "service": "yuxiaotu-book",
            "status": "ok" if db_status == "ok" else "degraded",
            "uptime_seconds": int(time.time() - _PROCESS_START),
            "db_status": db_status,
            "db_latency_ms": db_latency_ms,
        },
        "resources": {
            "memory": meminfo,
            "disk": disk or {},
            "load_avg": load_avg or [],
        },
        "table_counts": table_counts,
        "notes": [
            "当前为单机 Docker 部署，指标来自 API 容器内 /proc 与数据库探活。",
            "未接入独立 APM 时，接口 QPS / CDN 耗时需后续接入 Prometheus 或网关日志。",
        ],
    }
