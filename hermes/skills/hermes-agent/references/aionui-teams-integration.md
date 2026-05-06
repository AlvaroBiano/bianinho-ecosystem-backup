# AionUI Teams + Hermes Integration

## What Was Built

A Python MCP stdio wrapper that lets Hermes act as Team Leader in AionUI Teams.

**Files created/modified:**
- `~/.hermes/scripts/hermes_team_mcp_stdio.py` — the wrapper script
- `app.asar.unpacked/out/main/index.js` — patched to use Python for hermes backend
- `hermes_cli/_parser.py` — added `--experimental-acp` flag
- `hermes_cli/main.py` — added `--experimental-acp` handler

## TCP Protocol (AionUI → MCP stdio script)

Format: 4-byte big-endian unsigned int (body length) + UTF-8 JSON body

```python
import struct, socket, json

def read_tcp_message(sock):
    header = b""
    while len(header) < 4:
        chunk = sock.recv(4 - len(header))
        header += chunk
    body_len = struct.unpack(">I", header)[0]
    body = b""
    while len(body) < body_len:
        chunk = sock.recv(body_len - len(body))
        body += chunk
    return json.loads(body.decode("utf-8"))
```

## MCP Stdio Protocol (script ↔ Hermes)

JSON-RPC 2.0 over stdin/stdout. Each line is one JSON object.

## Tool Payloads Sent to AionUI

```python
payload = {
    "tool": "aion_create_team",
    "args": {...},
    "auth_token": AION_MCP_TOKEN,
    "backend": "hermes",
    "conversation_id": AION_MCP_CONVERSATION_ID
}
```

## Environment Variables

| Variable | Description |
|----------|-------------|
| `AION_MCP_PORT` | TCP port where AionUI's TeamGuideMcpServer is listening |
| `AION_MCP_TOKEN` | Auth token for TCP connection |
| `AION_MCP_BACKEND` | Set to "hermes" for Hermes sessions |
| `AION_MCP_CONVERSATION_ID` | Conversation ID for routing |

## Debugging

```bash
# Test the wrapper directly
cd /Applications/AionUI.app/Contents/Resources/app.asar.unpacked/out/main
printf '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{}}' \
  | AION_MCP_PORT=9999 AION_MCP_TOKEN=test AION_MCP_BACKEND=hermes \
    python3 hermes_team_mcp_stdio.py
```
