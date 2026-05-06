---
name: bianinho-guardian-3-layer
description: Sistema Guardian de 3 camadas de defesa proactiva — Watchdog + Validator + Stress Test. Arquitectura completa, thresholds, filtros, e padrões anti-bug.
category: devops
tags: [guardian, watchdog, defesa, proactivo, segurança, auto-correção]
---

# Guardian 3-Layer Defence System

## Arquitectura

```
Camada 1: Guardian Watchdog     (every 15min) → Detecta e mata processos anómalos
Camada 2: Guardian Validator    (every 45min) → Valida que o Watchdog funciona
Camada 3: Guardian Stress Test (every 2h)    → Validação real end-to-end
```

**Problema que resolve:** Um sistema de auto-monitorização pode falhar silenciosamente. Precisamos de validar que o validador funciona — e de validar que o validador do validador funciona. Por isso 3 camadas.

## Ficheiros

| Ficheiro | Camada | Descrição |
|----------|--------|-----------|
| `~/.hermes/scripts/guardian_watchdog.py` | Layer 1 | Detecta e mata processos anómalos |
| `~/.hermes/scripts/guardian_validator.py` | Layer 2 | Valida Guardian (3 checks) |
| `~/.hermes/scripts/guardian_stress_test_cron.py` | Layer 3 | Stress test real via cron |
| `~/.hermes/scripts/guardian_stress_test.py` | Layer 3 | Teste manual original |

## Logs e Estado

- `~/.hermes/logs/guardian.log` — log do Guardian
- `~/.hermes/logs/guardian_state.json` — estado (kills, pids)
- `~/.hermes/logs/guardian_validator.log` — log do Validator
- `~/.hermes/logs/guardian_validator_state.json` — estado do Validator
- `~/.hermes/logs/guardian_stress_test.log` — log do Stress Test

## Cron Jobs

| Job ID | Camada | Schedule |
|--------|--------|----------|
| `00c8472fb615` | Guardian Watchdog | every 15min |
| `7e26dd33a3f5` | Guardian Validator | every 45min |
| `51396e392b02` | Guardian Stress Test | every 2h |

---

## Layer 1 — Guardian Watchdog

### Thresholds
```python
MAX_RESUME_AGE = 120      # 2 min — --resume agents >2min = loop
HIGH_CPU_THRESHOLD = 30    # 30% CPU sustained = anomalous
```

### O Que Detecta
1. Agentes hermes com `--resume` em loop (mesma sessão a repetir)
2. Processos com `--yolo --source tool` (heartbeat retry pattern)
3. Context-mode sidecars órfãos (PPID=1)
4. RAG duplicado (mais de 1 instância `venv/bin/python ... rag_service.py`)

### CRÍTICO — Filtro Positivo

**USA SEMPRE positive matching.** Filtros negativos como `"hermes" in line.lower()` são demasiado amplos e capturam bash wrappers.

```python
# ✅ CERTO — positive matching
has_hermes_gateway = "hermes-gateway" in line.lower() or "hermes_cli.main gateway" in line
has_rag = "venv/bin/python" in line and "rag_service.py" in line
has_context = "context-mode" in line.lower()
if not (has_hermes_gateway or has_rag or has_context):
    continue

# ❌ ERRADO — filtro demasiado amplo (captura bash wrappers)
if "hermes" not in line.lower() and "rag_service" not in line.lower():
    continue
```

**Bug real que aconteceu:** O filtro amplo matou o RAG service legítimo (PID 525067) porque o bash wrapper continha "rag_service.py" na linha do `ps aux`.

### Como Testar
```bash
python3 ~/.hermes/scripts/guardian_watchdog.py
# Output esperado: "Expected: 2 | Anomalous: 0"
# (2 = Hermes Gateway + RAG, 0 = nenhum anómalo)
```

---

## Layer 2 — Guardian Validator

### 3 Checks
1. **Execução recente** — Guardian executou há < 20min?
2. **Kills consistency** — Houve kills novos? Alerta se 3+ ciclos sem kills
3. **Stress test real** — Invoca `guardian_stress_test_cron.py` a cada 4 ciclos OK

**Check 3 NOTA:** Usa stress test REAL, não `--dry-run`. O `--dry-run` só simula detecção — não valida que o Guardian realmente mata.

### Estado do Validator
```python
{
  "guardian_total_kills": int,    # Total de kills no log
  "consecutive_ok": int,          # Ciclos sem kills novos
  "stress_test_pass": bool,       # Último stress test
  "last_run": str                 # ISO timestamp
}
```

### Como Testar
```bash
python3 ~/.hermes/scripts/guardian_validator.py
# Output esperado: "VALIDATOR: Sistema saudável — Guardian OK"
```

---

## Layer 3 — Guardian Stress Test

### Fluxo
1. Spawn agente-testemuante (`hermes chat --yolo --source tool`)
2. Poll a cada 5s (até 90s max)
3. Verifica se Guardian o matou
4. Reporta PASS/FAIL

### Como Testar
```bash
python3 ~/.hermes/scripts/guardian_stress_test_cron.py
# Output esperado: "RESULT: PASS — Guardian matou o agente em ~Xs"
```

### Validação
- Guardian matou em 30s (teste original)
- Guardian matou em 5s (teste rápido)

---

## Lições Aprendidas (Anti-Bug Patterns)

### 1. Filtros Negativos Capturam Bash Wrappers
Bash wrappers (`/usr/bin/bash -c ... rag_service.py ...`) contêm o nome do script que estão a executar. Um filtro como `"rag_service.py" in cmd`captura o wrapper E o processo real, fazendo o Guardian pensar que há 2 instâncias.

**Solução:** Positive matching + verificar `venv/bin/python` (só o processo real tem isto).

### 2. `preset: enabled` no systemd
Serviços com `preset: enabled` reactivam-se após `systemctl disable`. O único fix definitivo é remover o ficheiro `.service`.

```bash
# Não basta disable — o preset re-ativa
systemctl --user disable paperclip.service
rm ~/.config/systemd/user/paperclip.service  # Isto é que resolve
systemctl --user daemon-reload
```

### 3. Stress Test Real > Dry-Run
`--dry-run` simula detecção mas não verifica se o Guardian realmente mata. O stress test real spawna um processo e espera que o Guardian o elimine.

### 4. Validar que o Sistema de Defesa Funciona
O Validator valida que o Watchdog executa. O Stress Test valida que o Watchdog realmente mata. Sem estas validações, o Watchdog pode estar silenciosamente quebrado.

---

## Comandos de Verificação

```bash
# Estado do sistema
python3 ~/.hermes/scripts/guardian_watchdog.py
python3 ~/.hermes/scripts/guardian_validator.py
python3 ~/.hermes/scripts/guardian_stress_test_cron.py

# Ver logs
tail ~/.hermes/logs/guardian.log
tail ~/.hermes/logs/guardian_validator.log

# Ver estado
cat ~/.hermes/logs/guardian_state.json
cat ~/.hermes/logs/guardian_validator_state.json

# Listar cron jobs
hermes cron list
```
