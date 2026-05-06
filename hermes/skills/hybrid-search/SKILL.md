---
name: hybrid-search
description: Hybrid Search — busca vetorial + BM25 no LanceDB para resultados superiores
---

# Hybrid Search — LanceDB + BM25

## O que é

Hybrid Search combina dois métodos de busca:

1. **Similarity Search (vetorial)** — captura contexto semântico ("saúde emocional" encontra "bem-estar")
2. **BM25 (keyword)** — captura correspondência exata de palavras

Resultado:.pega o melhor dos dois mundos.

## Arquivo

`~/KnowledgeBase/hybrid_search.py`

## Uso Rápido

```python
import sys
sys.path.insert(0, "~/KnowledgeBase")
from hybrid_search import hybrid_query

results = hybrid_query(
    query="sua pergunta aqui",
    top_k=5,
    collection="chunks",  # ou "metodoten" para SAC
    vector_weight=0.5,    # peso da busca vetorial
    bm25_weight=0.5       # peso BM25
)
```

## Parâmetros

| Parâmetro | Padrão | Descrição |
|-----------|--------|-----------|
| `query` | — | Pergunta/textp para buscar |
| `top_k` | 5 | Número de resultados |
| `collection` | "chunks" | Nome da tabela/coleção |
| `vector_weight` | 0.5 | Peso da busca vetorial (0-1) |
| `bm25_weight` | 0.5 | Peso do BM25 (0-1) |
| `category` | None | Filtrar por categoria |

## Exemplo Completo

```python
from hybrid_search import HybridSearch

hs = HybridSearch("chunks")
hs.build_index()  # Constrói índice BM25 (primeira vez)

results = hs.search(
    query="como controlar ansiedade",
    top_k=10,
    vector_weight=0.6,
    bm25_weight=0.4,
    category="psicologia"
)

for r in results:
    print(f"[{r['rank']}] {r['source']} | {r['text'][:200]}")
```

## Integração com Agente

Para usar no agente SAC:

```python
# No system prompt do agente SAC:
# Herramienta: hybrid_search.search(query=..., collection="metodoten")
# Regla: SIEMPRE buscar en el RAG antes de responder
```

## CLI

```bash
cd ~/KnowledgeBase
~/KnowledgeBase/venv/bin/python3 hybrid_search.py \
    --query "como controlar ansiedade" \
    --top-k 5 \
    --table chunks \
    --vw 0.5 --bw 0.5
```

## Instalação

```bash
uv pip install rank-bm25 --python ~/KnowledgeBase/venv/bin/python3
```

## Alternative: Pure Python BM25 (no dependencies)

For cases where `rank_bm25` is not installed, or for simple standalone use:

**Script**: `scripts/rag_search.py`

```python
#!/usr/bin/env python3
"""BM25 search over LanceDB — pure Python, no rank_bm25 needed.
Works with: ~/KnowledgeBase/knowledge_db (metodoten, 8k+ chunks).
Usage: python rag_search.py "query" [top_k]
"""
import sys, re
from collections import Counter
import lancedb

DB_PATH = "/home/alvarobiano/KnowledgeBase/knowledge_db"

def build_index():
    db = lancedb.connect(DB_PATH)
    tbl = db.open_table("metodoten")
    df = tbl.to_pandas()
    k1, b = 1.5, 0.75
    N = len(df)
    corpus, doc_lens, doc_freqs = [], [], Counter()
    for text in df['text']:
        tokens = re.findall(r'\b\w+\b', str(text).lower())
        corpus.append(tokens)
        doc_lens.append(len(tokens))
        for term in set(tokens):
            doc_freqs[term] += 1
    avgdl = sum(doc_lens) / max(N, 1)
    return df, corpus, doc_lens, doc_freqs, avgdl, k1, b, N

def bm25_search(query, df, corpus, doc_lens, doc_freqs, avgdl, k1, b, N, top_k=5):
    query_tokens = re.findall(r'\b\w+\b', query.lower())
    scores = []
    for i, doc in enumerate(corpus):
        score = 0.0
        for term in query_tokens:
            if term not in doc_freqs:
                continue
            df_val = doc_freqs[term]
            idf = max(0, (N - df_val + 0.5) / (df_val + 0.5))
            tf_val = sum(1 for t in doc if t == term)
            numerator = tf_val * (k1 + 1)
            denominator = tf_val + k1 * (1 - b + b * doc_lens[i] / max(avgdl, 0.001))
            score += idf * numerator / max(denominator, 0.001)
        scores.append((i, score))
    ranked = sorted(scores, key=lambda x: x[1], reverse=True)[:top_k]
    return [(df.iloc[i]['source'], df.iloc[i]['text'], df.iloc[i]['category'], score)
             for i, score in ranked if score > 0]

def search(query, top_k=5):
    df, corpus, doc_lens, doc_freqs, avgdl, k1, b, N = build_index()
    return bm25_search(query, df, corpus, doc_lens, doc_freqs, avgdl, k1, b, N, top_k)

if __name__ == "__main__":
    query = sys.argv[1] if len(sys.argv) > 1 else "vitamina D"
    top_k = int(sys.argv[2]) if len(sys.argv) > 2 else 5
    results = search(query, top_k)
    print(f"\n🔍 Busca: '{query}' — {len(results)} resultados\n")
    for i, (source, text, category, score) in enumerate(results, 1):
        print(f"[{i}] 📖 {source} (score={score:.2f}) [{category}]")
        print(f"    {text[:300]}...")
        print()

# Run with: ~/KnowledgeBase/venv/bin/python ~/.hermes/scripts/rag_search.py "jejum intermitente" 3
```

**Key difference from `rank_bm25` approach**: Loads ALL chunks into memory at once (works for 8k-70k chunks). The `rank_bm25` library streams chunks. For larger sets, consider streaming approach.

## ⚠️ Gotcha: rank_bm25 API

A API do `BM25Okapi` é diferente do esperado:

```python
# ERRADO - get_top_n retorna lista de tokens, não scores
scores = bm25.get_top_n(query, k)

# CERTO - usar get_scores + ordenação manual
all_scores = bm25.get_scores(query_tokens)  # query_tokens = tokenize(query)
sorted_indices = sorted(range(len(all_scores)), key=lambda i: all_scores[i], reverse=True)[:k]
bm25_scores = [(i, float(all_scores[i])) for i in sorted_indices]
```

`get_top_n` é para quando você já tem os documentos — retorna os documentos tokenizados, não os scores.
