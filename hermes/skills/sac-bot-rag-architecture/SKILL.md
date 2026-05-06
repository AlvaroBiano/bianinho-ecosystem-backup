---
name: sac-bot-rag-architecture
description: SAC Bot RAG pipeline architecture — how Q&A approved and LanceDB are combined as both sources for the LLM, not used alternatively
version: 1.0.0
date: 2026-04-25
tags: [sac-bot, rag, lancedb, architecture]
---

# SAC Bot RAG Architecture

## Context

The SAC Bot (Método TEN chatbot) uses a 2-source RAG pipeline. The original implementation had a critical flaw: Q&A approved and LanceDB were used **alternatively** (one or the other), not **combined**. This meant approved Q&As were rarely used even when they existed in the database.

**Date:** 2026-04-25
**Files:** `~/.hermes/sac_agent/sac_agent.py`, `~/.hermes/sac_agent/sac_db.py`

---

## Architecture

### Pipeline: Both Sources COMBINED (not alternative)

```
User Query
    │
    ▼
┌─────────────────────────┐
│ sac_db.buscar_qa_similar│  ← Jaccard keyword search (threshold 0.20)
│ Returns: up to 5 Q&As   │
└────────┬────────────────┘
         │
         ▼
┌─────────────────────────┐
│ embed_query()           │  ← Vector embedding
│ LanceDB.search()        │  ← top_k=5 chunks from metodoten collection
└────────┬────────────────┘
         │
         ▼
┌──────────────────────────────────┐
│ llm_generate_combined()          │
│ Receives: qa_results + rag_chunks│
│ Q&A = preferred base             │
│ RAG chunks = complement          │
└──────────────────────────────────┘
```

### Old (WRONG) Architecture
```
if qa_results:
    use Q&A only (return)    ← Q&A exclusive, LanceDB ignored
else:
    use LanceDB only          ← fallback, not combined
```

### New (CORRECT) Architecture
```
qa_results = buscar_qa_similar(...)     ← always run
rag_chunks = LanceDB.search(...)      ← always run
llm_generate_combined(qa_results, rag_chunks, ...)  ← always combined
```

---

## Key Parameters

| Parameter | Value | Reason |
|-----------|-------|--------|
| Jaccard threshold | 0.20 | Original 0.45 was too strict — "Como posso me matricular" ≠ "Como faço pra me matricular" at 45% |
| top_k Q&A | 5 | More candidates at low threshold |
| top_k RAG | 5 | Chunks from metodoten LanceDB collection |

---

## Files Reference

### `sac_agent.py`
- `rag_sac()` — main pipeline, always combines both sources
- `llm_generate_combined()` — LLM call with both sources in context
- `embed_query()` — gets vector embedding for query

### `sac_db.py`
- `buscar_qa_similar()` — Jaccard-based Q&A search against `approved_qa` table
- `_jaccard()` — token overlap similarity (0.0-1.0)
- `_tokenize()` — splits text, removes stopwords

### `sac_leads.db`
- `approved_qa` — hand-approved Q&A pairs (92 entries)
- `conversas` — conversation history per lead
- `leads` — lead records with metadata
- `avaliacoes` — star ratings

---

## RAG Collections

| Collection | Contents |
|------------|----------|
| `metodoten` | 6,559 chunks from apostilas, books, marketing docs |

---

## Critical Debugging Insight (2026-04-25)

**Problem:** LLM saying "não tenho essa informação específica" even when RAG found related content.

**Root cause:** Two issues combined:
1. `max_tokens=600` too low — HTML responses with CTAs got cut off
2. System prompt instructed LLM to be **defensive** — refuse if content not 100% exact match

**Diagnosis approach:**
```sql
-- Find leads with "não tenho" in their conversation
SELECT c.*, l.nome FROM conversas c JOIN leads l ON c.lead_id = l.id
WHERE c.mensagem_bot LIKE '%não tenho%';
```

**Fix applied (sac_agent.py):**
```python
# Patch 1: max_tokens 600 → 1200 in llm_generate_combined()
# Line ~415: max_tokens=1200

# Patch 2: Remove "não tenho essa informação específica" from system prompt
# Replace with: "use conteúdo RELACIONADO para formular resposta"
# Applied to: llm_generate(), llm_generate_qa(), llm_generate_combined()
```

**Key principle:** When RAG finds related content but LLM refuses → **prompt issue, not RAG issue**. The LLM was being too defensive. Fix: instruct it to USE related content instead of admitting ignorance.

**Verification:**
```bash
# Test via API
curl -s "http://localhost:5123/webhook/sac?lead_id=10063" | jq
```

**Commit:** `78ad135` / `1e803a2` (bianinho-cerebro)

## Related Skills
- `sac-agent-architecture` — full SAC Bot system overview
- `sac-rag-qa-workflow` — Q&A approval workflow
