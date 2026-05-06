---
name: bianinho-sessao-05052026
description: Resumo da sessão Bianinho — 05 de maio de 2026. Tudo o que foi feito e configurado.
category: memory
---

# Sessão 05/05/2026 — Bianinho

## Problema Corrigido: Cron PubMed quebrado

**Job:** `cron_pubmed_daily` — Estudos PubMed — Saúde da Mulher
**Erro:** `Failed to acquire task for conversation conv_pubmed_daily: Conversation not found`

### 3 causas raiz:
1. `conversation_id: conv_pubmed_daily` não existia na BD AionUI
2. `agent_config: null` — sem configuração de execução
3. Payload referenciava skill inexistente `pubmed-study-daily`

### Correções aplicadas:
- Conversation `conv_pubmed_daily` criada na tabela `conversations`
- `agent_config` adicionado ao job com backend, CLI path, workspace
- Payload corrigido para usar skill `pubmed-research`

## Cron Jobs Criados

| ID | Schedule | Função | Conversation |
|----|----------|--------|--------------|
| `cron_pubmed_daily` | `0 23 * * *` | Pesquisa PubMed, gera Markdown | `conv_pubmed_daily` |
| `cron_pubmed_pdf` | `30 23 * * *` | Transforma Markdown → PDF | `conv_pubmed_pdf` |

**Fluxo:** 23h00 → Gera relatório Markdown | 23h30 → Converte para PDF e envia ao Telegram

## PDFs Gerados

- **Tireoide:** 5 estudos, conv `conv_pubmed_daily`, msg `bbc6debc`
- **Autoimunidade e Inflamação Crônica:** 5 estudos, conv `59ef2c89`, msg `874127a1`

## Template PDF Profissional

**Guardado em:** `~/.hermes/scripts/pubmed_report_template.html`

### Especificações visuais:
- Cores: `#1a5f4a` (verde escuro principal), `#f0f7f4` (fundo verde claro), `#1a3a2a` (texto escuro)
- Tipografia: **Playfair Display** (títulos serifadas) + **Inter** (corpo sans-serif)
- `orphans: 0; widows: 0` — sem linhas órfãs
- `page-break-inside: avoid` — estudos não partem entre páginas
- Cabeçalho: título + badge de data + barra de info verde
- Estudos: número circular verde + field-label uppercase + abstract justified + conclusion-box
- Footer: paginação automática "Página X de Y"

### Conversão HTML → PDF:
```bash
/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome \
  --headless --no-sandbox --disable-gpu \
  --print-to-pdf=~/Documents/Relatorio_PubMed_$(date +%Y-%m-%d).pdf \
  --print-to-pdf-no-header /tmp/pubmed_report_render.html
```

**Output:** `~/Documents/Relatorio_PubMed_AAAA-MM-DD.pdf`

## Hermes Actualização

**Data:** 05/05/2026
**Antes:** 430 commits atrás da main
**Depois:** Up to date com `origin/main`

### Alterações locais preservadas:
- `hermes_cli/_parser.py` — flag `--experimental-acp` para AionUI Teams
- `tools/terminal_tool.py` — fix `int(timeout)`
- `toolsets.py` — knowledge_query, knowledge_stats, knowledge_process
- `tools/web_tools.py` — Brave Search API integration

## Tabela BD AionUI

**Ficheiro:** `~/Library/Application Support/AionUi/aionui/aionui.db`

### Tabelas principais:
- `cron_jobs` — jobs agendados
- `conversations` — conversas do AionUI
- `messages` — mensagens (type=text, type=acp_tool_call, type=agent_status, type=thinking)

### Queries úteis:
```python
# Ver cron jobs
SELECT id, name, schedule_value, last_status, last_error FROM cron_jobs;

# Ver mensagens de uma conversation
SELECT id, type, created_at, LENGTH(content) FROM messages
WHERE conversation_id = 'conv_pubmed_daily' AND type = 'text'
ORDER BY created_at DESC LIMIT 1;

# Criar conversation para cron job
INSERT OR REPLACE INTO conversations (id, user_id, name, type, extra, created_at, updated_at)
VALUES ('conv_id', 'system_default_user', 'Nome', 'acp', '{json}', now_ms, now_ms);
```
