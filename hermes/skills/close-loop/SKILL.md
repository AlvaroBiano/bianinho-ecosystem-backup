---
name: close-loop
description: End-of-session workflow para o Hermes — ship state, consolidar memória, aplicar self-improvements, preparar outputs. Safety gates para operações externas.
hermes-adapted: true
hermes-version: "2.1.1"
---

# Close Loop (Hermes)

Use when the user says "wrap up", "close session", "end session", or when a significant work session concludes.

Run four phases in order and return one consolidated report.

## Trigger Phrases

- "wrap up"
- "close session"
- "end session"
- "close out this task"
- `/wrap-up`

## 4 Phases

### Phase 1: Ship State

Execute:
1. `git status` em cada repo tocado
2. Se há mudanças sem commit → commit com mensagem descritiva
3. Se push é permitido por política → push; caso contrário, reportar ready-to-push
4. Validar placement e naming de ficheiros criados
5. Mover ficheiros misplaced (`.md`, `.docx`, `.pdf`, `.xlsx`, `.pptx`) para docs
6. Detetar deploy scripts → executar só se deploy aprovado
7. Reconciliar task tracking: fechar completados, marcar órfãos

### Phase 2: Consolidate Memory

**Two passes:**

**Pass A — Candidate extraction:**
1. Extrair aprendizagens do transcript, output de comandos, e diffs
2. Classificar: working, episodic, semantic, procedural
3. Normalizar para one-fact-per-line

**Pass B — Verification:**
1. Validar evidência e proveniência
2. Dedupe contra memória existente
3. Check de contradições antes de escrever
4. Aplicar scoring, confidence, retention, sensitivity

**Memory record schema:**
```json
{
  "id": "mem_<hash>",
  "type": "episodic|semantic|procedural",
  "statement": "facto verificável",
  "evidence": "source command/log/path",
  "confidence": "low|medium|high",
  "sourceStep": "phase.step",
  "createdAt": "ISO-8601",
  "status": "active|needs-review|expired"
}
```

**Retention:**
| Type | TTL | Notes |
|------|-----|-------|
| Episodic | 14 days | Session history, auto-expire unless promoted |
| Semantic | 180 days | Stable facts, renew on reuse |
| Procedural | 365 days | Reusable workflow patterns |
| Working | 0 days | Never persist |

### Phase 3: Review & Apply Improvements

Identificar:
- Skill gaps
- Friction
- Missing knowledge
- Automation opportunities

Aplicar low-risk improvements imediatamente:
1. Update `USER.md` or relevant rule files
2. Save stable insights com confidence labels
3. Draft skill specs para padrões repetitivos
4. Commit improvements separadamente quando possível

Se nada aplicável: `Nothing to improve`

### Phase 4: Publish Queue

Scan para material publicável:
- Debugging story com lição clara
- Padrão técnico reutilizável
- Milestone ou release-worthy update
- Educational walkthrough

Se existe conteúdo:
1. Create drafts under `Drafts/<slug>/`
2. Propose first post e schedule
3. **Não** auto-post a menos que explícito

Se nada: `Nothing worth publishing`

## Design Principles

- **Memória como sistema**: working, episodic, semantic, procedural
- **Escrever memória só com evidência e confiança**
- **Preferir ações idempotentes e outputs determinísticos**
- **High-impact side effectsgated**
- **Memória auditable, reversível, minimamente invasiva**

## Safety Gate Matrix

| Action | Allowed | Ask | Blocked |
|--------|---------|-----|---------|
| Commit | Repo changed + message clear | Unclear scope | Repo locked |
| Push | Explicit request | Ambiguous policy | User says no |
| Deploy | Explicit request | Target unclear | No script |
| Publish | Explicit request | — | No approval |

## Output Contract

Return two artifacts:

**Artifact A — Human-readable report:**
```
1. Ship State
2. Memory Writes (destination + item + confidence + evidence)
3. Findings (applied)
4. No action needed
5. Publish queue
6. Blocked items (only if any)
```

**Artifact B — Machine-readable JSON:**
```json
{
  "mode": "execute|dry-run",
  "shipState": {},
  "memoryWrites": [],
  "findingsApplied": [],
  "noActionNeeded": [],
  "publishQueue": [],
  "blockedItems": [],
  "kpis": {
    "noiseRate": 0,
    "reuseRate": 0,
    "correctionRate": 0
  }
}
```

## KPI Tracking

- `noiseRate = rejected_candidates / total_candidates`
- `reuseRate = reused_memories / total_memories_read`
- `correctionRate = corrected_memories / total_writes`

## Hermes Integration

- **Phase 1 (git)**: ✅ funciona no Hermes
- **Phase 2 (memory)**: Alinha com `~/self-improving/` — usar memory schema
- **Phase 3 (improve)**: Alinha com `auto_improver.py`
- **Phase 4 (output)**: Drafts vão para `~/.hermes/drafts/`
- **Design principles**: Adoptar integralmente

## Components

- `components/01-design-principles.md` — Princípios e action gates
- `components/02-phase-1-ship-state.md` — Git workflow
- `components/03-phase-2-memory.md` — Memory schema e classification
- `components/04-phase-3-4-and-output.md` — Improve + publish + output contract
- `references/memory-frameworks.md` — External frameworks (CoALA, A-MEM, Mem0, etc.)

## Autores

- Original: clarezoe (MIT)
- Hermes: Bianinho adapt. 20/04/2026
