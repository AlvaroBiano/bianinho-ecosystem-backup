# AionUI — Interface e Arquitectura (pesquisado em 02/05/2026)

## O que é o AionUI

**Descrição oficial:** "One desktop where Claude Code, Codex, Gemini CLI, and your assistants actually cowork — writing code, making slides, crunching numbers, running 24/7."

**Modelo de negócio:** Freemium — app gratuito, open-source (Apache-2.0), download em aionui.com

**Repositórios:**
- Upstream: `github.com/iOfficeAI/AionUi` (original)
- Fork Álvaro: `github.com/AlvaroBiano/AionUi`
- Site oficial: https://www.aionui.com

## Características Principais

| Feature | Descrição |
|---------|-----------|
| Multi-agent cowork | Vários agentes AI a trabalhar em conjunto |
| 20+ assistentes built-in | Claude Code, Gemini CLI, Codex, OpenCode, Goose CLI, Auggie, Kiro, etc. |
| Remote control | Telegram, WeChat, Lark, DingTalk, WhatsApp |
| 24/7 cron automation | Automação via cron jobs |
| Unified MCP | Suporte a Model Context Protocol |
| Office toolkit | PPT, Excel, Word, PDF |
| Any LLM | Suporte a qualquer provider de LLM |
| Privacy-first | API directa, sem proxy |

## Interface do AionUI

A interface não é um chatbot normal. É um **desktop de coworking** com:

1. **Cowork Assistants** — agentes que trabalham em conjunto
2. **Remote** — controlo remoto via Telegram/WeChat/etc.
3. **Automation** — cron automation
4. **Skills** — skills do sistema

### No Fork do Álvaro (AlvaroBiano/AionUi)

O fork adiciona:
- **Bianinho tab/página** — integração com o agente Bianinho/Hermes
- **Skills do Bianinho** — 71 skills listadas
- **RAG stats** — 16 chunks, categorias
- **Inbox autónomo** — tarefas pendentes do ciclo

### Como a interface se apresenta

O AionUI parece um IDE/workspace com:
- Sidebar com navegação (Assistants, Remote, Automation, Skills, Bianinho)
- Área principal de trabalho
- Agentes visíveis como "pets" ou avatares
- Chat conversacional com cada agente
- Sistema de automação

**Importante:** O Álvaro estava frustrado porque eu mandava verificar coisas que "não existem no AionUI". A interface do AionUI é específica — não é um chatbot genérico. Se alguém perguntar "como funciona a interface", verificar primeiro com `curl localhost:8765/screenshot.png` para ver o que está realmente a acontecer.

## Acesso Remoto — Opções

| Método | Interactivo | Estável | Requer |
|--------|------------|---------|--------|
| SSH tunnel | Não | Sim | SSH aberto |
| cloudflared named tunnel | Sim | Sim | Cloudflare API token |
| cloudflared quick tunnel | Sim | Não | Nada |
| DMG nativo no Mac | Sim | Sim | Build custom |

## DMG vs Servidor

| Aspecto | DMG (Mac nativo) | Servidor (Xvfb) |
|---------|-----------------|-----------------|
| Performance | Melhor | Limitado por Xvfb |
| Manutenção | Build após cada commit | Só reiniciar processo |
| Acesso | Só no Mac | De qualquer browser |
| Integração Bianinho | Via HTTP bridge | Directa (mesma máquina) |
| Complexidade | Alta (builds + debugging) | Baixa (só Xvfb + Flask) |

## Nota sobre debugging sem DevTools

O Álvaro no MacBook Pro com AionUI DMG conseguia abrir DevTools (Cmd+Alt+I), mas a interface mostrava `<anonymous>` nos stacks. No servidor, o debugging é mais simples: screenshot + logs directos.

Se precisar de saber o que está a acontecer no servidor:
```bash
# Screenshot em tempo real
curl -s http://localhost:8765/screenshot.png -o /tmp/aionui_screen.png

# Status do CDP
curl -s http://localhost:9223/json | python3 -c "import json,sys; [print(p['title'], p['url']) for p in json.load(sys.stdin)]"

# Logs do AionUi
tail -20 /tmp/aionui.log

# Logs do web viewer
tail -20 /tmp/aionui-web-viewer.log
```
