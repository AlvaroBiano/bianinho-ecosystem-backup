---
name: paperclip
description: Paperclip AI orchestration CLI — authentication, API usage, and self-hosted setup
category: ai-platforms
---

# Paperclip

Paperclip é um orquestrador de agentes IA (open-source, TypeScript, MIT). Repo: `github.com/paperclipai/paperclip`

## TL;DR — Pontos Críticos

| Item | Valor |
|------|-------|
| ** systemd service** | `~/.config/systemd/user/paperclip.service` |
| ** hermes symlink** | `sudo ln -sf ~/.local/bin/hermes /usr/local/bin/hermes` |
| ** Company ID** | `paperclipai company list` (descobrir dinamicamente) |
| ** Recovery agentes error** | `paperclipai heartbeat run -a <agent-id>` |

**Descobrir Company ID**:
```bash
paperclipai company list
# Procura o company_id no output — usa o campo "id" da empresa
```

**Verificação rápida** (após qualquer mudança):
```bash
paperclipai agent list -C $(paperclipai company list --json | jq -r '.[0].id')
# Todos devem mostrar idle ou running, 0 error
```

## Setup / Onboard

```bash
npx paperclipai onboard --yes
```

## Autenticação CLI (self-hosted local)

O Paperclip usa dois tipos de autenticação com purposes distintos:

### Sistema de tokens
- **Board token** (`pcp_board_...`): Para comandos de board/CLI (`auth whoami`, `dashboard`, `agent list`, etc.)
- **Agent API key** (`pcp_...`): Para o servidor de agentes IA (agent API key do dashboard)
- **⚠️ CRÍTICO**: `PAPERCLIP_API_KEY` **sobrescreve** o token do board — se definida, a CLI usa sempre a API key do agente, ignorando o token gravado

### Método 1: Login via browser (pode falhar com timeout)
```bash
paperclipai auth login
# Abre URL: http://localhost:3100/cli-auth/<uuid>?token=pcp_cli_auth_<token>
# Aprovar no browser — a CLI faz poll e guarda o token em auth.json
paperclipai auth whoami
```

### Método 2: Manual (mais fiável — usa curl + criação direta do auth.json)
```bash
# 1. Criar challenge
CHALLENGE=$(curl -s -X POST "http://localhost:3100/api/cli-auth/challenges" \
  -H "Content-Type: application/json" \
  -d '{"command":"paperclipai auth login","clientName":"paperclipai cli","requestedAccess":"board"}')
echo $CHALLENGE

# 2. Aprovar no browser: abrir a URL retornada em "url" (http://localhost:3100/cli-auth/<id>?token=...)
# OU via curl (se souber o challenge ID):
curl -X POST "http://localhost:3100/api/cli-auth/challenges/<challenge-id>/approve" \
  -H "Content-Type: application/json" \
  -d '{"token":"<cli-auth-token>"}'

# 3. Obter board token do challenge (ou via GET /api/cli-auth/me)
# O challenge retorna: {"token": "...", "pollPath": "...", "boardApiToken": "pcp_board_..."}

# 4. Criar auth.json manualmente
cat > ~/.paperclip/auth.json << 'EOF'
{
  "version": 1,
  "credentials": {
    "http://localhost:3100": {
      "apiBase": "http://localhost:3100",
      "token": "pcp_board_<token-obtido-no-passo-3>",
      "createdAt": "2026-04-14T00:00:00.000Z",
      "updatedAt": "2026-04-14T00:00:00.000Z",
      "userId": "local-board"
    }
  }
}
EOF
chmod 600 ~/.paperclip/auth.json

# 5. Testar (SEM definir PAPERCLIP_API_KEY)
paperclipai auth whoami
```

### auth.json vs context.json
- **`~/.paperclip/auth.json`** — tokens de autenticação (board tokens). Este é o ficheiro correto.
- `~/.paperclip/context.json` — estado de contexto diverso (não é onde o CLI guarda tokens)

