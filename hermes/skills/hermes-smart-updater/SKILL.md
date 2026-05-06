---
name: hermes-smart-updater
description: Smart auto-update system for Hermes Agent — detects active sessions, safe windows, Telegram notifications, systemd restart, cron integration.
tags: [hermes, update, automation, systemd, telegram]
version: 1.0
created: 2026-04-17
author: Bianinho
---

# Hermes Smart Auto-Updater Pattern

## Quando usar

Criar um sistema de auto-update automático para qualquer projeto que:
- Tem install base em git
- Roda como serviço systemd
- Precisa de janela de update segura
- Deve notificar via Telegram

## Arquitetura

```
hermes_smart_updater.py
├── State file (.json)        — persiste last_check, last_update, pending_version
├── Git ops                   — fetch, describe, pull
├── Session detection         — gateway running, sessions DB, last activity
├── Safe window logic         — hour-based OR no recent activity
├── Telegram notifications    — before/after update
├── Service restart           — systemctl --user restart
└── Health check             — run post-update health script
```

## Estrutura do Script

```python
# 1. State management
STATE_FILE = Path("~/.hermes/.hermes_updater_state.json")

def load_state() / save_state()

# 2. Git operations
run_git(["fetch", "origin", "main"])
run_git(["pull", "origin", "main"])
get_current_version()  # git describe --tags --always
get_latest_version()   # git describe --tags --always origin/main

# 3. Session detection
is_gateway_running()               # systemctl --user is-active
get_recent_session_count(minutes)  # SQLite sessions DB query
get_last_activity_minutes_ago()    # MAX(timestamp) from events table

# 4. Safe window
is_safe_to_update() -> (bool, reason, wait_minutes)
# Returns True if:
#   - Gateway not running OR no recent sessions
#   - OR within hour window (e.g. 3-5 AM)
#   - wait_minutes = minutes until next safe window

# 5. Telegram
load_telegram_config()  # Reads config.yaml or .env
send_telegram(message)
_discover_telegram_chat_id(bot_token)  # Via getUpdates API

# 6. Service management
restart_gateway()   # systemctl --user restart hermes-gateway
restart_paperclip() # systemctl --user restart paperclip (if exists)

# 7. Health check
health_check()  # Runs scripts/health_check.py if exists

# 8. Modes
check_for_updates()  # fetch + compare + state update
perform_update()      # check + notify_before + pull + restart + notify_after
cron_mode()           # check + if safe apply else schedule via at(1)
```

## Padrão de Safe Window

```python
UPDATE_WINDOW_START = 3  # 3 AM
UPDATE_WINDOW_END = 5    # 5 AM
MAX_WAIT_MINUTES = 30    # force update after this even if unsafe

def is_safe_to_update():
    if is_gateway_running() and recent_sessions > 0:
        return False, f"Active sessions ({recent})", wait=15
    
    current_hour = datetime.now().hour
    if UPDATE_WINDOW_START <= current_hour < UPDATE_WINDOW_END:
        return True, "Within update window", 0
    
    # Calculate next window
    next_window = now.replace(hour=UPDATE_WINDOW_START) + (days=1 if past midnight else 0)
    wait = (next_window - now).minutes
    return False, f"Outside window", wait
```

## Padrão de Cron Job (Hermes cronjob tool)

```python
cronjob(action="create", name="Project Auto-Updater", prompt="""
python3 /path/to/updater.py --cron 2>&1
""", schedule="0 */6 * * *", repeat=999, deliver="local")
# Schedule: every 6h
# Deliver: local (logs only, no Telegram spam)
```

## Sessão Detection via SQLite

```sql
-- Count active sessions in last N minutes
SELECT COUNT(DISTINCT session_id) FROM events 
WHERE timestamp > datetime('now', '-{minutes} minutes')

-- Minutes since last activity
SELECT MAX(timestamp) FROM events
-- Parse and compute delta from datetime.now()
```

## Padrão de Restart Seguro

```python
# 1. Pre-notify via Telegram
send_telegram(f"🔄 Updating {project}...")

# 2. Git pull
code, out, err = run_git(["pull", "origin", "main"], timeout=120)
if code != 0:
    send_telegram(f"❌ Update failed: {err[:200]}")
    return

# 3. Restart services
subprocess.run(["systemctl", "--user", "restart", "hermes-gateway"], timeout=60)
subprocess.run(["systemctl", "--user", "restart", "paperclip"], timeout=60)

# 4. Health check
health_ok = health_check()

# 5. Post-notify
send_telegram(f"✅ Updated to v{version}" + ("" if health_ok else " (health check failed)"))
```

