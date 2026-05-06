---
name: hermes-session-consolidation
description: Extrai facts estruturados dos eventos do Hermes Sessions DB e adiciona ao LanceDB — consolidação episódica→semântica.
---

# Hermes Session Consolidation

## Descrição
Script de consolidação diária que extrai facts estruturados dos eventos do Hermes Sessions DB e os adiciona ao LanceDB. Implementa a Fase 2 da arquitectura brain-inspired de memória (consolidação episódica→semântica, princípio CLS de McClelland).

Baseado nos 6 Domínios Cognitivos do Synthius-Mem:
- **biografia**: identidade, papéis
- **comunicação**: preferências, estilo
- **projectos**: activos, decisões
- **instruções**: directivas, regras, comandos
- **social**: relações, equipa
- **memória**: aprendizados, erros corrigidos, facts técnicos

## Ficheiros
- Script: `~/KnowledgeBase/consolidate_session.py`
- Sessions DB: `~/.hermes/hermes_sessions.db`
- LanceDB: `~/KnowledgeBase/knowledge_db/chunks.lance`
- Recall script: `~/KnowledgeBase/recall.py` (Phase 3 - cross-session binding)
- venv: `~/KnowledgeBase/venv/bin/python`

## Uso

```bash
# Dry-run (ver facts sem adicionar)
~/KnowledgeBase/venv/bin/python consolidate_session.py --dry-run --hours 24

# Consolidação real (últimas 8 horas)
~/KnowledgeBase/venv/bin/python consolidate_session.py --hours 8

# Consolidação completa (últimas 24 horas)
~/KnowledgeBase/venv/bin/python consolidate_session.py
```

## Automação (Cron)
Job diário criado automaticamente:
```
cronjob --action=create \
  --name="daily-session-consolidation" \
  --prompt="cd ~/KnowledgeBase && ~/KnowledgeBase/venv/bin/python consolidate_session.py --hours 24" \
  --schedule="0 23 * * *"
```

## ⚠️ Armadilhas Críticas (aprendidas na prática)

### LanceDB Schema — formato de vectores
Os vectores devem ser **flat `[float]`** (não `[[float]]`) e campos escalares devem usar o schema exacto:
```python
from lancedb.embeddings import openai
from lancedb.schema import Vector, Float32, Stone

# NÃO usar table.to_pandas() — pandas NÃO existe no venv
# USAR table.to_arrow() para queries

# Ao adicionar, garantir vectors são [float] não [[float]]
record["vector"] = embedding.tolist()  # flat list
```

### Deduplicação — Jaccard não hash exacto
Hash exacto perde facts relacionados mas com texto ligeiramente diferente.
Usar **Jaccard similarity 0.75** em vez de dedup exacto:
```python
def jaccard_similarity(a, b, threshold=0.75):
    a_words = set(a.lower().split())
    b_words = set(b.lower().split())
    if not a_words | b_words: return 1.0
    score = len(a_words & b_words) / len(a_words | b_words)
    return score >= threshold
```

### Saliência Emocional — facts com peso
Prioritizar facts de eventos de alto impacto:
```python
SALIENCE = {
    "finding": 2.0, "decision": 2.5, "error": 3.0,
    "rule": 2.0, "preference": 1.5, "api_key": 2.0,
    "correction": 1.5, "update": 1.0, "default": 0.5
}
```

### venv Python — binário específico
Usar sempre `~/KnowledgeBase/venv/bin/python`, não `python3` ou `python` do sistema.

## Verificação
```bash
cd ~/KnowledgeBase && ~/KnowledgeBase/venv/bin/python -c "
import lancedb, pyarrow as pa
db = lancedb.connect('knowledge_db')
tbl = db.open_table('chunks').to_arrow()
from collections import Counter
cats = Counter(tbl.column('category').to_pylist())
print('Total:', tbl.num_rows, '| Categories:', dict(cats))
"
```

## Recall (Phase 3 — Cross-session)
```bash
# Fact retrieval durante conversas
~/KnowledgeBase/venv/bin/python recall.py "query" [dias] [top_k]
```
