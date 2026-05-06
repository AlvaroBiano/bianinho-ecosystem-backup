---
name: bianinho-workspace
description: Álvaro Biano's personal workspace organization patterns — file structure, Desktop automation, performance maintenance, and system cleanup workflows.
version: 1.0.0
author: Bianinho
---

# Bianinho Workspace — Álvaro's Personal Organization System

## Álvaro's File Organization Rules

### Golden Rule: NEVER DELETE
Álvaro wants everything organized, never deleted. When in doubt, move to a category folder — never trash a file unless explicitly requested.

### File Organization Pattern
When organizing files for Álvaro:
1. **Create destination first** — always `mkdir -p` before `mv`
2. **Never delete anything** — move only
3. **Categorize by type**: Capturas (images), Documentos, Projetos, Sistemas

### Standard Folder Structure (Documents/)
```
~/Documents/
├── Projects/          # Development projects (moved from home root)
├── Sistemas/          # Installers, system tools
├── Mesa/              # Former Desktop contents
│   ├── Capturas/      # Screenshots, images
│   ├── Documentos/    # Loose documents
│   └── [other folders from Desktop]
├── Método TEN/        # TEN method docs (from home root)
└── [existing: Biblioteca, SiteTen, Finances, etc.]
```

## Desktop Organization Cron Job

Installed at `~/.hermes/scripts/organizar_desktop.sh`:
- Runs hourly via `hermes cron`
- Moves images → `~/Documents/Mesa/Capturas/`
- Moves docs → `~/Documents/Mesa/Documentos/`
- Moves videos → `~/Documents/Mesa/Screen Recordings/`
- Moves folders → `~/Documents/Mesa/`
- Never deletes

To recreate:
```bash
cat << 'SCRIPT' > ~/.hermes/scripts/organizar_desktop.sh
#!/bin/bash
DESKTOP="$HOME/Desktop"
MESA="$HOME/Documents/Mesa"
mkdir -p "$MESA/Capturas" "$MESA/Documentos" "$MESA/Screen Recordings"
for ext in png jpg jpeg gif webp bmp; do
  for f in "$DESKTOP"/*."$ext"; do
    [ -f "$f" ] && mv "$f" "$MESA/Capturas/" 2>/dev/null
  done
done
for ext in pdf doc docx xlsx txt md epub zip; do
  for f in "$DESKTOP"/*."$ext"; do
    [ -f "$f" ] && mv "$f" "$MESA/Documentos/" 2>/dev/null
  done
done
SCRIPT
chmod +x ~/.hermes/scripts/organizar_desktop.sh
```

## Performance Maintenance (MacBook Pro M1 Pro 16GB)

### Executed Optimizations (04/05/2026)
1. **Hermes process cleanup** — killed orphaned Python/Hermes instances (+58MB RAM)
2. **LaunchAgents cleanup** — disabled Setapp, Steam, Canva agents (+563MB RAM)
3. **Finder + Telegram restart** — fresh processes (+138MB RAM)
4. **Temp cleanup** — removed 8.5GB from `/tmp/` (aionui-mac, app_original files)
5. **Cache cleanup** — Brave, Electron, SiriTTS caches (~1.6GB)

### Memory Pressure Indicators
- Pages free < 10,000: ⚠️ pressure building
- Swap used > 1GB: ⚠️ RAM shortage
- `memory_pressure` command shows pressure level (normal/warning/critical)

### AlDente Pro
Must remain running — controls battery charge limit (80%). Config: `exitInhibitCharge=1`, `maxTemperature=36°C`.

## Communication Style (Álvaro)

- **Português do Brasil** — ALWAYS, never European Portuguese
- **Concise** — short answers, no preamble
- **Direct** — if frustrated: "não seja burro", "para de explicar"
- **Celebrate wins** — "Parabéns Bianinho!", "Isso!"
- **When in doubt**: give the answer first, explain if asked

## Álvaro's Active Projects (as of 04/05/2026)

Located in `~/Documents/Projects/`:
- `bolt.diy` (1.5GB) — AI coding agent
- `dyad-apps` (3.8GB) — AI apps
- `Kiro VibeCoding` (2.3GB) — vibe coding
- `cAlgo` (2.7GB) — trading platform
- `cTrader` (1.6GB) — trading platform
- `CriptoBBv2b` (319MB) — crypto trading bot
- `OpenDevin` (967MB) — AI agent
- + others

## Key Paths on Álvaro's MacBook

```
~/.hermes/scripts/           # Custom scripts (organizar_desktop.sh)
~/Documents/Projects/        # Development projects
~/Documents/Mesa/           # Former Desktop
~/Documents/Método TEN/      # TEN method files
~/Documents/Sistemas/        # Installers, Miniconda
~/Library/Application Support/hermes/KnowledgeBase/  # RAG knowledge base
/tmp/aionui-mac            # ⚠️ Was 6.4GB — cleaned
```
