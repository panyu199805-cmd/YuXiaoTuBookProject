from datetime import datetime
from typing import Any, Dict

from app.utils.timezone import to_beijing_str

from app.models import MemberPackage, MemberOrder, UserMember


def _utc_now() -> datetime:
    return datetime.utcnow()


def _naive_utc(dt: datetime) -> datetime:
    if dt.tzinfo is not None:
        return dt.replace(tzinfo=None)
    return dt


async def is_vip(user_id: int) -> bool:
    """只读 VIP 状态；写入由 Java trade-service 负责。"""
    record = await UserMember.get_or_none(user_id=user_id)
    if not record or not record.is_vip:
        return False
    if _naive_utc(record.expire_time) < _utc_now():
        record.is_vip = False
        await record.save()
        return False
    return True


async def get_member_profile(user_id: int) -> Dict[str, Any]:
    """只读会员资料；供 auth/books/admin 展示。"""
    record = await UserMember.get_or_none(user_id=user_id)
    active = await is_vip(user_id)
    if not record:
        return {"is_vip": False, "expire_time": None, "package_id": None, "package_name": None}
    package = await MemberPackage.get_or_none(id=record.package_id)
    return {
        "is_vip": active,
        "expire_time": record.expire_time.isoformat() if record.expire_time else None,
        "package_id": record.package_id,
        "package_name": package.package_name if package else None,
    }


def member_order_to_dict(order: MemberOrder) -> Dict[str, Any]:
    return {
        "id": order.id,
        "order_no": order.order_no,
        "amount": order.amount,
        "status": order.status,
        "pay_channel": order.pay_channel,
        "pay_time": to_beijing_str(order.pay_time),
        "created_at": to_beijing_str(order.created_at),
    }
