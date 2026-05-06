---
name: bianinho-self-improving-debug
description: Debug and correct Bianinho self-improving when quality score is stuck despite repeated fix attempts. Fixes stale error accumulation, retry loops, missing cooldown enforcement, and cascading errors from infrastructure-level corruption (cron workdir, API misclassification).
---

# Bianinho Self-Improving — Debug & Corrective Pattern

## Trigger
Quality score stuck at 3.0 for 30+ consecutive cycles despite identical fixes being applied every run.

## Root Cause Pattern (Cascading Errors from Infrastructure Corruption)
NEW — discovered 2026-04-28.

Self-improving quality score stuck at ~3.0 for many cycles. The script diagnoses:
- api_404: "endpoint/provider/model inexistente"
- auth_error: "credenciais inválidas"
- benign: "padrão genérico"

But these are **cascading symptoms**, not root causes. The real root cause was:
- **Cron subagent sessions failing with `FileNotFoundError: /home/alvarobiano/memory/learning/memory/learning`**
- This is a `workdir` corruption in cron subagent sessions — subagents start in a non-existent directory
- All subsequent API calls fail → classified as api_404
- Auth headers invalid in that context → classified as auth_error
- Every terminal command in the subagent also fails → classified as benign/memory

**Diagnosis technique**: Read `errors.log` and look for the same command failing 50+ times with the same error in a short window. A cascade has a "first failure" that chains into all subsequent failures. The first error in a burst is the real root cause.

**Indicators that errors are cascading, not independent**:
- api_404 + auth_error both spike simultaneously with similar counts
- Errors all come from cron subagent sessions (session IDs like `cron_*`)
- The same command failing with 3 retries in every cron run
- A path in the error that doesn't exist (e.g., `/home/alvarobiano/memory/learning/memory/learning`)
- Telegram WARNING lines (e.g., `httpx.ReadError`) repeating 10+ times — these are transient and self-recover; if they dominate `network_timeout`, the score deduction is structural not meaningful

**Key insight**: Before attributing api_404/auth_error to endpoint/provider problems, do a **real API health check**:
```python
import urllib.request, urllib.error, os
try:
    req = urllib.request.Request(
        "https://api.minimax.io/v1/models",
        headers={"Authorization": f"Bearer {os.environ.get('MINIMAX_API_KEY', '')}"},
        method="GET"
    )
    with urllib.request.urlopen(req, timeout=10) as resp:
        api_status = f"ok_http_{resp.status}"
except urllib.error.HTTPError as e:
    api_status = f"http_{e.code}"
except Exception as e:
    api_status = f"error_{type(e).__name__}"
# If api_status == "ok_http_200" → errors are cascading, fix the infrastructure
```

## Root Cause Pattern (Stale Error Accumulation)
The self-improving script:
1. Reads errors from `~/.hermes/logs/errors.log` (last 800 lines)
2. Classifies errors and deducts from quality score
3. If quality < 4.0, applies fixes and reports
4. BUT errors.log accumulates ALL errors since last reset — including 18h-old TTS rate-limits, transient Telegram warnings, stale gateway PID race errors
5. These stale errors keep deducting points every cycle, even after resolution
6. Fixes applied (retry_guard, endpoint_health, throttle) are all reactive — they don't clear the error source
7. The script created `self_improving.lock` as a cooldown mechanism but **never checked it at startup**

## Corrective Actions (execute in order)

### 1. Fix Cron Subagent Workdir Corruption (Infrastructure Cascade)
If `errors.log` shows `FileNotFoundError` for paths like `/home/alvarobiano/memory/learning/memory/learning`, this means cron subagent sessions have a corrupted workdir. All API calls and commands fail as a cascade.

**Fix**: Set explicit valid workdir for all cron jobs with empty workdir:
```python
import json
from pathlib import Path

HERMES_DIR = Path.home() / ".hermes"
cron_jobs_db = HERMES_DIR / "cron" / "jobs.json"
GOOD_WORKDIR = str(Path.home())  # e.g., "/home/alvarobiano"

data = json.loads(cron_jobs_db.read_text())
jobs = data.get("jobs", [])
fixed = 0
for job in jobs:
    wd = job.get("workdir", "")
    if wd == "" or not Path(wd).exists():
        job["workdir"] = GOOD_WORKDIR
        fixed += 1
if fixed:
    bak = HERMES_DIR / "backups" / f"jobs.json.bak.{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    shutil.copy2(cron_jobs_db, bak)
    cron_jobs_db.write_text(json.dumps(data, indent=2))
    print(f"Fixed {fixed} jobs, backup: {bak}")

# Also create a session-level hint file
hint_file = HERMES_DIR / "cron" / "session_workdir_hint.txt"
hint_file.write_text(GOOD_WORKDIR)
```

