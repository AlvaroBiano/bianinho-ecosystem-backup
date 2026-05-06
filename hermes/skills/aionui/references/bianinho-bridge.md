# BianinhoBridge — Protocolo e Referência Técnica

**Versão:** 1.0 (Fases 1-2 completas)
**Ficheiro:** `scripts/bianinho_bridge.py`
**Porta:** `18743` (TCP localhost)
**Estado:** Em produção (background, `proc_3b423d888a53`)

---

## Arquitectura

```
AionUI (Electron/Node.js)
    │
    │  TCP 127.0.0.1:18743
    │  4-byte length prefix (big-endian) + JSON payload
    ▼
BianinhoBridge (Python/bianinho-venv)
    │
    ├── RAG (LanceDB) — ~/KnowledgeBase/knowledge_db/
    ├── Hermes — ~/.hermes/
    ├── Skills — ~/.hermes/skills/
    ├── Backup — ~/.hermes/backups/
    └── Inbox/Memory — ~/.hermes/inbox.json, memory.json
```

---

## Protocolo TCP

### Formato da mensagem

```
[4 bytes: big-endian length][JSON payload]
```

**Exemplo:** `{"cmd":"ping","args":{"echo":"ok"}}`
- Bytes: `0x00 0x00 0x00 0x1D` (29 bytes em big-endian)
- Seguido pelo JSON

### Cliente Python (correcto)

```python
import socket, json

def call(cmd, args={}):
    sock = socket.socket()
    sock.connect(('127.0.0.1', 18743))
    payload = json.dumps({'cmd': cmd, 'args': args}).encode()
    sock.sendall(len(payload).to_bytes(4, 'big') + payload)
    len_bytes = sock.recv(4)
    if not len_bytes:
        return {"error": "No response"}
    length = int.from_bytes(len_bytes, 'big')
    data = b''
    while len(data) < length:
        chunk = sock.recv(length - len(data))
        if not chunk:
            break
        data += chunk
    sock.close()
    return json.loads(data.decode())
```

### Teste com `nc` (debugging manual)

```bash
# Protocolo usa length prefix, não newline — nc com pipe não funciona bem
# Correcto para scripting — parse length prefix:
timeout 5 bash -c 'echo "{\"cmd\":\"status\",\"args\":{}}" | nc -N 127.0.0.1 18743' | python3 -c "
import sys; d=sys.stdin.buffer.read()
import json
print(json.loads(d[4:].decode()))
"
```

### Erro comum: `shutdown(SHUT_WR)` quebra

O `shutdown(SHUT_WR)` após `send()` faz o servidor fechar ANTES de responder:

```python
# ERRADO — broken pipe no servidor
sock.send(payload)
sock.shutdown(socket.SHUT_WR)  # ❌
response = sock.recv(...)

# CORRECTO — sem shutdown, length prefix determina quando parar
sock.sendall(len(payload).to_bytes(4, 'big') + payload)
len_bytes = sock.recv(4)
```

---

## Comandos Disponíveis (22)

### Sistema
| Comando | Args | Descrição |
|---|---|---|
| `ping` | `echo` | Teste de conectividade |
| `status` | — | Uptime, msgs, errors, rate_limit_hits, auth_failures |
| `platform_info` | — | system, release, machine, python version |
| `check_hermes` | — | Verifica paths do Hermes (5/6 checks) |

### RAG
| Comando | Args | Descrição |
|---|---|---|
| `rag_search` | `query`, `category?`, `topK?`, `score_threshold?`, `access_level?` | Pesquisa com isolation |
| `rag_stats` | — | Estatísticas: total chunks, categorias |
| `rag_backup` | `label?` | Backup pre-write do RAG |
| `rag_restore` | `backup_name` | Restore de backup |
| `rag_list_backups` | — | Lista backups disponíveis |

### Inbox
| Comando | Args | Descrição |
|---|---|---|
| `inbox_list` | — | Lista todas as tarefas |
| `inbox_add` | `content`, `priority?`, `tags?`, `source?` | Adiciona tarefa |
| `inbox_done` | `id` | Marca como concluída |
| `inbox_delete` | `id` | Remove tarefa |

