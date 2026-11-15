"""ReelKit command line interface."""
from __future__ import annotations

import argparse
import os
import sys
import tempfile

from . import __version__
from .ffutil import ReelKitError, probe, require_ffmpeg


def _out(path: str, suffix: str, ext: str | None = None) -> str:
    base, e = os.path.splitext(path)
    return f"{base}{suffix}{ext or e}"


def _add_caption_opts(p: argparse.ArgumentParser) -> None:
    p.add_argument("--model", default="small", help="Whisper size: tiny, base, small, medium, large-v3 (default: small)")
    p.add_argument("--lang", default=None, help="Language code, e.g. hi, mr, en. Default: auto-detect")
    p.add_argument("--prompt", default=None, help="Hint text to improve accuracy (names, Hinglish style, jargon)")
    p.add_argument("--words", type=int, default=3, help="Words shown at once (default: 3)")
    p.add_argument("--font", default="Noto Sans Devanagari", help="Caption font name (must be installed)")
    p.add_argument("--fonts-dir", default=None, help="Folder with extra .ttf/.otf fonts to use")
    p.add_argument("--color", default="#FFFFFF", help="Text colour (default #FFFFFF)")
    p.add_argument("--highlight", default="#FFD400", help="Spoken-word colour (default #FFD400)")
    p.add_argument("--size", type=float, default=0.065, help="Font size as fraction of video height")
    p.add_argument("--upper", action="store_true", help="UPPERCASE captions (Latin scripts)")


def _add_cut_opts(p: argparse.ArgumentParser) -> None:
    p.add_argument("--threshold", type=float, default=-35.0, help="Silence level in dB (default -35; lower = stricter)")
    p.add_argument("--min-silence", type=float, default=0.45, help="Shortest pause to cut, seconds (default 0.45)")
    p.add_argument("--pad", type=float, default=0.12, help="Breathing room kept around speech (default 0.12s)")


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        prog="reelkit",
        description="Free offline AI toolkit for video creators: auto captions + silence cutting.",
    )
    ap.add_argument("--version", action="version", version=f"reelkit {__version__}")
    sub = ap.add_subparsers(dest="cmd", required=True)

    a = sub.add_parser("auto", help="Cut silences AND burn captions in one go (recommended)")
    a.add_argument("video")
    a.add_argument("-o", "--output")
    a.add_argument("--no-cut", action="store_true", help="Skip silence removal")
    a.add_argument("--srt", action="store_true", help="Also save an .srt subtitle file")
    _add_cut_opts(a)
    _add_caption_opts(a)

    c = sub.add_parser("caption", help="Burn word-by-word captions into a video")
    c.add_argument("video")
    c.add_argument("-o", "--output")
    c.add_argument("--srt", action="store_true", help="Also save an .srt subtitle file")
    _add_caption_opts(c)

    k = sub.add_parser("cut", help="Remove silent gaps from a video")
    k.add_argument("video")
    k.add_argument("-o", "--output")
    _add_cut_opts(k)

    s = sub.add_parser("srt", help="Only export a subtitle (.srt) file")
    s.add_argument("video")
    s.add_argument("-o", "--output")
    s.add_argument("--model", default="small")
    s.add_argument("--lang", default=None)
    s.add_argument("--prompt", default=None)
    return ap


def _caption(src: str, dst: str, args, want_srt: bool) -> None:
    from .burn import burn_ass
    from .captions import build_ass, build_srt
    from .transcribe import transcribe

    info = probe(src)
    print("Transcribing (first run downloads the AI model)...")
    words = transcribe(src, args.model, args.lang, args.prompt)
    if not words:
        raise ReelKitError("No speech detected, nothing to caption.")
    print(f"Found {len(words)} words. Rendering captions...")
    ass = build_ass(
        words, info["width"], info["height"], per_line=args.words, font=args.font,
        font_scale=args.size, color=args.color, highlight=args.highlight, uppercase=args.upper,
    )
    with tempfile.TemporaryDirectory() as tmp:
        ass_path = os.path.join(tmp, "captions.ass")
        with open(ass_path, "w", encoding="utf-8") as f:
            f.write(ass)
        burn_ass(src, ass_path, dst, args.fonts_dir)
    if want_srt:
        srt_path = os.path.splitext(dst)[0] + ".srt"
        with open(srt_path, "w", encoding="utf-8") as f:
            f.write(build_srt(words))
        print(f"Saved {srt_path}")


def run(args) -> None:
    require_ffmpeg()
    if not os.path.isfile(args.video):
        raise ReelKitError(f"File not found: {args.video}")

    if args.cmd == "cut":
        from .silence import cut_silence
        dst = args.output or _out(args.video, "_cut")
        old, new = cut_silence(args.video, dst, args.threshold, args.min_silence, args.pad)
        print(f"Done: {dst}  ({old:.1f}s -> {new:.1f}s, saved {old - new:.1f}s)")

    elif args.cmd == "caption":
        dst = args.output or _out(args.video, "_captioned")
        _caption(args.video, dst, args, args.srt)
        print(f"Done: {dst}")

    elif args.cmd == "auto":
        dst = args.output or _out(args.video, "_reel")
        if args.no_cut:
            _caption(args.video, dst, args, args.srt)
        else:
            from .silence import cut_silence
            with tempfile.TemporaryDirectory() as tmp:
                trimmed = os.path.join(tmp, "trimmed.mp4")
                print("Removing silences...")
                old, new = cut_silence(args.video, trimmed, args.threshold, args.min_silence, args.pad)
                print(f"Trimmed {old:.1f}s -> {new:.1f}s")
                _caption(trimmed, dst, args, args.srt)
        print(f"Done: {dst}")

    elif args.cmd == "srt":
        from .captions import build_srt
        from .transcribe import transcribe
        dst = args.output or os.path.splitext(args.video)[0] + ".srt"
        words = transcribe(args.video, args.model, args.lang, args.prompt)
        if not words:
            raise ReelKitError("No speech detected.")
        with open(dst, "w", encoding="utf-8") as f:
            f.write(build_srt(words))
        print(f"Done: {dst}")


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        run(args)
    except ReelKitError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print("\nCancelled.", file=sys.stderr)
        return 130
    return 0


if __name__ == "__main__":
    sys.exit(main())
