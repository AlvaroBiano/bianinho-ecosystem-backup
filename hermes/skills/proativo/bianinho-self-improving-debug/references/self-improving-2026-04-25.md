# Bianinho Self-Improving Debug Notes

## Error: `AttributeError: 'str' object has no attribute 'get'` in Phase 4

**Root cause:** `meta_cognition_journal.jsonl` was corrupted by a prior session that wrote a JSON object as `json.dumps(dict)` but one key-value pair per line (pretty-print style) instead of one `json.dumps()` call per line. The reader iterates lines and calls `json.loads(line)` which parses each fragment as a raw string `str` — not a `dict`.

**Fixes applied:**
1. `~/.hermes/scripts/bianinho_self_improving.py` line 360: Added `isinstance(e, dict)` guard in ratings list comprehension
2. Same file, lines 364-366: Added `if not isinstance(e, dict): continue` guard in today_entries loop
3. `~/.hermes/meta_cognition_journal.jsonl` backed up to `~/.hermes/meta_cognition_journal.jsonl.bak_20260425_0000`
4. Journal remains corrupted — the reader now guards against it; a future run should archive and reset it properly

## Error: `other(41x)` = MiniMax TTS code 2056 misclassified

**Root cause:** `classify_error_line()` in `bianinho_self_improving.py` checks for "rate limit", "usage limit", "429", "insufficient" but NOT "2056" — the MiniMax-specific quota error code. All 41 "other" errors were `MiniMax TTS API error (code 2056): usage limit exceeded`.

**Fixes applied:**
1. `bianinho_self_improving.py` line 269: Added `"2056" in s` to the rate_limit check
2. `hermes-agent/tools/tts_tool.py` line 50: Added `from tools.tts_cooldown_guard import on_tts_failure` (with try/except safe fallback)
3. `tts_tool.py` line 540: Added `on_tts_failure()` call before the `RuntimeError` raise on MiniMax status_code != 0 — this activates the cooldown guard so after 3 failures in 1 hour, no more TTS attempts are made for 30 minutes
4. `tts_cooldown.json` state file doesn't exist yet — cooldown will activate on the 3rd MiniMax failure

## Remaining issues
- Journal is still corrupted (one entry per line instead of one entry per line) — needs a full rewrite/reset
- `rate_limit(40x)` + `other(41x)` are the same underlying problem: MiniMax TTS quota exhausted, no cooldown enforcement until these fixes
- After these fixes, next run's error classification should show ~81 rate_limit and ~0 other
