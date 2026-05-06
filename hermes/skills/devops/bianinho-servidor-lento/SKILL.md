---
name: bianinho-servidor-lento
description: "Diagnóstico de servidor lento — identificação rápida de causas comuns: sessions explosion, cron duplicado, I/O wait em BTRFS, health monitors em conflito"
category: devops
tags: [servidor, diagnóstico, lentidão, performance, sessions, cron, iowait]
---

# Bianinho — Diagnóstico de Servidor Lent

## Quando usar
Servidor lento, load elevado (> 1.5), CPU com I/O wait alto, ou não saber porque o sistema está sobrecarregado.

## Diagnóstico Rápido — 5 comandos

```bash
uptime && top -b -n 1 | head -20
vmstat 1 3
ls ~/.hermes/sessions/*.json | wc -l && du -sh ~/.hermes/sessions/
crontab -l && hermes cron list
pgrep -a python | grep -v grep
```

## Causas Comuns e Como Identificar

### 1. Session Explosion (959MB, 3.000+ sessões)
**Sintoma:** `~/.hermes/sessions/` > 500MB ou > 500 ficheiros. Load alto, muitos processos python.

**Causa:** Scripts que usam `delegate_task`, `hermes chat -Q`, ou spawning de subagentes Hermes criam uma sessão por execução. Se um cron job corre a cada 30min há dias, multiplica-se rapidamente.

**Identificar:**
```bash
ls -lt ~/.hermes/sessions/session_*.json | head -20
ls -lt ~/.hermes/sessions/*.json | awk '{print $6,$7,$8}' | sort | uniq -c | sort -rn | head
```

**Fix imediato:**
```bash
ls -t ~/.hermes/sessions/*.json | tail -n +51 | xargs rm -f
```

**Prevenir:** Health monitors e scripts de monitorização devem usar `subprocess` directo em vez de `delegate_task` ou `hermes chat -Q`.

---

### 2. Cron Duplicado (2 health monitors em paralelo)
**Sintoma:** Load 2x o esperado, mesma verificação feita duas vezes.

**Causa:** Existe um health monitor no cron do sistema E outro via `hermes cron`. Ambos correm em paralelo.

**Identificar:**
```bash
crontab -l
cat /etc/cron.d/*
hermes cron list
```

**Fix:** Manter só UM health monitor — tipicamente o mais recente (hermes cron). Remover o legado:
```bash
crontab -l | grep -v "proativo_health_monitor.py" > /tmp/cron.txt && crontab /tmp/cron.txt
```

---

### 3. I/O Wait > 15% em BTRFS
**Sintoma:** `vmstat 1` mostra `wa` > 15%. Load alto mas CPU% normal.

**Causa mais comum:** `timeshift --check --scripted` a correr de hora em hora (:00). Em BTRFS, faz scan massivo de snapshots.

**Identificar:**
```bash
cat /etc/cron.d/timeshift-hourly
grep timeshift /var/log/syslog | tail -5
```

**Fix:**
```bash
sudo sed -i 's/^0 \* \* \* \* root/0 * * * * root #DISABLED: timeshift/' /etc/cron.d/timeshift-hourly
```

---

### 4. Swap em uso (si/so em vmstat)
**Sintoma:** `vmstat 1` mostra si/so > 0.

**Fix:**
```bash
sudo sync && echo 3 | sudo tee /proc/sys/vm/drop_caches
```

---

## Limpeza Pós-Diagnóstico

```bash
# Sessões Hermes antigas — manter 50 mais recentes
ls -t ~/.hermes/sessions/*.json | tail -n +51 | xargs rm -f
du -sh ~/.hermes/sessions/
```

## Métricas de Referência — Estado Saudável

| Métrica | Valor normal | Alerta |
|---------|------------|--------|
| Load average | < 1.0 | > 1.5 |
| I/O wait (wa) | < 5% | > 15% |
| RAM disponível | > 5GB | < 2GB |
| Swap usado | < 10% | > 30% |
| Sessões Hermes | < 100 | > 500 |
| Disco sessions/ | < 100MB | > 500MB |

## Fonte
Descobertas em produção — 20/04/2026 — Álvaro reported server slowness.
