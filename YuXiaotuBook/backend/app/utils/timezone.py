from __future__ import annotations

from datetime import date, datetime, time
import pytz

BEIJING = pytz.timezone("Asia/Shanghai")
UTC = pytz.UTC


def assume_utc(dt: datetime) -> datetime:
    """DB 中的 naive datetime 按 UTC 存储。"""
    if dt.tzinfo is None:
        return dt.replace(tzinfo=UTC)
    return dt.astimezone(UTC)


def to_beijing_str(dt: datetime | None) -> str | None:
    if not dt:
        return None
    return assume_utc(dt).astimezone(BEIJING).strftime("%Y-%m-%d %H:%M:%S")


def beijing_date_start_to_utc_naive(value: str) -> datetime:
    """日期筛选：北京时间当天 00:00:00 → UTC naive（供 ORM 比较）。"""
    local = datetime.combine(date.fromisoformat(value[:10]), time.min, tzinfo=BEIJING)
    return local.astimezone(UTC).replace(tzinfo=None)


def beijing_date_end_to_utc_naive(value: str) -> datetime:
    """日期筛选：北京时间当天 23:59:59.999999 → UTC naive。"""
    local = datetime.combine(date.fromisoformat(value[:10]), time.max, tzinfo=BEIJING)
    return local.astimezone(UTC).replace(tzinfo=None)
