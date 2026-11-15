import os, subprocess, tempfile
import pytest

from reelkit.captions import build_ass, build_srt, group_words
from reelkit.ffutil import probe
from reelkit.silence import cut_silence, keep_segments
from reelkit.transcribe import Word

WORDS = [Word(0.0, 0.4, "नमस्ते"), Word(0.5, 0.9, "दोस्तों,"), Word(1.0, 1.3, "आज"),
         Word(1.4, 1.8, "की"), Word(3.0, 3.4, "कहानी"), Word(3.5, 3.9, "सुनो")]


def test_keep_segments_inverts_silence():
    segs = keep_segments([(2.0, 4.0), (6.0, 9.0)], 11.0, pad=0.1)
    assert segs[0] == (0.0, 2.1)
    assert segs[1][0] == pytest.approx(3.9)
    assert segs[-1][1] == 11.0
    assert len(segs) == 3


def test_keep_segments_no_silence():
    assert keep_segments([], 5.0) == [(0.0, 5.0)]


def test_keep_segments_trailing_silence_open_ended():
    segs = keep_segments([(3.0, None)], 5.0, pad=0.1)
    assert segs == [(0.0, 3.1)]


def test_group_words_breaks_on_punct_and_pause():
    groups = group_words(WORDS, per_line=3)
    assert [len(g) for g in groups] == [2, 2, 2]  # comma break, then pause break


def test_ass_has_highlight_and_valid_times():
    ass = build_ass(WORDS, 1080, 1920)
    assert "PlayResX: 1080" in ass
    assert ass.count("Dialogue:") == len(WORDS)
    assert "&H00D4FF FF&".replace(" ", "") not in ass  # sanity: no malformed colour
    assert "\\c&H0000D4FF&" in ass  # #FFD400 -> BGR
    assert "नमस्ते" in ass


def test_srt_format():
    srt = build_srt(WORDS)
    assert srt.startswith("1\n00:00:00,000 --> ")


@pytest.fixture(scope="module")
def sample(tmp_path_factory):
    from make_sample import make
    p = str(tmp_path_factory.mktemp("v") / "sample.mp4")
    make(p)
    return p


def test_cut_silence_shortens_video(sample, tmp_path):
    dst = str(tmp_path / "cut.mp4")
    old, new = cut_silence(sample, dst)
    assert old == pytest.approx(11.0, abs=0.3)
    assert 6.0 < new < 8.5            # ~6s speech + padding
    real = probe(dst)["duration"]
    assert real == pytest.approx(new, abs=0.4)
    assert probe(dst)["width"] == 1080


def test_burn_captions(sample, tmp_path):
    from reelkit.burn import burn_ass
    ass = tmp_path / "c.ass"
    ass.write_text(build_ass(WORDS, 1080, 1920), encoding="utf-8")
    dst = str(tmp_path / "burned.mp4")
    burn_ass(sample, str(ass), dst)
    assert os.path.getsize(dst) > 1000
    assert probe(dst)["height"] == 1920
