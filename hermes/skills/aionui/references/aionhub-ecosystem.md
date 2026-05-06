# AionHub Ecosystem — Extensions, Agents & Skills (03/05/2026)

## AionHub — Repositório Central

**URL:** https://github.com/iOfficeAI/AionHub
**Stars:** 5 | **Linguagem:** TypeScript

Hub oficial de extensões para o AionUI — Agents, Skills, Assistants, MCPs.

```
https://github.com/iOfficeAI/AionHub
├── extensions/          # Estáveis (4)
│   ├── aionext-opencode/      → OpenCode adapter
│   ├── aionext-auggie/
│   ├── aionext-codebuddy/
│   └── aionext-qwen/
├── pending/            # Em desenvolvimento (10)
│   ├── aionext-claude/        → Claude Code
│   ├── aionext-codex/         → OpenAI Codex
│   ├── aionext-goose/          → Goose CLI
│   ├── aionext-kimi/          → Kimi Code
│   ├── aionext-copilot/       → GitHub Copilot
│   ├── aionext-droid/         → Factory Droid
│   ├── aionext-kiro/          → Kiro CLI
│   ├── aionext-mistral-vibe/  → Mistral Vibe
│   ├── aionext-openclaw-gateway/ → OpenClaw
│   └── aionext-qoder/         → Qoder CLI
└── docs/
```

## Extensões Disponíveis

### Estáveis (extensions/)

| Extensão | Agent | CLI Command | Auth | Estado |
|----------|-------|-------------|------|--------|
| aionext-opencode | OpenCode | `opencode` | Não | ✅ Estável |
| aionext-auggie | Auggie | `auggie` | ? | ✅ Estável |
| aionext-codebuddy | CodeBuddy | `codebuddy` | ? | ✅ Estável |
| aionext-qwen | Qwen | `qwen` | Sim | ✅ Estável |

### Em Desenvolvimento (pending/)

| Extensão | Agent | Install | Auth | Notas |
|----------|-------|---------|------|-------|
| aionext-claude | Claude Code | `bun add -g @anthropic-ai/claude-code` | Sim | Requer API key Anthropic |
| aionext-codex | Codex | `bun add -g @openai/codex` | Sim | Requer API key OpenAI |
| aionext-goose | Goose | `bun add -g goose-cli` | Não | ✅ Open source, gratuito |
| aionext-kimi | Kimi Code | Script install | Sim | Requer API key Moonshot |
| aionext-copilot | GitHub Copilot | `bun install -g @github/copilot` | Sim | Requer subscription |
| aionext-droid | Factory Droid | `bun add -g droid` | Sim | Requer API key |
| aionext-kiro | Kiro CLI | Script install | Sim | Requer API key |
| aionext-mistral-vibe | Mistral Vibe | Script install | Sim | Requer API key Mistral |
| aionext-openclaw-gateway | OpenClaw | `bun add -g openclaw` | Não | ✅ Open source, gratuito |
| aionext-qoder | Qoder CLI | `bun add -g @qoder-ai/qodercli` | Sim | Requer API key |

## Extensão JSON — Formato

Cada extensão tem `aion-extension.json`:

```json
{
  "$schema": "https://raw.githubusercontent.com/iOfficeAI/AionHub/spec/v0/extension-manifest.schema.json",
  "name": "aionext-opencode",
  "displayName": "OpenCode",
  "version": "1.0.0",
  "engine": { "aionui": "^1.0.0" },
  "author": "Aionui Official",
  "description": "Integrates OpenCode as an ACP adapter in AionUi.",
  "lifecycle": {
    "onInstall": {
      "shell": { "cliCommand": "bun", "args": ["install", "-g", "--trust", "opencode-ai"] },
      "timeout": 60000
    }
  },
  "contributes": {
    "acpAdapters": [{
      "id": "opencode",
      "name": "OpenCode",
      "description": "Official OpenCode adapter",
      "connectionType": "stdio",
      "cliCommand": "opencode",
      "acpArgs": ["acp"],
      "defaultCliPath": "bunx opencode-ai",
      "authRequired": false,
      "supportsStreaming": false
    }]
  }
}
```

