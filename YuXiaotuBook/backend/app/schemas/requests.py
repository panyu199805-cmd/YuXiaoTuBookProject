from __future__ import annotations

import re
from typing import List, Optional

from pydantic import BaseModel, Field


class RegisterRequest(BaseModel):
    username: str = Field(..., min_length=4, max_length=20)
    password: str = Field(..., min_length=8)
    nickname: Optional[str] = None
    province: Optional[str] = Field(None, max_length=50)
    city: Optional[str] = Field(None, max_length=50)


class LoginRequest(BaseModel):
    username: str
    password: str


class PlayReportRequest(BaseModel):
    position: float = 0


class FavoriteRequest(BaseModel):
    book_id: int


class BookCreateRequest(BaseModel):
    title: str
    author: str
    cover: str
    category_id: int
    price: float
    stock: int = 0
    summary: Optional[str] = None
    highlight: Optional[str] = None
    target_audience: Optional[str] = None
    status: str = "draft"


class BookUpdateRequest(BaseModel):
    title: Optional[str] = None
    author: Optional[str] = None
    cover: Optional[str] = None
    category_id: Optional[int] = None
    price: Optional[float] = None
    stock: Optional[int] = None
    summary: Optional[str] = None
    highlight: Optional[str] = None
    target_audience: Optional[str] = None
    status: Optional[str] = None


class VideoBindRequest(BaseModel):
    book_id: int
    video_cover: str
    video_url: str
    video_duration: float = 0
    video_intro: Optional[str] = None
    status: int = 1


class BookVideoItemRequest(BaseModel):
    video_cover: str = ""
    video_url: str
    video_duration: float = 0
    video_intro: Optional[str] = None
    status: int = 1


class BookVideosUpdateRequest(BaseModel):
    videos: List[BookVideoItemRequest] = Field(default_factory=list)


class CategoryRequest(BaseModel):
    name: str
    slug: str
    sort_order: int = 0


class SiteConfigRequest(BaseModel):
    bg_type: str = "image"
    bg_url: Optional[str] = None
    bg_videos: Optional[List[str]] = None
    bg_music: Optional[str] = None
    white_noise: Optional[str] = None
    music_enabled: bool = True
    bg_enabled: bool = True
    featured_book_id: Optional[int] = None
    promo_title: Optional[str] = None
    daily_sentence: Optional[str] = None


class DailyBookRequest(BaseModel):
    book_id: int
    daily_sentence: str
    daily_intro: Optional[str] = None
    publish_date: str
    is_top: bool = False
    status: int = 1


class DailyBookUpdateRequest(BaseModel):
    book_id: Optional[int] = None
    daily_sentence: Optional[str] = None
    daily_intro: Optional[str] = None
    publish_date: Optional[str] = None
    is_top: Optional[bool] = None
    status: Optional[int] = None


class MemberPackageRequest(BaseModel):
    package_name: str
    price: float
    valid_day: int = 30
    rights: str = "[]"
    status: int = 1


class UserPreferenceRequest(BaseModel):
    category_ids: List[int] = Field(default_factory=list)
    scene_tags: List[str] = Field(default_factory=list)
    bio: Optional[str] = None


class ShipOrderRequest(BaseModel):
    ship_company: str = Field(..., min_length=1, max_length=50)
    ship_tracking_no: str = Field(..., min_length=1, max_length=64)


class AdminOrderUpdateRequest(BaseModel):
    receiver_name: str = Field(..., min_length=1, max_length=50)
    receiver_phone: str = Field(..., min_length=1, max_length=20)
    receiver_address: str = Field(..., min_length=1, max_length=500)
    ship_company: Optional[str] = Field(None, max_length=50)
    ship_tracking_no: Optional[str] = Field(None, max_length=64)


class AdminUserUpdateRequest(BaseModel):
    nickname: Optional[str] = None
    province: Optional[str] = Field(None, max_length=50)
    city: Optional[str] = Field(None, max_length=50)
    status: Optional[int] = None


class AiGenerateRequest(BaseModel):
    book_ids: List[int] = Field(..., min_length=1)
    content_types: List[str] = Field(..., min_length=1)
    tone: str = "healing"
    length: str = "medium"
    extra_prompt: Optional[str] = Field(None, max_length=500)
    write_mode: str = "empty_only"


class AiItemUpdateRequest(BaseModel):
    text: str = Field(..., min_length=1)


class AiItemAcceptRequest(BaseModel):
    text: Optional[str] = None
    write_mode: Optional[str] = None
    publish_date: Optional[str] = None


def validate_username(username: str) -> bool:
    return bool(re.match(r"^[a-zA-Z0-9_]{4,20}$", username))
