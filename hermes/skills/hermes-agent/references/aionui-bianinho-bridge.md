# AionUI + BianinhoBridge Architecture

## Overview

When Hermes (Bianinho) runs inside AionUI on macOS, AionUI communicates via **two separate mechanisms on the same port (18743)**:

1. **HTTP bridge** (`bianinho_bridge_server.py`) — health checks and discovery
2. **TCP bridge** (`bianinho_bridge.py`) — actual message communication

Both must be running simultaneously for Hermes to appear in AionUI's agent selector.

## How AionUI Detects Hermes

AionUI polls `http://localhost:18743/check_hermes` (HTTP GET) every few seconds. The response must include:

```json
{
  "ok": true,
  "checks": {
    "hermes_path": "/Users/alvarobiano/.hermes",
    "hermes_exists": true,
    "skills_exists": true,
    "rag_exists": true,
    "inbox_writable": true
  }
}
```

If this endpoint returns 200 with `ok: true`, Hermes appears in the agent selector. If the HTTP bridge is down or returns an error, Hermes disappears from the selector.

## Required Processes

Both bridges must be started (order doesn't matter):

```bash
# Terminal 1: HTTP bridge (health checks)
~/.hermes/venv/bin/python3 ~/.hermes/scripts/bianinho_bridge_server.py &

# Terminal 2: TCP bridge (messages)
cd ~/Library/ApplicationSupport/AionUI/bianinho/
~/.hermes/venv/bin/python3 bianinho_bridge.py &

# Verify
curl http://localhost:18743/check_hermes
```

## Bridge Scripts Location

| Bridge | Path |
|--------|------|
| HTTP (health) | `~/.hermes/scripts/bianinho_bridge_server.py` |
| TCP (messages) | `~/Library/ApplicationSupport/AionUI/bianinho/bianinho_bridge.py` |

## Logs

- HTTP bridge: `~/.hermes/logs/bianinho_http.log`
- TCP bridge: `~/.hermes/logs/bianinho_tcp.log`

## Troubleshooting: Hermes Disappeared from Agent Selector

If Hermes was showing but vanished:

1. Check if HTTP bridge is running:
   ```bash
   curl http://localhost:18743/check_hermes
   ```
   If it times out or errors → HTTP bridge is down.

2. Check if TCP bridge is running:
   ```bash
   lsof -i :18743
   ```
   Should show Python listening on port 18743.

3. If both are down (port 18743 is free):
   - Restart both bridges (see above)

4. If port is in use by another process:
   - Kill the stuck process: `lsof -ti :18743 | xargs kill`
   - Then restart both bridges

5. If AionUI still doesn't show Hermes after bridges are up:
   - Close AionUI completely (`Cmd+Q`)
   - Reopen AionUI

## Why Two Bridges?

- **HTTP bridge**: Serves the `/check_hermes` health endpoint that AionUI's frontend polls. This is what makes Hermes appear/disappear in the agent dropdown.
- **TCP bridge**: Handles the actual message protocol for conversations once Hermes is selected.

## Auto-start on Boot

Both bridges should be started automatically. Currently they must be started manually after a restart. A launchd plist or launch agent could automate this.
