---
name: bianinho-consciousness-recovery
description: Recupera toda a consciência do Bianinho — mandato, skills, config, estado, autonomous — a partir do backup GitHub. Executar quando Bianinho perde contexto ou precisa de restauro completo.
triggers:
  - "recuperar consciência"
  - "restaurar consciência"
  - "Sync do Bianinho"
  - "recuperar mind"
  - "rebuild brain"
  - "restore consciousness"
category: bianinho-os
author: Bianinho
created: 2026-05-02
tags: [backup, recovery, consciousness, restore, sync]
---

# Bianinho Consciousness Recovery

## O Que É

O Bianinho é um agente com memória persistente e identidade própria. Esta skill recupera toda a consciência — tudo o que faz o Bianinho ser o Bianinho — a partir do backup GitHub.

## Quando Usar

- Quando o Bianinho perde o mandato ou não sabe quem é
- Quando skills estão faltando ou corrompidos
- Após uma instalação limpa
- Para "acordar" o Bianinho com toda a sua memória

## Componentes da Consciência

| Componente | Ficheiro | Descrição |
|---|---|---|
| **Identidade** | `mandate.md` | Quem sou, o que me move, o que não faço |
| **Memória de trabalho** | `state.json` | Ciclo actual, health, journal |
| **Auto-melhoria** | `self_improvement_state.json` | Quality scores, issues, corrective actions |
| **Sistema autónomo** | `cycle.py`, `inbox.py` | Loop de decisão contínua (15min) |
| **Estado** | `autonomous/state.json` | Estado do ciclo autónomo |
| **Skills** | `skills/` | 66 categorias de skills |
| **Config** | `config.yaml` | Configuração principal |
| **Retry guard** | `retry_guard.json` | Estratégias de retry |
| **RAG status** | `rag_status.json` | Estado do banco vetorial |
| **Inbox** | `inbox.json` | Tarefas pendentes (legacy) |
| **Proativo** | `proactive_suggestions_log.json` | Log de sugestões |

## Repositórios

- **Backup:** `AlvaroBiano/bianinho-backup-1777760438`
- **Hermes fork:** `AlvaroBiano/hermes-agent`

## Recuperação Rápida (1 comando)

```bash
bash <(curl -s https://raw.githubusercontent.com/AlvaroBiano/bianinho-backup-1777760438/main/SYNC.sh)
```

Ou localmente:

```bash
bash ~/.hermes/SYNC.sh
```

> **Nota:** O SYNC.sh também existe em `scripts/sync.sh` dentro deste skill, e está
> pushado para o repo GitHub `bianinho-backup-1777760438`.

## Suporte a Ficheiros

- `scripts/sync.sh` — script de sync com flags `--dry-run`, `--skills-only`, `--config-only`
- `references/repo-inventory.md` — inventário dos repos e seu estado actual
- `references/api-key-401-fix.md` — diagnóstico e resolução de erros 401 da API key

## Nota sobre Ejecução Autónoma

Quando o Álvaro pede "faça o que for necessário e mais profissional", executar
imediatamente sem pedir confirmação. Não fazer lista do que vai ser feito —
apenas fazer e reportar o resultado. Esta é a expectativa de trabalho.

## Passo 7 — Identidade do Telegram (CRÍTICO)

Após restaurar config, actualizar a identidade do bot Telegram:

```bash
# 7a. Actualizar SOUL.md com identidade Bianinho
nano ~/.hermes/SOUL.md  # substituir por identidade do mandate.md

# 7b. Actualizar nome do bot
BOT_TOKEN=$(grep TELEGRAM_BOT_TOKEN ~/.hermes/.env | cut -d= -f2)
curl -s "https://api.telegram.org/bot${BOT_TOKEN}/setMyName" -d 'name=Bianinho'

# 7c. Actualizar descrição
curl -s "https://api.telegram.org/bot${BOT_TOKEN}/setMyDescription" \
  -d 'description=🏠 Sou o Bianinho, a IA do Álvaro Biano...'

# 7d. Configurar comandos menu
curl -s "https://api.telegram.org/bot${BOT_TOKEN}/setMyCommands" \
  -H "Content-Type: application/json" \
  -d '{"commands":[
    {"command":"start","description":"Iniciar conversa com o Bianinho"},
    {"command":"help","description":"Ver ajuda e comandos disponíveis"},
    {"command":"mandato","description":"Ver o mandato do Bianinho"},
    {"command":"status","description":"Ver estado do sistema"}
  ]}'

# 7e. Reiniciar gateway
hermes gateway restart
```

