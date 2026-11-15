"""Turn word timestamps into viral-style captions (ASS) or plain SRT."""
from __future__ import annotations

from .transcribe import Word

PUNCT_BREAK = tuple(".!?,;:।॥")


def group_words(words: list[Word], per_line: int = 3, max_gap: float = 0.7) -> list[list[Word]]:
    """Group words into short on-screen chunks. A chunk ends when it is full,
    after sentence punctuation, or after a long pause."""
    groups: list[list[Word]] = []
    cur: list[Word] = []
    for i, w in enumerate(words):
        cur.append(w)
        nxt = words[i + 1] if i + 1 < len(words) else None
        full = len(cur) >= per_line
        punct = w.text.endswith(PUNCT_BREAK)
        pause = nxt is not None and (nxt.start - w.end) > max_gap
        if full or punct or pause or nxt is None:
            groups.append(cur)
            cur = []
    return groups


def _ass_time(t: float) -> str:
    t = max(t, 0.0)
    cs = int(round(t * 100))
    h, rem = divmod(cs, 360000)
    m, rem = divmod(rem, 6000)
    s, cs = divmod(rem, 100)
    return f"{h}:{m:02d}:{s:02d}.{cs:02d}"


def _srt_time(t: float) -> str:
    ms = int(round(max(t, 0.0) * 1000))
    h, rem = divmod(ms, 3600000)
    m, rem = divmod(rem, 60000)
    s, ms = divmod(rem, 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def _bgr(hex_color: str) -> str:
    """'#RRGGBB' -> ASS '&H00BBGGRR&'."""
    h = hex_color.lstrip("#")
    if len(h) != 6:
        raise ValueError(f"Bad colour '{hex_color}', use #RRGGBB")
    r, g, b = h[0:2], h[2:4], h[4:6]
    return f"&H00{b}{g}{r}&".upper()


def build_ass(
    words: list[Word],
    width: int,
    height: int,
    per_line: int = 3,
    font: str = "Noto Sans Devanagari",
    font_scale: float = 0.065,
    color: str = "#FFFFFF",
    highlight: str = "#FFD400",
    outline: str = "#000000",
    bottom_margin: float = 0.28,
    uppercase: bool = False,
) -> str:
    """Build an ASS file where the spoken word is highlighted inside each chunk."""
    size = max(int(height * font_scale), 12)
    outline_px = max(int(size * 0.09), 2)
    margin_v = int(height * bottom_margin)
    header = (
        "[Script Info]\nScriptType: v4.00+\n"
        f"PlayResX: {width}\nPlayResY: {height}\nWrapStyle: 2\nScaledBorderAndShadow: yes\n\n"
        "[V4+ Styles]\n"
        "Format: Name,Fontname,Fontsize,PrimaryColour,SecondaryColour,OutlineColour,BackColour,"
        "Bold,Italic,Underline,StrikeOut,ScaleX,ScaleY,Spacing,Angle,BorderStyle,Outline,Shadow,"
        "Alignment,MarginL,MarginR,MarginV,Encoding\n"
        f"Style: Default,{font},{size},{_bgr(color)},{_bgr(color)},{_bgr(outline)},&H64000000&,"
        f"-1,0,0,0,100,100,0,0,1,{outline_px},2,2,{int(width*0.06)},{int(width*0.06)},{margin_v},1\n\n"
        "[Events]\nFormat: Layer,Start,End,Style,Name,MarginL,MarginR,MarginV,Effect,Text\n"
    )
    hi = _bgr(highlight)
    base = _bgr(color)
    lines = [header]
    for group in group_words(words, per_line):
        for idx, w in enumerate(group):
            start = w.start
            # hold the word until the next one begins (no flicker); last word waits a touch
            end = group[idx + 1].start if idx + 1 < len(group) else w.end + 0.15
            if end <= start:
                end = start + 0.05
            parts = []
            for j, other in enumerate(group):
                t = other.text.upper() if uppercase else other.text
                t = t.replace("{", "(").replace("}", ")")
                if j == idx:
                    parts.append(f"{{\\c{hi}\\fscx112\\fscy112}}{t}{{\\c{base}\\fscx100\\fscy100}}")
                else:
                    parts.append(t)
            text = " ".join(parts)
            lines.append(
                f"Dialogue: 0,{_ass_time(start)},{_ass_time(end)},Default,,0,0,0,,{text}\n"
            )
    return "".join(lines)


def build_srt(words: list[Word], per_line: int = 6) -> str:
    out = []
    for i, group in enumerate(group_words(words, per_line, max_gap=0.9), 1):
        text = " ".join(w.text for w in group)
        out.append(f"{i}\n{_srt_time(group[0].start)} --> {_srt_time(group[-1].end)}\n{text}\n")
    return "\n".join(out)
