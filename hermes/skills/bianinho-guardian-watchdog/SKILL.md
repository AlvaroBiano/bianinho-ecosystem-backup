---
name: bianinho-guardian-watchdog
description: Guardian Watchdog — Camada 1 de defesa proactiva. Deteta e mata processos Hermes anómalos (em loop, CPU alta, órfãos). Positive matching filter — não usa filtros negativos amplos.
category: proativo
---

# Guardian Watchdog

## O Que Faz
Deteta e mata processos Hermes anómalos antes que consumam recursos do servidor.

## Arquitectura
```
paperclipai run (PID)
  └─ hermes chat --resume Product/Social/CEO/Content Agent (PPID = paperclipai)
       └─ loop infinito contra porta 3100 offline
```
O `paperclipai run` é o **parent** que faz heartbeat wake dos agentes. Se existir, os agentes vão sempre voltar em loop. Matar só os agentes não resolve — é preciso matar o parent.

## Detecção (thresholds actuais — 20/04/2026)

| Tipo | Threshold | Razão |
|------|-----------|--------|
| `paperclipai run` (node parent) | **REMOVIDO** | Paperclip eliminado — 20/04/2026 |
| Agente `--resume` + age > 120s | Imediato | Sobreviveu 2min = loop |
| Agente `--resume` + CPU > 30% | Imediato | Consumos anómalos |
| Agente com `--yolo --source tool` + age > 60s | Imediato | Heartbeat retry loop |
| rag_service.py duplicado | > 1 instance | Só 1 permitido |
| context-mode orphan | PPID = 1 | Sem pai activo |

## CRÍTICO — Filtro Positivo (Bug Corrigido 20/04/2026)

**O Guardian matou o RAG service legítimo** porque o filtro `"hermes" in line.lower()` era demasiado amplo e capturava bash wrappers.

**Solução — Positive matching:**
```python
has_hermes_gateway = "hermes-gateway" in line.lower() or "hermes_cli.main gateway" in line
has_rag = "venv/bin/python" in line and "rag_service.py" in line
has_context = "context-mode" in line.lower()
if not (has_hermes_gateway or has_rag or has_context):
    continue
```

**Filtros negativos NUNCA:**
```python
# ❌ ERRADO — captura bash wrappers que contêm "rag_service.py"
if "rag_service.py" not in line.lower(): continue
```

## Scripts Actuais
- `~/.hermes/scripts/guardian_watchdog.py` — Guardian Watchdog (Layer 1)
- `~/.hermes/scripts/guardian_validator.py` — Guardian Validator (Layer 2)
- `~/.hermes/scripts/guardian_stress_test_cron.py` — Guardian Stress Test (Layer 3)

## Papel no Sistema 3 Camadas
Ver: skill `bianinho-guardian-3-layer`

## Estado (20/04/2026)
- Paperclip REMOVIDO: `npm uninstall -g paperclipai` ✅, serviço removido ✅, `~/.paperclip` gone ✅
- Guardian OK: `Expected: 2 | Anomalous: 0` (Hermes Gateway + RAG legítimos)
- Bug do filtro corrigido com positive matching

## Descobertas de Campo (20/04/2026)

### `paperclipai run` pode reactivar-se
O serviço systemd (`paperclip.service`) pode estar **disabled** mas o processo ainda pode ser invocado por:
- `npm exec paperclipai run`
- `node paperclipai run`
- Outro processo de startup

**O Guardian agora detecta o parent `paperclipai run`** mesmo sem ser via systemd.

### CEO Agent também é padrão de loop
Os padrões conhecidos são: `Product Agent`, `Social Agent`, `Content Agent`, `CEO`
Todos fazem heartbeat wake contra a porta 3100 offline.

## Scripts
- `~/.hermes/scripts/guardian_watchdog.py` — Main watchdog (detecção paperclipai inclusive)
- `~/.hermes/scripts/guardian_stress_test_cron.py` — Camada 3 (stress test real via cron)
- `~/.hermes/scripts/guardian_validator.py` — Camada 2 (validação do Guardian)

## Como Testar
```bash
python3 ~/.hermes/scripts/guardian_watchdog.py --dry-run  # Ver sem matar
python3 ~/.hermes/scripts/guardian_stress_test_cron.py      # Teste real (spawn → verify → kill → report)
```

## Cron Job
- Job ID: `00c8472fb615`
- Schedule: every 15min
- Delivery: local

## Root Cause Conhecida (Paperclip REMOVIDO)
Paperclip foi completamente eliminado em 20/04/2026. Se aparecerem loops, verificar:
1. Outro processo a fazer spawn de agentes (não paperclipai)
2. Agentes `--resume` órfãos sem pai

## Quick Fix (context-aware)
```bash
# Ver o que está em loop
ps aux | grep -E "hermes.*--resume" | grep -v grep

# Se forem agentes hermes em loop:
# O Guardian (Layer 1) já trata — verificar se está a funcionar
python3 ~/.hermes/scripts/guardian_watchdog.py

# Se o Guardian não os apanha, verificar thresholds
# (MAX_RESUME_AGE=120s, HIGH_CPU=30%)
```
