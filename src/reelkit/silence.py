"""Remove dead air from a video."""
from __future__ import annotations

import os
import tempfile

from .ffutil import ReelKitError, detect_silences, probe, run_ffmpeg


def keep_segments(
    silences: list[tuple[float, float | None]],
    duration: float,
    pad: float = 0.12,
    min_keep: float = 0.15,
) -> list[tuple[float, float]]:
    """Invert silence ranges into the ranges we keep, leaving `pad` seconds of
    breathing room around speech so cuts don't sound clipped."""
    keeps: list[tuple[float, float]] = []
    cursor = 0.0
    for s, e in silences:
        end_of_speech = min(s + pad, duration)
        if end_of_speech - cursor >= min_keep:
            keeps.append((cursor, end_of_speech))
        cursor = max(cursor, (e if e is not None else duration) - pad)
    if duration - cursor >= min_keep:
        keeps.append((cursor, duration))
    # merge overlaps created by padding
    merged: list[tuple[float, float]] = []
    for s, e in keeps:
        if merged and s <= merged[-1][1]:
            merged[-1] = (merged[-1][0], max(merged[-1][1], e))
        else:
            merged.append((s, e))
    return merged


def cut_silence(
    src: str,
    dst: str,
    noise_db: float = -35.0,
    min_silence: float = 0.45,
    pad: float = 0.12,
) -> tuple[float, float]:
    """Write `dst` with silent gaps removed. Returns (old_duration, new_duration)."""
    info = probe(src)
    if not info["has_audio"]:
        raise ReelKitError("This video has no audio track, so there is no silence to cut.")
    duration = info["duration"]
    silences = detect_silences(src, noise_db, min_silence)
    segs = keep_segments(silences, duration, pad=pad)
    if not segs:
        raise ReelKitError("Everything was detected as silence. Try a lower --threshold (e.g. -45).")

    if len(segs) == 1 and segs[0][0] <= 0.01 and segs[0][1] >= duration - 0.01:
        # nothing to cut
        run_ffmpeg(["-i", src, "-c", "copy", dst])
        return duration, duration

    parts = []
    for i, (s, e) in enumerate(segs):
        parts.append(f"[0:v]trim=start={s:.3f}:end={e:.3f},setpts=PTS-STARTPTS[v{i}];")
        parts.append(f"[0:a]atrim=start={s:.3f}:end={e:.3f},asetpts=PTS-STARTPTS[a{i}];")
    inputs = "".join(f"[v{i}][a{i}]" for i in range(len(segs)))
    graph = "".join(parts) + f"{inputs}concat=n={len(segs)}:v=1:a=1[v][a]"

    # script file avoids OS command-length limits on long videos
    with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False) as f:
        f.write(graph)
        script = f.name
    try:
        run_ffmpeg([
            "-i", src, "-filter_complex_script", script,
            "-map", "[v]", "-map", "[a]",
            "-c:v", "libx264", "-preset", "veryfast", "-crf", "18",
            "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", dst,
        ])
    finally:
        os.unlink(script)
    new_duration = sum(e - s for s, e in segs)
    return duration, new_duration
