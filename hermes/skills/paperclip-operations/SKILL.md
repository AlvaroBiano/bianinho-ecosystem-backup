---
name: paperclip-operations
description: "Paperclip AI agent operations — creating agents with hierarchy, autonomous operation via hierarchical issues, and troubleshooting. Use when: creating agents, setting up org hierarchy, recovering from errors, or monitoring agent health."
triggers:
  - paperclip agent create
  - paperclip hierarchy
  - paperclip reportsTo
  - paperclip troubleshooting
  - paperclip monitor
  - paperclip error state
  - paperclip autonomous
category: ai-platforms
---

# Paperclip Operations — Agent Creation, Hierarchy, and Troubleshooting

## Overview

Three operational domains for Paperclip AI agents:
1. **Agent Creation** — creating agents with proper hierarchy and reporting structure
2. **Autonomous Operation** — structuring autonomous work via hierarchical issues
3. **Troubleshooting** — recovering agents from error state, monitoring, and common issues

---

## ◆ AGENT CREATION — Creating Agents with Hierarchy

### Quick Reference
```bash
BASE_URL="http://localhost:3100/api"
TOKEN="pcp_board_local"

curl -X POST "${BASE_URL}/companies/${COMPANY_ID}/agents" \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "AgentName",
    "role": "general",
    "title": "Agent Title",
    "reportsTo": "e9b62a24-9662-494c-b6ea-baf7f1dcd7af",
    "capabilities": "What this agent does",
    "adapterType": "hermes_local",
    "adapterConfig": {}
  }'
```

### The Critical Rule: `reportsTo` (uses UUID, not name!)

**IMPORTANT**: `reportsTo` expects the AGENT ID (UUID), NOT the agent name.

Example:
- CEO ID: `e9b62a24-9662-494c-b6ea-baf7f1dcd7af`
- To make an agent report to CEO: `"reportsTo": "e9b62a24-9662-494c-b6ea-baf7f1dcd7af"`

Get IDs with:
```bash
curl -s "${BASE_URL}/companies/${COMPANY_ID}/agents" \
  -H "Authorization: Bearer ${TOKEN}" | jq '.[] | {name, id, role}'
```

**Every agent except the CEO MUST have `reportsTo` set to their manager's ID.**

### Role Types
| Role | Description | Typical Reports |
|------|-------------|----------------|
| `ceo` | Chief Executive Officer - top of hierarchy | null |
| `cto` | Chief Technology Officer | ceo |
| `cmo` | Chief Marketing Officer | ceo |
| `coo` | Chief Operations Officer | ceo |
| `engineer` | Software/technical agent | cto |
| `general` | General purpose agent | varies |

### Adapter Types
| Adapter | Description | Requirements |
|---------|-------------|--------------|
| `claude_local` | Runs Anthropic Claude CLI | Claude CLI installed + authenticated |
| `codex_local` | Runs OpenAI Codex CLI | Codex CLI installed |
| `process` | Generic shell command | Command + args defined |
| `http` | External HTTP endpoint | URL endpoint |
| `hermes_local` | Runs Hermes CLI agent | Hermes installed (custom) |

### Complete Agent Creation Workflow

**Step 1**: Identify Your Company
```bash
curl -s "${BASE_URL}/companies" \
  -H "Authorization: Bearer ${TOKEN}" | jq '.[] | {id, name}'
```

**Step 2**: Get Current CEO/Manager Info
```bash
curl -s "${BASE_URL}/companies/${COMPANY_ID}/agents" \
  -H "Authorization: Bearer ${TOKEN}" | jq '.[] | {name, role, reportsTo}'
```

**Step 3**: Create the Agent with Hierarchy (example: Content Agent reporting to CEO)
```bash
curl -X POST "${BASE_URL}/companies/${COMPANY_ID}/agents" \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Content Agent",
    "role": "general",
    "title": "Content Lead",
    "reportsTo": "e9b62a24-9662-494c-b6ea-baf7f1dcd7af",
    "capabilities": "Create YouTube scripts, blog posts, social media content",
    "adapterType": "hermes_local",
    "adapterConfig": {
      "cwd": "/home/alvarobiano",
      "timeoutSec": 600
    }
  }'
```

**Step 4**: Create API Key for the Agent
```bash
AGENT_ID="<agent-id-from-response>"
curl -X POST "${BASE_URL}/agents/${AGENT_ID}/keys" \
  -H "Authorization: Bearer ${TOKEN}" | jq '.'
```

**Step 5**: Configure Agent Instructions
Via Paperclip UI: `/companies/{companyId}/agents/{agent-slug}/instructions`
Or writing directly to filesystem.

