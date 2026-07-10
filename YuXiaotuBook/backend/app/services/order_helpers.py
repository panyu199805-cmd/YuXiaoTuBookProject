from __future__ import annotations

from typing import Iterable, Optional

from tortoise.expressions import Q

from app.models import Order, OrderItem, User
from app.utils.timezone import beijing_date_end_to_utc_naive, beijing_date_start_to_utc_naive, to_beijing_str

STATUS_LABELS = {
    "pending_payment": "待支付",
    "paid": "待发货",
    "shipped": "运输中",
    "completed": "已完成",
    "cancelled": "已取消",
}


def summarize_book_names(items: Iterable[OrderItem]) -> str:
    items = list(items)
    if not items:
        return "—"
    first = items[0]
    if len(items) == 1:
        return first.book_title if first.quantity <= 1 else f"{first.book_title} × {first.quantity}"
    return f"{first.book_title} 等{len(items)}种"


async def filter_admin_orders(
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
):
    qs = Order.all()

    if order_no and order_no.strip():
        qs = qs.filter(order_no__icontains=order_no.strip())

    if receiver_phone and receiver_phone.strip():
        qs = qs.filter(receiver_phone__icontains=receiver_phone.strip())

    if ship_tracking_no and ship_tracking_no.strip():
        qs = qs.filter(ship_tracking_no__icontains=ship_tracking_no.strip())

    if status and status.strip():
        qs = qs.filter(status=status.strip())

    if created_start:
        qs = qs.filter(created_at__gte=beijing_date_start_to_utc_naive(created_start))
    if created_end:
        qs = qs.filter(created_at__lte=beijing_date_end_to_utc_naive(created_end))

    if pay_start:
        qs = qs.filter(pay_time__gte=beijing_date_start_to_utc_naive(pay_start))
    if pay_end:
        qs = qs.filter(pay_time__lte=beijing_date_end_to_utc_naive(pay_end))

    if book_name and book_name.strip():
        order_ids = await OrderItem.filter(
            book_title__icontains=book_name.strip()
        ).values_list("order_id", flat=True)
        unique_ids = list(set(order_ids))
        qs = qs.filter(id__in=unique_ids if unique_ids else [-1])

    if user_nickname and user_nickname.strip():
        keyword = user_nickname.strip()
        user_ids = await User.filter(
            Q(nickname__icontains=keyword) | Q(username__icontains=keyword)
        ).values_list("id", flat=True)
        unique_user_ids = list(set(user_ids))
        qs = qs.filter(user_id__in=unique_user_ids if unique_user_ids else [-1])

    return qs


async def order_to_dict(
    order: Order,
    include_shipping: bool = True,
    user: Optional[User] = None,
) -> dict:
    items = await OrderItem.filter(order_id=order.id)
    if user is None:
        user = await User.get_or_none(id=order.user_id)
    total_quantity = sum(i.quantity for i in items)
    data = {
        "id": order.id,
        "order_no": order.order_no,
        "user_id": order.user_id,
        "user_nickname": user.nickname if user else None,
        "username": user.username if user else None,
        "book_name": summarize_book_names(items),
        "total_quantity": total_quantity,
        "item_kind_count": len(items),
        "total_amount": float(order.total_amount),
        "status": order.status,
        "status_label": STATUS_LABELS.get(order.status, order.status),
        "receiver_name": order.receiver_name,
        "receiver_phone": order.receiver_phone,
        "receiver_address": order.receiver_address,
        "pay_time": to_beijing_str(order.pay_time),
        "created_at": to_beijing_str(order.created_at),
        "cancel_reason": order.cancel_reason,
        "cancelled_at": to_beijing_str(order.cancelled_at),
        "cancel_by": order.cancel_by,
        "items": [
            {
                "book_id": i.book_id,
                "book_title": i.book_title,
                "price": float(i.price),
                "quantity": i.quantity,
            }
            for i in items
        ],
    }
    if include_shipping:
        data.update(
            {
                "ship_company": order.ship_company,
                "ship_tracking_no": order.ship_tracking_no,
                "shipped_at": to_beijing_str(order.shipped_at),
                "completed_at": to_beijing_str(order.completed_at),
            }
        )
    return data
