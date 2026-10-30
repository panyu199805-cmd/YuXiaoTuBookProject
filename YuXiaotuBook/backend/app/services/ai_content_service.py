from __future__ import annotations

from datetime import date, datetime
from typing import Any, Dict, List, Optional

import httpx

from app.core.config import settings
from app.models import AiContentItem, AiContentTask, Book, BookVideo, Category, DailyBook

CONTENT_TYPE_META: Dict[str, Dict[str, str]] = {
    "book_summary": {
        "label": "书籍简介",
        "target_field": "book.summary",
        "instruction": "写一段适合图书详情页的书籍简介，突出主题与阅读价值，不要剧透结局。",
    },
    "book_highlight": {
        "label": "一句话亮点",
        "target_field": "book.highlight",
        "instruction": "写一句高转化亮点文案，适合卡片副标题，不超过 40 个汉字。",
    },
    "video_explain": {
        "label": "视频解说文案",
        "target_field": "book_video.explain_content",
        "instruction": "写适合 3-8 分钟解读视频的旁白文案，结构清晰：开场引入、核心观点、行动建议。",
    },
    "video_intro": {
        "label": "视频简介",
        "target_field": "book_video.video_intro",
        "instruction": "写一段视频简介，说明本集讲什么、适合谁看，100-180 字。",
    },
    "daily_sentence": {
        "label": "每日金句",
        "target_field": "daily_book.daily_sentence",
        "instruction": "提炼一句治愈向金句，可源自书中思想但不要编造虚假出处；单独一行输出金句本身。",
    },
    "daily_intro": {
        "label": "每日读书简介",
        "target_field": "daily_book.daily_intro",
        "instruction": "写一段每日读书专栏导语，承接金句与书籍主题，80-150 字。",
    },
    "reading_note": {
        "label": "读书笔记",
        "target_field": "ai_only.reading_note",
        "instruction": "写一篇短读书笔记：3 个要点 + 1 段个人启发，适合运营二次编辑，不落库到业务表。",
    },
}

TONE_LABELS = {
    "healing": "治愈温柔",
    "professional": "专业理性",
    "casual": "口语亲切",
}

LENGTH_HINTS = {
    "short": "偏短",
    "medium": "适中",
    "long": "偏长",
}

MAX_BOOKS_PER_TASK = 10
ALLOWED_TYPES = set(CONTENT_TYPE_META.keys())


def ai_runtime_config() -> Dict[str, Any]:
    has_key = bool(settings.AI_API_KEY)
    mock = (not has_key) and settings.AI_MOCK_ENABLED
    return {
        "configured": has_key,
        "mock_enabled": settings.AI_MOCK_ENABLED,
        "mode": "live" if has_key else ("mock" if mock else "disabled"),
        "base_url": settings.AI_BASE_URL if has_key else None,
        "model": settings.AI_MODEL if has_key else ("mock-local" if mock else None),
        "content_types": [
            {"value": key, "label": meta["label"], "target_field": meta["target_field"]}
            for key, meta in CONTENT_TYPE_META.items()
        ],
    }


def _source_text(book: Book, content_type: str, video: Optional[BookVideo]) -> str:
    if content_type == "book_summary":
        return book.summary or ""
    if content_type == "book_highlight":
        return book.highlight or ""
    if content_type == "video_explain":
        return (video.explain_content if video else "") or ""
    if content_type == "video_intro":
        return (video.video_intro if video else "") or ""
    return ""


def _build_user_prompt(
    book: Book,
    category_name: str,
    content_type: str,
    tone: str,
    length: str,
    extra_prompt: Optional[str],
    source_text: str,
) -> str:
    meta = CONTENT_TYPE_META[content_type]
    parts = [
        f"请为图书生成「{meta['label']}」。",
        f"书名：{book.title}",
        f"作者：{book.author}",
        f"分类：{category_name or '未分类'}",
        f"语气：{TONE_LABELS.get(tone, tone)}",
        f"篇幅：{LENGTH_HINTS.get(length, length)}",
        f"任务要求：{meta['instruction']}",
        "只输出正文，不要标题、不要 Markdown、不要解释过程。",
    ]
    if book.summary:
        parts.append(f"现有简介参考：{book.summary[:300]}")
    if book.highlight:
        parts.append(f"现有亮点参考：{book.highlight}")
    if source_text:
        parts.append(f"当前字段原文（可参考重写）：{source_text[:500]}")
    if extra_prompt:
        parts.append(f"补充要求：{extra_prompt.strip()}")
    return "\n".join(parts)


