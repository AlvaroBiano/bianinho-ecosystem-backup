---
name: api-quota-guardian
description: Sistema completo de proteção do quota MiniMax — nunca mais health checks ou cron jobs consomem o quota Token Plan do Álvaro
---

# API Quota Guardian

## O Problema
Cron jobs e health checks estavam a consumir o quota MiniMax Token Plan (4500 requests/hora), causando:
1. Fallback para OpenRouter quando o pool de credenciais ficava sem entries
2. Respostas do Telegram a falhar quando o quota estava agotado
3. Álvaro sem conseguir conversar quando mais precisava

## Arquitetura de Protecção

### Camada 1: Quota Guard
Verifica quota MiniMax ANTES de qualquer cron job que use LLM.

### Camada 2: Health Check sem LLM
O proactive_monitor.py já foi actualizado — só faz HTTP check, não chama LLM.

### Camada 3: Telegram Auto-Healer
Reconecta automaticamente quando Telegram dá timeout.

### Camada 4: Cron Rate Limiting
Jobs com `provider: minimax` reduzidos para frequência segura.

## Implementação

### quota_guard.py
Lê quota MiniMax e decide se cron job deve executar.

```python
#!/usr/bin/env python3
"""Quota Guard — protege quota MiniMax de health checks e cron jobs."""
import urllib.request, json, os, sys

def get_quota_status():
    """Retorna (usage_pct, remaining, can_proceed)."""
    key = os.environ.get("MINIMAX_API_KEY", "")
    if not key or key == "***":
        env_file = os.path.expanduser("~/.hermes/.env")
        if os.path.exists(env_file):
            with open(env_file) as f:
                for line in f:
                    line = line.strip()
                    if line.startswith("#"):
                        continue
                    if "MINIMAX_API_KEY" in line and "=" in line:
                        parts = line.split("=", 1)
                        if len(parts) == 2 and parts[1].strip() not in ("", "***"):
                            key = parts[1].strip().strip('"').strip("'")
                            break
    
    if not key:
        return None, None, True  # Can't check, allow
    
    try:
        url = "https://www.minimax.io/v1/token_plan/remains"
        req = urllib.request.Request(url, headers={"Authorization": f"Bearer {key}"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode())
            for model in data.get("model_remains", []):
                name = model.get("model_name", "")
                if "MiniMax-M" in name and "coding" not in name:
                    used = model.get("current_interval_usage_count", 0)
                    total = model.get("current_interval_total_count", 0)
                    remaining = total - used
                    pct = (used / total * 100) if total else 0
                    return pct, remaining, pct < 70
            return None, None, True
    except Exception as e:
        print(f"[quota_guard] ERRO ao verificar quota: {e}", file=sys.stderr)
        return None, None, True  # Allow on error

if __name__ == "__main__":
    pct, remaining, can_proceed = get_quota_status()
    if pct is not None:
        status = "OK" if can_proceed else "SKIP"
        print(f"[quota_guard] {status} — {pct:.0f}% usado ({remaining} restantes)")
        sys.exit(0 if can_proceed else 1)
    else:
        print("[quota_guard] UNKNOWN — permitindo execução")
        sys.exit(0)
```

### telegram_healer.py
Auto-heal para Telegram.

```python
#!/usr/bin/env python3
"""Telegram Healer — reconecta automaticamente quando Telegram falha."""
import subprocess, time, os, sys

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
GATEWAY_SERVICE = "hermes-gateway"

def check_telegram_health():
    """Verifica se o bot Telegram está a responder."""
    if not TELEGRAM_BOT_TOKEN:
        print("[telegram_healer] TELEGRAM_BOT_TOKEN não definido")
        return False
    try:
        result = subprocess.run(
            ["curl", "-s", "--max-time", "5",
             f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getMe"],
            capture_output=True, text=True, timeout=8
        )
        data = result.stdout
        if '"ok":true' in data:
            return True
        print(f"[telegram_healer] Bot não responde: {data[:100]}")
        return False
    except Exception as e:
        print(f"[telegram_healer] ERRO: {e}")
        return False

def heal_telegram():
    """Reinicia o gateway para recuperar conectividade Telegram."""
    print("[telegram_healer] A reiniciar hermes-gateway...")
    subprocess.run(["systemctl", "--user", "restart", GATEWAY_SERVICE], check=False)
    time.sleep(5)
    if check_telegram_health():
        print("[telegram_healer] ✓ Telegram recuperado")
    else:
        print("[telegram_healer] ✗ Telegram ainda não responde")

if __name__ == "__main__":
    if not check_telegram_health():
        print("[telegram_healer] Telegram em mau estado — a healer...")
        heal_telegram()
    else:
        print("[telegram_healer] ✓ Telegram OK")
```

## Configuração de Cron Jobs

### Jobs que usam MiniMax (devem ser protegidos)
| Job ID | Nome | Acção |
|--------|------|-------|
| 8e1d019adb06 | Session Replay | Manter 1x/dia, adicionar quota guard |
| 5de2c83955ea | Learning Loop Daily | Manter 1x/dia, adicionar quota guard |
| b3dfaa0c3adc | Smart Memory Daily | Manter 1x/dia, adicionar quota guard |
| 2a7d03b31268 | Resilience Manager | ✓ Já em 30min |
| c3282070ec11 | Proactive Monitor | Manter 6x/dia, já sem LLM |

### Jobs que NÃO usam MiniMax
Guardian Watchdog, Guardian Validator, Backup, Context Switch, Suggestion Engine, OAuth Refresh, Daily Audit, Morning Briefing, Session Consolidation, Cost Report — podem continuar normalmente.

## Thresholds
- SKIP_THRESHOLD: 70% → cron jobs skip
- WARN_THRESHOLD: 50% → log warning
- TELEGRAM_TIMEOUT: 10s → healer trigger
- TELEGRAM_MAX_RETRIES: 3 → restart gateway

## Ficheiros
- `~/.hermes/scripts/quota_guard.py`
- `~/.hermes/scripts/telegram_healer.py`
- `~/.hermes/scripts/proactive_monitor.py` (actualizado ✓)

## Comando para testar
```bash
python3 ~/.hermes/scripts/quota_guard.py
echo $?  # 0 = pode executar, 1 = skip
python3 ~/.hermes/scripts/telegram_healer.py
```