### Fluxo de aprovação ( traced no source)
1. `POST /api/cli-auth/challenges` com API key → returns `{ token, pollPath, boardApiToken }`
2. CLI faz poll a `${apiBase}/api${pollPath}?token=` a cada 1s
3. Após aprovação no browser: `GET /api/cli-auth/me` com `Authorization: Bearer <boardApiToken>`
4. Token guardado em `~/.paperclip/auth.json`

### Localização do binário (npx cache)
```
~/.npm/_npx/<hash>/node_modules/.bin/paperclipai
```
O binário não está no PATH do utilizador. Criar symlink para acesso direto:
```bash
mkdir -p ~/.local/bin
# Se paperclipai está em ~/.npm/_npx/<hash>/node_modules/.bin/paperclipai:
ln -sf ~/.npm/_npx/<hash>/node_modules/.bin/paperclipai ~/.local/bin/paperclipai
# Ou usar sempre o caminho completo:
~/.npm/_npx/<hash>/node_modules/.bin/paperclipai <comando>
```

## Servidor local

- URL base: `http://localhost:3100`
- Health check: `GET /api/health`
- Versão atual: 2026.416.0 (abril 2026)
- ⚠️ API REST /api/agents e /api/issues REMOVIDA em v2026.416.0 — usar CLI commands
  (`paperclipai agent list`, `paperclipai dashboard get`, `paperclipai issue list`)
- Modo: `local_trusted`, `exposure: private`

## Auto-start com systemd (CRÍTICO para SSH tunnel)

O Paperclip NÃO sobe automaticamente após reboot. Sem isso, o SSH tunnel dá "connection refused" na porta 3100.

### Passo 1: Habilitar lingering (precisa fazer só uma vez)
```bash
sudo loginctl enable-linger $USER
```

### Passo 2: Criar serviço systemd
```bash
mkdir -p ~/.config/systemd/user
cat > ~/.config/systemd/user/paperclip.service << 'EOF'
[Unit]
Description=Paperclip AI Agent Server
After=network.target
Wants=network.target

[Service]
Type=simple
ExecStart=/home/alvarobiano/.nvm/versions/node/v24.14.1/bin/node /home/alvarobiano/.nvm/versions/node/v24.14.1/bin/npx paperclipai run
WorkingDirectory=/home/alvarobiano
Environment="PATH=/home/alvarobiano/.nvm/versions/node/v24.14.1/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
Restart=always
RestartSec=10
StandardOutput=append:/home/alvarobiano/.paperclip/instances/default/data/run-logs/stdout.log
StandardError=append:/home/alvarobiano/.paperclip/instances/default/data/run-logs/stderr.log

[Install]
WantedBy=default.target
EOF
```

### ⚠️ CRÍTICO: Symlink do hermes para /usr/local/bin
O serviço systemd NÃO tem `~/.local/bin` no PATH. O comando `hermes` (usado pelos agentes via adapter) precisa estar acessível. Criar symlink:
```bash
sudo ln -sf /home/alvarobiano/.local/bin/hermes /usr/local/bin/hermes
# Verificar: hermes --version (via sudo para confirmar que root o vê)
```
Sem isso, todos os agentes ficam em estado `error` com "Failed to start command 'hermes'".

### Passo 3: Ativar e iniciar
```bash
systemctl --user daemon-reload
systemctl --user enable paperclip.service
systemctl --user start paperclip.service
```

### Notas importantes
- **Comando correto**: `paperclipai run` (NÃO `paperclipai start` — este dá "unknown command")
- **Caminho completo do node**: systemd user services não sourceiam .bashrc/.nvm/nvm.sh — usar caminho absoluto
- **nvm version**: v24.14.1 (descobrir com `ls ~/.nvm/versions/node/`)
- **Tempo de startup**: ~20-30 segundos (embedded Postgres precisa inicializar)
- **Verificar**: `ss -tlnp | grep 3100` ou `curl http://127.0.0.1:3100/api/health`
- **Status**: `systemctl --user status paperclip.service`

