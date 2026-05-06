---
name: team-leader-monitor
description: Lê e monitoriza as mensagens do Team Leader do TEN Team na base de dados do AionUI. Permite ao Bianinho ver (mas não intervir directamente) nas conversas do Team Leader.
---

# Team Leader Monitor

Lê mensagens do Team Leader do TEN Team a partir da base de dados SQLite do AionUI (`~/Library/Application Support/AionUI/aionui/aionui.db`).

## Arquitectura Real: Main Hermes ≠ Team Leader

**MAIN Hermes** (chat principal / Bianinho) e **TEN Team Leader** são **PROCESSOS SEPARADOS**:

```
Main Hermes (Bianinho)          TEN Team Leader
┌─────────────────────┐        ┌─────────────────────┐
│ ACP session: A       │        │ ACP session: B      │
│ (chat principal)     │        │ (spawned via Teams)  │
│                     │        │                     │
│ Não consegue ver     │        │ Não consegue ver     │
│ mensagens do         │        │ mensagens do        │
│ Team Leader          │        │ Main Hermes         │
└─────────────────────┘        └─────────────────────┘
         ↑                              ↑
         └──────── AionUI DB ──────────┘
              (mensagens guardadas aqui)
```

**O que JÁ funciona:**
- Ler mensagens do Team Leader a partir da BD SQLite do AionUI
- Polling para detectar novas mensagens

**O que NÃO funciona (limitação arquitectural):**
- Responder COMO Team Leader — não há canal de comunicação
- "Mergiar" sessões — são processos Hermes completamente isolados
- Intervir em tempo real — só leitura

**Conversation ID do TEN Team Leader:** `d124e72a`

**Nota importante:** Todos os tipos de mensagem (user, Team Leader) aparecem como `type='text'` na BD — não há distinção automática user/assistant no campo `type`. Inferir pelo contexto ou timestamp.

## Ferramentas

### Query directa (terminal)

```bash
# Resumo da conversa
python3 ~/.hermes/scripts/team_leader_bridge.py read

# Ver mensagens
python3 ~/.hermes/scripts/team_leader_bridge.py messages [limit]

# Polling (30s)
python3 ~/.hermes/scripts/team_leader_bridge.py poll [timeout]
```

### Query manual à BD

```bash
sqlite3 ~/Library/Application\ Support/AionUI/aionui/aionui.db \
  "SELECT id, type, content, created_at FROM messages \
   WHERE conversation_id='d124e72a' AND type='text' \
   ORDER BY created_at DESC LIMIT 10;"
```

## Scripts Disponíveis

| Script | Função |
|--------|--------|
| `~/.hermes/scripts/team_leader_bridge.py` | Bridge de monitorização (ler + polling) |
| `~/.hermes/skills/team-leader-monitor/references/team_leader_query.py` | Query alternativa |
| `~/.hermes/skills/team-leader-monitor/references/team_leader_tools.py` | Módulo Python para tools |

## Configuração

**BD:** `~/Library/Application Support/AionUI/aionui/aionui.db`
**Conversation ID:** `d124e72a`
**Tabela:** `messages` — colunas: `id, conversation_id, type, content, created_at`

## Limitações

1. **Sem distinção user/assistant** — todas as mensagens são `type='text'`
2. **Sem capacidade de resposta** — só leitura, não há API para injetar mensagens
3. **Polling required** — não há webhook ou callback para novas mensagens
4. **Sessões ACP isoladas** — cada processo Hermes tem sessão própria
