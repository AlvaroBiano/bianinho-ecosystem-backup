---
name: aionui-scheduled-task
description: Criar tasks visíveis no painel AionUI Scheduled Tasks — inserir diretamente na SQLite do AionUI
triggers:
  - criar task
  - criar tarefa
  - agendar algo
  - scheduled task
  - nova automation
  - criar automação
---

# AionUI Scheduled Task — Criar Task Visível no Painel

## Quando Usar
Quando o Álvaro pedir para criar uma "task", "tarefa", "agendar algo", "criar agendamento" ou "scheduled task" no AionUI.

## Regra de Ouro
**SEMPRE** inserir na base de dados SQLite do AionUI, NUNCA no Hermes Cron.
- AionUI SQLite: `~/Library/Application Support/AionUi/aionui/aionui.db` (tabela `cron_jobs`)
- Hermes Cron: `~/.hermes/cron/jobs.json` → **NÃO aparece no painel AionUI**

## Passos

### 1. Definir parâmetros da task

| Campo | Valor |
|---|---|
| `id` | `cron_` + 8随机hex字符 |
| `name` | Nome da task |
| `schedule_kind` | `cron` |
| `schedule_value` | Expressão cron (ex: `0 * * * *` = hourly) |
| `schedule_description` | Descrição legível (ex: `Every hour`) |
| `payload_message` | Prompt que o agente vai executar |
| `conversation_id` | `b6a516ca` (válido, mesmo da "Saúde da Mulher") |
| `conversation_title` | `${name} - AionUI` |
| `agent_type` | `hermes` |
| `created_by` | `user` |
| `enabled` | `1` |
| `execution_mode` | `existing` |
| `max_retries` | `3` |
| `run_count` | `0` |
| `retry_count` | `0` |
| `last_status` | `NULL` |
| `last_error` | `NULL` |
| `last_run_at` | `NULL` |

### 2. Calcular `next_run_at` (timestamp em milisegundos)

```python
import datetime
now = datetime.datetime.now()
# Para hourly (0 * * * *): próximo topo de hora
next_hour = now.replace(minute=0, second=0, microsecond=0) + datetime.timedelta(hours=1)
next_run_ms = int(next_hour.timestamp() * 1000)
```

### 3. Calcular `agent_config`

```json
{
  "backend": "hermes",
  "name": "Hermes Agent",
  "cliPath": "/Users/alvarobiano/.hermes/venv/bin/hermes",
  "mode": "yolo",
  "workspace": "/Users/alvarobiano"
}
```

### 4. Inserir na SQLite

```python
import sqlite3, time, uuid, json

db_path = '/Users/alvarobiano/Library/Application Support/AionUi/aionui/aionui.db'
conn = sqlite3.connect(db_path)
cur = conn.cursor()

now_ms = int(time.time() * 1000)
new_id = 'cron_' + uuid.uuid4().hex[:8]

cur.execute('''
INSERT INTO cron_jobs (
    id, name, enabled, schedule_kind, schedule_value, schedule_tz,
    schedule_description, payload_message, conversation_id, conversation_title,
    agent_type, created_by, created_at, updated_at, next_run_at,
    last_run_at, last_status, last_error, run_count, retry_count,
    max_retries, execution_mode, agent_config, description
) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
''', (
    new_id, name, 1, 'cron', schedule_value, None,
    schedule_description, payload_message, 'b6a516ca', f'{name} - AionUI',
    'hermes', 'user', now_ms, now_ms, next_run_ms,
    None, None, None, 0, 0, 3, 'existing', json.dumps(agent_config),
    description or ''
))

conn.commit()
print(f'Task criada: {new_id} — {name}')
conn.close()
```

### 5. Verificar

```bash
~/.hermes/venv/bin/python3 -c "
import sqlite3
conn = sqlite3.connect('/Users/alvarobiano/Library/Application Support/AionUi/aionui/aionui.db')
cur = conn.cursor()
cur.execute('SELECT id, name, schedule_value, enabled, next_run_at FROM cron_jobs')
for r in cur.fetchall(): print(r)
conn.close()
"
```

## Armadilhas
- `conversation_id` NÃO pode ser NULL — usar sempre `b6a516ca`
- `schedule_tz` pode ser NULL
- Timestamps são em **milisegundos**, não segundos
- `agent_config` tem de ser JSON string, não dict

## Exemplo Completo — Cron Expressions

| Frequência | `schedule_value` | `schedule_description` |
|---|---|---|
| De hora em hora | `0 * * * *` | `Every hour` |
| Diário às 8h | `0 8 * * *` | `Every day at 08:00` |
| Diário às 22h45 | `45 22 * * *` | `Every day at 22:45` |
| Seg a Sex às 9h | `0 9 * * 1-5` | `Weekdays at 09:00` |
| Semanal (Segunda) | `0 9 * * 1` | `Every Monday at 09:00` |
| A cada 10 min | `*/10 * * * *` | `Every 10 minutes` |