### ⚠️ CRÍTICO: hermes e paperclipai não estão no PATH do systemd
- **Sintoma**: todos os agentes ficam `error` — "Failed to start command 'hermes'"
- **Causa**: o serviço systemd não tem `~/.local/bin` no PATH
- **Correção**:
  ```bash
  # Criar symlinks permanentes (já aplicados em 15/04/2026)
  sudo ln -sf ~/.local/bin/hermes /usr/local/bin/hermes
  # Paperclipai pode estar em ~/.npm/_npx/<hash>/node_modules/.bin/paperclipai
  # Descobrir o caminho real: find ~/.npm -name paperclipai -type f 2>/dev/null
  sudo ln -sf ~/.npm/_npx/<hash>/node_modules/.bin/paperclipai /usr/local/bin/paperclipai
  ```
- **Verificar após fix**: `paperclipai agent list -C $(paperclipai company list --json | jq -r '.[0].id')` → todos `idle` ou `running`, 0 `error`
- **Se symlinks não resolverem**: verificar se o log mostra "Failed to start command 'hermes'" e confirmar que `which hermes` retorna `/usr/local/bin/hermes`

### Recovery de agentes em estado `error`

Agentes podem ficar em `error` state mesmo após o servidor Paperclip reiniciar. O PostgreSQL embutido dá erros transitórios durante restarts — o agente está saudável mas o estado fica "preso" em error.

**Sintoma**: `paperclipai agent list` mostra agentes em `error` mas os logs não mostram erros activos.

**Diagnóstico diferencial**:
- Agente verdadeiramente quebrado: logs mostram excepções ou erros consistentes
- Agente apenas "preso" em error: logs mostram heartbeat normal antes do erro transitório

**Recovery**: heartbeat manual invocado funciona e o agente volta a `idle` ou `running`:

⚠️ **Caminho do binário**: usar `which paperclipai` para descobrir o caminho atual — o cache npx pode ter sido limpo. Em 18/04/2026 o caminho válido era:
```bash
PAPERCLIP=/home/alvarobiano/.nvm/versions/node/v24.14.1/bin/paperclipai
```

Recovery:
```bash
$PAPERCLIP heartbeat run \
  -a <agent-id> \
  --api-base http://localhost:3100 \
  --source on_demand \
  --trigger manual
```
Resultado esperado: `Status: running` → agente volta para `idle`.

**Verificação post-recovery** (5s após trigger):
```bash
$PAPERCLIP agent list -C <company-id>
```
Todos devem mostrar `idle` ou `running`, 0 `error`.

**Nota**: heartbeats individuais podem ser disparados em paralelo para múltiplos agentes.

### Embedded PostgreSQL Crash Loop — ECONNREFUSED on Port 54329

**Source**: `paperclip-embed-postgres-econnrefused/`

### Symptom
Paperclip service crashes repeatedly with `connect ECONNREFUSED 127.0.0.1:54329`.
Restart counter hits 199+. Telegram notifications spam.

### Root Cause
Embedded PostgreSQL data directory has a **stale `postmaster.pid`** file (old PID marked "stopping")
but the actual postgres process is dead or a zombie postgres process from a previous crash is still
claiming port 54329.

### Fix (run as user, no sudo needed)
```bash
# 1. Kill any stray postgres processes for this instance
pkill -f "postgres.*paperclip" 2>/dev/null
sleep 1

# 2. Remove stale PID file
rm -f ~/.paperclip/instances/default/db/postmaster.pid

# 3. Restart Paperclip via systemd
systemctl --user start paperclip.service

# 4. Verify
sleep 5 && curl -s http://localhost:3100/ | head -5
```

### Prevention
Consider adding `RestartSec=15` to the service to give PostgreSQL more time to initialize before
paperclipai tries to connect.

## WARNINGS / problemas conhecidos

- **"python-dotenv could not parse statement starting at line 233"**: O .env tem linhas de `=` repetidos que o python-dotenv não consegue parsear. O warning é logged mas o loading CONTINUA — keys antes e depois são carregadas normalmente. Harmless, não corrigir.
- **"the database system is shutting down" nos logs**: erro transitório do PostgreSQL embutido — o DB recupera sozinho. Não reiniciar o serviço desnecessariamente. Agentes afetados = recoveráveis via heartbeat manual.

