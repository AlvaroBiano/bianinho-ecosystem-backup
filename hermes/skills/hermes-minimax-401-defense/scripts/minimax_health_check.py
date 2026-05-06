#!/usr/bin/env python3
"""
MiniMax API Key Health Check + Credential Pool Guardian
========================================================
Runs before gateway starts to validate the API key.
Runs every 15 minutes via cron to ensure the credential pool is clean.

Usage:
    python3 minimax_health_check.py          # Full check + pool guardian
    python3 minimax_health_check.py --check   # Check only, exit code only
    python3 minimax_health_check.py --guard  # Pool guardian only
"""
import sys
import json
import time
import subprocess
import requests
from pathlib import Path

HERMES_DIR = Path.home() / ".hermes"
AUTH_FILE = HERMES_DIR / "auth.json"
ENV_FILE = HERMES_DIR / ".env"
LOG_FILE = HERMES_DIR / "logs" / "minimax_health.log"


def get_minimax_key() -> str | None:
    """Get MINIMAX_API_KEY from .env file (not os.environ, not masked)."""
    try:
        with open(ENV_FILE, 'rb') as f:
            content = f.read()
        idx = content.find(b'MINIMAX_API_KEY=')
        if idx == -1:
            return None
        end = content.find(b'\n', idx)
        line = content[idx:end].rstrip(b'\r\n')
        parts = line.split(b'=', 1)
        if len(parts) == 2:
            return parts[1].decode('utf-8', errors='replace')
    except Exception:
        pass
    return None


def check_api_key(key: str) -> tuple[bool, str]:
    """Test the MiniMax API key with a simple chat completion."""
    if not key or len(key) < 10:
        return False, "Key is empty or too short"
    if key == '***':
        return False, "Key is still placeholder *** in .env"

    url = "https://api.minimax.io/v1/chat/completions"
    headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
    payload = {"model": "MiniMax-M2.7", "messages": [{"role": "user", "content": "Hi"}], "max_tokens": 5}

    try:
        resp = requests.post(url, headers=headers, json=payload, timeout=15)
        if resp.status_code == 200:
            return True, "Key is valid"
        elif resp.status_code == 401:
            try:
                err = resp.json()
                msg = err.get('error', {}).get('message', 'Unknown 401 error')
            except Exception:
                msg = resp.text[:100]
            return False, f"401 Unauthorized: {msg}"
        else:
            return False, f"HTTP {resp.status_code}"
    except requests.exceptions.Timeout:
        return False, "Request timed out"
    except requests.exceptions.ConnectionError:
        return True, "Network unreachable (not key problem)"
    except Exception as e:
        return False, f"Error: {e}"


def enforce_credential_pool(key: str) -> bool:
    """Ensure only the valid MINIMAX_API_KEY entry exists in the pool."""
    try:
        with open(AUTH_FILE) as f:
            data = json.load(f)

        cp = data.get('credential_pool', {}).get('minimax', [])
        original_count = len(cp)

        # Keep only entries matching the env key
        cleaned = [e for e in cp if e.get('access_token') == key]

        if len(cleaned) != original_count:
            data['credential_pool']['minimax'] = cleaned
            with open(AUTH_FILE, 'w') as f:
                json.dump(data, f, indent=2)
            log(f"POOL GUARDIAN: Removed {original_count - len(cleaned)} bad entries")
            return True
        else:
            log(f"POOL GUARDIAN: Pool clean ({len(cleaned)} entries)")
            return False
    except Exception as e:
        log(f"POOL GUARDIAN ERROR: {e}")
        return False


def log(msg: str):
    ts = time.strftime("%Y-%m-%d %H:%M:%S")
    line = f"{ts} {msg}"
    try:
        LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(LOG_FILE, 'a') as f:
            f.write(line + "\n")
    except Exception:
        pass
    print(line)


def restart_gateway():
    try:
        subprocess.run(
            ["systemctl", "--user", "restart", "hermes-gateway"],
            timeout=30, capture_output=True,
        )
        log("Gateway restarted")
    except Exception as e:
        log(f"Restart failed: {e}")


def main():
    mode = "full"
    if "--guard" in sys.argv:
        mode = "guard_only"
    elif "--check" in sys.argv:
        mode = "check_only"

    key = get_minimax_key()
    if not key:
        log("ERROR: No MINIMAX_API_KEY in .env")
        sys.exit(1)

    # Always enforce pool guardian
    pool_changed = enforce_credential_pool(key)

    if mode == "guard_only":
        sys.exit(0)

    # Health check
    is_healthy, msg = check_api_key(key)
    log(f"API Health: {msg}")

    if not is_healthy:
        log("ACTION: Restarting gateway to trigger credential refresh...")
        restart_gateway()
        sys.exit(1)

    # If pool was cleaned, restart gateway to pick up changes
    if pool_changed:
        log("ACTION: Pool was cleaned, restarting gateway...")
        restart_gateway()

    sys.exit(0)


if __name__ == "__main__":
    main()
