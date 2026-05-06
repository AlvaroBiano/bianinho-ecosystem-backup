---
name: whisper-local-transcription
description: Transcribe audio and video files locally using faster-whisper (100% offline, free, high quality). Optimized for Portuguese (pt) on MacBook.
---

# Whisper Local Transcription

Transcribe audio (Telegram voice messages) and video files (MP4) using faster-whisper 100% locally and free.

## Quick Use (MacBook)

```bash
PYTHONPATH="" ~/.hermes/venv/bin/python -c "
from faster_whisper import WhisperModel
model = WhisperModel('medium', device='cpu', compute_type='int8')
segments, info = model.transcribe('/path/to/file.mp4', language='pt', beam_size=1, vad_filter=True)
for s in segments:
    print(f'[{s.start:.1f}s - {s.end:.1f}s] {s.text}')
"
```

**User style: respostas curtas, sem explicações desnecessárias. Output: "✅ Pronto" + preview, não "a processar...".**

## Optimal Configuration

| Context | Model | compute_type | beam_size | Notes |
|---------|-------|-------------|-----------|-------|
| **Speed + confiabilidade** | `small` | `int8` | `1` | 0.10xRT, funciona bem em todos os tamanhos |
| **Equilíbrio** | `medium` | `int8` | `1` | 0.24xRT, excelente para <15min |
| **Qualidade máxima** | `medium` | `int8` | `5` | ~0.40xRT, para curtas |

## ⚠️ CRITICAL: medium EM VÍDEOS LONGOS (>20 min) — USA `small`

Testado: `medium` + CPU fica **bloqueado >20min** em vídeos de 30min (Aula 5 M2).
`small` completa no tempo esperado. **Regra: para >20min usa sempre `small`.**

Benchmarks completos: `references/transcription-benchmarks.md`

**For Portuguese (pt):** beam_size=1 produces near-identical quality to beam=5. Use beam=1 for speed.

## MacBook Python

- **Python:** `~/.hermes/venv/bin/python` (Python 3.14, venv do Hermes)
- **Sempre usar:** `PYTHONPATH=""` para evitar conflicts
- **Modelo cache:** `~/.cache/huggingface/hub/models--Systran--faster-whisper-large-v3/` e `models--distil-whisper--distil-medium.pt/`

## Linux Server (100.79.189.95)

```bash
/usr/bin/python3 /home/alvarobiano/transcribe_audio.py <audio_file>
```

Server: `/usr/bin/python3` (Python 3.12). Script auto-switches from broken Python 3.14 at `~/.local/bin/python3`.

## VAD Filter

Always use `vad_filter=True` — removes silence and noise, produces cleaner text.

## ⚠️ CRITICAL: Long Videos (>20 min) — Extract Audio First

Direct video transcription hangs on long files. **Always extract audio to WAV first:**

```bash
ffmpeg -i "/path/to/video.mp4" \
  -vn -acodec pcm_s16le -ar 16000 -ac 1 -y \
  "/tmp/audio.wav"
```

Then transcribe the WAV:
```python
model.transcribe('/tmp/audio.wav', language='pt', beam_size=1, vad_filter=True)
```

This avoids a hang bug in faster-whisper's video pipeline on Mac Python 3.14.

## Output Format

```python
transcript = []
for seg in segments:
    transcript.append(f'[{seg.start:.1f}s - {seg.end:.1f}s] {seg.text}')
text = '\n'.join(transcript)
# Save to .txt file alongside the source
```

## Background Execution

For long videos (>5 min), **write script to file first then run in background** — more reliable than inline Python:

```python
# Write script to file
with open('/tmp/transcribe.py', 'w') as f:
    f.write(script_content)

# Run via background terminal
terminal(background=true, notify_on_complete=true,
         command='PYTHONPATH="" ~/.hermes/venv/bin/python /tmp/transcribe.py')
```

Then poll periodically. Do NOT use `setsid` — use `background=true`.

## Quick Duration Check

```bash
ffprobe -v quiet -show_entries format=duration -of csv=p=0 /path/to/video.mp4
```

## Benchmarks (MacBook, video 90s, CPU)

See: `references/transcription-benchmarks.md`
