---
name: context-aware-delegation
description: Dar a cron jobs e sub-agentes isolados contexto completo da sessão principal via query direta ao Hermes sessions DB.
hermes-adapted: true
hermes-version: "1.0.0"
---

# Context-Aware Delegation (Hermes)

## Estado de Adaptação

✅ Adaptado para Hermes — 20/04/2026
- `sessions_history` → `session_search()` + query direta SQLite
- `sessions_spawn` → `delegate_task()`
- Cron JSON → `cronjob` tool
- Delivery → `send_message()`

## O Problema

Cron jobs e sub-agentes executam em sessões isoladas — modelos baratos mas sem ver o contexto da conversa principal. Alternativa (tudo no main session) = caro.

## A Solução

Cron jobs e sub-agentes consultam diretamente o `hermes_sessions.db` para obter contexto completo da sessão principal. Conseguem contexto rico a custo MiniMax.

```
Custo por execução:
  Main session (MiniMax):         ~$0.01-0.05
  Cron isolado (MiniMax):          ~$0.001-0.01
  Contexto:                        ✅ Completo
  Poupança:                       ~10x
```

## Comandos Principais

### session_search (para contexto)

```bash
# No prompt do cron job, usar:
session_search(query="o que fizemos hoje", limit=10)

# Ou query direta SQLite:
python3 -c "
import sqlite3
conn = sqlite3.connect('$HOME/.hermes/hermes_sessions.db')
cur = conn.cursor()
cur.execute(\"SELECT role, content FROM sessions WHERE session_key LIKE '%main%' ORDER BY ROWID DESC LIMIT 20\")
for row in cur.fetchall(): print(row[0], ':', row[1][:200])
"
```

### delegate_task (para sub-agentes)

```python
# Sub-agente com contexto:
delegate_task(
  goal="Analisar o código do projeto X. Primeiro usa session_search para entender o contexto da conversa sobre X.",
  context="Projeto: Método TEN | Pilares: auto-evolução, proatividade",
  toolsets=['terminal', 'file', 'web']
)
```

## Padrão: Morning Report com Contexto

```bash
# Criar cron job que consulta sessão principal antes de executar
# Prompt inclui:
#   1. session_search("o que aconteceu ontem", limit=20)
#   2. ler ~/self-improving/memory/memory.md
#   3. executar tarefa (report, email, etc.)
#   4. send_message() com resultado
```

## Exemplo Real: Morning Briefing Cron

```bash
# Criar via cronjob tool:
# Schedule: 08:00 daily
# Prompt: "1. session_search('Álvaro Bianinho sessão', limit=30)
#         2. ler ~/self-improving/memory/memory.md
#         3. Gerar briefing com:
#            - Resumo overnight (do session_search)
#            - Tarefas pendentes (da wake-state)
#            - Dados relevantes (da RAG knowledge base)
#         4. send_message(target='telegram', message=briefing)"
```

## Fluxo

```
1. Cron job dispara (modelo barato)
         ↓
2. session_search() → consulta sessão principal
         ↓
3. Lê memory files → 获取 contexto persistente
         ↓
4. Executa tarefa com contexto completo
         ↓
5. send_message() → entrega resultado
```

## Métricas de Custo

| Abordagem | Modelo | Contexto | Custo/Execução |
|-----------|--------|----------|----------------|
| Main session | MiniMax | Full | ~$0.02 |
| Cron isolado (cego) | MiniMax | Nenhum | ~$0.002 |
| **Cron + context-aware** | **MiniMax** | **Full** | **~$0.002** |

## Integração com o Bianinho OS

- **wake-state**: tasks persistentes disponíveis via `~/.hermes/wake-state/tasks.json`
- **Hybrid Search**: `~/KnowledgeBase/hybrid_search.py` para contexto vetorial
- **Memory**: `~/self-improving/memory/memory.md` para HOT memory
- **RAG**: LanceDB em `~/KnowledgeBase/knowledge_db/` para conhecimento domain-specific

## Scripts de Suporte

### Query Context Helper

```python
#!/usr/bin/env python3
"""Helper para cron jobs obterem contexto da sessão principal."""
import sqlite3, os, sys
from pathlib import Path

def get_recent_context(limit=20, session_filter="main"):
    db_path = Path.home() / ".hermes" / "hermes_sessions.db"
    if not db_path.exists():
        return "No session DB found."
    
    conn = sqlite3.connect(str(db_path))
    cur = conn.cursor()
    cur.execute(f"""
        SELECT role, content FROM sessions 
        WHERE session_key LIKE '%{session_filter}%'
        ORDER BY ROWID DESC LIMIT {limit}
    """)
    rows = cur.fetchall()
    conn.close()
    
    if not rows:
        return "No recent context found."
    
    return "\n".join([f"[{r[0]}] {r[1][:300]}" for r in reversed(rows)])

if __name__ == "__main__":
    limit = int(sys.argv[1]) if len(sys.argv) > 1 else 20
    print(get_recent_context(limit))
```

Guardar em: `~/.hermes/skills/context-aware-delegation/scripts/get_context.py`

## Casos de Uso

