"""
开发环境数据初始化（含建表，仅限本地/首次使用）。
生产环境请使用 aerich migrate + aerich upgrade。
"""
from __future__ import annotations

import asyncio
import os
import sys
from datetime import date, timedelta

BACKEND_DIR = os.path.join(os.path.dirname(__file__), "..", "backend")
sys.path.insert(0, os.path.abspath(BACKEND_DIR))

from tortoise import Tortoise

from app.core.security import hash_password
from app.db.database import TORTOISE_ORM
from app.models import Book, BookVideo, Category, DailyBook, MemberPackage, SiteConfig, User

sys.path.insert(0, os.path.dirname(__file__))
from book_covers import TITLE_TO_COVER, cover_path_by_title
from book_video_asset import BOOK_INTRO_VIDEO_URL, sync_book_review_to_uploads
from site_video_asset import home_exhibition_upload_urls, sync_home_exhibition_to_uploads

CATEGORIES = [
    ("成长", "growth", 1),
    ("治愈", "healing", 2),
    ("文学", "literature", 3),
    ("职场", "career", 4),
    ("心理", "psychology", 5),
    ("育儿", "parenting", 6),
]

SAMPLE_BOOKS = [
    {
        "title": "被讨厌的勇气",
        "author": "岸见一郎",
        "cover": cover_path_by_title("被讨厌的勇气", 1),
        "category_slug": "psychology",
        "price": 39.8,
        "stock": 100,
        "summary": "阿德勒心理学入门，帮助你摆脱他人期待的束缚。",
        "highlight": "自由就是被别人讨厌",
        "target_audience": "焦虑职场人",
        "video_url": BOOK_INTRO_VIDEO_URL,
    },
    {
        "title": "小王子",
        "author": "圣埃克苏佩里",
        "cover": cover_path_by_title("小王子", 2),
        "category_slug": "literature",
        "price": 29.9,
        "stock": 80,
        "summary": "一部写给大人的童话，关于爱与责任。",
        "highlight": "真正重要的东西，用眼睛是看不见的",
        "target_audience": "文艺爱好者",
        "video_url": BOOK_INTRO_VIDEO_URL,
    },
    {
        "title": "非暴力沟通",
        "author": "马歇尔·卢森堡",
        "cover": cover_path_by_title("非暴力沟通", 3),
        "category_slug": "psychology",
        "price": 45.0,
        "stock": 60,
        "summary": "学会倾听与表达，改善人际关系。",
        "highlight": "言语背后的需要，才是沟通的关键",
        "target_audience": "职场人、伴侣",
        "video_url": BOOK_INTRO_VIDEO_URL,
    },
]

EXTRA_TITLES = [
    ("原则", "瑞·达利欧", "career"),
    ("活着", "余华", "literature"),
    ("正面管教", "简·尼尔森", "parenting"),
    ("心流", "米哈里", "growth"),
    ("解忧杂货店", "东野圭吾", "healing"),
    ("深度工作", "卡尔·纽波特", "career"),
    ("我们仨", "杨绛", "literature"),
]


async def main() -> None:
    await Tortoise.init(config=TORTOISE_ORM)
    await Tortoise.generate_schemas(safe=True)

    admin, created = await User.get_or_create(
        username="admin",
        defaults={
            "password_hash": hash_password("admin123456"),
            "nickname": "管理员",
            "role": "admin",
        },
    )
    if created:
        print("管理员已创建: admin / admin123456")

    slug_map = {}
    for name, slug, order in CATEGORIES:
        cat, _ = await Category.get_or_create(
            slug=slug, defaults={"name": name, "sort_order": order}
        )
        slug_map[slug] = cat.id

    book_ids = []
    for i, item in enumerate(SAMPLE_BOOKS):
        cat_id = slug_map[item["category_slug"]]
        book, _ = await Book.get_or_create(
            title=item["title"],
            defaults={
                "author": item["author"],
                "cover": item["cover"],
                "category_id": cat_id,
                "price": item["price"],
                "stock": item["stock"],
                "summary": item["summary"],
                "highlight": item["highlight"],
                "target_audience": item["target_audience"],
                "status": "published",
                "view_count": 100 - i * 10,
            },
        )
        book_ids.append(book.id)
        video, v_created = await BookVideo.get_or_create(
            book_id=book.id,
            defaults={
                "video_cover": item["cover"],
                "video_url": item["video_url"],
                "video_duration": 360,
                "video_intro": "3分钟读懂全书精华",
                "status": 1,
            },
        )
        if v_created:
            print(f"视频已绑定: {book.title}")

    for j, (title, author, slug) in enumerate(EXTRA_TITLES):
        await Book.get_or_create(
            title=title,
            defaults={
                "author": author,
                "cover": cover_path_by_title(title, j + 4),
                "category_id": slug_map[slug],
                "price": 35.0 + j,
                "stock": 50,
                "summary": f"《{title}》精彩解读即将上线。",
                "status": "published",
                "view_count": 20 - j,
            },
        )

    if book_ids:
        upload_root = os.path.join(BACKEND_DIR, "uploads")
        sync_home_exhibition_to_uploads(upload_root)
        sync_book_review_to_uploads(upload_root)
        bg_urls = home_exhibition_upload_urls(upload_root) or [BOOK_INTRO_VIDEO_URL]
        await SiteConfig.get_or_create(
            id=1,
            defaults={
                "bg_type": "video",
                "bg_url": bg_urls[0],
                "bg_videos": bg_urls,
                "music_enabled": False,
                "bg_enabled": True,
                "featured_book_id": book_ids[0],
                "promo_title": "读书视频，宇小兔更懂你",
                "daily_sentence": "先看懂一本书，再决定买不买",
            },
        )

    packages = [
        ("月度会员", 19.9, 30, '["全站视频高清","每日读书独家文摘","购书9折"]'),
        ("年度会员", 199.0, 365, '["全站视频高清","每日读书独家文摘","购书8折","笔记下载"]'),
    ]
    for name, price, days, rights in packages:
        pkg, created = await MemberPackage.get_or_create(
            package_name=name,
            defaults={"price": price, "valid_day": days, "rights": rights, "status": 1},
        )
        if created:
            print(f"会员套餐已创建: {pkg.package_name}")

    today = date.today()
    for offset in range(7):
        pub = today - timedelta(days=offset)
        book_id = book_ids[offset % len(book_ids)]
        book = await Book.get(id=book_id)
        daily, created = await DailyBook.get_or_create(
            publish_date=pub,
            defaults={
                "book_id": book_id,
                "daily_sentence": book.highlight or f"今日金句 · {book.title}",
                "daily_intro": book.summary,
                "is_top": offset == 0,
                "status": 1,
            },
        )
        if created:
            print(f"每日读书已创建: {pub.isoformat()} -> {book.title}")

    demo_users = [
        ("demo_hz", "杭州读者", "浙江省", "杭州市"),
        ("demo_sh", "上海读者", "上海市", "上海市"),
        ("demo_bj", "北京读者", "北京市", "北京市"),
    ]
    for username, nickname, province, city in demo_users:
        u, created = await User.get_or_create(
            username=username,
            defaults={
                "password_hash": hash_password("demo123456"),
                "nickname": nickname,
                "province": province,
                "city": city,
                "role": "user",
            },
        )
        if created:
            print(f"演示用户: {username} / demo123456 ({province} {city})")

    print("Seed 完成。")
    await Tortoise.close_connections()


if __name__ == "__main__":
    asyncio.run(main())
