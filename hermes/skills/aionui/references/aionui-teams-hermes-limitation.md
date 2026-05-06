# AionUI Teams — Hermes Team Leader não aparece no dropdown

**Date:** 03/05/2026  
**Finding:** Hermes Agent doesn't appear in Teams → Team Leader dropdown

## Root Cause (CORRIGIDO 03/05/2026 - Nova Investigação)

**CORRIGIDO:** Hermes JÁ está em `KNOWN_TEAM_CAPABLE_BACKENDS` no app.asar ORIGINAL. O problema não é falta de registo.

```javascript
// app.asar ORIGINAL (não modificado)
const KNOWN_TEAM_CAPABLE_BACKENDS = new Set(["gemini", "claude", "codex", "aionrs", "hermes"]);
```

Hermes é detectado correctamente (logs AionUI):
```
[AgentRegistry] Completed in 71ms, found 3 agents: Aion CLI, Gemini CLI, Hermes Agent
```

O problema está no filtro `isTeamCapableBackend()`:

```javascript
function isTeamCapableBackend(backend, cachedInitResults) {
  if (KNOWN_TEAM_CAPABLE_BACKENDS.has(backend)) return true;  // Hermes passa aqui
  const initResult = cachedInitResults?.[backend];
  return initResult?.capabilities.mcpCapabilities.stdio === true;  // Mas pode falhar aqui
}
```

Se `cachedInitResults['hermes']` não existir ou não tiver `mcpCapabilities.stdio: true`, Hermes é filtrado mesmo estando em `KNOWN_TEAM_CAPABLE_BACKENDS`.

**Situação actual (03/05/2026):** Hermes aparece no agent selector normal mas NÃO no Teams Leader dropdown. O debugging continua — a causa exacta do filtro UI ainda está a ser investigada.

## Investigação Metodologia

**LIÇÃO:** Quando algo não aparece na UI, PERGUNTAR primeiro o que o utilizador vê antes de vasculhar código backend.

### Passos de Debug Teams Leader dropdown

```bash
# 1. Perguntar ao utilizador: o que aparece no dropdown?
# Teams → New Team → que agentes estão visíveis no Team Leader dropdown?

# 2. Ver logs — agente detectado?
grep "AgentRegistry.*found" ~/Library/Logs/AionUi/$(date +%Y-%m-%d).log
# Output: found 3 agents: Aion CLI, Gemini CLI, Hermes Agent  ← Hermes DETECTADO

# 3. Verificar cachedInitResults
sqlite3 ~/Library/Application\ Support/AionUI/aionui/aionui.db \
  "SELECT id, agents, acpSessionId FROM conversations WHERE agents LIKE '%hermes%';"

# 4. Ver o que o Teams UI vê como team-capable
# No AionUI: Settings → Agents → verificar se Hermes aparece como team-capable
```

## Investigation Methodology Used

### 1. Extract strings from ASAR bundle
```bash
strings /Applications/AionUI.app/Contents/Resources/app.asar 2>/dev/null | grep -E "KNOWN_TEAM_CAPABLE|TeamLeader|team.*leader|dropdown.*leader"
```

### 2. Decode AionUI config
```python
import base64, urllib.parse, json
with open('~/Library/Application Support/AionUI/config/aionui-config.txt') as f:
    content = f.read()
decoded = base64.b64decode(content)
url_decoded = urllib.parse.unquote(decoded.decode('utf-8'))
data = json.loads(url_decoded)

# Check keys in cachedInitializeResult
print(data['acp.cachedInitializeResult'].keys())  # ['hermes']
print(data['acp.cachedInitializeResult']['hermes']['capabilities']['mcpCapabilities'])
# {'stdio': False, 'http': False, 'sse': False}
```

### 3. Query SQLite for Teams schema
```bash
sqlite3 ~/Library/Application\ Support/AionUI/aionui/aionui.db ".schema teams"
```

### 4. Search for backend registration
```bash
grep -rn "aionrs.*backend\|backend.*aionrs\|kind.*aionrs" app.asar.unpacked/out/
```

## Key Code Locations

| File | Purpose |
|------|---------|
| `app.asar.unpacked/out/main/team-guide-mcp-stdio.js` | Teams MCP server, `KNOWN_TEAM_CAPABLE_BACKENDS` |
| `app.asar.unpacked/out/main/team-mcp-stdio.js` | `handleListModels()`, agent spawning |
| `~/Library/Application Support/AionUI/config/aionui-config.txt` | base64+URL-encoded JSON, `cachedInitializeResult` |
| `~/Library/Application Support/AionUI/aionui/aionui.db` | Teams, agents, remote_agents tables |

## Hermes Registration State

```python
# Hermes cachedInitializeResult (from aionui-config.txt)
{
  "hermes": {
    "protocolVersion": 1,
    "capabilities": {
      "mcpCapabilities": {"stdio": False, "http": False, "sse": False},
      "sessionCapabilities": {"fork": {}, "resume": {}, "list": {}, "close": None}
    },
    "agentInfo": {"name": "hermes-agent", "version": "0.12.0"}
  }
}
```

