# Hermes Gateway Restart — Procedimentos

## Restart Simples (só recarregar)

```bash
hermes gateway stop
hermes gateway start
hermes gateway status
```

## Restart Completo (rebuild + restart)

Para updates de código ou quando há mudanças em dependências:

```bash
# 1. Parar
hermes gateway stop

# 2. Rebuild Python — venv Python directo (UV marca python3 sistema como externally managed)
~/.hermes/hermes-agent/venv/bin/python -m pip install -e ".[dev]" --quiet

# 3. Rebuild npm
cd ~/.hermes/hermes-agent && npm install 2>&1 | tail -3

# 4. Iniciar
hermes gateway start

# 5. Verificar
sleep 5 && hermes gateway status
```

## Verificações Pós-Restart

Bons indicadores:
- `Active: active (running)` since < 30s
- `API Health: Key is valid`
- Memory < 200 MB (cold start limpo)
- Hooks visíveis nos logs (ex: `deep_reasoning`)

 Maus indicadores:
- Memory > 1 GB → processos órfãos
- HTTP 401 → .env com placeholder `***`, verificar auth.json
- "Cannot lock ref" → locks git salvage namespace

## Caminho da Venv

```
~/.hermes/hermes-agent/venv/bin/python
```

**Não** é `.venv` padrão — é `venv/` no raíz do projeto.

## Reset After Tool/Config Changes

| O que mudou | Como reiniciar |
|---|---|
| Skills | `/reset` ou nova sessão |
| Tools (toolsets) | `/reset` ou nova sessão |
| Config (config.yaml) | Gateway: `/restart` · CLI: sair e reabrir |
| Código fonte | Restart completo |
| Dependências pip/npm | Restart completo |
| Gateway plugins | Gateway: `/restart` |
| .env | Gateway: `/restart` · CLI: sair e reabrir |
| Cron jobs | Não precisa restart — recarrega automaticamente |

## Git Stash com Changes Locais

Antes de `git pull` com mudanças locais:

```bash
# Verificar se há stash anterior
git stash list

# Se stash existe, usar drop ou pop conforme necessário
git stash pop  # aplicar + remover
git stash drop # só remover

# Pull
git fetch origin && git pull origin main
```

Se stash falha por arquivos untracked conflituantes: ver `hermes-update-with-local-changes`.

## Divergência de Branches — Reset Completo

**Cenário**: `git pull` fez merge automático com conflitos. Você resolveu e committou. Mesmo assim `git pull` pede para especificar como reconciliar — os branches divergiram.

**Passo-a-passo para sincronizar**:

```bash
cd ~/.hermes/hermes-agent

# 1. Verificar estado
git status --short
git log --oneline HEAD..origin/main | wc -l   # commits atrás do origin

# 2. Se há stash anterior
git stash list
git stash drop   # se existir stash de sessão anterior

# 3. Rebase dos commits locais sobre origin/main
git rebase origin/main

# 4. Se rebase resolver (sem conflicts):
git log --oneline HEAD..origin/main | wc -l   # deve mostrar 0

# 5. Push do branch local se necessário
git push alvaro main
```

**Sinais de alerta durante o processo**:
- `fatal: need to specify how to reconcile` → branches já divergiram, não usar `git pull` novamente
- `error: could not restore untracked files from stash` → stash está vazio ou já foi aplicado, normal
- Conflitos de merge: resolver com `git checkout --ours` ou `git checkout --theirs`

**Decisão --ours vs --theirs**: Em conflito de merge no Hermes Agent, quase sempre aceitar `--ours` para preservar customizações locais (configs, patches do Álvaro).

**Após resolver conflitos de merge**:
```bash
git add <arquivo>
git commit -m "Merge origin/main — conflitos resolvidos"
```

**Pós-sync — restart do gateway**:
```bash
hermes gateway restart
sleep 5 && hermes gateway status
```
