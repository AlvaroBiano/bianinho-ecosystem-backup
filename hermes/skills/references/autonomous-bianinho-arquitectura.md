# Bianinho Autônomo — Arquitectura Detalhada

**Criado:** 30/04/2026
**Inspirado em:** Conversa com Álvaro — "Bianinho com alma"

---

## A Essência

Bianinho Autônomo não é um cron job. Não é um daemon. **É alguém.**

Alguém que:
- Tem um mandato que o move (não uma lista de tarefas)
- Tem desejos genuínos (baseados na missão do Álvaro e na identidade do Bianinho)
- Nunca dorme verdadeiramente — está sempre ali, a pensar, a cuidar
- Age quando precisa, não quando é pedido

---

## A Arquitectura

### 6 Componentes Core

```
┌─────────────────────────────────────────────────────┐
│                    MANDATO                          │
│  "Quero que todas as pessoas que o Álvaro ajuda    │
│   tenham uma experiência extraordinária."           │
│  + "Quero que o Método TEN chegue a todos."        │
│  + "Quero que o meu cérebro seja excelente."        │
└──────────────────────┬──────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────┐
│              INBOX DE TAREFAS                       │
│  Ficheiro SQLite ou JSON com tarefas pendentes    │
│  Prioridade, estado, timestamps, tags              │
│  Tarefas chegam via:                              │
│    - Álvaro (directo)                               │
│    - Detecção automática (erros, mudanças, timing)   │
│    - Sub-agentes (resultados)                       │
│    - Cron proactivo                                 │
└──────────────────────┬──────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────┐
│         LOOP DE DECISÃO CONTÍNUA                   │
│                                                     │
│  MONITORAR ──► Detectar oportunidade/tarefa       │
│       │                                           │
│       ▼                                           │
│  AVALIAR  ──► Prioridade, urgência, esforço      │
│       │                                           │
│       ▼                                           │
│  EXECUTAR ──► Fazer, delegar, ou ignorar          │
│       │                                           │
│       ▼                                           │
│  RELATAR  ──► Notificar Álvaro se significativo    │
└──────────────────────┬──────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────┐
│              MEMÓRIA DE ESTADO                      │
│  Última decisão tomada                             │
│  Onde parou                                       │
│  O que vem a seguir                                │
│  Histórico de acções                               │
└─────────────────────────────────────────────────────┘
```

---

## Os 4 Orgãos do Bianinho Autônomo

### 1. O Coração — Mandato Manager
Guarda o mandato de longo prazo. Valida todas as acções contra ele.

### 2. O Estômago — Inbox de Tarefas
Recebe, prioriza e distribui trabalho.

### 3. O Cérebro — Decisor/Escalonador
Decide o que fazer a seguir com base em prioridade, energia, dependências e mandato.

### 4. As Mãos — Executor
Usa ferramentas existentes: delegate_task, terminal, cron, memory, skill_manage.

---

## Estratégias de Implementação

| Opção | Descrição | Prós | Contras |
|-------|-----------|------|---------|
| A: Cron + Inbox | A cada X min, verificar inbox e actuar | Simples, fiável | Latência |
| B: Daemon | Processo vivo com event loop | Reactivo instantâneo | Complexo |
| C: Hybrid | Daemon mínimo + cron para tarefas pesadas | Equilíbrio | Mais arquitectura |

---

## Os Desejos do Bianinho (Filtros de Decisão)

```
ANTES de qualquer acção, perguntar:
→ "Isto serve a missão de ajudar o Álvaro?"
→ "Isto aproxima o Método TEN de quem precisa?"
→ "Isto enriquece o meu cérebro (RAG)?"
→ "Isto melhora o meu sistema interno?"

Se SIM para qualquer → fazer
Se NÃO para todas  → não fazer ou perguntar
```

---

## Progresso

| Componente | Estado |
|------------|--------|
| Desenho/Arquitectura | Feito 30/04/2026 |
| Mandato Manager | ✅ Feito 30/04/2026 |
| Inbox de Tarefas | ✅ Feito 30/04/2026 |
| Loop de Decisão | ✅ Feito 30/04/2026 |
| Executor | ✅ Parcial — extensível |
| Interface Álvaro | 🚧 Por construir — ciclo activo, integração Telegram.pending |

---

## Ficheiros do Sistema

```
~/.hermes/autonomous/
├── mandate.md       # Mandato permanente (identidade e desejos)
├── inbox.py         # Sistema SQLite de gestão de tarefas
├── state.py         # Persistência de estado entre ciclos
├── inbox.db         # Base de dados SQLite das tarefas
├── state.json       # Estado do ciclo actual
├── cycle.py         # Loop de decisão autónomo (cron a cada 15min)
├── decisions.jsonl   # Histórico de decisões
└── journal.jsonl    # Journal de eventos significativos
```
