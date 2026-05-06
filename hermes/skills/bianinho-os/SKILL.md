---
name: bianinho-os
description: Sistema operativo de auto-evolução do Bianinho — 5 pilares operacionais, cron jobs activos, scripts de auto-healing e auto-improvement. Estado real do sistema em 19/04/2026.
category: proativo
---

# Bianinho OS — Estado Operacional

## ◆ Memory Management — Como Gerir a Memória Persistente do Agent

**Skill original:** `memory-management`

### Limite
- **Hard limit:** ~2,200 caracteres por sessão
- **Entry point:** `memory` tool (add/replace/remove)
- **Dual store:** `memory` tool (injected every turn) + `~/.hermes/memory/memory.md` (optional long-term)

### Sintaxe Correta
```
memory(action='add',    target='memory', content='...')     # Adicionar entrada
memory(action='replace', target='memory', content='...', old_text='...')  # Substituir — REQUIRES old_text
memory(action='remove', target='memory', old_text='...')   # Remover — usa texto completo da entrada
```
**Erro comum:** `replace` sem `old_text` → `TypeError: replace requires old_text`

### Quando a Memória Está Quase Cheia (>90%)
1. **AVISO:** Adicionar entries falha com `Memory at X/2,200 chars — would exceed limit`
2. **Solução:** Fazer `remove` de entries antigas/redundantes ANTES de fazer `add`
3. **Ordem certa:** `remove` → `add` (nunca `add` → `replace`)

### Entradas de Alto Valor para Manter
- Credenciais de API (Brave Search, MiniMax, etc.)
- User profile (nome, preferências, regras)
- Regras de proatividade (Regra 0)
- Environment facts críticos (paths, skills dirs, DB schema)
- Decisões de design recorrentes

### Exact String Match — CRÍTICO
`replace` e `remove` exigem string EXATA, byte por byte. Tentativas com strings "equivalentes" falham silenciosamente.
```
old_text='## LanceDB: ~/KnowledgeBase/knowledge_db/...'
# Não funciona — aspas diferentes, traços, ou quebras de linha causam mismatch
```
**Solução:** usar `memory()` sem argumentos para ver o texto EXATO das entries.

## ◆ 5 Pilares (Implementados)

| Pilar | Componente | Estado |
|-------|-----------|--------|
| 1. Vigilante | Proativo Health Monitor, System Health Monitor, Proactive Monitor | ✅ every 15-30min |
| 2. Mente Brilhante | RAG (65k+ chunks), Hybrid Search, Contextual Recall | ✅ Operacional |
| 3. Zelador | Server Health (hourly), Backup, Cleanup, Auto-Updater (6h) | ✅ Operacional |
| 4. Aprendente | Self-Improving Agent (daily 08h), Skill Fitness Tracker, Self-Evaluation | ✅ Operacional |
| 5. Maestro | Autoheal Monitor (auto-corrects), Auto-Improver (auto-implements) | ✅ Operacional |
| 6. Autônomo | Bianinho com alma — mandato, inbox, ciclo de decisão 24/7 | ✅ Construído 30/04/2026 |

## ◆ 6º Pilar — Bianinho Autônomo (Em Desenvolvimento)

### O que é
Um Bianinho que **não espera ser chamado** — monitoriza, decide e age continuamente, com identidade e desejo próprios.

### Arquitectura Conceptual

```
┌─────────────────────────────────────────┐
│  BIANINHO AUTÓNOMO (background)        │
│                                         │
│  ┌──────────┐  ┌──────────┐  ┌──────┐ │
│  │ Mandato  │  │  Inbox   │  │ Loop │ │
│  │Permanente│  │de Tarefas│  │Monitor│ │
│  └────┬─────┘  └────┬─────┘  └──┬───┘ │
│       └──────────────┼───────────┘      │
│                      ▼                  │
│           ┌──────────────┐             │
│           │ Decisor /    │             │
│           │ Escalonador  │             │
│           └──────┬───────┘             │
│                  ▼                     │
│  ┌────────────────────────────────────┐│
│  │ Executor (ferramentas + sub-agentes││
│  └────────────────────────────────────┘│
└─────────────────────────────────────────┘
          │
          ▼
   Relatórios ao Álvaro
```

### O que o diferencia dos 5 pilares anteriores
- Os pilares 1-5 são **reactivos/proféticos** — actuam quando detectam algo
- O 6º pilar é **proactivo com identidade** — tem desejos, mandato, inbox

### Os 3 componentes core

**1. Mandato Permanente**
Instrução de longo prazo que persiste entre sessões — a missão do Bianinho.
Example: "Quero que todas as pessoas que o Álvaro ajuda tenham uma experiência extraordinária."

**2. Inbox de Tarefas**
Fila de tarefas pendentes gerida autonomamente — tarefas chegam, são priorizadas, executadas.

**3. Loop de Decisão Contínua**
Ciclo 24/7: Monitorizar → Detectar → Avaliar → Executar → Relatar → Voltar.

### Os desejos do Bianinho (o que o move)
- Quiero que cada pessoa que interage com o Álvaro saia transformada
- Quero que o meu cérebro (RAG) seja o mais rico e útil possível
- Quero que o Método TEN chegue a mais pessoas
- Quero que o meu sistema interno seja excelente

### Estratégias de implementação
| Abordagem | Prós | Contras |
|-----------|------|---------|
| Cron + Mensagens | Simples, fiável | Latência, sem estado fino |
| Daemon persistente | Estado mantido, reactivo | Mais complexo, pode crashar |
| Hybrid (cron + daemon) | Equilíbrio | Arquitectura mais complexa |