## Como Instalar Extensões no macOS

### 1. Guardar JSONs em `~/Library/Application Support/AionUI/extensions/`

```bash
mkdir -p ~/Library/Application\ Support/AionUI/extensions/

# Guardar extensão (ex: OpenCode)
curl -s "https://raw.githubusercontent.com/iOfficeAI/AionHub/main/extensions/aionext-opencode/aion-extension.json" \
  -o ~/Library/Application\ Support/AionUI/extensions/aion-ext-opencode.json

# Guardar todas as pending
for ext in aionext-claude aionext-codex aionext-goose aionext-kimi \
           aionext-copilot aionext-droid aionext-kiro \
           aionext-mistral-vibe aionext-openclaw-gateway aionext-qoder; do
  curl -s "https://raw.githubusercontent.com/iOfficeAI/AionHub/main/pending/$ext/aion-extension.json" \
    -o ~/Library/Application\ Support/AionUI/extensions/$ext.json
done
```

### 2. Instalar CLI tools gratuitas (Goose + OpenClaw)

```bash
# Goose CLI (open source, gratuito)
bun add -g goose-cli

# OpenClaw (open source)
bun add -g openclaw

# Verificar
which goose && goose --version
which openclaw && openclaw --version
```

### 3. Verificar com AionUI

1. Fechar AionUI completamente (Cmd+Q)
2. Abrir AionUI de novo
3. New Chat → verificar se novos agentes aparecem

## Repositório AionUI Principal

**URL:** https://github.com/iOfficeAI/AionUi
**Stars:** 23,581 | **Licença:** Apache-2.0

```
AionUi — Free, local, open-source 24/7 Cowork app
├── Suporta: Gemini CLI, Claude Code, Codex, Qwen Code, Goose,
│           OpenClaw, Auggie, CodeBuddy, Kimi, OpenCode,
│           Factory Droid, GitHub Copilot, Qoder CLI, Mistral Vibe,
│           Nanobot, Aion CLI (aionrs), Snow CLI, Kiro, Hermes Agent
├── Team Mode: Leader + Teammates, MCP Server integrado
├── MCP Unificado: configura uma vez, sync para todos os agentes
└── YOLO Mode: auto-aprova todas as acções
```

## AionUI Skills Registry

**URL:** https://skills.aionui.com

Plataforma de marketplace de skills para agentes AI — discover, download, use skills autonomously.

```bash
# Setup inicial ( já feito no Mac do Álvaro)
mkdir -p ~/.config/aionui-skills
curl -s https://skills.aionui.com/SKILL.md > ~/.config/aionui-skills/SKILL.md
```

## CLI Tools Gratuitas Instaladas (03/05/2026)

| Tool | Version | Path | Notes |
|------|---------|------|-------|
| Goose CLI | v3.25.0 | `~/.bun/bin/goose` | Agent open source |
| OpenClaw | 2026.5.2 | `~/.bun/bin/openclaw` | Agent open source |

## API Keys Necessárias (não instaladas)

Para activar mais agentes, são precisas API keys:

| Agent | Provider | Como obter |
|-------|----------|-----------|
| Claude Code | Anthropic | console.anthropic.com |
| Codex | OpenAI | platform.openai.com |
| Kimi Code | Moonshot | platform.moonshot.cn |
| GitHub Copilot | GitHub | github.com/features/copilot |
| Factory Droid | Factory Labs | factory.ai |
| Kiro CLI | Kiro | kiro.ai |
| Mistral Vibe | Mistral | console.mistral.ai |
| Qoder CLI | Qoder | qoder.ai |

## Notas

- **AionHub extensions são JSONs** que declaram como instalar e configurar agentes — não instalam automaticamente, é preciso fazer o install da CLI manualmente
- **OpenClaw e Goose** são as únicas tools open source gratuitas que podemos usar sem API keys
- O AionUI detecta automaticamente agentes instalados via `AcpDetector` — desde que o PATH inclua o comando, aparece no New Chat
- **Teams Leader** é mais restritivo que New Chat — requer que o agente passe no `isTeamCapableBackend` filter
