---
name: ai-agent-integration
description: Integrate existing autonomous agents (like Hermes) into multi-agent orchestration platforms (AionUI, LangChain, etc.) via ACP over stdio.
triggers:
  - integrate hermes into aionui
  - make agent available as teammate
  - spawn agent as subprocess in platform
  - connect hermes to orchestration layer
  - multi-agent team mode setup
  - acp protocol integration
---

# AI Agent Integration — Spawning Autonomous Agents into Orchestration Platforms

## Trigger

When the user wants to: integrate an existing autonomous agent (like Hermes) into a multi-agent orchestration platform (AionUI, LangChain, CrewAI, etc.), or make an agent available as a teammate in a team-based AI system.

---

## What This Is

Many AI orchestration platforms (AionUI, LangChain Agents, CrewAI, etc.) can spawn external CLI agents as subprocesses. This skill covers the pattern of taking an already-installed, already-configured autonomous agent and exposing it to such a platform — without rebuilding the agent from scratch.

**Key distinction**: This is NOT about building a new agent. It's about connecting an existing one to a new orchestration layer.

---

## Core Pattern: ACP over Stdio

Most modern orchestration platforms communicate with external agents via **ACP (Agent Communication Protocol)** over **stdio** (standard input/output). This is the same pattern used by Claude Code, Codex, and AionUI's multi-agent system.

### Agent Side (the already-installed agent)

The agent needs to accept ACP commands on stdin and emit ACP responses on stdout:

```bash
hermes --acp --stdio --model minimax
```

Typical flags:
- `--acp` — enables ACP mode (JSON over stdio)
- `--stdio` — uses stdin/stdout for communication (no TTY required)
- `--model` — specifies which LLM backend to use
- `--verbose` — enable debug logging

### ACP Message Format

**Leader → Agent (task assignment)**:
```json
{
  "type": "task",
  "id": "task-001",
  "content": "Analise o padrão emocional do paciente",
  "context": {
    "method": "TEN",
    "patient_id": "X"
  }
}
```

**Agent → Leader (result)**:
```json
{
  "type": "result",
  "id": "task-001",
  "content": "Padrão identificado: ciclo evade-ressignifica",
  "status": "complete"
}
```

### Platform Side (AionUI example)

In `~/.aionui/agents/<agent-name>.json`:
```json
{
  "name": "Hermes",
  "command": "/path/to/hermes",
  "args": ["--acp", "--stdio"],
  "description": "Agente autônomo especializado",
  "capabilities": ["file-read", "file-write", "web-search", "rag-query"]
}
```

---

## AionUI-Specific Patterns

### AionUI Architecture

AionUI is an Electron + TypeScript app with these key directories:
```
src/
  ├── common/       # Shared code
  ├── preload/      # Electron preload scripts
  ├── process/      # Main process (no DOM APIs)
  ├── renderer/     # UI (no Node.js APIs)
  └── server.ts    # Built-in server

assistant/          # 20 built-in professional assistants
skills/             # Three-layer skill system (built-in, custom, extension)
package/            # Internal MCP servers
```

### Team Mode

AionUI's Team Mode lets multiple agents work as a coordinated team:
- **Leader**: Receives instruction, breaks into subtasks, delegates
- **Teammates**: Execute subtasks in parallel, each with isolated permissions
- Communication: via ACP over stdio
- Workspace: shared folder, each agent has own permission context

**Configuration** (`~/.aionui/teams/<team-name>.json`):
```json
{
  "team": {
    "name": "TEN-Clinical-Team",
    "leader": { "agent": "gemini", "model": "gemini-2.5-pro" },
    "teammates": [
      { "id": "hermes", "agent": "hermes", "role": "analyst" },
      { "id": "coder", "agent": "claude-code", "role": "materials" }
    ],
    "workspace": { "shared": true, "path": "~/team-workspace/" }
  }
}
```

### Multi-Agent MCP Sharing Pattern

Configure MCP tools once in AionUI, sync to all agents automatically:
```json
{
  "mcpServers": {
    "rag": {
      "command": "python3",
      "args": ["~/.hermes/scripts/rag_search.py"],
      "description": "RAG Knowledge Base"
    }
  }
}
```

### YOLO Mode / Auto-Approve

AionUI supports "approve all actions automatically" mode for unattended execution — all agents support fully automatic mode.

---

## Project Bootstrap Pattern

When creating an integration project for an agent into a platform:

### Directory Structure
```
<project>/
├── README.md              # Vision + quick start
├── CLAUDE.md              # AI agent context (for future agents)
├── AGENTS.md              # Contributor conventions
├── docs/
│   ├── SETUP.md           # Step-by-step install
│   ├── INTEGRATION.md     # Technical integration details
│   └── TEAM_MODE.md       # Team orchestration config
├── config/
│   ├── agent.json         # Platform agent definition
│   └── env.yaml           # Environment variables template
├── scripts/
│   ├── setup.sh           # Configuration script
│   └── validate.sh        # Validation script
└── platform-skills/       # Custom skills for the platform
    └── <skill-name>/
        └── SKILL.md
```

### Setup Script Pattern

```bash
#!/usr/bin/env bash
set -e

# 1. Detect existing agent
command -v hermes &>/dev/null && info "✓ Hermes found" || error "✗ Hermes not found"

# 2. Copy agent config to platform directories
cp config/hermes-agent.json ~/.aionui/agents/

# 3. Create team config
mkdir -p ~/.aionui/teams
cp config/team-*.json ~/.aionui/teams/

# 4. Install custom skills
cp -r platform-skills/* ~/.aionui/skills/
```

