---
name: minimax-agent-platform
description: MiniMax Agent Platform (agent.minimax.io) — MaxHermes, MaxClaw, Skills marketplace. Relacao com Hermes Agent (NousResearch) e OpenClaw.
category: ai-platforms
---

# MiniMax Agent Platform — agent.minimax.io

## O Que E

Plataforma de agentes de IA da MiniMax. Disponibiliza agentes autonomos MaxHermes e MaxClaw alimentados pelo modelo MiniMax-M2.7. Acesso via web, Telegram, Discord, Slack.

**URL:** https://agent.minimax.io

---

## Produtos

### MaxHermes
**Tagline:** "An Agent That Grows With You"
**Modelo:** MiniMax-M2.7

**Caracteristicas:**
- **Self-evolution:** cada tarefa complexa concluida desbloqueia uma nova skill exclusiva
- **Always on:** deploy em 10s, 24/7 na cloud
- **All-scenario accessibility:** Telegram, Discord, Slack
- **Token Plan:** conecta ao credito MiniMax para tool calls

### MaxClaw
**Tagline:** "Your 24/7 personal assistant"
**Modelo:** MiniMax M2.7

**Caracteristicas:**
- **Personalizacao:** nome, personalidade, memoria entre sessoes
- **Always on:** 24/7 cloud
- Mesmas integracoes que MaxHermes

---

## Relacao com Hermes Agent

**MAXCLAW** e baseado em **OpenClaw** — fork open-source que por sua vez derivou do **Hermes Agent** (NousResearch).

**MAXHERMES** usa o nome "Hermes" por branding — mas e uma implementacao proprietaria da MiniMax sobre a mesma arquitectura.

```
OpenClaw (open-source, comunidade)
    fork
Hermes Agent (NousResearch) — github.com/NousResearch/hermes-agent
    fork
MaxHermes + MaxClaw (MiniMax) — agent.minimax.io
```

---

## Skills Marketplace

**URL:** https://agent.minimax.io/skills

Sistema de capacidades modulares instalveis. Categorias: By MiniMax, User Contributions.

**Skills populares:**
- html-presentation-generator (7.462 usos)
- landing-page-builder (7.015 usos)
- minimax-pdf (6.072 usos)
- minimax-docx (5.398 usos)
- pptx-generator (4.677 usos)
- minimax-xlsx (3.902 usos)
- industry-research-report-writer (3.897 usos)
- video-story-generator (3.858 usos)

---

## Expert Collection

Agentes pre-configurados por dominio:
- **Office** — produtividade documental
- **Finance** — analise financeira
- **Coding** — programacao

---

## API e Context Window

**API Endpoints (confirmado 30/04/2026):**
- OpenAI兼容: `https://api.minimaxi.com/v1`
- Anthropic兼容: `https://api.minimaxi.com/anthropic`
- Docs: https://platform.minimaxi.com/docs/llms.txt

**Model Context Windows:**
| Modelo | Context Window |
|--------|---------------|
| MiniMax-M2.7 | 204,800 tokens |
| MiniMax-M2.7-highspeed | 204,800 tokens |
| MiniMax-M2.5 | 204,800 tokens |
| MiniMax-M2.1 | 204,800 tokens |

**IMPORTANTE:** Nao existe modelo MiniMax com 1M de contexto. Rumores sobre isso sao incorretos.

---

## Para Bianinho

O nosso Hermes Agent (em `~/.hermes/hermes-agent/`) e a mesma arquitectura que MaxHermes/MaxClaw. A diferenca:
- Nos usamos o codigo original (NousResearch)
- A MiniMax usa o seu proprio fork com M2.7
- O MaxHermes tem self-evolution autonomo (cria skills de tarefas completadas)
- Temos skills em `~/.hermes/skills/` — equivalente ao marketplace