**Step 6**: Validate Hierarchy
```bash
curl -s "${BASE_URL}/companies/${COMPANY_ID}/org" \
  -H "Authorization: Bearer ${TOKEN}" | jq '.'
```

### Batch Creation Script
```bash
#!/bin/bash
BASE_URL="http://localhost:3100/api"
TOKEN="pcp_board_local"
COMPANY_ID="f63fa443-eb1a-4de8-8d61-aebc42dae20f"

create_agent() {
  local name="$1" role="$2" title="$3" reports_to="$4" capabilities="$5"
  curl -s -X POST "${BASE_URL}/companies/${COMPANY_ID}/agents" \
    -H "Authorization: Bearer ${TOKEN}" \
    -H "Content-Type: application/json" \
    -d "{\"name\": \"${name}\", \"role\": \"${role}\", \"title\": \"${title}\", \"reportsTo\": \"${reports_to}\", \"capabilities\": \"${capabilities}\", \"adapterType\": \"hermes_local\", \"adapterConfig\": {\"cwd\": \"/home/alvarobiano\", \"timeoutSec\": 600}}"
  echo ""
}

# Create agents reporting to CEO
create_agent "Content Agent" "general" "Content Lead" "e9b62a24-9662-494c-b6ea-baf7f1dcd7af" "Create content for YouTube and social media"
create_agent "Social Agent" "general" "Social Media Manager" "e9b62a24-9662-494c-b6ea-baf7f1dcd7af" "Manage social media presence"
create_agent "Product Agent" "general" "Product Lead" "e9b62a24-9662-494c-b6ea-baf7f1dcd7af" "Lead product development"
```

### Post-Creation Checklist
- [ ] `reportsTo` is set correctly (not null unless CEO)
- [ ] `capabilities` clearly describes what the agent does
- [ ] `adapterConfig.cwd` points to correct working directory
- [ ] `adapterConfig.timeoutSec` is appropriate (300-600 for complex tasks)
- [ ] Agent instructions (AGENTS.md) are written
- [ ] Initial tasks are assigned to get agent started

### Fixing Agents with Wrong reportsTo
```bash
curl -X PATCH "${BASE_URL}/agents/${AGENT_ID}" \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{"reportsTo": "e9b62a24-9662-494c-b6ea-baf7f1dcd7af"}'
```

---

## ◆ AUTONOMOUS HIERARCHY — Structuring Autonomous Operations

### Principle
Agents should operate **autonomously**. The orchestrator's role is **create the initial structure** and **never interfere directly** — only observe and adjust structure when needed.

### Hierarchical Issue Structure
```
BRA-X: Projecto Principal (CEO Agent — supervisor)
│
├── BRA-X.1: Rotina do Agente A
│   ├── BRA-X.1.1: Tarefa específica 1
│   └── BRA-X.1.2: Tarefa específica 2
│
├── BRA-X.2: Rotina do Agente B
│   ├── BRA-X.2.1: Tarefa específica 1
│   └── BRA-X.2.2: Tarefa específica 2
│
└── BRA-X.3: Rotina do Agente C
    └── ...
```

### Creating Hierarchical Issues
```bash
# Create parent issue (CEO)
paperclipai issue create \
  -C <company-id> \
  --title "BRA-X: Nome do Projecto" \
  --description "Descrição do Objectivo" \
  --priority critical \
  --assignee-agent-id <ceo-agent-id> \
  --json

# Create child issues (one per agent)
paperclipai issue create \
  -C <company-id> \
  --title "BRA-X.Y: Nome da Rotina" \
  --description "Criar rotina autónoma para [agente]..." \
  --priority critical \
  --assignee-agent-id <agent-id> \
  --parent-id <parent_id> \
  --json
```

### Real Example — BRA-5
```
BRA-5: Autonomous Content Production System
├── BRA-5.1: Content Agent — Produção de Conteúdo
│   ├── BRA-5.1.1: Calendários editoriais
│   └── BRA-5.1.2: Templates de roteiros
├── BRA-5.2: Social Agent — Distribuição e Engajamento
│   ├── BRA-5.2.1: Auto-response FAQs
│   └── BRA-5.2.2: Monitoramento métricas
├── BRA-5.3: Product Agent — Gestão de Produtos
│   ├── BRA-5.3.1: Mapear produtos digitais
│   └── BRA-5.3.2: Integrar RAG metodoten
└── BRA-5.4: CEO Agent — Supervisão
    ├── BRA-5.4.1: Critérios de escalação
    └── BRA-5.4.2: Daily brief via Telegram
```

