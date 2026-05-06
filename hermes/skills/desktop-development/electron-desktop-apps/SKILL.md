---
name: electron-desktop-apps
description: Build, run, and extend Electron desktop applications on Linux — source builds, native module fixes, headless Xvfb, and protocol integration with AI agent platforms (aionrs, ACP).
version: 1.0.0
author: Bianinho
metadata:
  tags: [electron, desktop, linux, headless, xvfb, native-modules, aionui]
---

# Electron Desktop Apps on Linux

How to build Electron apps from source on Linux, run them headless (Xvfb), fix native module incompatibilities, and integrate them with AI agent platforms via custom protocols.

## When to Use This Skill

- Building an Electron app that has no official Linux binary
- Running a desktop GUI app on a headless Linux server
- Fixing native module (better-sqlite3, etc.) crashes after build
- Integrating an Electron app (like AionUI) with Hermes Agent or other agent platforms
- Any task involving electron-builder, electron-rebuild, or Xvfb on Linux

## Source Build from GitHub

Most Electron apps with a `electron-vite` + `electron-builder` stack can be built on Linux:

```bash
# Clone with depth=1 (full repo can be 2GB+)
git clone --depth 1 https://github.com/USER/REPO.git /tmp/electron-app
cd /tmp/electron-app

# Install dependencies (use npmmirror for speed if behind Great Firewall)
npm install

# Build renderer (if electron-vite)
npx electron-vite build

# Package as unpacked directory (not .dmg/.AppImage)
npx electron-builder --dir
```

Output lands in `out/` or `dist/`. The unpacked app is at `out/linux-unpacked/`.

**Important:** Some apps (like AionUI) do NOT publish Linux binaries — building from source is the only option on Linux.

## ELECTRON_MIRROR for Fast Downloads

Electron binaries are large (~130MB for Electron 37). Use a mirror:

```bash
export ELECTRON_MIRROR="https://npmmirror.com/mirrors/electron/"
npm install
```

## Xvfb: Running Electron Headless on Linux

Electron requires a display. Xvfb (virtual framebuffer) provides one without a physical screen.

### Setup

```bash
# Install
sudo apt install xvfb

# Basic run
Xvfb :99 -screen 0 1920x1080x24 &
export DISPLAY=:99
./AionUi  # or electron, etc.
```

### Robust Launcher Script

```bash
#!/bin/bash
# aionui-start.sh — robust Xvfb launcher with PID management

PIDFILE="/tmp/aionui-xvfb.pid"
DISPLAY_NUM=99

start() {
  if [ -f "$PIDFILE" ] && kill -0 $(cat "$PIDFILE") 2>/dev/null; then
    echo "AionUI already running (PID $(cat $PIDFILE))"
    return
  fi
  echo "Starting Xvfb :$DISPLAY_NUM..."
  Xvfb :$DISPLAY_NUM -screen 0 1920x1080x24 &>/tmp/xvfb.log &
  echo $! > "$PIDFILE"
  export DISPLAY=:$DISPLAY_NUM
  sleep 1
  echo "Xvfb running (PID $(cat $PIDFILE))"
}

stop() {
  if [ -f "$PIDFILE" ]; then
    kill $(cat "$PIDFILE") 2>/dev/null && rm "$PIDFILE"
    echo "Xvfb stopped"
  fi
}

case "$1" in
  start) start ;;
  stop)  stop ;;
  *)     echo "Usage: $0 {start|stop}" ;;
esac
```

### Testing with Logs

```bash
export DISPLAY=:99
./AionUi &>/tmp/aionui.log &
sleep 5
cat /tmp/aionui.log | head -50
```

## Native Module Incompatibility (Critical)

### The Problem

Electron bundles its own Node.js version (e.g., Electron 37 uses Node 22.21.1). `npm install` on Linux typically uses the system Node (e.g., nvm Node 24.14.1). Native modules (better-sqlite3, sqlite3, bcrypt, etc.) are compiled for the wrong Node version. The app crashes on startup with:

```
Error: The module '/path/to/node_modules/better-sqlite3/build/Release/better_sqlite3.node'
was compiled for Node.js 24.x but this is Node.js 22.x — upgrade or rebuild
```

### Fix: electron-rebuild

```bash
# Install electron-rebuild globally
npm install -g @electron/rebuild

# Rebuild native modules for Electron's Node version
npx electron-rebuild

# If the app uses electron-builder with asar:
# 1. Build unpacked first
npx electron-builder --dir
# 2. Copy rebuilt module to the unpacked app's asar.unpacked dir
cp -r node_modules/better-sqlite3/build/Release/better_sqlite3.node \
      out/linux-unpacked/resources/app.asar.unpacked/node_modules/better-sqlite3/build/Release/
```