## Log Location

```
~/.hermes/logs/hermes_updater.log
```

## Armadilhas

1. **Git fetch precisa vir antes de describe** — senão `origin/main` está desatualizado
2. **Versão pode ser `None` na primeira run** — tratar como "unknown"
3. **State file pode estar corrompido** — usar try/except no load
4. **Telegram chat_id pode não estar no config** — usar `getUpdates` API como fallback
5. **at(1) pode não estar instalado** — wrap em try/except, cron job seguinte tenta de novo
6. **Usar venv python** — não python3 do sistema, pode ter dependências diferentes
7. **git stash pode falhar com "Cannot save the current status"** — quando há ficheiros untracked + modificados locais conflituantes. Fallback: usar a skill `hermes-update-with-local-changes` (backup /tmp → checkout → pull → restore).
8. **Lock files no namespace `salvage/` bloqueiam TODAS as operações git** — incluindo fetch. Sintoma: `hermes update` falha com "Cannot lock ref". Solução: `sudo rm -rf .git/refs/remotes/origin/salvage/` + `mkdir -p .git/logs/refs/remotes/origin/salvage/` + `sudo chown -R user:user .git/logs/refs/remotes/origin/salvage/`. Se persistir, `git remote prune origin` seguido de `git fetch --all` resolve.

9. **Cache `.update_check` pode mostrar "147 behind" mesmo depois de update correcto** — `hermes --version` lê este cache (TTL 6h). Limpar com `rm ~/.hermes/.update_check` após update manual.

10. **Após `git reset --hard`, venv pip pode ter sido sobrescrita** — reinstalar: `~/.hermes/hermes-agent/venv/bin/python3 -m pip install -e .`

11. **`.env` MINIMAX_API_KEY pode ter placeholder `***` literal** — o `.env` pode ser sobrescrito com `MINIMAX_API_KEY=***` (placeholder) enquanto `auth.json` tem a key real. O Hermes sourceia `.env` e usa placeholder → 401 em tudo. Fix: escrever a key real no `.env` via escrita binária (`rb`/`wb`) para evitar mask do terminal. Verificar: `python3 -c "with open('.env','rb') as f: c=f.read(); i=c.find(b'MINIMAX'); print(c[i:i+80])"`.

12. **Credential pool em `auth.json` acumula entries** — cada `hermes auth add` ou falha adiciona entry. Entries más ficam com `status=exhausted` + `last_error_code=401`. O round_robin tenta todas antes da válida. Pool guardian (cron 15 min) limpa automaticamene. Verificar: `python3 -c "import json; d=json.load(open('~/.hermes/auth.json')); print([(e['label'], e.get('last_status')) for e in d['credential_pool']['minimax']])"`.

## Fallback: Update manual quando hermes update falha

Quando `hermes update` bloqueia por lock files:

```bash
# 1. Limpar locks do salvage namespace (sudo necessário)
sudo rm -rf ~/.hermes/hermes-agent/.git/refs/remotes/origin/salvage/
mkdir -p ~/.hermes/hermes-agent/.git/logs/refs/remotes/origin/salvage/
sudo chown -R $(id -un):$(id -gn) ~/.hermes/hermes-agent/.git/logs/refs/remotes/origin/salvage/

# 2. Fetch directo (não usa stash)
git fetch origin main

# 3. Hard reset (sobrescreve mudanças locais — guarda stash primeiro se necessário)
git reset --hard origin/main

# 4. Reinstalar dependências na venv
~/.hermes/hermes-agent/venv/bin/python3 -m pip install -e .

# 5. Limpar cache do update check
rm ~/.hermes/.update_check

# 6. Reiniciar gateway
systemctl --user restart hermes-gateway
```

Verificar: `hermes --version` deve mostrar "Up to date" e `git describe --tags --always HEAD` deve coincidir com `git describe --tags origin/main`.

## Defesa permanente contra 401 — Pool Guardian + Health Check