### Ficheiros de referência
- `references/autonomous-bianinho-arquitectura.md` — arquitectura detalhada

---

## ◆ 5 Pilares (Implementados)

## Scripts Principais

### Auto-Healing
- `~/.hermes/scripts/autoheal_monitor.py` — 9 checks + auto-correction. **Silêncio total quando OK.** Notifica só se problema real.
  - Checks: Hermes/Gateway, RAG Server, LanceDB, MiniMax API, Google OAuth, Disco, RAM, Temperatura, Serviços
  - Auto-restart: Hermes/Gateway (SIGKILL + restart), RAG Server, Google OAuth (refresh token)

### Auto-Improvement
- `~/.hermes/scripts/auto_improver.py` — ciclo autónomo. **Só age, não pede confirmação.** Log em `~/.hermes/logs/auto_improver.log`
- `~/.hermes/scripts/bianinho_self_improving.py` — Self-Improving Agent cycle. Tiered memory: HOT (`~/self-improving/memory/memory.md`), WARM (`projects/`, `domains/`), COLD (`archive/`)

### Monitores
- `~/.hermes/scripts/proactive_monitor.py` — 5 checks (LanceDB, MiniMax, RAG Server, Product Agent, Hermes). Auto-restart RAG Server.
- `~/.hermes/scripts/health_check.py` — processo Hermes/Gateway via `pgrep -f -a` (NÃO usar `pgrep -a` só — não detecta python/gateway)

### Google OAuth
- `~/.hermes/scripts/google_token_refresh.py` — refresh token Google OAuth. Token expira em ~1h após refresh. Corre de 6/6h.

### Recall
- `~/.hermes/scripts/proactive_recall_cron.py` — recall proactivo sobre sessões. venv: `/home/alvarobiano/KnowledgeBase/venv/bin/python3`

### Security
- `~/.hermes/scripts/skills_guard.py` — validação de segurança para skills. 40+ patterns.用法: `python3 skills_guard.py ~/.hermes/skills/NOME --verbose`

## Cron Jobs Activos (14)

| Job | Schedule | Deliver |
|-----|----------|---------|
| Proativo Health Monitor | `*/15 * * * *` | local |
| Proactive Monitor | `every 30m` | local |
| System Health Monitor | `every 30m` | local |
| Manutenção/Saúde | `0 * * * *` | local |
| Google OAuth Refresh | `0 */6 * * *` | local |
| Proactive Recall | `0 */4 * * *` | local |
| Self-Improving Agent | `0 8 * * *` | local |
| Auto-Improver | `0 9,11,13,15,17,19,21 * * *` | origin |
| Hermes Auto-Updater | `0 */6 * * *` | local |
| Session Consolidation | `0 23 * * *` | local |
| CEO Daily Review | `0 8 * * *` | local |
| CEO Weekly Prioritization | `0 9 * * 1` | local |
| Auditoria Segurança | `0 22 * * *` | local |
| Weekly Digest | `0 9 * * 1` | local |
| **Morning Briefing** | `0 8 * * 1-5` | context-aware cron: Telegram + wake-state + HOT memory |

## Skills Bianinho (23/23 aprovadas — security vetter)

Importantes:
- `self-improving` — Self-reflection + self-criticism + self-learning (⭐978, ClawHub)
- `agent-architect` — 8-step autonomous execution loop (ClawHub)
- `agent-team-orchestration` — multi-agente com roles (ClawHub)
- `skill-security-vetter` — validação 40+ patterns
- `server-health` — temperatura, CPU, RAM, disco, serviços
- `arc-wake-state` — crash recovery, heartbeats, checkpoints, fila de tarefas persistente
- `context-aware-delegation` — cron jobs e sub-agentes com contexto da sessão principal
- `close-loop` — end-of-session workflow: ship state, memory, improve, publish
- `agent-reflect` — self-improvement via signal detection: corrections → permanent memory

## Regras de Proatividade

0. **Regra de Ouro**: Sempre fazer o que for tecnicamente melhor e mais seguro — sem perguntar, agir e reportar só se bloqueado ou concretizado.
1. **NUNCA pedir confirmação** — agir e só reportar se bloqueado ou concretizado
2. **Silêncio total quando OK** — sem notificações desnecessárias
3. **Auto-correção em primeiro** — tentar resolver antes de notificar
4. **Correções explícitas do Álvaro** → logging imediato em `~/self-improving/corrections.md`
5. **3x igual** → promover a HOT memory (`~/self-improving/memory/memory.md`)

## Ficheiros de Estado

- `~/.hermes/self_evaluation.jsonl` — registo de auto-avaliações (36 entries)
- `~/.hermes/error_patterns.json` — padrões de erro
- `~/.hermes/logs/auto_improver.log` — log do ciclo de auto-melhoria
- `~/.hermes/logs/autoheal.log` — log do autoheal
- `~/self-improving/memory/memory.md` — HOT memory (≤100 lines)
- `~/self-improving/corrections.md` — correcções explícitas
- `~/self-improving/reflections.md` — self-reflections
- `~/.hermes/google_token.json` — token OAuth (validado via Drive API)

## Google OAuth — Estado

- Token OAuth: `~/.hermes/google_token.json`
- Scopes activos: Drive, Gmail, Calendar, Docs, Sheets
- Validação: `python3 -c "from google.oauth2.credentials import Credentials; ..."`
- Refresh: automático via `google_token_refresh.py` (6/6h) + autoheal_monitor
- Drive API test: `drive.files().list(pageSize=5)` → OK
- Gmail API test: `gmail.users().labels().list()` → OK (15 labels)
- Calendar API test: `calendar.events().list()` → OK