### Validation Script Pattern

Always include a `validate.sh` that checks:
- Agent binary exists and is executable
- Agent version/flags work
- Platform config files are in place
- Dependent tools (Python, Node) are available
- RAG/knowledge base paths exist

Exit 0 on success, non-zero on any failure.

---

## Pitfalls

### 1. ACP Flag Required
Many agents have `--acp` or equivalent as a SEPARATE flag from `--stdio`. Without `--acp`, the agent may not emit proper JSON on stdout. Always test manually first:
```bash
echo '{"type":"ping"}' | hermes --acp --stdio
```

### 2. Platform Detaches the Subprocess
When the orchestration platform (AionUI) closes, the agent subprocess is killed. For truly persistent agents, run separately as a service and connect via HTTP API or socket — don't rely on the platform to keep it alive.

### 3. Environment Variables in Config
Platform agent configs often use `${ENV_VAR}` syntax. The platform must inject these. If they come up empty, the agent won't have credentials. Validate: `hermes --acp --stdio` should show API errors, not "missing API key."

### 4. MCP Tool Sharing Semantics
When you configure an MCP server in AionUI, it syncs to ALL agents. But not all agents can use all MCP tools. Tag capabilities properly in the agent config to avoid silent failures.

### 5. Workspace Isolation
In Team Mode, each Teammate has isolated permissions. The Leader shares a workspace. If a Teammate can't see files the Leader wrote, check the workspace path and permission config — not the agent.

### 6. Protocol Incompatibility — Hermes ACP ≠ AionUI aionrs (CRITICAL)

**This is the most important pitfall for Hermes + AionUI integration.**

AionUI uses **aionrs JSON Stream Protocol** for agent communication. Hermes Agent has an `acp` mode, but it implements **JSON-RPC 2.0** (LSP-like), NOT aionrs. The protocols are fundamentally incompatible:

| Aspect | Hermes ACP | AionUI aionrs |
|---|---|---|
| Protocol | JSON-RPC 2.0 | aionrs JSON Stream |
| Init | `initialize` command | `ready` event (stdout) |
| Streaming | `notification` messages | `text_delta` events |
| End marker | none | `stream_end` event |
| Tools | `tools/call` | `tool_request` / `tool_result` |

**This means: Hermes ACP does NOT work with AionUI out of the box.** A bridge is required.

**Solution: Build a protocol bridge** (`aionrs_bridge.py`). See `references/aionui-deep-research.md` for full implementation details.

**Key implementation findings:**
- `hermes acp` command exists but speaks JSON-RPC, not aionrs
- Hermes IS natively listed in AionUI's `POTENTIAL_ACP_CLIS` — but detection ≠ compatibility
- The bridge must emit `ready` event on stdout BEFORE processing any stdin
- Hermes `AIAgent` class is at `/home/alvarobiano/.hermes/hermes-agent/run_agent.py` (root, NOT `src/`)
- `AIAgent` requires the hermes-agent venv Python (has `dotenv` etc.) — system Python will fail to import
- Best approach: subprocess with hermes-agent venv Python, inline script calling `AIAgent.chat()`

**Bridge implementation (working, tested 2026-04-30):**
```python
# SubprocessHermes pattern — use hermes-agent venv Python
venv_python = '/home/alvarobiano/.hermes/hermes-agent/venv/bin/python'
hermes_root = '/home/alvarobiano/.hermes/hermes-agent'

script = f'''
import sys; sys.path.insert(0, '{hermes_root}')
from run_agent import AIAgent
agent = AIAgent(provider='minimax', model='MiniMax-M2.7', ...)
print(agent.chat({repr(message)}), end='')
'''
result = subprocess.run([venv_python, '-c', script], capture_output=True, text=True, timeout=120)
```

**Bridge protocol events (stdout → AionUI):**
- `ready` — first event, MUST be sent before processing stdin
- `stream_start` / `text_delta` (chunks) / `stream_end`
- `thinking`, `tool_request`, `tool_result`, `error`, `pong`

**Bridge protocol commands (stdin ← AionUI):**
- `message`, `stop`, `ping`, `tool_approve`, `tool_deny`, `set_config`, `set_mode`

**Timeout consideration:** Each subprocess call takes ~2-3s overhead. Test timeout must be ≥60s.
```bash
echo '{"type":"message","msg_id":"t1","content":"Olá"}' | python3 aionrs_bridge.py
```

**Live result (tested 2026-04-30):**
- Bianinho responded correctly: *"Olá! Eu sou o **Bianinho**, a inteligência artificial do Álvaro Bianoi..."*
- 12 events received: ready ✓, stream_start ✓, text_delta ✓, stream_end ✓

See: `~/repos/aionui-hermes-ten/scripts/aionrs-bridge/aionrs_bridge.py`

---

## Integration Checklist

For a new integration:

- [ ] Agent binary found and version confirmed
- [ ] ACP + stdio mode manually tested
- [ ] Platform agent config written (JSON structure)
- [ ] Environment variables templated
- [ ] Team Mode config (if applicable)
- [ ] Custom skill created (if agent has special domain knowledge)
- [ ] Setup script written and tested
- [ ] Validation script written and passes
- [ ] GitHub repo created and pushed

---

## Related Skills

- `github` — for repo creation when gh CLI has issues (Node 24 + nvm bug). The `aionui-hermes-ten` project was created using this pattern.
- `autonomous-ai-agents` — spawning and orchestrating autonomous agents
