---
name: query-expander
description: Query Expansion — expande perguntas do usuário para buscas mais inteligentes e ricas
---

# Query Expansion — Busca Inteligente

## O que é

Expande perguntas do usuário em múltiplas variações para capturar mais contexto antes de buscar no RAG.

**Estratégias:**
1. **LLM Expansion** — usa MiniMax para gerar variações semânticas (requer API key)
2. **Template Expansion** — templates por contexto (preço, duração, etc.)
3. **Keyword Expansion** — extrai keywords + sinônimos
4. **Domain Expansion** — adiciona contexto de domínio

## Arquivo

`~/KnowledgeBase/query_expander.py`

## Uso Rápido

```python
import sys
sys.path.insert(0, "~/KnowledgeBase")
from query_expander import expand_query

# Só expandir
expansions = expand_query("quanto custa o curso", verbose=True)

# Expandir + Buscar
results = expand_query(
    query="como funciona a formação",
    context="metodoten",  # Contexto de domínio
    search=True,
    collection="chunks",
    top_k=5
)
```

## Parâmetros

| Parâmetro | Padrão | Descrição |
|-----------|--------|-----------|
| `query` | — | Pergunta original |
| `context` | None | Domínio: "metodoten", "sac", etc. |
| `search` | False | Também buscar no RAG |
| `collection` | "chunks" | Coleção para buscar |
| `top_k` | 5 | Resultados |

## Para SAC/Atendimento

```python
# Contextos úteis para atendimento:
results = expand_query(
    query="pergunta do cliente",
    context="metodoten",  # Usa expansões específicas de curso/formação
    search=True,
    collection="metodoten",  # Busca só na coleção do SAC
    top_k=5
)
```

## Contexto de Domínio

Expansões automáticas para:
- **metodoten** — termos de formação, terapia, Método TEN
- **marketing** — termos de vendas, funil, tráfego
- **financas** — termos de investimento, orçamento
- **produto** — termos de cursos, livros, serviços
