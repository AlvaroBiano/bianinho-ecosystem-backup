---
name: knowledgebase-self-monitor-debug
description: Debug format mismatch between SelfMonitor (saves lists) and SessionReflection (expects dicts) in the KnowledgeBase pipeline
triggers:
  - "session_reflection.py error"
  - "KeyError errors_total"
  - "SelfMonitor KeyError"
  - "breakthroughs dict expected"
---

# KnowledgeBase SelfMonitor Pipeline — Debug & Fix

## Trigger Condition
When running `~/KnowledgeBase/venv/bin/python session_reflection.py <session_id>` and getting `KeyError` or `AttributeError`, or when the reflection report has missing/unexpected fields.

## The Problem
`SelfMonitor` (in `self_monitor.py`) saves session data with `errors` and `breakthroughs` as **lists** of raw dicts:
```python
# Saved format (sessions/{id}.json):
"errors": [{"description": "...", "resolved": true, ...}, ...]
"breakthroughs": [{"description": "...", "impact": "alto", ...}, ...]
```

But `SessionReflection` (in `session_reflection.py`) originally expected them as **structured dicts**:
```python
# Expected format:
"errors": {"total": N, "resolved": N, "unresolved": [], "recurring": []}
"breakthroughs": {"total": N, "high_impact": [...]}
```

## Debugging Steps

### 1. Find correct method signatures
```python
import inspect
from session_reflection import SessionReflection
sr = SessionReflection()
print(inspect.signature(sr.generate))  # → (session_id: str | None = None)
```

### 2. Check what SessionReflection._load_session expects
It loads from `sessions/{session_id}.json` — NOT from the reflection file.

### 3. Verify actual saved format
```python
import json
from pathlib import Path
files = sorted(Path('sessions').glob('*.json'))
with open(files[-1]) as f:
    data = json.load(f)
# Inspect data['errors'] and data['breakthroughs'] types
```

## The Fix Pattern
In `session_reflection.py`, add `isinstance()` checks for `errors` and `breakthroughs` in every method that accesses them:

```python
errors = session.get("errors", {})
if isinstance(errors, dict):
    errors_total = errors.get("total", 0)
    errors_resolved = errors.get("resolved", 0)
    unresolved = errors.get("unresolved", [])
else:
    # raw list format from SelfMonitor._save_metrics
    errors_total = session.get("errors_total", 0)
    errors_resolved = session.get("errors_resolved", 0)
    unresolved = [e.get("description", "") for e in errors if not e.get("resolved", False)]

breakthroughs = session.get("breakthroughs", {})
if isinstance(breakthroughs, dict):
    bt_total = breakthroughs.get("total", 0)
    high_impact = breakthroughs.get("high_impact", [])
else:
    # raw list format
    bt_total = len(breakthroughs) if isinstance(breakthroughs, list) else 0
    high_impact = [b.get("description", "") for b in breakthroughs 
                   if b.get("impact") == "alto"] if isinstance(breakthroughs, list) else []
```

### Methods that needed patching (session_reflection.py):
- `_analyze_session()` — initial field extraction
- `_summarize_highlights()` — errors/high_impact display
- `_identify_improvements()` — unresolved errors list
- `_extract_lessons()` — iterating unresolved errors and breakthroughs
- `_detect_cross_session_themes()` — recurring error keywords
- `_compute_evolution_score()` — error resolution bonus, breakthrough bonus
- `_should_auto_improve()` — unresolved count check
- `_build_executive_summary()` — errors_total count

## Key Files
- `/home/alvarobiano/KnowledgeBase/self_monitor.py` — tracker, saves to `sessions/`
- `/home/alvarobiano/KnowledgeBase/session_reflection.py` — reads from `sessions/`, generates reports
- `/home/alvarobiano/KnowledgeBase/sessions/` — raw session JSON files
- `/home/alvarobiano/KnowledgeBase/reflections/` — generated reflection JSON files

## Verification
```bash
cd ~/KnowledgeBase && ~/KnowledgeBase/venv/bin/python -c "
from self_monitor import SelfMonitor
sm = SelfMonitor(session_id='test-verify')
sm.track_error(description='Test error', resolved=True)
sm.track_breakthrough(description='Test breakthrough', impact='alto')
reflection = sm.end_session()

from session_reflection import SessionReflection
sr = SessionReflection()
report = sr.generate('test-verify')
print('Score:', report['evolution_score'])
print('OK')
"
```
