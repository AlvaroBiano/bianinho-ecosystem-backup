---
name: proativo-master
description: "Meta-skill — Bianinho Proativo. Acesso centralizado a todos os comandos proactivos. Estado real: 14 cron jobs, 5 pilares operacionais, auto-healing activo."
category: proativo
---

# Proativo Master Skill

## Comandos Disponíveis

### Status do Sistema
```
/proativo status
```
Mostra resumo de estado — processos, serviços, espaço, RAM, token Google OAuth.

### Health Check
```
/proativo health
```
Executa `autoheal_monitor.py` — 9 verificações com auto-correcção.

### Auto-Improvement
```
/proativo improve
```
Executa `auto_improver.py` — ciclo autónomo. Implementa melhorias sem perguntar.

### Self-Improving Agent
```
/proativo selfimprove
```
Executa `bianinho_self_improving.py` — self-reflection, skill fitness, corrections log.

### Backup
```
/proativo backup
```
Executa backup local. Backup Google Drive disponível via OAuth.

### Google OAuth Status
```
/proativo oauth
```
Verifica estado do token Google OAuth (Drive, Gmail, Calendar, Docs, Sheets).

## Scripts Subjacentes (Estado Real)

| Script | Função |
|--------|--------|
| `autoheal_monitor.py` | 9 checks + auto-correction. Hermes/Gateway, RAG, LanceDB, MiniMax, Google OAuth, disco, RAM, temp, serviços |
| `auto_improver.py` | Ciclo autónomo — implementa, não pergunta |
| `bianinho_self_improving.py` | Self-Improving Agent — reflections, corrections, skill fitness, tiered memory |
| `proactive_monitor.py` | 5 checks + auto-restart RAG |
| `google_token_refresh.py` | Refresh token Google OAuth |
| `proactive_recall_cron.py` | Recall proactivo sobre sessões |
| `skills_guard.py` | Validação segurança skills (40+ patterns) |

## Cron Jobs Reais (14)

| Job | Schedule |
|-----|----------|
| Proativo Health Monitor | `*/15 * * * *` |
| Proactive Monitor | `every 30m` |
| System Health Monitor | `every 30m` |
| Manutenção/Saúde | `0 * * * *` |
| Google OAuth Refresh | `0 */6 * * *` |
| Proactive Recall | `0 */4 * * *` |
| Self-Improving Agent | `0 8 * * *` |
| Auto-Improver | `0 9,11,13,15,17,19,21 * * *` |
| Hermes Auto-Updater | `0 */6 * * *` |
| Session Consolidation | `0 23 * * *` |
| CEO Daily Review | `0 8 * * *` |
| CEO Weekly Prioritization | `0 9 * * 1` |
| Auditoria Segurança | `0 22 * * *` |
| Weekly Digest | `0 9 * * 1` |

## Regra de Ouro da Proactividade

**NÃO pedir confirmação — AGIR e só reportar se bloqueado.**

Padrão antigo (errado):
```
Cron → Gera sugestão → Manda p/ Telegram → Álvaro decide → Eu faço
```

Padrão correcto:
```
Cron → Identifica oportunidade → Implementa → Só reporta se bloqueado ou concretizado
```

**Silêncio total quando OK. Notificação só quando problema real + correcção aplicada.**
