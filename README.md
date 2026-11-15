<div align="center">

# 🎬 ReelKit

**Turn a raw talking video into a ready-to-post Reel in one command.**
Auto captions (Hindi, Marathi, English + 90 more languages) and silence cutting. Free, offline, no API keys, no watermark.

[![CI](https://github.com/mandalerajesh-byte/reelkit/actions/workflows/ci.yml/badge.svg)](https://github.com/mandalerajesh-byte/reelkit/actions)
![Python](https://img.shields.io/badge/python-3.9+-blue)
![License](https://img.shields.io/badge/license-MIT-green)

<img src="docs/preview.png" width="260" alt="ReelKit word-by-word Hindi caption preview">

</div>

<p align="center"><a href="docs/demo.mp4"><b>▶ Watch the 14-second demo</b></a> (Hindi speech → silence cut → highlighted captions, one command)</p>

> Paid tools charge ₹500–2000/month for this. ReelKit does it on your own laptop, for free.

## ✨ Features

- 🗣️ **Word-by-word highlighted captions**, the viral Reels/Shorts style
- 🇮🇳 **Hindi & Marathi (Devanagari) supported**, plus ~99 languages via Whisper
- ✂️ **Silence remover**: cuts dead air so your video feels fast
- 📱 Auto-sizes for vertical 9:16 or any resolution
- 📝 Export `.srt` subtitles for YouTube
- 🔒 100% offline. Your videos never leave your computer
- 🎨 Custom colours, fonts, words per line

## 🚀 Quick start

```bash
# 1. Install FFmpeg (Windows: winget install ffmpeg | Mac: brew install ffmpeg | Linux: apt install ffmpeg)
# 2. Install ReelKit
pip install git+https://github.com/mandalerajesh-byte/reelkit.git

# 3. Magic
reelkit auto my_video.mp4 --lang hi
```

You get `my_video_reel.mp4`: silences removed, captions burned in. The first run downloads the AI model once (~460 MB for `small`).

## 🧰 Commands

| Command | What it does |
|---|---|
| `reelkit auto video.mp4` | Cut silences **and** add captions (recommended) |
| `reelkit caption video.mp4` | Captions only |
| `reelkit cut video.mp4` | Remove silences only |
| `reelkit srt video.mp4` | Export `.srt` subtitles only |

### Handy options

```bash
reelkit auto video.mp4 --lang hi --words 2 --highlight "#00FF99"   # 2 words at a time, green highlight
reelkit auto video.mp4 --model medium                              # more accurate, slower
reelkit auto video.mp4 --prompt "Hinglish, names: Ram, Sita"        # hint for tricky words
reelkit cut  video.mp4 --threshold -40 --min-silence 0.6           # gentler cutting
reelkit caption video.mp4 --font "Poppins" --fonts-dir ./fonts --upper
```

## 🔤 Fonts for Hindi / Marathi

Captions need a font that has Devanagari letters. The default is **Noto Sans Devanagari** (free from Google Fonts). If you don't have it installed, download it, put the `.ttf` in a folder and run:

```bash
reelkit auto video.mp4 --fonts-dir ./fonts --font "Noto Sans Devanagari"
```

## 💡 Tips

- **Hindi/Marathi accuracy:** ReelKit automatically uses the `medium` model for Indian languages (the small model mishears words). For the best result use `--model large-v3`. In our test it transcribed a Hindi clip almost perfectly, and `--prompt "रील किट, कैप्शन"` fixes tricky spellings and brand names.
- Not accurate enough? Use `--model medium` or `--model large-v3` and set `--lang`.
- Cutting too aggressively? Lower `--threshold` (e.g. `-45`) or raise `--min-silence`.
- Have a GPU? It's used automatically, which is much faster.

## 🗺️ Roadmap

- [ ] Emoji / keyword auto-highlighting
- [ ] Auto hook-title generator
- [ ] B-roll suggestions
- [ ] Simple GUI (drag & drop)
- [ ] Batch mode for whole folders

Ideas and PRs welcome, see [CONTRIBUTING.md](CONTRIBUTING.md). Look for the `good first issue` label.

## 🙏 Built with

[faster-whisper](https://github.com/SYSTRAN/faster-whisper) · [FFmpeg](https://ffmpeg.org)

## 📄 License

MIT. Free for personal and commercial use. If ReelKit saved you time, a ⭐ helps others find it!
