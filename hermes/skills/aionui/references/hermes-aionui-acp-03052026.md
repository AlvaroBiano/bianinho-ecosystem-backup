# Hermes + AionUI ACP Connection — Setup 03/05/2026

## How it Works

AionUI spawns `hermes acp` as a subprocess. Communication is via stdin/stdout (JSON messages, NOT HTTP).

```
AionUI (Electron main process)
  └── spawns: hermes acp (stdin/stdout JSON)
```

NOT via BianinhoBridge HTTP. NOT via port 18743.

## Setup

### 1. Install hermes-agent as editable (makes acp_adapter discoverable)

```bash
cd ~/.hermes/hermes-agent
pip install -e '.[acp]'
```

Without this: `acp_adapter` module not found → AionUI shows "ACP dependencies not installed".

### 2. Hermes must be in PATH

AionUI's AcpDetector does `command -v hermes` to find it.

```bash
mkdir -p ~/.local/bin
ln -sf ~/.hermes/venv/bin/hermes ~/.local/bin/hermes
```

### 3. acp_adapter installed and working

```bash
hermes acp
# Should stay running, respond to {"type":"ping"}
```

## Verifying

```bash
# Check logs
grep "ACP\|acp_adapter" ~/Library/Logs/AionUi/$(date +%Y-%m-%d).log

# Good log lines:
[INFO] acp_adapter.entry: Loaded env from /Users/alvarobiano/.hermes/.env
[INFO] acp_adapter.server: ACP client connected
[INFO] acp_adapter.server: Initialize from AionUi (protocol v1)
[INFO] acp_adapter.session: Restored ACP session ... from DB (NN messages)
[INFO] acp_adapter.server: Session ...: mode switched to default

# Bad log (acp_adapter not found):
[ACP hermes STDERR]: ERROR: ModuleNotFoundError: No module named 'acp_adapter'
```

## Key Files

| File | Purpose |
|------|---------|
| `~/.hermes/hermes-agent/` | hermes-agent repo |
| `~/.hermes/.env` | Environment variables |
| `~/.local/bin/hermes` | Symlink for PATH |

## Architecture

```
AionUI (Electron)
  → spawns `hermes acp` subprocess
  → JSON messages over stdin/stdout
  → acp_adapter handles protocol
  → Hermes Agent core
  → Tools (skills, RAG, etc.)
```

The TCP BianinhoBridge (port 18743) is SEPARATE from the ACP connection.
