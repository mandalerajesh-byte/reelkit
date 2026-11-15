"""Burn an ASS subtitle file into a video."""
from __future__ import annotations

import os
import shutil
import tempfile

from .ffutil import run_ffmpeg


def burn_ass(src: str, ass_path: str, dst: str, fonts_dir: str | None = None) -> None:
    # ffmpeg's filter syntax treats ':' and '\' specially, so copy the subtitle
    # file to a plain temp name and run from that directory.
    with tempfile.TemporaryDirectory() as tmp:
        local_ass = os.path.join(tmp, "subs.ass")
        shutil.copy(ass_path, local_ass)
        vf = "ass=subs.ass"
        if fonts_dir:
            fd = os.path.join(tmp, "fonts")
            shutil.copytree(fonts_dir, fd)
            vf += ":fontsdir=fonts"
        src_abs, dst_abs = os.path.abspath(src), os.path.abspath(dst)
        cwd = os.getcwd()
        os.chdir(tmp)
        try:
            run_ffmpeg([
                "-i", src_abs, "-vf", vf,
                "-c:v", "libx264", "-preset", "veryfast", "-crf", "18",
                "-c:a", "copy", "-movflags", "+faststart", dst_abs,
            ])
        finally:
            os.chdir(cwd)