### Skills
| Comando | Args | Descrição |
|---|---|---|
| `list_skills` | — | Lista 72 skills do Hermes |
| `skill_execute` | `skill_name`, `params?` | Executa em sandbox |
| `skill_validate` | `skill_name` | Verifica permissão |

### Ciclo Autónomo
| Comando | Args | Descrição |
|---|---|---|
| `cycle_status` | — | Estado do ciclo autónomo |
| `cycle_trigger` | — | Força ciclo manual (marker file) |

### Memória
| Comando | Args | Descrição |
|---|---|---|
| `memory_get` | `key` | Lê valor da memória |
| `memory_set` | `key`, `value` | Escreve na memória |

### Snapshots
| Comando | Args | Descrição |
|---|---|---|
| `snapshot_export` | `path?` | Export encriptado do estado |
| `snapshot_import` | `path` | Import de snapshot |

---

## Segurança

### HMAC Auth (opcional por comando)
- Token: `timestamp.signature` (timestamp em Unix seconds)
- TTL: 24h
- Gerado em `~/.hermes/config/bridge_secret.key`

### Rate Limiting
- **100 req/min** por `client_id` (endereço TCP + porta)
- Cada nova conexão TCP é um cliente diferente
- Em produção (Electron = 1 conexão): todos os pedidos contam
- Em teste com `nc` (1 conexão = 1 pedido): cada `nc` é cliente diferente

### Skills Sandbox
- **safe**: executa sem confirmação
- **sensitive**: `terminal`, `file_write`, `github`, `cron_create`
- **dangerous**: `file_delete`, `system_exec`, `kill_process`, `db_delete` — requer confirmação UI
- Resource limits: CPU 60s, RAM 500MB, 100 ficheiros abertos
- Timeout: 30s por skill

### RAG Access Levels
- `full`: Bianinho admin — todas as categorias
- `read_sac`: só `sac_leads`
- `read_personal`: `metodoten`, `livros`, `memoria`, `default`, `api`, `prd_collection`

---

## Payload Validation

Schemas implementados para: `rag_search`, `rag_process`, `inbox_add`, `inbox_done`, `inbox_update`, `skill_execute`, `cron_job_create`, `subagent_create`, `memory_set`, `config_set`, `snapshot_export`, `snapshot_import`.

Campos validados: tipo, min/max, required, defaults.

---

## Backup / Rollback

- **Nível 1**: pre-write (antes de cada write RAG/memory)
- Mantém últimos **10** backups pre-write
- Restore: `rag_restore` com `backup_name`
- Lista: `rag_list_backups`

---

## PRD — Estado da Integração

### Fase 1 — Completa ✅
- BianinhoBridge auth + rate limiting ✅
- RAG isolation (access levels) ✅
- Skills sandbox ✅
- Payload validation ✅
- Backup/rollback mechanism ✅

### Fase 2 — Completa ✅
- Página Bianinho React com 4 tabs ✅ (build: `✓ built in 35.32s`)
- Tab Visão Geral: status cards, Hermes check, bridge metrics, RAG categories, skills grid, latência em tempo real
- Tab Inbox Manager: CRUD completo com modal, prioridades, tags, done/delete
- Tab RAG Search: pesquisa por query + categoria, resultados com score
- Tab Ciclo Autónomo: estado + forçar ciclo manual
- 22 comandos bridge todos testados e funcionais ✅

### Fase 3 — Pendente
- Subagentes, Skill Studio, Memory Visualizer

### Fase 4 — Pendente
- 50+ testes E2E, Performance < 50ms, Security audit

### Secção 18 — Pendente
- Login screen + onboarding
- Admin privileges (sudoers)
- Dual-way sync (SSH tunnel)
- Update button 3 etapas
- Skills 100% → MCP tools
- GeekHub packaging

**pdoc:** `~/.hermes/docs/PRD-AionUI-Hermes-Native-Integration.md`
