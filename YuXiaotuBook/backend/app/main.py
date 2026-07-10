from __future__ import annotations

import os

from fastapi import FastAPI, Response
from fastapi.middleware.cors import CORSMiddleware

from app.core.static_files import CachedStaticFiles
from app.services.home_page_video_service import home_page_dir

from app.api.v1 import api_router
from app.api.v1.media import router as media_router
from app.core.config import settings
from app.core.openapi import setup_openapi
from app.core.response import success
from app.db.database import close_db, init_db
from app.models import Book

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PLACEHOLDERS_DIR = os.path.join(BASE_DIR, "static", "placeholders")

APP_DESCRIPTION = """
宇小兔每日读书 · 后台管理 API（与 `/admin` 管理台功能对应）。

**使用说明**
1. 调用 `POST /api/v1/auth/login` 登录（管理员：`admin` / `admin123456`）
2. 点击右上角 **Authorize**，填入 `Bearer {token}`
3. 调试 Admin-* 分组下的接口
"""


def create_app() -> FastAPI:
    app = FastAPI(
        title="宇小兔每日读书 · 管理后台",
        version="1.0.0",
        description=APP_DESCRIPTION,
        docs_url="/docs" if settings.DEBUG else None,
        redoc_url="/redoc" if settings.DEBUG else None,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    os.makedirs(PLACEHOLDERS_DIR, exist_ok=True)
    os.makedirs(home_page_dir(), exist_ok=True)
    # homePage 需优先挂载（本地可能指向 网站素材/首页展览素材，不在 UPLOAD_DIR 下）
    app.mount(
        "/uploads/homePage",
        CachedStaticFiles(directory=home_page_dir()),
        name="home-page-uploads",
    )
    app.mount("/uploads", CachedStaticFiles(directory=settings.UPLOAD_DIR), name="uploads")
    app.mount(
        "/placeholders",
        CachedStaticFiles(directory=PLACEHOLDERS_DIR),
        name="placeholders",
    )
    app.include_router(api_router, prefix="/api/v1")
    app.include_router(media_router, prefix="/media")
    setup_openapi(app)

    @app.on_event("startup")
    async def startup() -> None:
        await init_db()

    @app.on_event("shutdown")
    async def shutdown() -> None:
        await close_db()

    @app.get("/api/health", tags=["系统"])
    async def health():
        return success({"status": "ok", "service": "yuxiaotu-book"})

    @app.get("/sitemap.xml", include_in_schema=False)
    async def sitemap() -> Response:
        books = await Book.filter(status="published").all()
        urls = "\n".join(
            f"  <url><loc>https://example.com/books/{b.id}</loc></url>" for b in books
        )
        xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url><loc>https://example.com/</loc></url>
  <url><loc>https://example.com/books</loc></url>
{urls}
</urlset>"""
        return Response(content=xml, media_type="application/xml")

    return app


app = create_app()
