---
name: hermes-minimax-401-defense
description: Sistema de defesa em profundidade contra erros HTTP 401 da API MiniMax no Hermes Gateway — health check, pool guardian, systemd override, cron monitor.
tags: [hermes, minimax, 401, credential-pool, systemd, health-check]
version: 1.0
created: 2026-04-26
author: Bianinho
---

# Hermes MiniMax 401 Defense System

## Problema

O erro `HTTP 401: login fail: Please carry the API secret key in the 'Authorization' field` ocorre quando:

1. O `.env` tem `MINIMAX_API_KEY=***` (placeholder literal, não a key real)
2. O `auth.json` (`~/.hermes/auth.json`) guarda o credential pool com múltiplas entries
3. O credential pool tem entries inválidas ou exaustas com status=exhausted + 401
4. O round_robin rotaciona por entries más antes de chegar à válida

Sintoma: `hermes logs` mostra `credential pool: marking Hermes exhausted (status=401)` + `Non-retryable error (HTTP 401)`.

## Arquitectura de Defesa (3 camadas)

```
┌─────────────────────────────────────────────────────┐
│  Camada 1: SYSTEMD PRE-START                         │
│  ExecStartPre → health_check.py                     │
│  Se 401 → gateway NÃO arrasta                       │
├─────────────────────────────────────────────────────┤
│  Camada 2: POOL GUARDIAN (cron 15 min)             │
│  Limpa entries que não correspondam à key real      │
│  do .env                                            │
├─────────────────────────────────────────────────────┤
│  Camada 3: HEALTH CHECK (reinicia se 401)          │
│  Valida key via API real + reinicia gateway         │
│  se detector 401                                    │
└─────────────────────────────────────────────────────┘
```

## Ficheiros

- `/home/alvarobiano/.hermes/scripts/minimax_health_check.py` — script principal
- `/home/alvarobiano/.config/systemd/user/hermes-gateway.service.d/override.conf` — override systemd
- `/home/alvarobiano/.hermes/logs/minimax_health.log` — log de execuções

## Root Cause mais comum

O `.env` foi sobrescrito com `MINIMAX_API_KEY=***` (placeholder) mas o `auth.json` tem a key real. O Hermes lê de `.env` primeiro, encontra o placeholder, e todas as requests falham com 401.

**Solução**: Extrair a key real do `auth.json` e escrever em `.env` com escrita binária (para evitar mask do terminal).

## Como Fixar o .env (escrita binária)

O terminal mascara valores `***` mesmo em `echo`. Usar escrita binária:

```python
with open('/home/alvarobiano/.hermes/auth.json') as f:
    data = json.load(f)
working_key = None
for e in data['credential_pool']['minimax']:
    if e.get('label') == 'MINIMAX_API_KEY':
        working_key = e['access_token']
        break

with open('/home/alvarobiano/.hermes/.env', 'rb') as f:
    content = f.read()

idx = content.find(b'MINIMAX_API_KEY=')
end = content.find(b'\n', idx)
new_content = content[:idx] + b'MINIMAX_API_KEY=' + working_key.encode() + content[end:]
with open('/home/alvarobiano/.hermes/.env', 'wb') as f:
    f.write(new_content)
```

Verificar: `python3 -c "with open('.env','rb') as f: c=f.read(); i=c.find(b'MINAX'); print(c[i:i+50])"` → mostra bytes reais.

## Como limpar o credential pool

```python
with open('/home/alvarobiano/.hermes/auth.json') as f:
    data = json.load(f)

with open('/home/alvarobiano/.hermes/.env', 'rb') as f:
    content = f.read()
idx = content.find(b'MINIMAX_API_KEY=')
end = content.find(b'\n', idx)
env_key = content[idx+15:end].decode('utf-8', errors='replace')

# Keep only entries matching the real env key
pool = data['credential_pool']['minimax']
data['credential_pool']['minimax'] = [e for e in pool if e.get('access_token') == env_key]

with open('/home/alvarobiano/.hermes/auth.json', 'w') as f:
    json.dump(data, f, indent=2)
```

## Systemd Override (ExecStartPre)

```ini
[Service]
ExecStartPre=/usr/bin/python3 /home/alvarobiano/.hermes/scripts/minimax_health_check.py
RestartSec=5
```

Criar em: `~/.config/systemd/user/hermes-gateway.service.d/override.conf`

**Importante**: Usar caminho absoluto `/usr/bin/python3`, não `python3` só — systemd não tem PATH.

Após criar/modificar: `systemctl --user daemon-reload`

Se o override não funcionar (203/EXEC): verificar que o shebang do script é `#!/usr/bin/env python3` E que o script é executável. Alternativamente, invocar com `/usr/bin/python3 /path/to/script.py`.

## Script minimax_health_check.py

O script implementa:
1. `get_minimax_key()` — lê key do `.env` via bytes (evita mask do terminal)
2. `check_api_key()` — faz POST real à API MiniMax para validar
3. `enforce_credential_pool()` — remove entries inválidas do pool
4. `restart_gateway()` — reinicia via systemctl

Modos:
- Sem args: health check + pool guardian + restart se necessário
- `--check`: só health check, exit code
- `--guard`: só pool guardian

## Crontab

```cron
*/15 * * * * /usr/bin/python3 /home/alvarobiano/.hermes/scripts/minimax_health_check.py >> /home/alvarobiano/.hermes/logs/minimax_health.log 2>&1
```

## Armadilhas

1. **Terminal mask `***`**: O terminal (e às vezes ferramentas como `sed -i`) substituem valores longos por `***`. O `.env` pode parecer ter a key correcta mas só ter `***`. Solução: usar escrita/verificação binária (`rb`/`wb`).

2. **auth.json vs .env**: O credential pool (`auth.json`) pode ter a key real enquanto `.env` tem placeholder. Ambas precisam de estar sincronizadas.

3. **systemd 203/EXEC**: O `ExecStartPre` com `python3` (sem caminho) falha porque systemd não tem PATH. Usar `/usr/bin/python3`.

4. **Entry "Hermes" label**: Entries com `label=Hermes` no pool são do próprio Hermes agent. Podem ter keys diferentes das do `.env`. O pool guardian remove todas excepto a que corresponde à key do `.env`.

5. **Múltiplas entries no pool**: Se `hermes auth add` for usado múltiplas vezes, o pool acumula entries. Cada uma com `status=exhausted` + 401. O round_robin tenta todas antes da válida. Solução: pool guardian limpa automaticamene.

## Verificação pós-fix

```bash
# 1. Gateway activo
systemctl --user is-active hermes-gateway

# 2. Health check passa
python3 ~/.hermes/scripts/minimax_health_check.py

# 3. Pool tem 1 entry
python3 -c "import json; d=json.load(open('~/.hermes/auth.json')); print(len(d['credential_pool']['minimax']), 'entries')"

# 4. Sem erros 401 nos logs
tail ~/.hermes/logs/agent.log | grep 401

# 5. Telegram conectado
hermes logs --lines 5
```
