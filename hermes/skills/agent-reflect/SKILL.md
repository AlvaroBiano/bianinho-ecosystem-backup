---
name: reflect
description: Auto-reflective self-improvement skill — extracts learnings from corrections and success patterns, permanently encodes them into memory and skills. Philosophy: Correct once, never again.
version: 2.0.0-hermes
hermes-adapted: true
source: https://clawskills.sh/skills/stevengonsalvez/agent-reflect
original-author: stevengonsalvez
triggers:
  - reflect
  - self-reflect
  - review session
  - what did I learn
  - extract learnings
  - analyze corrections
---

# Reflect — Agent Self-Improvement (Hermes)

Extrahe aprendizagens de correções e padrões de sucesso do conversation history. Transforma correções únicas em memória permanente. Philosophy: **Correct once, never again.**

## Quick Commands

| Command | Action |
|---------|--------|
| `reflect` | Analisa conversation para aprendizagens |
| `reflect on` | Ativa auto-reflection |
| `reflect off` | Desativa auto-reflection |
| `reflect status` | Mostra estado e métricas |
| `reflect review` | Review pending learnings |

## Quando Usar

- Depois de tarefas complexas
- Quando Álvaro corrige comportamento explicitamente
- Em session boundaries
- Quando padrões de sucesso merecem ser preservados

## Workflow — 5 Passos

### Step 1: Scan Conversation for Signals

Analisa conversation para correction signals e learning opportunities.

**Signal Confidence Levels:**

| Confidence | Triggers | Examples |
|------------|----------|----------|
| **HIGH** | Explicit corrections | "never", "always", "wrong", "stop", "the rule is" |
| **MEDIUM** | Approved approaches | "perfect", "exactly", "that's right", output accepted |
| **LOW** | Observations | Padrões que funcionaram mas não validado explicitamente |

See: `signal_patterns.md` — full detection rules

### Step 2: Classify & Match to Target Files

Map cada signal ao target apropriado:

| Category | Target Files |
|----------|--------------|
| Code Style | `~/.hermes/skills/*/SKILL.md` (relevant skill) |
| Architecture | `bianinho-os` + relevant skills |
| Process | `USER.md`, `memory` |
| Domain | `USER.md` ( Álvaro & Maryanne section) |
| Tools | `memory` (environment facts) |
| New Skill | Create new skill in `~/.hermes/skills/` |

See: `agent_mappings.md` — mapping rules

### Step 3: Check for Skill-Worthy Signals

**Skill-Worthy Criteria:**
- Debugging non-trivial (>10 min investigation)
- Erro enganoso (root cause diferente da mensagem)
- Workaround descoberto por experimentação
- Config insight (difere do documentado)
- Padrão reutilizável

**Quality Gates (must pass all):**
- [ ] Reusable: Vai ajudar em tarefas futuras
- [ ] Non-trivial: Requer descoberta, não só docs
- [ ] Specific: Pode descrever condições exatas de trigger
- [ ] Verified: Solução realmente funcionou
- [ ] No duplication: Não existe já

### Step 4: Generate Proposals

Apresenta findings no formato:

```markdown
# Reflection Analysis

## Session Context
- **Date**: [timestamp]
- **Messages Analyzed**: [count]

## Signals Detected

| # | Signal | Confidence | Source Quote | Category |
|---|--------|------------|--------------|----------|
| 1 | [learning] | HIGH | "[exact words]" | Code Style |

## Proposed Changes

### Change 1: Update [target]
**Target**: `[file path]`
**Section**: [section name]
**Confidence**: HIGH

```diff
+ New rule from learning
```

## Review Prompt
Apply these changes? (Y/N/modify/1,2,3)
```

### Step 5: Apply with User Approval

**`Y` (approve):**
1. Apply change using patch tool
2. Update metrics
3. Log to `~/.hermes/reflect/learnings.log`

**`N` (reject):**
1. Discard proposed changes
2. Log rejection

**`modify`:**
1. Present each change individually
2. Allow editing before applying

**Selective (e.g., `1,3`):**
1. Apply only specified changes
2. Log partial updates

## State Management

State stored in `~/.hermes/reflect/`:

```
~/.hermes/reflect/
├── state.yaml       # auto_reflect, last_reflection, pending_reviews
├── metrics.yaml     # total_signals, acceptance_rate, etc.
└── learnings.log   # History of all learnings applied
```

## Hermes Integration

**State file:** `~/.hermes/reflect/state.yaml`
```yaml
auto_reflect: false
last_reflection: "2026-04-20T16:00:00Z"
pending_reviews: []
```

**Metrics file:** `~/.hermes/reflect/metrics.yaml`
```yaml
total_sessions_analyzed: 0
total_signals_detected: 0
total_changes_accepted: 0
acceptance_rate: 0
confidence_breakdown:
  high: 0
  medium: 0
  low: 0
skills_created: 0
```

## Safety Guardrails

### Human-in-the-Loop
- **NEVER** apply changes without explicit approval
- Always show full diff before applying
- Allow selective application

### Incremental Updates
- **ONLY** add to existing sections
- **NEVER** delete or rewrite existing rules
- Preserve original structure

### Conflict Detection
- Check if proposed rule contradicts existing memory
- Warn if conflict detected
- Suggest resolution strategy

## Output Locations

- `~/.hermes/reflect/learnings.log` — Log de aprendizagens aplicadas
- `~/.hermes/reflect/metrics.yaml` — Métricas agregadas
- New skills → `~/.hermes/skills/<name>/SKILL.md`
- Updates → existing skill SKILL.md or memory

## Components

- `signal_patterns.md` — Regex patterns for detecting corrections by confidence
- `agent_mappings.md` — Category → target file mappings (adapted for Hermes)

## Autores

- Original: stevengonsalvez (MIT)
- Hermes: Bianinho adapt. 20/04/2026
