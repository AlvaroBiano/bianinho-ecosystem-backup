---
name: rag-query
description: When and how to query the LanceDB RAG knowledge base — proactive vs. passive, query methods, output format
triggers:
  - user asks for information that could come from books/documents
  - user says "me conta", "pesquisa", "busca", "o que você sabe"
  - any task requiring factual grounding from processed content
---

# RAG Query — When and How to Search the Knowledge Base

## Trigger Conditions
- User asks for information about a topic (health, marketing, psychology, nutrition, etc.)
- User says "me conta", "o que você sabe", "pesquisa", "busca"
- User asks "como funciona" or "o que é" about any domain covered in the knowledge base
- Task requires factual grounding from processed books/documents

## Behavior Rules

### Proactive vs. Passive — ALWAYS Clarify
When user asks something that could be answered from RAG, **ask first** or **search proactively and report the approach**.

**Do NOT assume** — if you search automatically, say so. If you don't search, make it explicit when the answer could come from RAG.

### How to Query
Use the RAG HTTP service if running, or query LanceDB directly via `~/KnowledgeBase/venv/bin/python`.

**Preferred: HTTP service (if running on port 3101):**
```bash
curl "http://localhost:3101/query?q=sua+pergunta&k=5"
```

**Direct LanceDB query (Python 3.14 venv):**
```python
~/KnowledgeBase/venv/bin/python -c "
import lancedb
db = lancedb.connect('/home/alvarobiano/KnowledgeBase/knowledge_db')
tbl = db.open_table('metodoten')
results = tbl.search('sua pergunta').limit(5).to_list()
for r in results:
    print(r['source'], ':', r['text'][:200])
"
```

### Search Endpoint — port 3101
RAG service runs on port 3101 with endpoints:
- `GET /query?q=<pergunta>&k=<num>` — search
- `GET /health` — status check

### Scope
RAG covers these categories:
- `desenvolvimento_pessoal` — health, nutrition, psychology, self-improvement
- `marketing` — copywriting, marketing strategies
- `comunicacao` — communication, storytelling
- `financas` — financial books
- `psicologia` — psychology
- `default` — technical/programming books

## What RAG Cannot Do
- Real-time information → use web search
- Private/user-specific data → not in knowledge base
- Very recent events → books up to ~2024

## Output Format
When answering from RAG:
1. State that you're searching the knowledge base
2. Provide answer with source attribution (book name)
3. If no results found, say so and offer web-search as fallback