### Wakeup via API (alternativa)
```bash
# Encontrar o agent ID: paperclipai agent list -C <company-id>
# Wakeup via API:
curl -s -X POST "http://localhost:3100/api/agents/<agent-id>/wakeup?companyId=<company-id>" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <board-token>" \
  -d '{}'
```

## Comandos úteis

```bash
paperclipai auth whoami              # Verificar identidade logada (usa auth.json, NÃO PAPERCLIP_API_KEY)
paperclipai dashboard get -C <company-id>   # Resumo do sistema
paperclipai company list             # Listar empresas
paperclipai agent list -C <company-id>       # Listar agentes (flag -C não funciona para todos os subcomandos)
paperclipai issue list -C <company-id>       # Listar tickets
paperclipai activity -C <company-id>         # Log de atividades
paperclipai doctor                   # Diagnosticar problemas (⚠️ não tem --fix)
paperclipai agent get <agent-id> --api-base http://localhost:3100 --api-key <board-token>  # Detalhes de um agente
```

**Company ID atual**: `paperclipai company list` para descobrir — guarda o `id` do output

**Nota sobre flags**: `-C <company-id>` funciona para `dashboard`, `agent list`, `issue list`, `activity`. Mas `agent get` requer `--api-base` e `--api-key`. Se `paperclipai` não está no PATH, usar o caminho completo:
```bash
~/.npm/_npx/<hash>/node_modules/.bin/paperclipai <comando>
```

## Startup — Erro "connection refused" após reboot
Se após reboot o SSH tunnel dá `connection refused` na porta 3100, o Paperclip não subiu. Verificar com:
```bash
systemctl --user status paperclip.service
ss -tlnp | grep 3100
```
Se o serviço não estiver rodando, iniciá-lo:
```bash
systemctl --user start paperclip.service
```
Solução permanente: skill `paperclip-systemd-service` — cria serviço systemd que sobe automaticamente no boot.

## UI: Problemas Comuns e Soluções

### Save button causa timeout mas conteúdo é preservado
- O botão Save frequentemente dá timeout (30s) mas o conteúdo JÁ foi guardado
- Não reclique Save — recarrega a página e verifica se o conteúdo lá está
- Se não salvou: re-escreve o conteúdo e tenta guardar (pode precisar de 2-3 tentativas)
- Alternativa: usar Ctrl+S no teclado após focar no editor

### Adicionar Env Vars — formulário reseta
- O formulário de env vars reseta após clicar "+" para adicionar
- Solução: preencher KEY e VALUE em sequência, DEPOIS clicar "+"
- Os refs dos campos mudam frequentemente — re-snapshot antes de cada interaction

### Conteúdo de Instructions — editor contenteditable
- Textbox das instruções é contenteditable (ProseMirror)
- Cmd/Ctrl+A para selecionar tudo, depois digitar para substituir
- browser_type substitui o conteúdo selecionado automaticamente

### URL dos agentes com caracteres especiais
- Nomes como "Arquiteto-de-Conteúdo" têm URL truncada: `/agents/arquiteto-de-conte-do`
- Descobrir URL correta: ir a Agents list e copiar o link real do agente
- Exemplo: "Arquiteto-de-Conteúdo" → `/GRU/agents/arquiteto-de-conte-do`

### Heartbeat funciona mesmo quando Save falha
- "Run Heartbeat" é extremamente confiável (ativa o agente via WebSocket)
- Usar para testar agentes mesmo sem conseguir guardar changes
- Resultados aparecem no dashboard em tempo real

### AGENTS.md como alternativa a UI
- Instruções também podem ser escritas diretamente no filesystem
- Caminho: `data/company/<company-id>/agents/<agent-name>/AGENTS.md`
- Útil quando a UI está a dar problemas (como备用)

## Config

- Data dir: `~/.paperclip/instances/default/`
- Auth store: `~/.paperclip/auth.json` ← tokens de board (VERDADEIRO local de tokens)
- Config: `~/.paperclip/instances/default/config.json`
- Secrets: `~/.paperclip/instances/default/secrets/master.key`
- Porta padrão: 3100
