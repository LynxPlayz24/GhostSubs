# GhostSubs 👻

A live, low-latency Japanese-to-English subtitle overlay system for your desktop.

GhostSubs runs a transparent, always-on-top subtitle bar that floats over any application (like your browser or a game). It captures live Japanese audio (e.g., from a livestream using a virtual audio cable), transcribes it, translates it to English using Whisper, and displays the subtitles in real-time.

## Features
- **Real-Time Translation**: Uses Whisper's built-in translation to convert Japanese speech to English text with minimal latency.
- **YouTube-Style Subtitles**: Shows only the last two lines of dialogue so your screen doesn't get cluttered.
- **Transparent Desktop Overlay**: A draggable, resizable (via scroll wheel) overlay that sits on top of everything. No OBS needed if you're just watching!
- **One-Click Startup**: Everything launches automatically via `start_all.bat`.

## Prerequisites
1. **Python**
2. **VB Audio Cable** (or similar virtual audio cable to route audio into the program)
3. Installed dependencies (see original WhisperLive requirements)

## How to Run

1. Double click `start_all.bat`.
2. This will launch:
   - The backend Whisper transcription server
   - The desktop subtitle overlay
   - The client that listens to your audio and feeds it to the server
3. You can click and drag the subtitle bar anywhere on your screen. Use your **scroll wheel** to make the text larger or smaller. Right-click to close the overlay.

---

*Note: This project is a heavily modified, low-latency overlay fork of the original [WhisperLive](https://github.com/collabora/WhisperLive) project by Collabora.*
