---
name: rag-query
description: When and how to query the LanceDB RAG knowledge base — proactive vs. passive, query methods, output format
triggers:
  - user asks for information that could come from books/documents
  - user says "me conta", "pesquisa", "busca", "o que você sabe"
  - user asks "consegue pesquisar no RAG?"
  - any task requiring factual grounding from processed content
  # CRITICAL: content creation triggers — NEVER skip RAG for these
  - user asks to write copy, description, ad, post, email, or any promotional text about Method TEN → MUST consult RAG first
  - user asks to create content about psicotherapy, psychology, marketing, desenvolvimento_pessoal → consult RAG for factual grounding
  - user asks "o que é", "quem pode", "como funciona" about any topic in the knowledge base scope
---

# RAG Query — When and How to Search the Knowledge Base

## Álvaro's Communication Style
**Respostas curtas e directas.** Não expliques o que vais fazer — apenas faz. Se uma pergunta é simples ("consegue pesquisar no RAG?"), a resposta é "Consigo!" e ponto. Só entra em detalhe quando ele pedir.

## Trigger Conditions
- User asks "consegue pesquisar no RAG?" → resposta curta: "Consigo!"
- User asks for information about a topic (health, marketing, psychology, nutrition, etc.)
- User says "me conta", "o que você sabe", "pesquisa", "busca"
- User asks "como funciona" or "o que é" about any domain covered in the knowledge base
- Task requires factual grounding from processed books/documents

## Behavior Rules

### CRITICAL: Content Creation About Method TEN
**Sempre consultar RAG antes de criar conteúdo sobre o Método TEN.** Isso inclui: textos publicitários, descrições, posts, e-mails, landing pages, copies para redes sociais, ou qualquer material que mencione o método, seus pilares, estrutura ou formação.

O Álvaro foi claro: sem consultar o RAG, não escrever nada sobre o Método TEN.

### Proactive vs. Passive
- Pergunta simples de confirmação ("consegue pesquisar no RAG?") → resposta curta, não fazer dump de estado
- Pergunta de conhecimento ("o que sabes sobre X?") → pesquisar e responder com fonte
- **Tarefa de criação de conteúdo sobre Método TEN → consultar RAG primeiro, SEM EXCEÇÃO, mesmo que o Álvaro não peça explicitamente**

### How to Query (MacBook paths)

**Step 1 — Check table row counts:**
```bash
~/.hermes/venv/bin/python -c "
import lancedb
db = lancedb.connect('/Users/alvarobiano/Library/Application Support/hermes/KnowledgeBase/knowledge_db')
resp = db.list_tables()
for t in resp.tables:  # list_tables() → ListTablesResponse, .tables é lista de strings
    print(f'{t}: {db.open_table(t).count_rows():,}')
"
```

**Step 2 — Get table metadata (categories, sources):**
```bash
~/.hermes/venv/bin/python -c "
import lancedb
db = lancedb.connect('/Users/alvarobiano/Library/Application Support/hermes/KnowledgeBase/knowledge_db')
for table_name in ['chunks', 'metodoten']:
    tbl = db.open_table(table_name)
    df = tbl.to_pandas()
    print(f\"{table_name}: {len(df):,} chunks, {df['source'].nunique()} fontes, {df['category'].nunique()} categorias\")
"
```

**Step 3 — For actual search queries,** use `~/KnowledgeBase/hybrid_search.py` which combines vector + BM25 search. The vector search requires an embedding (OpenAI via OpenRouter); BM25 provides keyword fallback.

**⚠️ `execute_code` sandbox:** does NOT have lancedb/pandas installed — always use `~/.hermes/venv/bin/python` for RAG queries.

**Tables available:** `api` (5), `chunks` (72,001), `default` (0), `metodoten` (8,155), `prd_collection` (2)

**Embedding:** OpenAI `text-embedding-3-small` (1536 dim) via OpenRouter.

### RAG Knowledge Base Locations
- **MacBook:** `~/Library/Application Support/hermes/KnowledgeBase/knowledge_db/`
- **Symlink:** `~/KnowledgeBase/` → above path
- **Note:** `~/KnowledgeBase/venv/` is Linux (broken symlinks on Mac) — always use `~/.hermes/venv/bin/python`

### Scope
RAG covers: `desenvolvimento_pessoal`, `marketing`, `comunicacao`, `financas`, `psicologia`, `default`

## What RAG Cannot Do
- Real-time information → use web search
- Private/user-specific data → not in knowledge base
- Very recent events → books up to ~2024

## Output Format (when searching)
1. State briefly that you're searching
2. Provide answer with source attribution (book name)
3. If no results found, say so and offer web-search as fallback
