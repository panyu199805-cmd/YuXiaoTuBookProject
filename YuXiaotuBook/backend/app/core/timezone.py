from __future__ import annotations

from datetime import date, datetime, time
from zoneinfo import ZoneInfo

BEIJING = ZoneInfo("Asia/Shanghai")
UTC = ZoneInfo("UTC")


def assume_utc(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=UTC)
    return dt.astimezone(UTC)


def format_beijing(dt: datetime | None) -> str | None:
    if not dt:
        return None
    return assume_utc(dt).astimezone(BEIJING).strftime("%Y-%m-%d %H:%M:%S")


def beijing_date_start(value: str) -> datetime:
    """日期筛选起点：北京时间当日 00:00:00 → UTC naive（与库内 UTC 比较）"""
    local = datetime.combine(date.fromisoformat(value[:10]), time.min, tzinfo=BEIJING)
    return local.astimezone(UTC).replace(tzinfo=None)


def beijing_date_end(value: str) -> datetime:
    """日期筛选终点：北京时间当日 23:59:59.999 → UTC naive"""
    local = datetime.combine(date.fromisoformat(value[:10]), time.max, tzinfo=BEIJING)
    return local.astimezone(UTC).replace(tzinfo=None)
