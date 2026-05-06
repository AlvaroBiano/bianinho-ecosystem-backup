# Pesquisa Automática RAG + Web — Bianinho OS

## Quando Ativar
Esta skill deve ser carregada **em toda conversa** com o Álvaro. O fluxo é:

1. **Pergunta do Álvaro** → carrega esta skill → busca RAG automaticamente
2. Se ele pedir "pesquisa na internet" → busca web também e combina

## Busca RAG (Sempre Automática)

### Comando para buscar:
```bash
~/KnowledgeBase/venv/bin/python ~/.hermes/scripts/rag_search.py "sua pergunta" 5
```

### Implementação do script (`~/.hermes/scripts/rag_search.py`):
```python
#!/usr/bin/env python3
"""BM25 search sobre a tabela metodoten (8.155 chunks)."""
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
```

## Busca Web (Só se Pedido)

### Como buscar:
- `web_search` tool: busca no Google
- `mcp_context_mode_ctx_batch_execute` com navegador

### Exemplos de triggers que pedem web:
- "pesquisa na internet"
- "busca web"
- "vá além dos livros"
- "veja o que tem de mais recente"

## Formato da Resposta Combinada

Quando Álvaro pede RAG + web:

```
🎯 **Sobre [tema] — resposta integrada**

📚 **Dos seus livros ({n} resultados):**
[Resumo do que encontrou nos livros, com nome do livro]

🌐 **Pesquisa web ({n} resultados):**
[Informação complementar da internet, com fonte]

💡 **Análise integrada:**
[Resposta completa combinando as duas fontes, em português, tom direto]
```

## Formato Só RAG

Quando é só RAG:

```
🎯 **Sobre [tema] — dos seus livros ({n} resultados):**

📖 **[Nome do Livro 1]:**
[Contexto relevante]

📖 **[Nome do Livro 2]:**
[Contexto relevante]

💡 **Resumo:**
[Síntese do Bianinho]
```

## Database Stats
- `metodoten`: 8.155 chunks (livros processados)
- `chunks`: 70.501 chunks (banco geral)
- Tabelas disponíveis: `api`, `chunks`, `default`, `metodoten`, `prd_collection`

## Notas Importantes
- Se RAG não encontrar nada → avisa e sugere web search
- Sempre formata como resposta fluida, nunca como lista técnica
- Prioriza livros mais recentes processados
- Limita a 3-5 resultados por fonte para não poluir
