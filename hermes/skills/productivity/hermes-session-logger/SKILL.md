---
name: hermes-session-logger
description: Sistema de logging permanente SQLite com plugin auto-import — tudo gravado para sempre, 100% automático
---

# Hermes Session Logger — Sistema de Logging Automático e Persistência

## Verificação de Versão (primeiro passo)

```bash
# Verifica se o plugin está ativo e os patches aplicados
~/.hermes/hermes-agent/venv/bin/python3 -c "
import sitecustomize as sc
print('Logger disponível:', sc._logger_available)
print('PATCH 1 (tools) aplicado:', sc._model_tools_patched)
print('PATCH 2 (msgs) aplicado:', sc._run_agent_patched)

# Verifica banco
import hermes_logger as hl
conn = hl.get_conn()
cur = conn.execute('SELECT COUNT(*) FROM events')
print('Eventos no banco:', cur.fetchone()[0])
conn.close()
"
```

Se todos os valores forem `True` / `> 0`, está funcionando.

## Conceito

Agentes de IA são stateless. Este sistema resolve:
- Tool calls **não são consultáveis** depois → ✅ log automático
- Mensagens de chat **somem** → ✅ log automático (v1.1)
- Sessões crashadas **perdem contexto** → ✅ SQLite permanente
- Não há **trilha de auditoria** → ✅ timestamp + tipo + detalhes

## Sistema de Logging Automático (Plugin v1.1)

O logging é **100% automático** via `sitecustomize.py` — dois patches:

1. **PATCH 1** — `model_tools.handle_function_call` → toda tool call
2. **PATCH 2** — `run_agent.AIAgent.run_conversation` → user message + agent response

### Plugin (sitecustomize.py)
- **Local:** `~/.hermes/hermes-agent/venv/lib/python3.11/site-packages/sitecustomize.py`
- **Versão:** 1.1 (atualizada 2026-04-16)
- **Carrega:** automaticamente com qualquer comando hermes (CLI, gateway, subagentes)
- **Fallback:** se não houver sessão ativa, cria `auto_plugin_TIMESTAMP` automaticamente
- **Verificar patches:**
  ```bash
  ~/.hermes/hermes-agent/venv/bin/python3 -c "
  import model_tools; import run_agent
  print('PATCH 1 (tools):', getattr(model_tools, '_hermes_logging_patched', False))
  print('PATCH 2 (msgs):', getattr(run_agent.AIAgent, '_hermes_msg_logging_patched', False))
  "
  ```

## O Que É Capturado Automaticamente (v1.1)

| Tipo | Status | Exemplo |
|------|--------|---------|
| `tool_call_start` | ✅ Automático | `[terminal] args={...}` |
| `tool_call_result` | ✅ Automático | `[terminal] → {...}` |
| `user_message` | ✅ Automático (novo v1.1) | conteúdo integral |
| `agent_response` | ✅ Automático (novo v1.1) | conteúdo integral |

## Arquivos

| Arquivo | Responsabilidade |
|---------|-----------------|
| `~/.hermes/hermes_logger.py` | API de logging + banco SQLite |
| `~/.hermes/hermes-agent/venv/lib/python3.11/site-packages/sitecustomize.py` | Plugin auto-loading v1.1 |
| `~/.hermes/hermes_sessions.db` | Banco SQLite permanente |
| `~/KnowledgeBase/hermes-logging-blueprint.md` | Documentação completa (replicável) |

## Ver Logs

```bash
python3 ~/.hermes/hermes_logger.py recent 20    # últimos 20 eventos
python3 ~/.hermes/hermes_logger.py sessions     # lista sessões
python3 ~/.hermes/hermes_logger.py session ID  # sessão completa
python3 ~/.hermes/hermes_logger.py search "termo"  # busca
python3 ~/.hermes/hermes_logger.py search "termo" tool_call_start  # busca por tipo
python3 ~/.hermes/hermes_logger.py new          # nova sessão
python3 ~/.hermes/hermes_logger.py status      # sessão ativa
```

## API Python

```python
import os, sys
sys.path.insert(0, os.path.expanduser("~/.hermes"))
from hermes_logger import (
    start_session, set_active_session, get_active_session,
    log, log_user, log_agent, log_tool, log_tool_auto,
    log_error, log_web, log_skill, log_file,
    search_events, get_session_events, format_event
)

# Sessão ativa
set_active_session("minha_sessao")
get_active_session()

# Criar sessão
sid = start_session("telegram", {"user": "Álvaro"})

# Logs manuais (para casos específicos)
log_user(sid, "mensagem")
log_agent(sid, "resposta")
log_tool(sid, "terminal", {"command": "ls"}, "output...")
log_error(sid, "erro que ocorreu")
log_web(sid, "https://url.com", "Título")
log_skill(sid, "nome-da-skill", "used")

# Buscar
for row in search_events("termo"):
    print(format_event(row))
```

## Quando Usar

| Cenário | Como |
|---------|------|
| Tool calls | **AUTOMÁTICO** via PATCH 1 (plugin) |
| user_message + agent_response | **AUTOMÁTICO** via PATCH 2 (plugin) |
| Acessos web | `log_web()` manual |
| Skills | `log_skill()` manual |
| Erros específicos | `log_error()` manual |
| Início de tarefa | `start_session()` manual |

## Tipos de Evento no Banco

`tool_call_start`, `tool_call_result`, `user_message`, `agent_response`, `tool_call`, `error`, `system`, `skill`, `web_access`, `file_access`, `context`, `finding`, `rule`, `search`, `profile`, `config_update`, `env_update`, `memory_update`, `agent_commitment`, `files_created`, `event`, `api_key`, `user_feedback`, `profile_found`

## Estrutura do Banco

```sql
sessions: session_id, platform, started_at, ended_at, metadata
events: id, session_id, timestamp, event_type, content, details
```

## Replicar em Outro Ambiente

1. Identificar venv: `which hermes` → path do venv
2. Criar `~/.hermes/hermes_logger.py` (copiar do blueprint)
3. Criar `venv/lib/pythonX.Y/site-packages/sitecustomize.py` (**v1.1** — copiar do blueprint)
4. Testar: `~/.hermes/hermes-agent/venv/bin/python3 -c "import model_tools; print('_hermes_logging_patched:', getattr(model_tools, '_hermes_logging_patched', False))"`
5. Gateway: reiniciar serviço

Blueprint completo: `~/KnowledgeBase/hermes-logging-blueprint.md`
