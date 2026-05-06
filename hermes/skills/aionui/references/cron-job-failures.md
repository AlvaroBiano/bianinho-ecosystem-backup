# AionUI Cron Job — "Conversation not found" Failure Pattern

**Data:** 05/05/2026

## Sintoma

Cron job no AionUI Scheduled Tasks mostra erro:
```
Failed to acquire task for conversation conv_pubmed_daily: Conversation not found: conv_pubmed_daily
```

## Causas Raiz Identificadas

| # | Problema | Como verificar |
|---|----------|----------------|
| 1 | `conversation_id` do job **não existe** na tabela `conversations` | `SELECT * FROM conversations WHERE id = 'conv_XXX'` |
| 2 | `agent_config` é `null` — job sem configuração de execução | `SELECT agent_config FROM cron_jobs WHERE id = 'cron_XXX'` |
| 3 | Skill referenciada no `payload_message` **não existe** em `~/.hermes/skills/` | `ls ~/.hermes/skills/ \| grep skill-name` |

## Tabela `cron_jobs` — Estrutura Relevante

```sql
id               TEXT PRIMARY KEY
name             TEXT
enabled          INTEGER (1=activo, 0=inactivo)
schedule_kind    TEXT ('cron')
schedule_value   TEXT ('0 23 * * *')
payload_message  TEXT
conversation_id  TEXT  -- DEVE existir em conversations.id
agent_type       TEXT ('hermes')
agent_config     TEXT  -- JSON, NUNCA null para jobs activos
last_status      TEXT ('ok'|'error'|NULL)
last_error       TEXT
```

## Tabela `conversations` — Estrutura Relevante

```sql
id               TEXT PRIMARY KEY
user_id          TEXT
name             TEXT
type             TEXT ('acp')
extra            TEXT  -- JSON com workspace, backend, cliPath, sessionMode
created_at       INTEGER (unix ms)
updated_at       INTEGER (unix ms)
```

## Fix Completo (sempre aplicar na ordem)

### Passo 1 — Criar conversation se não existir

```python
import sqlite3, json, time

conn = sqlite3.connect('/Users/alvarobiano/Library/Application Support/AionUi/aionui/aionui.db')
cursor = conn.cursor()

conv_id = 'conv_pubmed_daily'  # o conversation_id do job
now_ms = int(time.time() * 1000)

extra = json.dumps({
    "workspace": "/Users/alvarobiano/Documents/TEN Team - AionUI",
    "customWorkspace": True,
    "backend": "hermes",
    "cliPath": "/Users/alvarobiano/.hermes/venv/bin/hermes",
    "agentName": "Hermes Agent",
    "excludeBuiltinSkills": ["cron"],
    "sessionMode": "yolo",
    "cronJobId": "cron_pubmed_daily",
    "cronWorkspace": "/Users/alvarobiano/Documents/TEN Team - AionUI"
})

cursor.execute("""
    INSERT OR REPLACE INTO conversations
    (id, user_id, name, type, extra, model, status, source, channel_chat_id, created_at, updated_at)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
""", (conv_id, 'system_default_user', 'Nome do Job', 'acp', extra, None, None, None, None, now_ms, now_ms))

conn.commit()
```

### Passo 2 — Adicionar agent_config se null

```python
agent_config = json.dumps({
    "backend": "hermes",
    "name": "Hermes Agent",
    "cliPath": "/Users/alvarobiano/.hermes/venv/bin/hermes",
    "mode": "yolo",
    "workspace": "/Users/alvarobiano/Documents/TEN Team - AionUI"
})

cursor.execute("""
    UPDATE cron_jobs
    SET agent_config = ?,
        last_status = NULL,
        last_error = NULL
    WHERE id = 'cron_pubmed_daily'
""", (agent_config,))

conn.commit()
```

### Passo 3 — Verificar skill existe

```bash
ls ~/.hermes/skills/ | grep -i skill-name
```

Se a skill não existir, corrigir o `payload_message` para usar skill existente.

## Query de Diagnóstico Completo

```python
import sqlite3

conn = sqlite3.connect('/Users/alvarobiano/Library/Application Support/AionUi/aionui/aionui.db')
cursor = conn.cursor()

cursor.execute("""
    SELECT
        j.id, j.name, j.enabled, j.last_status, j.last_error,
        j.conversation_id,
        j.agent_config IS NOT NULL as has_agent_config,
        c.id as conv_exists
    FROM cron_jobs j
    LEFT JOIN conversations c ON j.conversation_id = c.id
    ORDER BY j.last_status
""")

for row in cursor.fetchall():
    job_id, name, enabled, status, error, conv_id, has_config, conv_exists = row
    print(f"{'🔴' if error else '🟢'} {name}")
    print(f"   enabled={enabled} status={status}")
    print(f"   conv_id={conv_id} conv_exists={bool(conv_exists)}")
    print(f"   has_agent_config={bool(has_config)}")
    if error:
        print(f"   ERROR: {error[:100]}")
```

## Prevenção

Antes de criar um cron job no AionUI via Scheduled Tasks UI, o sistema deveria:
1. Criar a `conversation` automaticamente no momento da criação do job
2. Validar que `agent_config` é preenchido antes de activar

Este bug ocorre quando o job é criado por um sub-sistema (ex: um agent cria um cron job) sem seguir o fluxo completo de inicialização.
