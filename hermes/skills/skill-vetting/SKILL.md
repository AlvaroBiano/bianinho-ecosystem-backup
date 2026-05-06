---
name: skill-vetting
description: Processo de verificação, análise e adaptação de skills externas para o ecossistema Hermes Agent. Usa como referência o OpenClaw skills registry (18,721 packages).
version: "1.0.0"
hermes-adapted: true
category: skills
---

# OpenClaw Skill Vetting — Verificar, Adaptar, Instalar

## Processo de Descoberta

### Como o Repo Está Estruturado

O repo `openclaw/skills` tem **61.234 SKILL.md files** em `skills/skills/{author}/{skill-name}/SKILL.md`.

**DOIS níveis de `skills/`:**
```
repos/skills/                          ← repo clonado
  skills/                               ← pasta dentro do repo
    edoserbia/agent-autopilot/SKILL.md ← skill real
    rgba-research/context-aware/SKILL.md
    ...
```

**O repo `VoltAgent/awesome-openclaw-skills`** é apenas o **índice curado** (5.127 URLs para clawskills.sh). Não contém as skills.

## Processo Correcto — 3 Fases

### Fase 1: Verificar (Ler todo o conteúdo)

Para cada skill identificada como relevante:
1. Ler o `SKILL.md` principal
2. Ler TODOS os scripts (`scripts/*.sh`, `scripts/*.py`)
3. Ler componentes (`components/*.md`)
4. Ler README e examples
5. Mapear a estrutura de ficheiros completa

```bash
# Encontrar skill no repo
find ~/repos/skills/skills -name "SKILL.md" -path "*/{author}/{skill-name}/*"

# Listar todos os ficheiros
find ~/repos/skills/skills/{author}/{skill-name} -type f | sort
```

### Fase 2: Analisar (Mapear para Hermes)

Criar tabela de mapeamento OpenClaw → Hermes:

| Componente | OpenClaw | Hermes | Ação |
|-----------|----------|--------|------|
| Paths | `~/.openclaw/` | `~/.hermes/` | 🔧 |
| Sessions | `sessions_history()` tool | `session_search()` tool | 🔧 |
| Spawn | `sessions_spawn()` | `delegate_task()` | 🔧 |
| Cron | JSON config `openclaw cron` | `cronjob` tool | 🔧 |
| Delivery | `announce` mode | `send_message()` | 🔧 |
| Todo system | `todo-management` skill | Não existe | ❌ |
| LLM | `ACC_MODELS` (Anthropic/Ollama) | MiniMax M2.7 | ❌ |

**Categorias de adaptação:**
- ✅ = Hermes-ready (funciona sem mudanças)
- 🔧 = Adaptar (precisa mudança de path/ferramenta equivalente)
- ❌ = Reescrever (lógica dependente de backend OpenClaw)

### Fase 3: Adaptar Antes de Instalar

**Regra de ouro:** Nunca instalar uma skill OpenClaw sem adaptar primeiro. Skills OpenClaw foram desenhadas para backend OpenClaw e vão falhar ou funcionar mal no Hermes.

**Passos de adaptação:**
1. Substituir todos os paths `~/.openclaw/` → `~/.hermes/`
2. Trocar ferramentas OpenClaw pelas equivalentes Hermes
3. Adaptar cron jobs do formato OpenClaw para `cronjob` tool
4. Traduzir delivery de `announce` mode para `send_message()`
5. Se a skill depende de `todo-management` → criar sistema equivalente primeiro
6. Se a skill usa LLM externo para screening → adaptar para MiniMax

## Padrões Comuns de Backend-Specific

### OpenClaw-specific mais frequente
- `sessions_history(sessionKey, limit=50)` → `session_search()` + SQLite
- `sessions_spawn(task, model)` → `delegate_task()`
- `~/.openclaw/workspace/` → `~/.hermes/`
- `openclaw cron add` → `cronjob` tool
- `todo-management` skill + `todo.sh` → não existe no Hermes
- `ACC_MODELS` (claude haiku/sonnet) → MiniMax
- `HIPPOCAMPUS_CORE.md` → RAG do Hermes (LanceDB)
- HEARTBEAT.md (ficheiro de configuração de agente) → não existe

### Funcionalidades universais (✅ ready)
- Crashes detection via heartbeat
- State management (state.json)
- Error pattern tracking
- Memory consolidation
- Safety gate matrices (commit/push/deploy)
- Adaptive reasoning (framework mental, não comando)

## Scoring de Prioridade

| Score | Significado |
|-------|-------------|
| 9-10/10 | Instalar já — impacto imediato no Bianinho OS |
| 7-8/10 | Integrar com o existente — complementa funcionalidades |
| 5-6/10 | Inspiração — ler e adaptar ideias |
| <5/10 | Descartar para o contexto actual |

## Skills Avaliadas (20/04/2026)

### TIER 1 — Instalar já
- **context-aware-delegation** (9/10) — cron jobs inteligentes com contexto
- **agent-autopilot** (9/10) — framework heartbeat-driven (depende de sistema de todos)

### TIER 2 — Integrar com o existente
- **arc-wake-state** (8/10) — crash recovery estruturado (🔧 só 1 path)
- **close-loop** (8/10) — end-of-session discipline
- **acc-error-memory** (7/10) — error pattern tracking (🔧 precisa MiniMax)
- **agent-reflect** (7/10) — extract learnings de correções

### INSPIRAÇÃO
- **adaptive-reasoning** (7/10) — complexidade dinâmica
- **hippocampus-memory** (6/10) — decay + reinforcement

## Ficheiros

- Repo: `~/repos/skills/` (clonado de https://github.com/openclaw/skills)
- Índice curado: `~/repos/awesome-openclaw-skills/`
- Skills avaliadas em detalhe: context-aware, autopilot, arc-wake-state, close-loop, acc-error-memory, agent-reflect, adaptive-reasoning, hippocampus, evo-clone, ai-daily-briefing

## Notas

- O agent-autopilot precisa de `todo-management` skill que não existe no Hermes — é prerequisite para instalar
- arc-wake-state é a skill mais fácil de adaptar (1 path apenas)
- close-loop e agent-reflect são os mais alinhados com o Bianinho OS actual