def _mock_text(book: Book, content_type: str, tone: str) -> str:
    tone_word = TONE_LABELS.get(tone, "治愈")
    title = book.title
    author = book.author
    templates = {
        "book_summary": (
            f"《{title}》是{author}的代表作品之一。本书以{tone_word}的叙事，"
            f"帮助读者理解关系、自我与行动之间的连接，适合希望在忙碌生活中找回阅读节奏的人。"
            f"（Mock 生成，可编辑后采纳）"
        ),
        "book_highlight": f"用{tone_word}的方式读懂《{title}》——把书里的力量带进日常。",
        "video_explain": (
            f"大家好，今天我们一起解读《{title}》。开场先讲这本书想回答什么问题；"
            f"中间拆解 3 个核心观点，并结合生活场景说明；最后给你一个马上能用的小练习。"
            f"希望这场{tone_word}的解读，帮你把书读薄、把行动做实。（Mock）"
        ),
        "video_intro": (
            f"本集用约几分钟讲透《{title}》的核心框架，适合想快速抓住作者思路、"
            f"并带回生活的听众。风格{tone_word}，边听边做笔记更佳。（Mock）"
        ),
        "daily_sentence": f"真正的成长，是把《{title}》里读到的一句，变成今天敢迈出的一小步。",
        "daily_intro": (
            f"今日共读《{title}》。愿这句话陪你放慢一点，把注意力从焦虑拉回呼吸与行动。"
            f"（Mock 导语，可编辑后写入每日专栏）"
        ),
        "reading_note": (
            f"【读书笔记·《{title}》】\n"
            f"1. 先看见自己的需求，再谈改变。\n"
            f"2. 把抽象观点拆成可执行的小步骤。\n"
            f"3. 用复盘代替自责，让进步可累积。\n"
            f"启发：今天只选一个场景练习，比一次读完整本更重要。（Mock）"
        ),
    }
    return templates.get(content_type, f"《{title}》相关文案（Mock）")