### Golden Rules
1. **Never interfere** — if agent is working, let it work
2. **Escalation rule** — only create new issue if agent can't resolve; only bother Álvaro for critical cases
3. **Each issue = one clear responsibility** — vague description = agent doesn't know what to do
4. **Consistent priorities** — `critical` for structural, `high` for important tasks, `medium` for optimizations

### Escalation Rules
```
CRITICAL (escalate to Álvaro):
- Metrics drop >30%
- Image/reputation crises
- Financial decisions >R$5.000
- Opportunities requiring human decision

AUTONOMOUS (resolve without bothering):
- Everything within defined routines
- Day-to-day tasks
- Adjustments within established parameters
```

---

## ◆ TROUBLESHOOTING — Recovery, Monitoring, and Common Issues

### Recovering Agents from Error State

**Problem**: Agents stuck in `error` state after Paperclip restart — embedded PostgreSQL gives transient errors.

**Solution**: Trigger manual heartbeat:
```bash
paperclipai heartbeat run \
  -a <agent-id> \
  --api-base http://localhost:3100 \
  --api-key "<board-token>" \
  --source on_demand \
  --trigger manual
```

**Result**: agent exits `error` → `idle` or `running`.

### Company Deletion — API Broken

**Problem**: `paperclipai company delete <id> --yes` returns `API error 500`.

**What DOESN'T work**:
- CLI `company delete` → 500
- API `DELETE /api/companies/{id}` → 500
- "Archive company" button in UI → no visible effect
- Deleting company directory → persists in DB

**What WORKS**: Delete agents individually via API:
```bash
curl -s -X DELETE "http://localhost:3100/api/agents/<agent-id>" \
  -H "Authorization: Bearer <board-token>"
```

**Workaround**: Recreate with different name — old one stays inaccessible but not deleted.

### ⚠️ HTTP 400: "invalid function arguments json string"

**Cause**: `delegate_task` with very long goals containing shell commands, newlines, pipes, or embedded JSON. JSON gets malformed and MiniMax API rejects it.

**Symptom**:
```
⚠️ Non-retryable error (HTTP 400)
❌ invalid params, invalid function arguments json string, tool_call_id: call_function_xxx
```

**Solution**: DON'T use `delegate_task` with goals containing:
- Curl commands with multiple flags
- Newlines or line breaks
- Embedded JSON or complex quoted strings
- Pipes (`|`), redirects (`>`), or subshells

**Alternative**: Do the work directly with `terminal()` or `execute_code()` instead of delegating.

### API Breaking Change in v2026.416.0

**Problem**: After update to v2026.416.0, REST endpoints `/api/agents` and `/api/issues` were REMOVED.

**Symptom**: `curl http://127.0.0.1:3100/api/agents` → `{"error":"API route not found"}`

**What STILL works**:
```bash
paperclipai agent list -C <company-id>       # List agents
paperclipai dashboard get -C <company-id>     # Dashboard summary
paperclipai issue list -C <company-id>        # List issues
paperclipai activity -C <company-id>          # Activity log
```

**What DOESN'T work anymore**:
- `GET /api/agents` → 404
- `GET /api/issues` → 404
- `GET /api/health` → WORKS (still available)

### Automated Monitoring Script

```bash
# Script: ~/.hermes/scripts/paperclip-agent-monitor.sh (bash — NOT python)
# Cron: */5 * * * * — every 5 minutes
# Log: ~/.hermes/logs/paperclip-monitor.log

# IMPORTANT: Use ABSOLUTE PATH — cron doesn't have nvm PATH
/home/alvarobiano/.nvm/versions/node/v24.14.1/bin/paperclipai agent list \
  -C <company-id>

# Recovery from error state:
~/.hermes/scripts/paperclipai heartbeat run \
  -a <agent-id> \
  --source on_demand \
  --trigger manual
```

### Embedded PostgreSQL Crash Loop (ECONNREFUSED on Port 54329)

**Symptom**: Service crashes repeatedly with `connect ECONNREFUSED 127.0.0.1:54329`. Restart counter hits 199+.

**Root Cause**: Stale `postmaster.pid` file but postgres process dead/zombie.

**Fix**:
```bash
pkill -f "postgres.*paperclip" 2>/dev/null
sleep 1
rm -f ~/.paperclip/instances/default/db/postmaster.pid
systemctl --user start paperclip.service
sleep 5 && curl -s http://localhost:3100/ | head -5
```

**Prevention**: Add `RestartSec=15` to the service.

---

## Current State (do not modify)
- Company ID: `f63fa443-eb1a-4de8-8d61-aebc42dae20f`
- Issue prefix: `BRA`
- Server: `localhost:3100`
- Agents: CEO `e9b62a24-9662-494c-b6ea-baf7f1dcd7af` (role: ceo), Content Agent, Social Agent, Product Agent
