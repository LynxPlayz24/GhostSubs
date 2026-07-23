# GhostSubs 👻

A live, low-latency Japanese-to-English subtitle overlay system for your desktop.

GhostSubs runs a transparent, always-on-top subtitle bar that floats over any application (like your browser, a game, or media player). It captures live Japanese audio (e.g., from a livestream using a virtual audio cable), transcribes it, translates it to English using a hybrid AI pipeline, and displays the subtitles in real-time.

## Features
- **Hybrid Real-Time Translation Pipeline**: Combines `large-v3-turbo` for high-accuracy Japanese speech recognition with `OPUS-MT` (`Helsinki-NLP/opus-mt-ja-en`) for lightweight, low-latency (~100-150ms) Japanese-to-English translation.
- **Ultra Low-Latency Streaming**: Tuned VAD thresholds, audio buffer accumulation, and fast UI polling (~600ms–1s end-to-end delay).
- **YouTube-Style Subtitles**: Displays recent lines of dialogue clearly without cluttering your screen.
- **Transparent Desktop Overlay**: A draggable, resizable (via mouse scroll wheel) overlay that sits on top of all windows.
- **One-Click Startup**: Launch the entire pipeline (server, overlay UI, and streaming client) via `start_all.bat`.

## Prerequisites
1. **Python 3.10+**
2. **VB-Audio Virtual Cable** (or similar virtual audio cable to route system/browser audio into the microphone input)
3. **PyTorch & Dependencies** (see `requirements.txt`)

## How to Run

1. Double-click `start_all.bat`.
2. This will launch:
   - **WhisperLive Backend Server**: Runs `large-v3-turbo` ASR + `OPUS-MT` translation.
   - **Desktop Subtitle Overlay UI**: Transparent floating window.
   - **Translation Client**: Streams audio input to the backend server.
3. Drag the subtitle bar anywhere on your screen. Use your **mouse scroll wheel** over the bar to resize the text. Right-click to close.

---

*Note: This project is a low-latency, hybrid translation overlay fork built on top of [WhisperLive](https://github.com/collabora/WhisperLive).*