## Available Workarounds

1. **Fork patch** — Add `"hermes"` to `KNOWN_TEAM_CAPABLE_BACKENDS` in `team-guide-mcp-stdio.js`
2. **Rename backend** — Register Hermes as `"aionrs"` instead of `"hermes"` (if possible)
3. **Use sub-agent** — Create Team with Claude/Codex Leader, spawn Hermes as sub-agent
4. **Request upstream** — Ask AionUI maintainers to add `"hermes"` to the list

## Related Findings

- Hermes WAS appearing in agent selector (03/05/2026) after fixing AcpDetector.ts regex
- But Teams Leader dropdown remained broken — different issue
- Teams MCP server runs internally to AionUI process, cannot be started externally
- `aion_create_team` tool only available when acting as agent within AionUI

## Extension System Architecture (Discovered 03/05/2026)

The AionUI has a full Extension System (`ExtensionRegistry`) that supports custom plugins, but Channel Plugins are NOT for internal inter-process communication.

### Extension Locations

Extensions are loaded from multiple sources (checked in order):
```javascript
// getExtensionScanSources() in index.js
1. Environment: AIONUI_EXTENSIONS_PATH env variable (colon-separated)
2. Local: ~/Library/Application Support/AionUI/extensions/
3. AppData: ~/Library/Application Support/AionUI/extensions/  (same as local)
```

### Extension Manifest Format

Each extension lives in its own directory with `aion-extension.json`:
```json
{
  "name": "hermes-bridge",
  "version": "1.0.0",
  "type": "extension",
  "contributes": {
    "channelPlugins": [{
      "type": "hermes-internal",
      "name": "Hermes Bridge",
      "description": "Internal bridge between Hermes processes",
      "entryPoint": "dist/plugin.js"
    }]
  }
}
```

### BasePlugin Required Methods

Channel Plugins MUST implement:
- `start()` — called when plugin starts
- `stop()` — called when plugin stops
- `sendMessage(chatId, message)` — send message to platform

The BasePlugin class also has:
- `onMessage(handler)` — receive incoming messages
- `emitMessage(message)` — forward to AionUI

### Why Extension System Doesn't Solve the Problem

The Channel Plugin system is designed for **external platforms** (Telegram, DingTalk, Weixin, Wecom). Each plugin connects to an external service API. The `sendMessage()` method sends TO the external platform, `onMessage()` receives FROM it.

There is NO mechanism for:
- Internal agent-to-agent communication
- Shared EventBus between processes
- Routing messages between main Hermes and Team Leader

The fundamental limitation:
```
Main Hermes (ACP session A)     Team Leader Hermes (ACP session B)
        ↑                               ↑
   Hermes Gateway                 team-mcp-stdio.js
        │                               │
        └─────────── AionUI DB ────────┘
                   (read-only)
```

Both processes write to the same SQLite database, but they have no shared memory, no message bus, no IPC channel. The AionUI's internal messaging (ChannelEventBus, teamEventBus) only exists within the AionUI main process.

### Database Access for Monitoring

The mailbox table stores inter-agent messages:
```sql
-- Read Team Leader mailbox (team_id from teams table)
SELECT * FROM mailbox WHERE team_id='515f1892-7709-41d7-ac67-7683380b33a8' ORDER BY created_at DESC;

-- Read Team Leader conversation messages
SELECT * FROM messages WHERE conversation_id='d124e72a' ORDER BY created_at DESC LIMIT 20;
```

Both message types ('user' and 'assistant') are stored as `type='text'` — no distinction in the type field.

### Practical Workarounds

1. **Monitoring only** — Poll the database for new Team Leader messages (read-only visibility)
2. **Asynchronous response** — Write to mailbox table and hope Team Leader checks it
3. **Request upstream feature** — Ask AionUI maintainers to add internal agent-to-agent messaging support

There is NO update-safe way to modify the inter-process communication without modifying AionUI core code.

## Update: Session Isolation Discovery (03/05/2026)

Even after Hermes appears as Team Leader, a fundamental architectural limitation remains:

**Main Hermes (chat principal / Bianinho) and TEN Team Leader are SEPARATE PROCESSES:**

```python
# Conversation IDs from aionui.db
Main Hermes session:  conversation_id = "27adf026"  # acpSessionId = "ca10a9c5..."
TEN Team Leader:     conversation_id = "d124e72a"  # acpSessionId = "b524f69f..."
```

These are **completely different ACP sessions** — different session IDs, different processes, different memory. The AionUI stores messages from both in the same SQLite database, but they cannot communicate with each other directly.

**What works:**
- Reading Team Leader messages from `messages` table (conversation_id = "d124e72a")
- All message types stored as `type='text'` — no user/assistant distinction in the type field

**What doesn't work:**
- Responding AS the Team Leader
- Real-time intervention in Team Leader conversations
- "Merging" sessions — architecturally impossible without modifying AionUI core

**If true real-time intervention is needed:** Requires modifying AionUI to route Team Leader messages to main Hermes via webhook, or implementing a shared inbox system that both processes can access.
