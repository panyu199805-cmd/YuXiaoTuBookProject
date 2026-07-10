from __future__ import annotations

from typing import Literal

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from app.services.video_url_service import resolve_video_file

router = APIRouter()


@router.get("/v/{category}/{name}", include_in_schema=False)
async def stream_protected_video(
    category: Literal["homePage", "bookReview"],
    name: str,
):
    path = resolve_video_file(category, name)
    if not path:
        raise HTTPException(status_code=404, detail="视频不存在")

    ext = path.suffix.lower()
    media_type = "video/webm" if ext == ".webm" else "video/mp4"
    return FileResponse(
        path,
        media_type=media_type,
        headers={
            "Content-Disposition": f'inline; filename="{path.name}"',
            "Accept-Ranges": "bytes",
            "Cache-Control": "public, max-age=31536000, immutable",
            "X-Content-Type-Options": "nosniff",
        },
    )
