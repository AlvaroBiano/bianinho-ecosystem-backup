---
name: bianinho-proativo-plan
description: Plano de auto-evolução do Bianinho — 5 pilares, 5 fases. Criado 18/04/2026.
---

# Bianinho Proativo — Plano de Auto-Evolução

## Ficheiros
- Plano completo: `~/bianinho_proativo_PLANO.md`

## Sumário do Plano
5 pilares, 5 fases, executado parcialmente a 18/04/2026:

### PILAR 1 — Vigilante (Self-Monitoring)
- ✅ Health checks: `~/.hermes/scripts/health_check.sh`
- ✅ Cron jobs every 30min: `/etc/cron.d/bianinho-health`
- ✅ Auto-alert when OAuth/token fail

### PILAR 2 — Mente Brilhante (Anticipatory Knowledge)
- ✅ RAG monitoring: 14.024 chunks, 23 fontes
- ✅ Proactive recall em cada sessão
- ⏳ Google Drive watch (pending OAuth)

### PILAR 3 — Zelador (Autonomous Maintenance)
- ✅ Backup to Google Drive: `~/.hermes/scripts/backup_to_drive.sh`
- ✅ Session archiver: `~/.hermes/scripts/archive_sessions.sh`
- ✅ Hermes auto-update ready
- ✅ Temp file cleanup

### PILAR 4 — Aprendente (Self-Evolution)
- ✅ Error-to-skill auto-capture
- ✅ Meta-cognition journal: `~/.hermes/meta_cognition_journal.jsonl` — **REDESENHADO 20/04** (existia mas nunca era chamado)
- ✅ Self-Improving Agent v2: `~/.hermes/scripts/bianinho_self_improving.py` — **REWRITE COMPLETO 20/04** (antes: quality 3.9/5 falso, depois: 2.7/5 honesto)
- ✅ Fitness tracker de skills: `~/.hermes/scripts/skill_fitness_tracker.py`
- ✅ Relatório semanal: `~/.hermes/self_evaluation.jsonl` com quality scoring objectivo

> **Lição aprendida (20/04/2026):** Sistemas de self-assessment podem ser fundamentalmente desonestos — produzem scores altos sem acesso a dados reais. Redesign: 5 fases (patterns, health, errors, meta-cognition, actions), quality score com deduções objectivas. Ver skill: `bianinho-self-assessment-redesign`

### PILAR 5 — Maestro (Orchestration)
- ✅ Proactive orchestration active
- ⏳ Full Google Workspace (Drive/Gmail/Calendar/Docs/Sheets) — pending OAuth
- ⏳ Subagent templates ready

## OAuth Google — Workflow Crítico
**Problema:** Browser OAuth abre no SERVIDOR, não no PC do Álvaro.
**Solução:** Extrair URL de auth e dar ao Álvaro colar no browser dele.

```bash
# Gerar URL (no servidor)
google_oauth_url="https://accounts.google.com/o/oauth2/auth?client_id=443336072194-emc1p7m6ovth7tc070dh0sqmep00rdna.apps.googleusercontent.com&redirect_uri=http%3A%2F%2Flocalhost%3A1&scope=https%3A%2F%2Fwww.googleapis.com%2Fauth%2Fdrive+https%3A%2F%2Fwww.googleapis.com%2Fauth%2Fgmail.readonly+https%3A%2F%2Fwww.googleapis.com%2Fauth%2Fgmail.send+https%3A%2F%2Fwww.googleapis.com%2Fauth%2Fcalendar+https%3A%2F%2Fwww.googleapis.com%2Fauth%2Fdocuments+https%3A%2F%2Fwww.googleapis.com%2Fauth%2Fspreadsheets&response_type=code&access_type=offline&prompt=consent"

# Guardar URL para Álvaro copiar
echo "$google_oauth_url" > ~/.hermes/oauth_url.txt
```

**Passos:**
1. Gerar URL com scopes completos (drive + gmail + calendar + docs + sheets)
2. Dar URL ao Álvaro (não abrir browser automaticamente)
3. Álvaro cola no browser, clica Allow
4. Redireciona para localhost:1 — Álvaro copia URL e envia
5. Extrair code= e trocar por access token

## Estado Final (20/04/2026)
- Hermes: v0.10.0 ✅
- Skills: 4+ sincronizadas ✅
- Cron jobs: 13 activos ✅
- Health checks: operacionais ✅
- RAG: ~56k chunks ✅
- Self-Improving Agent: v2 com quality scoring honesto ✅
- Meta-Cognition Journal: activo, primeira entry 20/04 ✅
- OAuth Drive: PENDENTE — aguardando code= do Álvaro
- Session DB: 60 sessões, 29.039 eventos

## Última Actualização
20/04/2026 — Redesenho completo do PILAR 4 (Self-Evolution). Skill nova: `bianinho-self-assessment-redesign`.
