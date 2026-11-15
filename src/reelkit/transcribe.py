"""Speech -> word-level timestamps using faster-whisper (runs fully offline)."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Word:
    start: float
    end: float
    text: str


def transcribe(
    path: str,
    model_size: str = "small",
    language: str | None = None,
    prompt: str | None = None,
) -> list[Word]:
    try:
        from faster_whisper import WhisperModel
    except ImportError as e:  # pragma: no cover
        from .ffutil import ReelKitError
        raise ReelKitError("faster-whisper is missing. Run: pip install faster-whisper") from e

    model = WhisperModel(model_size, device="auto", compute_type="auto")
    segments, info = model.transcribe(
        path,
        language=language,
        word_timestamps=True,
        vad_filter=True,
        initial_prompt=prompt,
    )
    words: list[Word] = []
    for seg in segments:
        for w in seg.words or []:
            text = w.word.strip()
            if text:
                words.append(Word(float(w.start), float(w.end), text))
    return words
