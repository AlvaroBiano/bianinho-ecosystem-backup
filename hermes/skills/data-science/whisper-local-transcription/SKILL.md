---
name: whisper-local-transcription
description: Transcribe audio files locally using faster-whisper (100% offline, free, high quality)
---

# Whisper Local Transcription - Setup & Usage

Transcribe audio files (Telegram voice messages, etc.) using faster-whisper 100% locally and free.

## Status: READY TO USE

Model: `medium` (already downloaded and cached)
Python: 3.12 (system Python at `/usr/bin/python3`)
Location: `/home/alvarobiano/transcribe_audio.py`

## Installation (if needed)

```bash
# Install in user space (Python 3.12)
pip3 install --break-system-packages faster-whisper

# Verify (use system Python, NOT the one at ~/.local/bin)
export PYTHONPATH=""
/usr/bin/python3 -c "from faster_whisper import WhisperModel; print('OK')"
```

## IMPORTANT: Python Version Conflict

**The server has two Python versions:**
- `/home/alvarobiano/.local/bin/python3` → Python 3.14 (BROKEN for faster-whisper)
- `/usr/bin/python3` → Python 3.12 (WORKS)

**The script auto-switches to the correct Python version.** Just run:

```bash
/home/alvarobiano/transcribe_audio.py <audio_file>
```

## Usage

When user sends audio via Telegram, the audio is saved to a temp file. Run:

```bash
/usr/bin/python3 /home/alvarobiano/transcribe_audio.py <path_to_audio>
```

## Verification (100% Offline)

```python
from faster_whisper import WhisperModel
model = WhisperModel('medium', device='cpu', compute_type='int8')
segments, info = model.transcribe("audio.ogg", language="pt")
```

- No internet required after model download
- No API keys or external services
- All processing local

## Files

- Script: `/home/alvarobiano/transcribe_audio.py`
- Model cache: `~/.cache/huggingface/hub/`
