from __future__ import annotations

import os
from typing import List

from dotenv import load_dotenv

load_dotenv()


class Settings:
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "mysql://root:123456@127.0.0.1:3306/yuxiaotu_book",
    )
    JWT_SECRET: str = os.getenv("JWT_SECRET", "dev-secret-change-in-production-32chars")
    JWT_EXPIRE_HOURS: int = int(os.getenv("JWT_EXPIRE_HOURS", "168"))
    GUEST_VIDEO_PREVIEW_SECONDS: int = int(os.getenv("GUEST_VIDEO_PREVIEW_SECONDS", "180"))
    CORS_ORIGINS: List[str] = [
        o.strip()
        for o in os.getenv(
            "CORS_ORIGINS", "http://localhost:5188,http://127.0.0.1:5188"
        ).split(",")
        if o.strip()
    ]
    DEBUG: bool = os.getenv("DEBUG", "true").lower() == "true"
    UPLOAD_DIR: str = os.getenv("UPLOAD_DIR", os.path.join(os.getcwd(), "uploads"))
    # 留空则自动：本地用 网站素材/首页展览素材，生产用 UPLOAD_DIR/homePage
    HOME_PAGE_VIDEO_DIR: str = os.getenv("HOME_PAGE_VIDEO_DIR", "")


settings = Settings()