O erro `HTTP 401: login fail: Please carry the API secret key` é causado por:
- `.env` sobrescrito com placeholder `***` literal (a key real fica em `auth.json`)
- Credential pool com entries más acumuladas (`status=exhausted`, `last_error_code=401`)
- Round-robin tenta as entries más antes da entry válida

### Sistema implementado em ~/.hermes/scripts/minimax_health_check.py

Executa em 3 camadas:
1. **ExecStartPre do systemd** — gateway só arr
2. **Cron 15 min** — pool guardian limpa entries más automaticamente
3. **Restart automático** — se 401 detectado, reinicia gateway

### Systemd override (já configurado)

~/.config/systemd/user/hermes-gateway.service.d/override.conf:
```
[Service]
ExecStartPre=/usr/bin/python3 /home/alvarobiano/.hermes/scripts/minimax_health_check.py
RestartSec=5
```

### Cron job (já configurado)

*/15 * * * * /usr/bin/python3 /home/alvarobiano/.hermes/scripts/minimax_health_check.py

### Script핵심: Pool Guardian

O script tem lógica dupla:
- get_minimax_key() — lê .env via binário, ignora mask do terminal
- check_api_key() — POST real à API MiniMax
- enforce_credential_pool() — mantém só entry que corresponde ao .env

### Verificação

tail ~/.hermes/logs/minimax_health.log

# Ver pool
python3 -c "import json; d=json.load(open('~/.hermes/auth.json')); print([(e['label'], e.get('last_status')) for e in d['credential_pool']['minimax']])"

# Ver .env key real (binário, ignora mask)
python3 -c "with open('/home/alvarobiano/.hermes/.env','rb') as f: c=f.read(); i=c.find(b'MINIMAX_API_KEY='); print(c[i:i+80])"

## Restart Completo (Rebuild + Reinício)

Quando o update envolve mudanças em código-fonte ou dependências (não só assets), fazer restart completo:

```bash
cd ~/.hermes/hermes-agent

# 0. Preservar mudanças locais (crítico — stash não funciona com untracked files)
git status --short
# Se M (modified) + ?? (untracked) coexistem → usar git add -A + commit
git add -A && git commit -m "feat(local): preserve local changes before update"
# Guardar o commit hash para referência: git log --oneline -1

# 1. Parar gateway
hermes gateway stop

# 2. Rebuild Python deps — venv Python é hardcoded (find retorna vazio)
#    O hermes-agent usa UV, pip direto falha com "externally managed"
~/.hermes/hermes-agent/venv/bin/python -m pip install -e ".[dev]" --quiet

# 3. Rebuild npm packages (node_modules está no raíz do projeto)
npm install 2>&1 | tail -3

# 4. Iniciar gateway
hermes gateway start

# 5. Verificar
sleep 5 && hermes gateway status
```

**Verificações pós-restart:**
- `Active: active (running)` — gateway no ar
- `API Health: Key is valid` — API key funcional
- `Memory` < 200 MB — bom sinal de cold start limpo (memória alta = leak ou órfãos)
- Hooks carregados visíveis nos logs (ex: `deep_reasoning`)

**Nota sobre a venv Python:** `find ~/.hermes/hermes-agent -name "python" -type f` retorna vazio neste ambiente. O path hardcoded `~/.hermes/hermes-agent/venv/bin/python` é o fiable. Usar SEMPRE este path para operações de pip/venv.

**Verificações pós-restart:**
- `Active: active (running)` — gateway no ar
- `API Health: Key is valid` — API key funcional
- `Memory` deve ser baixa (< 200 MB é bom sinal de cold start limpo)
- Hooks carregados visíveis nos logs (ex: `deep_reasoning`)

**Sinais de problema:**
- Memory > 1 GB → leak ou processos órfãos
- "HTTP 401" → key inválida, verificar .env
- "Cannot lock ref" → locks do git namespace salvage, ver armadilha #8

**Nota sobre a venv:** O hermes-agent NÃO usa `.venv` padrão — usa `venv/` no raíz do projeto. Isso significa que `find ~/.hermes/hermes-agent -name "python" -type f` retorna vazio; procurar em `~/.hermes/hermes-agent/venv/bin/python`.

## Verificação

```bash
python3 ~/.hermes/scripts/hermes_smart_updater.py --status
python3 ~/.hermes/scripts/hermes_smart_updater.py --check
tail -f ~/.hermes/logs/hermes_updater.log
```