async def _call_llm(prompt: str) -> str:
    url = f"{settings.AI_BASE_URL}/chat/completions"
    headers = {
        "Authorization": f"Bearer {settings.AI_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": settings.AI_MODEL,
        "messages": [
            {
                "role": "system",
                "content": (
                    "你是宇小兔每日读书的内容编辑，文风克制、温暖、可落地，"
                    "不使用夸张营销词，不编造虚假书评数据。"
                ),
            },
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.7,
    }
    async with httpx.AsyncClient(timeout=settings.AI_TIMEOUT_SECONDS) as client:
        resp = await client.post(url, headers=headers, json=payload)
        resp.raise_for_status()
        data = resp.json()
    try:
        text = data["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as exc:
        raise RuntimeError(f"AI 返回格式异常: {data}") from exc
    return (text or "").strip()


def _parse_csv_ids(raw: str) -> List[int]:
    if not raw:
        return []
    result: List[int] = []
    for part in raw.split(","):
        part = part.strip()
        if part.isdigit():
            result.append(int(part))
    return result


def item_to_dict(item: AiContentItem, book: Optional[Book] = None) -> Dict[str, Any]:
    meta = CONTENT_TYPE_META.get(item.content_type, {})
    return {
        "id": item.id,
        "task_id": item.task_id,
        "book_id": item.book_id,
        "book_title": book.title if book else None,
        "book_author": book.author if book else None,
        "book_cover": book.cover if book else None,
        "content_type": item.content_type,
        "content_type_label": meta.get("label", item.content_type),
        "target_field": item.target_field,
        "source_text": item.source_text,
        "generated_text": item.generated_text,
        "edited_text": item.edited_text,
        "final_text": item.edited_text or item.generated_text,
        "status": item.status,
        "error_message": item.error_message,
        "applied_at": item.applied_at.isoformat(sep=" ", timespec="seconds")
        if item.applied_at
        else None,
        "created_at": item.created_at.isoformat(sep=" ", timespec="seconds")
        if item.created_at
        else None,
        "updated_at": item.updated_at.isoformat(sep=" ", timespec="seconds")
        if item.updated_at
        else None,
    }


def task_to_dict(
    task: AiContentTask,
    items: Optional[List[AiContentItem]] = None,
    books: Optional[Dict[int, Book]] = None,
) -> Dict[str, Any]:
    book_map = books or {}
    return {
        "id": task.id,
        "operator_id": task.operator_id,
        "status": task.status,
        "content_types": [x for x in task.content_types.split(",") if x],
        "book_ids": _parse_csv_ids(task.book_ids),
        "tone": task.tone,
        "length": task.length,
        "extra_prompt": task.extra_prompt,
        "write_mode": task.write_mode,
        "provider_mode": task.provider_mode,
        "model_name": task.model_name,
        "error_message": task.error_message,
        "created_at": task.created_at.isoformat(sep=" ", timespec="seconds")
        if task.created_at
        else None,
        "finished_at": task.finished_at.isoformat(sep=" ", timespec="seconds")
        if task.finished_at
        else None,
        "items": [
            item_to_dict(item, book_map.get(item.book_id)) for item in (items or [])
        ],
    }


async def create_and_run_task(
    *,
    operator_id: int,
    book_ids: List[int],
    content_types: List[str],
    tone: str = "healing",
    length: str = "medium",
    extra_prompt: Optional[str] = None,
    write_mode: str = "empty_only",
) -> Dict[str, Any]:
    runtime = ai_runtime_config()
    if runtime["mode"] == "disabled":
        raise ValueError("未配置 AI_API_KEY，且已关闭 Mock，无法生成")

    uniq_books = []
    seen = set()
    for book_id in book_ids:
        if book_id not in seen:
            seen.add(book_id)
            uniq_books.append(book_id)
    if not uniq_books:
        raise ValueError("请至少选择一本书")
    if len(uniq_books) > MAX_BOOKS_PER_TASK:
        raise ValueError(f"单次最多选择 {MAX_BOOKS_PER_TASK} 本书")

    types = []
    for content_type in content_types:
        if content_type not in ALLOWED_TYPES:
            raise ValueError(f"不支持的生成类型: {content_type}")
        if content_type not in types:
            types.append(content_type)
    if not types:
        raise ValueError("请至少选择一种生成类型")

    if tone not in TONE_LABELS:
        tone = "healing"
    if length not in LENGTH_HINTS:
        length = "medium"
    if write_mode not in ("empty_only", "overwrite"):
        write_mode = "empty_only"

    books = await Book.filter(id__in=uniq_books)
    book_map = {book.id: book for book in books}
    missing = [book_id for book_id in uniq_books if book_id not in book_map]
    if missing:
        raise ValueError(f"书籍不存在: {missing}")

    categories = {
        cat.id: cat.name
        for cat in await Category.filter(id__in=list({b.category_id for b in books}))
    }
    videos = await BookVideo.filter(book_id__in=uniq_books).order_by("sort_order", "id")
    video_map: Dict[int, BookVideo] = {}
    for video in videos:
        if video.book_id not in video_map:
            video_map[video.book_id] = video

    mode = runtime["mode"]
    task = await AiContentTask.create(
        operator_id=operator_id,
        status="running",
        content_types=",".join(types),
        book_ids=",".join(str(x) for x in uniq_books),
        tone=tone,
        length=length,
        extra_prompt=(extra_prompt or "").strip() or None,
        write_mode=write_mode,
        provider_mode=mode,
        model_name=runtime.get("model"),
    )

    items: List[AiContentItem] = []
    try:
        for book_id in uniq_books:
            book = book_map[book_id]
            video = video_map.get(book_id)
            category_name = categories.get(book.category_id, "")
            for content_type in types:
                meta = CONTENT_TYPE_META[content_type]
                source = _source_text(book, content_type, video)
                item = await AiContentItem.create(
                    task_id=task.id,
                    book_id=book_id,
                    content_type=content_type,
                    target_field=meta["target_field"],
                    source_text=source or None,
                    status="generating",
                )
                try:
                    prompt = _build_user_prompt(
                        book,
                        category_name,
                        content_type,
                        tone,
                        length,
                        extra_prompt,
                        source,
                    )
                    if mode == "mock":
                        text = _mock_text(book, content_type, tone)
                    else:
                        text = await _call_llm(prompt)
                    if not text:
                        raise RuntimeError("模型返回空内容")
                    item.generated_text = text
                    item.status = "draft"
                    await item.save()
                except Exception as exc:  # noqa: BLE001
                    item.status = "failed"
                    item.error_message = str(exc)[:500]
                    await item.save()
                items.append(item)

        failed_all = items and all(item.status == "failed" for item in items)
        task.status = "failed" if failed_all else "completed"
        if failed_all:
            task.error_message = "全部条目生成失败"
        task.finished_at = datetime.utcnow()
        await task.save()
    except Exception as exc:  # noqa: BLE001
        task.status = "failed"
        task.error_message = str(exc)[:500]
        task.finished_at = datetime.utcnow()
        await task.save()
        raise

    return task_to_dict(task, items, book_map)


async def list_tasks(limit: int = 20) -> List[Dict[str, Any]]:
    safe_limit = max(1, min(limit, 50))
    tasks = await AiContentTask.all().order_by("-id").limit(safe_limit)
    if not tasks:
        return []
    task_ids = [task.id for task in tasks]
    items = await AiContentItem.filter(task_id__in=task_ids).order_by("id")
    items_by_task: Dict[int, List[AiContentItem]] = {task_id: [] for task_id in task_ids}
    book_ids = set()
    for item in items:
        items_by_task.setdefault(item.task_id, []).append(item)
        book_ids.add(item.book_id)
    book_map = {book.id: book for book in await Book.filter(id__in=list(book_ids))}
    return [task_to_dict(task, items_by_task.get(task.id, []), book_map) for task in tasks]


async def get_task_detail(task_id: int) -> Dict[str, Any]:
    task = await AiContentTask.get_or_none(id=task_id)
    if not task:
        raise ValueError("任务不存在")
    items = await AiContentItem.filter(task_id=task_id).order_by("id")
    book_ids = list({item.book_id for item in items})
    book_map = {book.id: book for book in await Book.filter(id__in=book_ids)}
    return task_to_dict(task, items, book_map)


async def update_item_text(item_id: int, text: str) -> Dict[str, Any]:
    item = await AiContentItem.get_or_none(id=item_id)
    if not item:
        raise ValueError("生成条目不存在")
    if item.status in ("accepted",):
        raise ValueError("已采纳的内容不可再编辑，请重新生成")
    cleaned = (text or "").strip()
    if not cleaned:
        raise ValueError("文案不能为空")
    item.edited_text = cleaned
    if item.status == "failed":
        item.status = "draft"
        item.error_message = None
    await item.save()
    book = await Book.get_or_none(id=item.book_id)
    return item_to_dict(item, book)


async def discard_item(item_id: int) -> Dict[str, Any]:
    item = await AiContentItem.get_or_none(id=item_id)
    if not item:
        raise ValueError("生成条目不存在")
    if item.status == "accepted":
        raise ValueError("已采纳内容不可丢弃")
    item.status = "discarded"
    await item.save()
    book = await Book.get_or_none(id=item.book_id)
    return item_to_dict(item, book)


async def accept_item(
    item_id: int,
    *,
    write_mode: Optional[str] = None,
    publish_date: Optional[date] = None,
    text: Optional[str] = None,
) -> Dict[str, Any]:
    item = await AiContentItem.get_or_none(id=item_id)
    if not item:
        raise ValueError("生成条目不存在")
    if item.status == "discarded":
        raise ValueError("已丢弃的内容不可采纳")
    if item.status == "failed" and not (text or item.edited_text or item.generated_text):
        raise ValueError("失败条目无可用文案")

    final_text = (text if text is not None else (item.edited_text or item.generated_text) or "").strip()
    if not final_text:
        raise ValueError("文案为空，无法采纳")

    book = await Book.get_or_none(id=item.book_id)
    if not book:
        raise ValueError("关联书籍不存在")

    task = await AiContentTask.get_or_none(id=item.task_id)
    mode = write_mode or (task.write_mode if task else "empty_only")
    if mode not in ("empty_only", "overwrite"):
        mode = "empty_only"

    content_type = item.content_type

    if content_type == "reading_note":
        raise ValueError("读书笔记仅作运营草稿，不支持写入业务表；可复制后自行使用")

    if content_type == "book_summary":
        if mode == "empty_only" and (book.summary or "").strip():
            raise ValueError("书籍简介已有内容，请改用覆盖模式")
        book.summary = final_text
        await book.save()
    elif content_type == "book_highlight":
        if mode == "empty_only" and (book.highlight or "").strip():
            raise ValueError("亮点已有内容，请改用覆盖模式")
        if len(final_text) > 500:
            raise ValueError("亮点文案过长（最多 500 字）")
        book.highlight = final_text
        await book.save()
    elif content_type in ("video_explain", "video_intro"):
        video = await BookVideo.filter(book_id=book.id).order_by("sort_order", "id").first()
        if not video:
            raise ValueError("该书尚未绑定解读视频，请先在「解读视频管理」创建后再采纳")
        if content_type == "video_explain":
            if mode == "empty_only" and (video.explain_content or "").strip():
                raise ValueError("解说文案已有内容，请改用覆盖模式")
            video.explain_content = final_text
        else:
            if mode == "empty_only" and (video.video_intro or "").strip():
                raise ValueError("视频简介已有内容，请改用覆盖模式")
            video.video_intro = final_text
        await video.save()
    elif content_type in ("daily_sentence", "daily_intro"):
        if not publish_date:
            raise ValueError("写入每日专栏需要指定 publish_date（YYYY-MM-DD）")
        daily = await DailyBook.get_or_none(publish_date=publish_date)
        if daily and daily.book_id != book.id and mode == "empty_only":
            raise ValueError(
                f"{publish_date} 已有其他书籍的每日内容，请更换日期或使用覆盖模式"
            )
        if not daily:
            if content_type == "daily_intro":
                raise ValueError("该日期尚无每日读书记录，请先采纳金句或先到每日专栏创建")
            daily = await DailyBook.create(
                book_id=book.id,
                daily_sentence=final_text if content_type == "daily_sentence" else "（待补充金句）",
                daily_intro=final_text if content_type == "daily_intro" else None,
                publish_date=publish_date,
                is_top=False,
                status=1,
            )
        else:
            if mode == "overwrite":
                daily.book_id = book.id
            if content_type == "daily_sentence":
                if mode == "empty_only" and (daily.daily_sentence or "").strip() and daily.daily_sentence != "（待补充金句）":
                    raise ValueError("该日金句已有内容，请改用覆盖模式")
                daily.daily_sentence = final_text
            else:
                if mode == "empty_only" and (daily.daily_intro or "").strip():
                    raise ValueError("该日简介已有内容，请改用覆盖模式")
                daily.daily_intro = final_text
            await daily.save()
    else:
        raise ValueError(f"未知内容类型: {content_type}")

    if text is not None:
        item.edited_text = final_text
    item.status = "accepted"
    item.applied_at = datetime.utcnow()
    await item.save()
    return item_to_dict(item, book)
