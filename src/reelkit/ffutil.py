"""Thin helpers around ffmpeg / ffprobe."""
from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys


class ReelKitError(Exception):
    """User-facing error (printed without a traceback)."""


def require_ffmpeg() -> None:
    for tool in ("ffmpeg", "ffprobe"):
        if shutil.which(tool) is None:
            raise ReelKitError(
                f"'{tool}' not found. Install FFmpeg first:\n"
                "  Windows: winget install ffmpeg   |  macOS: brew install ffmpeg\n"
                "  Linux:   sudo apt install ffmpeg"
            )


def probe(path: str) -> dict:
    """Return width, height, duration and has_audio for a media file."""
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-print_format", "json",
         "-show_streams", "-show_format", path],
        capture_output=True, text=True,
    )
    if out.returncode != 0:
        raise ReelKitError(f"Could not read '{path}': {out.stderr.strip()}")
    info = json.loads(out.stdout)
    video = next((s for s in info["streams"] if s["codec_type"] == "video"), None)
    audio = next((s for s in info["streams"] if s["codec_type"] == "audio"), None)
    if video is None:
        raise ReelKitError("No video stream found in the input file.")
    return {
        "width": int(video["width"]),
        "height": int(video["height"]),
        "duration": float(info["format"].get("duration", 0) or 0),
        "has_audio": audio is not None,
    }


def run_ffmpeg(args: list[str], quiet: bool = True) -> str:
    cmd = ["ffmpeg", "-y", "-hide_banner"] + (["-loglevel", "error"] if quiet else []) + args
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        print(proc.stderr, file=sys.stderr)
        raise ReelKitError("ffmpeg failed (see message above).")
    return proc.stderr


def detect_silences(path: str, noise_db: float, min_silence: float) -> list[tuple[float, float | None]]:
    """Run ffmpeg silencedetect; return (start, end) pairs (end None = until EOF)."""
    proc = subprocess.run(
        ["ffmpeg", "-hide_banner", "-nostats", "-i", path, "-vn",
         "-af", f"silencedetect=noise={noise_db}dB:d={min_silence}", "-f", "null", "-"],
        capture_output=True, text=True,
    )
    starts = [float(x) for x in re.findall(r"silence_start: (-?[\d.]+)", proc.stderr)]
    ends = [float(x) for x in re.findall(r"silence_end: (-?[\d.]+)", proc.stderr)]
    pairs: list[tuple[float, float | None]] = []
    for i, s in enumerate(starts):
        pairs.append((max(s, 0.0), ends[i] if i < len(ends) else None))
    return pairs
