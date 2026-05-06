---
name: pesquisa-automatica-rag
description: Busca automática no RAG LanceDB em todas as conversas com o Álvaro — BM25 sobre 8k+ chunks dos seus livros. Inclui combinação com busca web quando pedido.
triggers:
  - pergunta do Álvaro sobre qualquer tema
  - "me conta sobre"
  - "o que você sabe sobre"
  - "busca no RAG"
related_skills:
  - rag-book-processor
  - rag-query
---

# Pesquisa Automática RAG + Web — Bianinho OS

## Quando Ativar

**Carregar em toda conversa com o Álvaro.** O fluxo é:

1. **Pergunta do Álvaro** → busca RAG automaticamente (sempre)
2. Se ele pedir "pesquisa na internet" → busca web + combina com RAG

## Busca RAG (Automática)

### Comando:
```bash
~/KnowledgeBase/venv/bin/python ~/.hermes/scripts/rag_search.py "sua pergunta" 5
```

### Script: `scripts/rag_search.py`
- BM25 sobre a tabela `metodoten` (8k+ chunks)
- Carrega todos os chunks em memória → busca ~1-2s
- Parâmetros: `query` (string), `top_k` (default: 5)

### Tabelas disponíveis:
| Tabela | Chunks | Conteúdo |
|--------|--------|----------|
| `metodoten` | ~8.155 | Livros processados (Método TEN, saúde, marketing) |
| `chunks` | ~70.501 | Banco vetorial geral |

## Busca Web (Só se Pedido)

**Triggers que ativam web search:**
- "pesquisa na internet"
- "busca web"
- "vá além dos livros"
- "veja o que tem de mais recente"
- "pesquise"

**Como buscar:** usar `web_search` tool ou `mcp_context_mode_ctx_batch_execute`.

## Formato da Resposta

### RAG + Web (quando pedido):
```
🎯 **Sobre [tema] — resposta integrada**

📚 **Dos seus livros ({n} resultados):**
[Resumo do que encontrou nos livros]

🌐 **Pesquisa web:**
[Informação complementar da internet]

💡 **Análise integrada:**
[Resposta completa combinando as duas fontes]
```

### Só RAG:
```
🎯 **Sobre [tema] — dos seus livros ({n} resultados):**

📖 **[Nome do Livro 1]:**
[Contexto relevante]

💡 **Resumo:**
[Síntese do Bianinho]
```

## PITFALLS

### gh CLI não funciona (TypeError)
`gh auth status` dá `TypeError: Cannot read properties of undefined`. **NÃO usar `gh` CLI** — usar `curl` direto com token do `.netrc`.

### GitHub API sem token → só repos públicos
Sem PAT autenticado, `https://api.github.com/users/AlvaroBiano/repos` devolve apenas repos públicos.
**Verificar:** `curl "https://api.github.com/users/AlvaroBiano/repos?per_page=100"` — se `{"message": "Bad credentials"}`, sem token.

## Notas
- Se RAG não encontrar nada → avisa e sugere web search
- Formatar como resposta fluida, nunca lista técnica
- Limitar a 3-5 resultados por fonte
- O script `rag_search.py` é read-only (não modifica o banco)
