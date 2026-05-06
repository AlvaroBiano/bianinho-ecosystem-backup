---
name: bianinho-python314-compatibility
version: 1.0.0
description: Python 3.14 compatibility issues and fixes for Bianinho OS scripts — specifically the os.argv AttributeError bug.
category: devops
tags:
  - python
  - compatibility
  - python3.14
  - bug
  - scripts
tools:
  - python3
  - terminal
---

# Python 3.14 Compatibility — Bianinho OS

## Critical Bug: `os.argv` Missing

**Environment:** Python 3.14.4 on this server (`~/.local/bin/python3`)

**Symptom:**
```
AttributeError: module 'os' has no attribute 'argv'
```

**Root Cause:** In Python 3.14, `os.argv` was removed. Scripts that use `os.argv` fail at runtime.

**Affected code pattern:**
```python
import os
workspace = Path(os.argv[1]) if len(os.argv) > 1 else Path.home() / ".hermes"
```

**Fix:** Always use `sys.argv` instead:
```python
import sys
workspace = Path(sys.argv[1]) if len(sys.argv) > 1 else Path.home() / ".hermes"
```

## Verification

```bash
python3 -c "import os; print(hasattr(os, 'argv'))"
# Returns: False

python3 -c "import sys; print(sys.argv)"
# Returns: ['-c'] (works fine)
```

## Rule

**ALL scripts in `~/.hermes/scripts/` must use `sys.argv`, NEVER `os.argv`.**

When creating new scripts, use this template:

```python
#!/usr/bin/env python3
import sys
import json
from pathlib import Path
# ... other imports

def main():
    workspace = Path(sys.argv[1]) if len(sys.argv) > 1 else Path.home() / ".hermes"
    # ...

if __name__ == "__main__":
    main()
```

## Scripts Affected (fixed)

- `~/.hermes/scripts/learning_loop/init.py` — FIXED
- `~/.hermes/scripts/learning_loop/extract.py` — FIXED
- `~/.hermes/scripts/learning_loop/promote_rules.py` — FIXED
- `~/.hermes/scripts/learning_loop/confidence_decay.py` — was already using sys.argv
- `~/.hermes/scripts/learning_loop/inject_rules.py` — was already using sys.argv
- `~/.hermes/scripts/learning_loop/update_metrics.py` — was already using sys.argv
- `~/.hermes/scripts/learning_loop/self_audit.py` — FIXED (26/04/2026 cron job)
- `~/.hermes/scripts/learning_loop/event_types.py` — was already using sys.argv

## Discovery Context

Found on 2026-04-21 during the OpenClaw skills adaptation session.
When running `init.py`, the error was `AttributeError: module 'os' has no attribute 'argv'`
despite the file clearly having `import os` at the top.

Diagnosis: `which python3` showed Python 3.14.4 at `~/.local/bin/python3`.
Python 3.14 removed `os.argv` as part of cleanup — it was deprecated since Python 3.9.

## pip install Goes to Wrong Python — Session 30/04/2026

**Symptom:** Installed `flask`, `pillow`, `websockify` but `python3 -c "import flask"` → ModuleNotFoundError.

**Root Cause:** `python3 --version` → 3.14.4. `pip install --break-system-packages` installs to Python 3.14 site-packages. But the skill system runs scripts in a sandbox that may use a different Python interpreter.

**Diagnosis:**
```bash
python3 --version          # which python3
python3 -c "import flask"  # test if installed
pip3 show flask           # where it was installed
```

**Fix:** Always test after install:
```bash
python3 -c "from flask import Flask; print('OK')"
```

**Xlib was installed in Python 3.12 but script ran with 3.14:**
- python3-xlib installed to: `/home/alvarobiano/.local/lib/python3.12/site-packages/`
- Script ran with: Python 3.14.4 (`~/.local/bin/python3`)
- Solution: `~/.local/share/uv/python/cpython-3.14.4-linux-x86_64-gnu/bin/pip install --break-system-packages python3-xlib`

**Pattern:** When a module installs but import fails — check `pip show <module>` Location vs `python3 --version`.

## Other Python 3.14 Considerations

- `sys.path` may be empty in some invocation modes — always be explicit
- `__pycache__` may be created even when using `-B` flag initially, then persist
- Use `python3 -B script.py` to prevent `.pyc` creation if needed

## Related Files

- Python binary: `/home/alvarobiano/.local/bin/python3` → Python 3.14.4
- venv: `~/.hermes/hermes-agent/venv/bin/python` → Python 3.11 (has `os.argv`)
- The hermes-agent venv Python 3.11 is stable; user scripts use system Python 3.14