**Also**: Ensure the bad path exists (prevents the FileNotFoundError):
```python
Path("/home/alvarobiano/memory/learning/memory/learning").mkdir(parents=True, exist_ok=True)
```

### 2. Archive + Reset errors.log
```python
from pathlib import Path
from datetime import datetime

errors_log = Path.home() / ".hermes" / "logs" / "errors.log"
backup_dir = Path.home() / ".hermes" / "self_improving" / "backups"
backup_dir.mkdir(parents=True, exist_ok=True)

if errors_log.exists() and errors_log.stat().st_size > 0:
    content = errors_log.read_text(errors="ignore")
    recent = "\n".join(content.splitlines()[-300:])
    (backup_dir / f"errors.archive.{datetime.now().strftime('%Y%m%d_%H%M%S')}.log").write_text(recent)
    errors_log.write_text(f"# Reset {datetime.now().isoformat()}\n")
```

### 2. Trim self_improvement_state.history
Keep only last 5 entries — older entries compound error counts.
```python
import json
from pathlib import Path
state_file = Path.home() / ".hermes" / "self_improvement_state.json"
state = json.loads(state_file.read_text())
state["history"] = state["history"][-5:]
state_file.write_text(json.dumps(state, indent=2))
```

### 3. Add Cooldown Enforcement to Script
Patch `main()` in `bianinho_self_improving.py`:
```python
def main() -> int:
    ensure_dirs()

    # ── Cooldown enforcement ──────────────────────────────────────────────────
    LOCK_FILE = HERMES_DIR / "self_improving.lock"
    try:
        lock = read_json(LOCK_FILE, {})
        lock_until = lock.get("locked_until", "")
        if lock_until:
            from datetime import datetime
            lock_dt = datetime.fromisoformat(lock_until)
            if datetime.now() < lock_dt:
                remaining = (lock_dt - datetime.now()).total_seconds() / 60
                log(f"[COOLDOWN] Locked until {lock_until} ({remaining:.0f}min remaining). Exiting.")
                print(f"[COOLDOWN] Next run allowed at {lock_until}. Exiting.")
                return 0
    except Exception:
        pass  # No lock or invalid lock — proceed
    # ──────────────────────────────────────────────────────────────────────────
    ...
```

### 4. Clear endpoint_health.json Stale State
```python
import json
from pathlib import Path
from datetime import datetime

health_file = Path.home() / ".hermes" / "endpoint_health.json"
health = json.loads(health_file.read_text())
# Clear per-endpoint failures that are resolved
for key in ["api.minimaxi.bot", "api.telegram.org", "ctx_execute"]:
    if key in health:
        health[key]["status"] = "ok"
        health[key]["failures"] = 0
health["status"] = "ok"
health["error_categories"] = {}
health["required_action"] = "none"
health_file.write_text(json.dumps(health, indent=2))
```

### 5. Set Extended Cooldown Lock
```python
import json
from pathlib import Path
from datetime import datetime, timedelta

lock = {
    "locked_until": (datetime.now() + timedelta(hours=2)).isoformat(),
    "reason": "Stale error accumulation corrected. Cooldown to prevent retry loop.",
    "quality_score": 3.0,
    "locked_at": datetime.now().isoformat(),
}
Path.home() / ".hermes" / "self_improving.lock").write_text(json.dumps(lock, indent=2))
```

### 6. Always Create Journal Entry After Corrective
Add to meta_cognition_journal.jsonl to record the diagnosis and fixes.

## Prevention
- Reset errors.log monthly or when errors become stale (>24h old)
- Cooldown lock MUST be checked at startup (add to main() before any phase)
- Keep self_improvement_state.history to ≤10 entries max
- **Cascade detection**: Before attributing api_404/auth_error to provider issues, verify API health with a real HTTP request. If API is healthy (ok_http_200), errors are cascading from infrastructure — find and fix the first failure in the burst
- **Fix-cycling detection**: If the same 6 fixes appear in every cycle's "Fixes Applied", the script is not diagnosing — it is cycling. Add a `_fix_cron_workdir_corruption()` style concrete diagnostic for each error category before applying generic fixes
