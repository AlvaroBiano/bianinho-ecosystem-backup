---
name: sac-approved-qa-rag
description: Sistema de Q&As aprovadas como camada prioritária no RAG do SAC Bot — com isolamento por collection e matching Jaccard
triggers:
  - approved qa rag sac
  - q&a aprovada sac bot
  - camada prioritária rag
---

# SAC Approved Q&A — RAG com Camada de Respostas Aprovadas

## O que é

Sistema de 2 camadas no RAG do SAC Bot:
- **Camada 1 (prioritária):** Q&As previamente aprovadas pelo administrador — respondidas com fidelidade
- **Camada 2 (fallback):** Busca vetorial no LanceDB (apostilas)

## Arquitectura

```
Pergunta → Jaccard similarity (threshold 0.35)
         → [Match ≥ 0.35] → Camada 1: Q&A aprovada
         → [Match < 0.35] → Camada 2: LanceDB vetorial
```

## Tabela SQLite

```sql
CREATE TABLE IF NOT EXISTS approved_qa (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    collection      TEXT NOT NULL DEFAULT 'metodo-ten',  -- isolar por assunto
    pergunta        TEXT NOT NULL,
    resposta        TEXT NOT NULL,
    tema            TEXT NOT NULL DEFAULT '',
    aprovado_em     TEXT NOT NULL,
    uso_count       INTEGER DEFAULT 0,
    last_used       TEXT
);

CREATE INDEX IF NOT EXISTS idx_qa_collection ON approved_qa(collection);
```

## Matching: Jaccard > LIKE/keyword

### ❌ NÃO USE matching por palavras-chave (LIKE/OR)
Problema: se a Q&A "O que é o Método TEN?" está guardada e alguém pergunta "Qual é a origem e história do Método TEN?", o LIKE/OR casava pelas palavras "Método TEN" — resposta errada para pergunta errada.

### ✅ USE Jaccard Similarity
```python
STOPWORDS = {'o', 'a', 'os', 'as', 'um', 'uma', 'uns', 'umas', 'e', 'é', 'que', 'de', 'do', 'da', 'em', 'no', 'na', 'se', 'para', 'com', 'por', 'mais', 'ou'}

def _tokenize(texto: str) -> set:
    """Extrai palavras significativas de um texto, excluindo stopwords."""
    return set(w.strip().lower() for w in re.split(r'\W+', texto)
               if len(w.strip()) > 2 and w.strip().lower() not in STOPWORDS)

def _jaccard(s1: str, s2: str) -> float:
    """Retorna similarity score 0.0-1.0 entre dois textos (sem stopwords)."""
    a, b = _tokenize(s1), _tokenize(s2)
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)

def buscar_qa_similar(query: str, top_k: int = 3,
                     collection: str = "metodo-ten") -> list:
    # ...
    # Threshold: 0.45 — rigoroso para evitar perguntas semanticamente diferentes
    return [(sim, r) for sim, r in scored if sim >= 0.45][:top_k]
```

## Parâmetros Importantes

| Parâmetro | Valor | Razão |
|---|---|---|
| `collection` default | `"metodo-ten"` | Isola Q&As de outros assuntos |
| Jaccard threshold | `0.35` | Abaixo disso = pergunta semanticamente diferente |
| `max_tokens` | `500` | Respostas curtas e directas |
| `temperature` | `0.3` | Respostas consistentes |

## Endpoint Admin

```bash
# Salvar Q&A aprovada
POST /admin/qa
{
  "pergunta": "...",
  "resposta": "...",
  "tema": "O que é o Método TEN",
  "collection": "metodo-ten"
}

# Response: { "ok": true, "qa_id": 1, "collection": "metodo-ten" }
```

## No SAC Agent — rag_sac()

```python
def rag_sac(query, top_k=5, historico="", primeiro_nome="",
            conversa_count=0, collection="metodo-ten"):
    qa_results = sac_db.buscar_qa_similar(query, top_k=3, collection=collection)
    if qa_results:
        # Camada 1: usa Q&A aprovada
        return llm_generate_qa(query, qa_results, historico, ...)
    else:
        # Camada 2: LanceDB
        return llm_generate(query, lancedb_results, ...)
```

## Lição Aprendida

1. **LIKE/OR é demasiado permissivo** em corpus pequeno de Q&As — qualquer palavra em comum casava
2. **Jaccard similarity** mede overlap real de vocabulário — muito mais preciso
3. **Collection field** é obrigatório se quiseres isolar por assunto/tema
4. **Fallback para LanceDB** funciona bem quando não há Q&A com threshold alto — a qualidade do RAG vectorial é boa

## Adicionar Facts ao LanceDB

Para atualizar dados (ex: número de terapeutas formados) sem re-processar todos os PDFs:

```python
# Via embed_query do próprio sac_agent — não precisa de sentence-transformers
import sys
sys.path.insert(0, '/home/alvarobiano/.hermes/sac_agent')
from sac_agent import embed_query
import lancedb, hashlib
from datetime import datetime

fact = "O Método TEN já formou mais de 550 psicoterapeutas ao redor do mundo."
emb = embed_query(fact)

db = lancedb.connect('/home/alvarobiano/KnowledgeBase/knowledge_db')
tbl = db.open_table('metodoten')

tbl.add([{
    "text": fact,
    "vector": emb,
    "source": "fatos_metodo_ten.md",
    "category": "metodoten",
    "chunk_index": 0, "total_chunks": 1,
    "filepath": "/home/alvarobiano/.hermes/sac_agent/fatos_metodo_ten.md",
    "language": "pt",
    "chunk_hash": hashlib.md5(fact.encode()).hexdigest(),
    "processed_at": datetime.now().isoformat(),
    "copyright": ""
}])
```

## Ficheiros

- `~/.hermes/sac_agent/sac_db.py` — `salvar_qa_aprovada()`, `buscar_qa_similar()`, `marcar_qa_usada()`, `_jaccard()`, `_tokenize()`
- `~/.hermes/sac_agent/sac_agent.py` — `rag_sac()`, `llm_generate_qa()`, endpoint `/admin/qa`
- `~/.hermes/sac_agent/sac_schema.sql` — schema da tabela `approved_qa`
