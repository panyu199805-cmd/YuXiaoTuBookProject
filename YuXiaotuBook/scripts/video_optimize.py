"""将 MP4 转码为 Web 播放友好格式（720p H.264 + faststart）。"""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

# 超过此大小（或 force）则转码
WEB_MAX_BYTES = 12 * 1024 * 1024


def find_ffmpeg() -> str | None:
    found = shutil.which("ffmpeg")
    if found:
        return found
    try:
        import imageio_ffmpeg

        exe = imageio_ffmpeg.get_ffmpeg_exe()
        if exe and Path(exe).is_file():
            return exe
    except ImportError:
        pass
    if sys.platform == "win32":
        local = os.environ.get("LOCALAPPDATA", "")
        for root in (
            Path(local) / "Microsoft" / "WinGet" / "Links",
            Path("C:/ffmpeg/bin"),
        ):
            candidate = root / "ffmpeg.exe"
            if candidate.is_file():
                return str(candidate)
    return None


def optimize_mp4_if_needed(path: Path, *, force: bool = False) -> bool:
    """
    就地优化 MP4。成功返回 True，跳过返回 False。
    """
    path = Path(path)
    if not path.is_file() or path.suffix.lower() != ".mp4":
        return False

    size = path.stat().st_size
    if not force and size <= WEB_MAX_BYTES:
        return False

    ffmpeg = find_ffmpeg()
    if not ffmpeg:
        print(f"[video] 跳过（未安装 ffmpeg）: {path.name} ({size // 1024 // 1024}MB)", file=sys.stderr)
        return False

    tmp = path.with_name(f"{path.stem}.web.tmp.mp4")
    if tmp.exists():
        tmp.unlink()

    cmd = [
        ffmpeg,
        "-y",
        "-hide_banner",
        "-loglevel",
        "error",
        "-i",
        str(path),
        "-c:v",
        "libx264",
        "-preset",
        "fast",
        "-crf",
        "24",
        "-vf",
        "scale='min(1280,iw)':-2",
        "-movflags",
        "+faststart",
        "-c:a",
        "aac",
        "-b:a",
        "96k",
        "-ac",
        "2",
        "-pix_fmt",
        "yuv420p",
        str(tmp),
    ]
    print(f"[video] 转码: {path.name} ({size // 1024 // 1024}MB) ...")
    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError:
        if tmp.exists():
            tmp.unlink()
        print(f"[video] 转码失败: {path}", file=sys.stderr)
        return False

    new_size = tmp.stat().st_size
    tmp.replace(path)
    print(f"[video] 完成: {path.name} -> {new_size // 1024 // 1024}MB")
    return True


def optimize_directory(directory: Path | str, *, force: bool = False) -> int:
    directory = Path(directory)
    if not directory.is_dir():
        return 0
    count = 0
    for mp4 in sorted(directory.glob("*.mp4")):
        if optimize_mp4_if_needed(mp4, force=force):
            count += 1
    return count
