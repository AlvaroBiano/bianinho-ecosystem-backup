# AionUI Deep Research — Collected 2026-04-30

**Source**: GitHub API (iOfficeAI/AionUi)
**Stars**: 23,162 | **Forks**: 1,998 | **License**: Apache-2.0
**Created**: 2025-08-07 | **Latest release**: v1.9.23 (2026-04-30)

---

## What Is AionUI

AionUI is a **multi-agent Cowork platform** — not just a chat client, but a desktop app where multiple AI agents work alongside you on your computer, reading files, writing code, browsing the web, and automating tasks. Built with Electron + TypeScript (89.9% TS, 5.3% Shell, 2.6% CSS).

**Key differentiator**: Built-in agent engine works zero-config. Ships with full AI agent capabilities without needing to install CLI tools separately.

---

## Architecture

```
src/
├── common/       # Shared code
├── preload/      # Electron preload scripts
├── process/      # Main process (no DOM APIs)
├── renderer/     # UI (no Node.js APIs)
└── server.ts     # Built-in server

assistant/        # 20 built-in professional assistants
skills/           # Three-layer skill system
mobile/           # Mobile component
docs/             # Multi-language docs (10 languages)
```

**Build tools**: Electron Vite, UnoCSS, Playwright, Vitest

---

## Multi-Agent Support

AionUI auto-detects installed CLI agents. Supported:
- Built-in Agent (zero config)
- Claude Code, Codex, Qwen Code
- Goose AI, OpenClaw, Augment Code
- Kimi CLI, OpenCode, Factory Droid
- GitHub Copilot, Qoder CLI, Mistral Vibe
- Nanobot, Aion CLI (aionrs), Snow CLI
- **Kiro**, **Hermes Agent**, Cursor Agent
- And 16+ more

---

## Team Mode

Leader receives instruction, breaks into subtasks, delegates to Teammates via Team MCP Server:
- Parallel execution
- Shared workspace per team
- Leader backends: Claude Code, Codex, Gemini, Snow CLI, Aion CLI
- Teammates each have isolated permission dialog
- Dynamic scaling (add/remove while running)
- Silent agents auto-marked for failure

---

## Supported AI Platforms (20+)

| Category | Providers |
|---|---|
| Official | Gemini, Vertex AI, Anthropic, OpenAI |
| Cloud | AWS Bedrock, NewAPI Gateway |
| China | Dashscope, Zhipu, Moonshot, Qianfan, Hunyuan, Lingyi, ModelScope, InfiniAI, Ctyun, StepFun |
| International | DeepSeek, **MiniMax**, OpenRouter, SiliconFlow, xAI, Ark, Poe |
| Local | Ollama, LM Studio |

---

## Built-in Assistants (20)

1. Cowork (autonomous task execution)
2. PPT Creator (PPTX generation)
3. Morph PPT (animated transitions)
4. Morph PPT 3D (3D transitions)
5. Pitch Deck Creator
6. Dashboard Creator
7. Word Creator (.docx)
8. Excel Creator (.xlsx with charts)
9. Academic Paper Writer
10. Financial Model Creator
11. Star Office Helper
12. PDF para PPT
13. Jogo 3D
14. UI/UX Pro Max (57 styles, 95 palettes)
15. Planejamento com arquivos (Manus-style)
16. Treinador HUMAN 3.0
17. Publicador de empregos sociais
18. moltbook (social media)
19. Beautiful Mermaid (diagrams)
20. Configuração OpenClaw

---

## Skills System (3 Layers)

1. **Built-in**: pptx, docx, pdf, xlsx, mermaid
2. **Custom**: User-created in `skills/` directory
3. **Extension**: Via Extension SDK from third parties

---

## Remote Access

- **WebUI**: Browser/tablet/phone, supports LAN + cross-network + server deployment
- **Telegram Bot**
- **Lark/Feishu Bot**
- **DingTalk**
- **WeChat** (personal account)
- **WeCom** (enterprise)

Auth: QR code or password.

---

## Automation (Cron)

Three modes:
- **Cron expression** (with timezone, e.g. `0 9 * * 1`, Asia/Shanghai)
- **Fixed interval** (every N minutes/hours)
- **One-time trigger**

Linked to conversation for context. Prevents system sleep during execution.

---

## AionHub Ecosystem

| Project | Stars | Purpose |
|---|---|---|
| iOfficeAI/AionUi | 23,162 | Main platform |
| iOfficeAI/OfficeCLI | 2,631 | Word/Excel/PPT editing CLI (no Office required) |
| iOfficeAI/AionHub | 3 | Extension hub for agents/skills/MCPs |

---

## Installation Methods

```bash
# macOS/Linux via Homebrew
brew install --cask aionui

# Windows / direct download
# https://github.com/iOfficeAI/AionUi/releases

# Docker
git clone https://github.com/iOfficeAI/AionUi.git && cd AionUi && docker build -t aionui .
```

---

## Key GitHub Data

- **Top contributors**: kuishou68 (685), IceyLiu (551), piorpua (269)
- **Release cadence**: Near-daily (v1.9.23 on 2026-04-30)
- **Branches**: Advanced, Pocket, Startup-guidance-optimization, aion-app-store, multiple feature branches
- **Topics**: acp, ai-agent, cowork, gemini-cli, claude-code, clawd, clawdbot, openclaw, skills, webui

---

## Hermes Agent in AionUI

Hermes is listed as natively supported:
> "Claude Code, Codex, Qwen Code, Kiro, Hermes Agent, Snow CLI, Cursor Agent and more"

For AionUI to detect Hermes:
1. `hermes` must be in PATH
2. Or manually add in Settings → Agents

For ACP integration, configure `~/.aionui/agents/hermes-agent.json` with:
```json
{
  "command": "/home/alvarobiano/.local/bin/hermes",
  "args": ["--acp", "--stdio"]
}
```

---

### Live Integration Example: aionui-hermes-ten

**Repo**: https://github.com/AlvaroBiano/aionui-hermes-ten

Concrete project integrating Hermes Agent (Bianinho) with AionUI as the orchestration layer — created and pushed in a real session on 2026-04-30.

**Contents:**
- `config/hermes-agent.json` — agent config with MCP RAG server, workspace, autonomous mode
- `config/aionui-env.yaml` — env var template (MINIMAX_API_KEY, HERMES_MANDATE, HERMES_RAG_PATH)
- `docs/TEAM_MODE.md` — Team Mode config (Hermes + Gemini + Claude Code)
- `.aionui-skills/method-ten/SKILL.md` — Method TEN custom skill for AionUI
- `scripts/setup.sh` — automated setup + validation
- `scripts/validate.sh` — exit 0 on all checks

**Validation (2026-04-30 — all green):** Hermes v0.11.0 ✓ | RAG KB ✓ | Config installed ✓ | Team ✓ | Skill ✓ | Python 3.14 ✓ | RAG script ✓

**Stack note:** Repo created via Python urllib (not `gh` CLI) — `gh` has a known bug with Node 24 + nvm returning `TypeError`. See `github` skill for the raw-bytes token-extraction workaround.

## Useful Links

- Repo: https://github.com/iOfficeAI/AionUi
- Website: https://www.aionui.com
- Discord: https://discord.gg/2QAwJn7Egx
- Twitter: https://twitter.com/AionUI