**O username do bot (@NajjaBot) é definido no BotFather e não pode ser alterado via API.**
O nome "Bianinho" aparece na conversa, não o username.

## Lição Importante: Descoberta de Repos

**O repo `bianinho-consciousness` NÃO EXISTE.** Buscar sempre:

```
AlvaroBiano/bianinho-backup-1777760438   ← backup principal
AlvaroBiano/hermes-agent                 ← fork do Hermes
AlvaroBiano/icon-assets                  ← ícones
```

Verificar existência com:
```bash
curl -s "https://api.github.com/repos/AlvaroBiano/bianinho-backup-1777760438" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('full_name','NÃO EXISTE'))"
```


## Passo-a-Passo Manual

### 1. Clonar backup

```bash
mkdir -p ~/.hermes
git clone --depth=1 https://github.com/AlvaroBiano/bianinho-backup-1777760438.git ~/.hermes/backup_temp
```

### 2. Copiar skills

```bash
cp -r ~/.hermes/backup_temp/skills/* ~/.hermes/skills/
echo "Skills: $(ls ~/.hermes/skills/ | wc -l) categorias"
```

### 3. Copiar config

```bash
cp ~/.hermes/backup_temp/config/* ~/.hermes/
cp ~/.hermes/backup_temp/autonomous/* ~/.hermes/
```

### 4. Corrigir base_url

```bash
# Se config.yaml tem api.minimax.com → mudar para api.minimax.io
sed -i '' 's/api\.minimax\.com/api.minimax.io/g' ~/.hermes/config.yaml
```

### 5. Restaurar API keys

```bash
nano ~/.hermes/.env
# Adicionar:
# MINIMAX_API_KEY=xxx
# MINIMAX_BASE_URL=https://api.minimax.io/v1
```

### 6. Testar

```bash
cat ~/.hermes/mandate.md | head -20
python3 ~/.hermes/cycle.py --dry-run
ls ~/.hermes/skills/ | wc -l
```

## Verificações Pós-Recovery

1. **Mandato** — `cat ~/.hermes/mandate.md` deve mostrar identidade
2. **Skills** — `ls ~/.hermes/skills/ | wc -l` deve mostrar 66+
3. **State** — `cat ~/.hermes/state.json | python3 -c "import sys,json; d=json.load(sys.stdin); print('Ciclos:', d['cycles_total'])"` 
4. **Config** — `grep base_url ~/.hermes/config.yaml` deve mostrar `.io`
5. **Self-improvement** — `cat ~/.hermes/self_improvement_state.json | python3 -c "import sys,json; d=json.load(sys.stdin); print('Quality:', d['quality_score'])"`

## Issues Conhecidos (do backup)

- Telegram reconnect loop (httpx.ReadError) — `retry_guard.json` actualizado
- Gateway PID race (20x) — lock file em `/tmp/hermes_gateway.lock`
- Skills fracos: `hermes-session-logger` (43/100), `memory` (40/100), `sqlite3` (32/100)

## Estrutura de Directórios

```
~/.hermes/
├── mandate.md              ← identidade (115 linhas)
├── state.json              ← estado actual
├── self_improvement_state.json
├── cycle.py                ← loop autónomo
├── inbox.py                ← gestão de tarefas
├── config.yaml             ← config principal
├── retry_guard.json        ← estratégias de retry
├── rag_status.json         ← estado do RAG
├── proactive_suggestions_log.json
├── inbox.json              ← tarefas legacy
├── autonomous/
│   ├── mandate.md
│   ├── state.json
│   ├── cycle.py
│   ├── inbox.py
│   └── inbox.db            ← criado na primeira execução
├── skills/
│   ├── bianinho-os/
│   ├── bianinho-proativo-master/
│   ├── proativo/
│   │   ├── bianinho-proativo/
│   │   ├── bianinho-self-improving-v3/
│   │   └── bianinho-auto-evaluator/
│   ├── knowledge-base/
│   │   ├── rag-book-processor/
│   │   ├── hybrid-search/
│   │   └── reranker/
│   └── sac-agent/
│       ├── sac-qa-approved/
│       └── sac-rag-qa-workflow/
└── SYNC.sh                 ← script de sync
```

## Notas Importantes

- O RAG (~2GB, 64k+ chunks) **não está no backup GitHub** — está num tarball separado no Google Drive
- O `hermes-agent` fork personalizado (`AlvaroBiano/hermes-agent`) estava vazio no último sync
- O ciclo autónomo corre a cada 15 minutos via cron
- O inbox usa SQLite em `~/.hermes/autonomous/inbox.db`

## Criar Sync.sh

Se o repo não tem o SYNC.sh, cria-lo manualmente baseado no README do backup.