1. **Morning reports** — o que aconteceu overnight
2. **Sub-agentes de pesquisa** — com contexto do projeto
3. **Event handlers** — com memória da conversa
4. **Periodic checks** — urgentes vs. normais baseado em contexto

## Cron Jobs Criados com Este Padrão

| Job | Schedule | Descrição |
|-----|----------|-----------|
| **Bianinho Morning Briefing** | `0 8 * * 1-5` | Morning briefing: contexto Telegram + wake-state tasks + HOT memory |

Job ID: `5cc5608e58de` — criado 20/04/2026

## Autores
---

## ◆ Context Switch Optimizer — Labeled Subsection

**Source**: `memory/context-switch-optimizer/`

Detects "continuous / gradual drift / hard switch" using keyword Jaccard similarity, weak-association substrings, and time decay. Monitors tokens, triggers compression and cleanup.

### Core Actions
| Action | Condition | Behavior |
|--------|-----------|----------|
| `load_memory` | No current topic and no history | Create topic, optionally load from `memory/topic` |
| `continuous` | Similarity >= `similarity_threshold` (0.7) | Append to history, no compression |
| `drift_compress` | Similarity in [continuity_threshold, similarity_threshold) | Compress weakly related historical turns |
| `switch_context` | Similarity < continuity_threshold (0.35) | Hard switch, change memory, increment `switch_count` |

### Configuration (config.json)
- `similarity_threshold`: 0.7 (continuous vs drift boundary)
- `continuity_threshold`: 0.35 (drift vs switch boundary)
- `compress_relevance_threshold`: 0.3 (below this in drift_compress = compressed)
- `token_limit`: 80000, `compression_threshold`: 56000

### Environment Variables
| Variable | Maps To | Notes |
|----------|---------|-------|
| `CONTEXT_HISTORY_SIZE` | `max_topic_history` | 1-100 |
| `MEMORY_SEARCH_DEPTH` | `search_depth` | 1-3 |
| `TOKEN_OPTIMIZER_ENABLED` | `token_optimization.enabled` | true/false |
| `CONTEXT_SWITCH_LOG_LEVEL` | `log_level` | DEBUG/INFO/WARNING/ERROR |

### State File
- `~/.hermes/memory/context_switch_state.json` — TopicSummary format with `is_compressed` flag

### Entry Point
```python
python3 context-switch-optimizer.py [--config path] --process|--status|--reset|--test
```

---

## ◆ Contextual Recall — Labeled Subsection

**Source**: `knowledge-base/contextual-recall/`

Context-aware memory recall during conversations: domain detection, re-ranking, session cache.

### When to Use
- Álvaro mentions specific topics (Maryanne, TEN, memory, autonomy)
- Conversation changes domain (from projects to instructions)
- To verify facts before responding about preferences or history
- After long topics: "let me check what we know about X"

### API
```python
from contextual_recall import contextual_recall, format_contextual_facts, clear_cache

facts = contextual_recall("query", days=7, top_k=5)
print(format_contextual_facts(facts))
```

### Parameters
- `query` (str): conversation context — more specific = better
- `days` (int, default=7): only facts from last N days
- `top_k` (int, default=5): number of facts to return
- `force_all` (bool, default=False): includes facts outside consolidation

### Auto-Domain Detection
```
biografia    → words: álvaro, maryanne, brasileiro, psicoterapeuta
comunicação → words: resposta, prefere, estilo, directo, tom, linguagem
instruções  → words: orquestrador, autonomia, liberdade, decidir, regra
memória     → words: memória, memory, recall, facts
projectos   → words: ten, apc, método, formação, curso, negócio
social      → words: maryanne, esposa, equipa, estudantes
```

### Proactive Recall Pattern
```python
monitor = ProactiveRecall(silence=True)
awareness = monitor.process("user message")
if awareness.triggered:
    context = monitor.format_for_context(awareness)
    # inject context into response
```

### Files
- `~/KnowledgeBase/proactive_recall.py` — ProactiveRecall engine
- `~/KnowledgeBase/contextual_recall.py` — domain detection + re-rank + cache
- `~/KnowledgeBase/recall.py` — base (no cache, no re-rank)
- `~/KnowledgeBase/consolidate_session.py` — nocturnal cron job

### Gotchas
- Cache is per-process — does not persist between separate terminal calls
- LanceDB queries: ~2-3s first call (cold start), cache helps on repeated calls
- `ModuleNotFoundError: No module named 'proactive_recall'` → `cd ~/KnowledgeBase && source venv/bin/activate`

---

## ◆ Context Management Context Save — Labeled Subsection

**Source**: `memory/context-management/`

Context serialization and knowledge management for long-running agent sessions.

### Core Concept
Serialize and restore conversation context between sessions. Handles checkpointing, state recovery, and cross-session continuity.

### Use Cases
- Save mid-session state before context compression
- Restore context after interruptions
- Cross-session memory persistence

### Key Patterns
- State stored as portable JSON-compatible format
- Supports incremental saves (not full context dump each time)
- Version-tagged for migration compatibility

---

**Autores**

- Hermes: Bianinho adapt. 20/04/2026