### Identifying Which Module is Broken

Run the app and check the error traceback — it names the specific `.node` file that fails.

### When electron-rebuild Alone Is Not Enough

In some cases (old native modules, complex native deps), you need to force a full rebuild:
```bash
rm -rf node_modules/better-sqlite3/build
npm rebuild better-sqlite3 --runtime=electron --dist-url=https://electronjs.org/headers
```

## Protocol Integration: Electron App ↔ AI Agent

### AionUI aionrs Protocol

AionUI (and apps built on the AionUI platform) communicate with agent CLIs via the **aionrs JSON Stream Protocol** over stdio. Each line is a JSON event.

**Event directions:**
- App → Agent: `ready`, `message`, `ping`
- Agent → App: `ready`, `message`, `message_end`, `stream_start`, `text_delta`, `stream_end`, `error`, `pong`

**Example `ready` (Agent → App):**
```json
{"type":"ready","agentId":"hermes","agentName":"Hermes Agent"}
```

**Example `message` (App → Agent):**
```json
{"type":"message","message":{"role":"user","content":"Hello"}}
```

**Example `stream_start` + `text_delta` (Agent → App):**
```json
{"type":"stream_start","messageId":"msg_abc123"}
{"type":"text_delta","messageId":"msg_abc123","delta":"Olá!"}
{"type":"stream_end","messageId":"msg_abc123"}
```

### Writing a Protocol Bridge

A bridge translates between two protocols. Example: AionUI aionrs ↔ Hermes JSON-RPC.

Core pattern (Python):
```python
import subprocess, json, sys

# Start Hermes via subprocess using venv Python
HERMES_PY = "/path/to/.hermes/hermes-agent/venv/bin/python"
RUN_AGENT = "/path/to/.hermes/hermes-agent/run_agent.py"

proc = subprocess.Popen(
    [HERMES_PY, RUN_AGENT],
    stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    text=False
)

# Read aionrs events from stdin, translate, send to Hermes, translate back
for line in sys.stdin:
    event = json.loads(line.strip())
    if event["type"] == "message":
        hermes_req = translate_to_hermes(event)
        proc.stdin.write(json.dumps(hermes_req).encode() + b"\n")
        proc.stdin.flush()
        # Read Hermes streaming response, translate to aionrs, write to stdout
```

Full working example: `scripts/aionrs-bridge/aionrs_bridge.py` in `~/repos/aionui-hermes-ten/`.

## App-Specific Notes

### AionUI

- **Repo:** https://github.com/iOfficeAI/AionUi (23k+ stars)
- **Version tested:** v1.9.23 (Electron 37.10.3, Chromium 138)
- **Stack:** TypeScript 89.9%, Electron Vite, UnoCSS, Tailwind
- **Source size:** ~2.6GB (shallow clone)
- **ACP detection:** AionUI auto-detects agents in PATH matching `POTENTIAL_ACP_CLIS` — includes `hermes`
- **Team Mode:** Supports multi-agent teams with role assignment, shared context
- **Installed location (server):** `/home/alvarobiano/repos/aionui/AionUi`
- **MCP Server:** `TeamGuideMcpServer` runs on TCP port 36245 when AionUI starts

## Key Paths (Server)

| Component | Path |
|-----------|------|
| AionUI binary | `/home/alvarobiano/repos/aionui/AionUi` |
| AionUI source | `/tmp/aionui-build/` (temporary, ~2.6GB) |
| Xvfb PID file | `/tmp/aionui-xvfb.pid` |
| AionUI logs | `/tmp/aionui.log` |
| Xvfb logs | `/tmp/xvfb.log` |
| Hermes venv Python | `/home/alvarobiano/.hermes/hermes-agent/venv/bin/python` |

## Pitfalls

1. **Don't clone the full repo** — use `--depth 1`. Full AionUI repo is ~2.6GB.
2. ** ELECTRON_MIRROR is mandatory** on slow connections — Electron downloads are ~130MB each.
3. **Native modules break after `npm install`** — always run `electron-rebuild` AND copy to `app.asar.unpacked` if using asar.
4. **Xvfb display must be set** — `export DISPLAY=:99` before launching the app. Not setting this = silent crash.
5. **PID management** — always use a PID file for Xvfb so you can stop it cleanly and avoid orphan processes.
6. **Direct AIAgent import fails** — never use `from run_agent import AIAgent` from an external Python script. Use subprocess with the venv Python binary.
