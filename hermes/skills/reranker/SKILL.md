---
name: reranker
description: Re-Ranker para Hybrid Search — usa embeddings existentes para re-ordenar resultados
---

# Re-Ranker — Hybrid Search + Cross-Score

## O que é

Re-ranker que usa os embeddings já calculados para re-ordenar resultados do hybrid search. Combina múltiplos sinais:

1. **Keyword Match** — termos exatos da query aparecem
2. **Term Density** — termos relevantes bem distribuídos
3. **Position Score** — termos aparecem no início do texto
4. **Original Hybrid Score** — mantém o score base

## Arquivo

`~/KnowledgeBase/reranker.py`

## Uso Rápido

```python
import sys
sys.path.insert(0, "~/KnowledgeBase")
from reranker import rerank_query

results = rerank_query(
    query="sua pergunta",
    top_k=5,
    collection="chunks"
)
```

## Uso Avançado

```python
from reranker import ReRanker, get_reranker

rr = get_reranker()

# Configurar pesos personalizados
results = rr.search_with_rerank(
    query="...",
    top_k=10,
    rerank_top_k=100,  # Quantos resultados do hybrid re-rankear
    weights={
        'keyword': 0.4,   # Peso para match exato
        'density': 0.2,    # Peso para densidade
        'position': 0.1,   # Peso para posição
        'original': 0.3     # Peso para score original
    }
)
```

## Parâmetros

| Parâmetro | Padrão | Descrição |
|-----------|--------|-----------|
| `top_k` | 5 | Resultados finais |
| `rerank_top_k` | 50 | Resultados do hybrid a re-rankear |
| `weights` | {k:0.3, d:0.2, p:0.1, o:0.4} | Pesos por sinal |

## Dependências

- `hybrid_search.py` (já existente)
- `rank_bm25` (para hybrid search)
- LanceDB e embedder (já configurados)

NÃO precisa de modelos adicionais — usa embeddings já calculados.
