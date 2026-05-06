---
name: hermes-update-with-local-changes
description: Update Hermes Agent when git stash fails due to untracked/new files conflicting with local modifications. Manual backup → checkout → pull → restore workflow.
tags: [hermes, git, update, troubleshooting]
version: 1.3
created: 2026-04-19
updated: 2026-04-24
author: Bianinho
---

# Hermes Update — Complete Workflow

## Fluxo Completo de Update

### 1. Update Padrão (quando stash funciona)

```bash
hermes update 2>&1
```

**Output esperado:**
```
→ Fetching updates...
→ Local changes detected — stashing before update...
→ Found N new commit(s)
  ✓ Pre-update snapshot: <timestamp>-pre-update
→ Pulling updates...
→ Restoring local changes...
⚠ Local changes were restored on top of the updated codebase.
  ✓ Cleared N stale __pycache__ directories
→ Updating Python dependencies...
→ Updating Node.js dependencies...
→ Building web UI...
  ✓ Web UI built
✓ Code updated!
→ Syncing bundled skills...
  + N new: <skill1>, <skill2>
  ~ N user-modified (kept)
✓ Update complete!
```

### 2. Verificação Post-Update (SEMPRE fazer)

```bash
# Confirmar versão
hermes --version

# Confirmar sync com upstream
cd ~/.hermes/hermes-agent
git rev-parse HEAD
git rev-parse origin/main
# Devem ser IGUAIS

# Listar commits novos (N últimos)
git log --oneline HEAD~N..HEAD
**Verificar.plugins novos no upstream (v0.12.0+):**
```bash
ls -la ~/.hermes/hermes-agent/plugins/context_engine/
ls -la ~/.hermes/hermes-agent/plugins/rag_context_injector/
ls -la ~/.hermes/hermes-agent/gateway/gateway_session_bridge_integration.py
ls -la ~/.hermes/hermes-agent/tools/knowledge_vector_tool.py
```
# Verificar skills bundladas novas
hermes skills list | grep -E "touchdesigner|humanizer"
```

### 3. Gerar Relatório de Mudanças

**Comandos para listar todos os commits novos:**
```bash
# Commits desde o último update (via snapshot pré-update)
cd ~/.hermes/hermes-agent
git log --format="%h %s" --date=short <last-head>..HEAD

# Commits por categoria (fix/feat/chore/docs/perf)
git log --format="%s" <last-head>..HEAD | grep -E "^(fix|feat|chore|docs|perf|refactor)" | sort | uniq -c | sort -rn

# Ficheiros alterados no upstream
git diff --stat <last-head>..HEAD | tail -20
```

**Categorias de changes a reportar:**
1. **Fixes** — correções de bugs
2. **Features** — funcionalidades novas
3. **Performance** — otimizações
4. **Plugins novos** — descobertos como ficheiros untracked
5. **Skills bundladas novas** — listadas no output do `hermes update`
6. **Dependências** — Python/Node packages atualizados
7. **Breaking changes** — se há resetting de config

---

## O Problema: Quando Git Stash Falha

`git stash` fails with "Cannot save the current status" (exit 1) even when there ARE local changes to stash — THIS IS THE KEY INSIGHT.

O erro acontece quando **já existe um stash anterior** no repo. O git impede novo stash se já houver entries na stash stack.

**PRIMEIRO DIAGNÓSTICO — sempre:**
```bash
cd ~/.hermes/hermes-agent
git stash list
# Se retornar algo → há stash anterior a bloquear
git status -sb
# Se vir ?? (untracked) + M (modified) → usar abordagem hard reset, não stash
```

**Sintomas confundidores:**
- `git diff` mostra alterações → há changes para stashear
- `git stash` diz "Cannot save the current status" → parece que não há changes
- `git stash list` → revela que há stash entry anterior a bloquear

This blocks the standard `hermes-smart-updater` flow.

## Solução Recomendada — Hard Reset + Restore (22/04/2026)

**Use esta abordagem quando há MUITOS ficheiros modificados no upstream (374+ commits) — é mais simples e limpa que tentar resolver conflitos um a um.**

### Passo 1: Backup completo

```bash
cd ~/.hermes/hermes-agent
mkdir -p /tmp/hermes-pre-update
# Todos os ficheiros com alterações locaisknown:
cp gateway/run.py run_agent.py /tmp/hermes-pre-update/
cp gateway/gateway_session_bridge_integration.py /tmp/hermes-pre-update/ 2>/dev/null || true
cp tools/knowledge_vector_tool.py /tmp/hermes-pre-update/ 2>/dev/null || true
git diff > /tmp/hermes-pre-update-diff.patch
echo "Backup feito: $(ls /tmp/hermes-pre-update/)"
```

### Passo 2: Hard reset para origin/main

```bash
git fetch origin main
git reset --hard origin/main
# Todos os ficheiros locais modificados são apagados — por isso o backup no passo 1
```

### Passo 3: Restaurar TODOS os ficheiros locais

```bash
# gateway/run.py — SIM, precisa de restore (hook-modified message integration é local)
cp /tmp/hermes-pre-update/run.py gateway/

# run_agent.py — SIM, precisa de restore (Pre-Compression Save é local)
cp /tmp/hermes-pre-update/run_agent.py ./

# gateway_session_bridge_integration.py — se existir
cp /tmp/hermes-pre-update/gateway_session_bridge_integration.py ~/.hermes/hermes-agent/gateway/ 2>/dev/null || true

# tools/knowledge_vector_tool.py — se existir
cp /tmp/hermes-pre-update/knowledge_vector_tool.py ~/.hermes/hermes-agent/tools/ 2>/dev/null || true

echo "Restore feito"
```

### Passo 4: Verificar integridade

```bash
source venv/bin/activate
cd ~/.hermes/hermes-agent

# Teste 1: run_agent
python3 -c "import run_agent; print('run_agent OK')"

# Teste 2: gateway/run (import correto quando em running from repo dir)
python3 -c "from gateway.run import GatewayRunner; print('gateway/run OK')"

# Teste 3: tool discovery count (72 = knowledge tools carregadas, 69 = sem)
python3 -c "from hermes_agent.model_tools import _discover_builtin_tools; print(f'Tools: {len(_discover_builtin_tools())}')"
```

### Passo 5: Restart do Gateway

**Se o systemd estava ativo, limpa primeiro o estado do gateway:**

```bash
# Limpar estado systemd e restart
systemctl --user daemon-reload

# Limpar gateway_state.json (contém PID antigo que causa race condition)
python3 -c "import json; d=json.load(open('$HOME/.hermes/gateway_state.json')); d.update({'pid': None, 'gateway_state': 'stopped', 'active_agents': 0, 'platforms': {}}); json.dump(d, open('$HOME/.hermes/gateway_state.json', 'w'))"

# Remover PID files residuais
find ~/.hermes -name "*.pid" -delete 2>/dev/null || true

# Testar gateway manualmente (mais fiável que systemd para debug)
cd ~/.hermes/hermes-agent && source venv/bin/activate && python -m hermes_cli.main gateway run --replace &
sleep 8

# Verificar estado
cat ~/.hermes/gateway_state.json | python3 -c "import json,sys; d=json.load(sys.stdin); print('pid:', d.get('pid'), 'state:', d.get('gateway_state'))"
```

**Se o systemd entrar em loop de restart (PID file race), o gateway funciona manualmente — é um bug do systemd service, não do Hermes.**

## Abordagem Alternativa: git add -A + git commit (30/04/2026)

Quando há **ficheiros untracked + modificados** e o stash falha, usar em vez de hard reset:

```bash
# 1. Ver situação
git status --short

# 2. Preservar tudo num commit local (untracked são incluídos com -A)
git add -A && git commit -m "feat(local): preserve local changes before update"

# 3. Guardar o commit hash para referência
git log --oneline -1

# 4. Pull (fast-forward, sem conflitos porque changes estão no commit)
git pull origin main

# 5. gateway restart completo (ver hermes-smart-updater)
```

**Vantagem:** mantém histórico local, mais limpo que hard reset. Funciona quando não há conflitos reais com o upstream.

**Quando usar em vez de hard reset:** quando os ficheiros locais são compatíveis com o upstream (sem conflitos de merge). Se o upstream reescreveu as mesmas linhas, usar hard reset.

## Fluxo Anterior (Stash Pop — para updates menores)

Se o upstream tem poucas mudanças, usar em vez disso:

```bash
# 1. Fazer backup
mkdir -p /tmp/hermes-pre-update
cp cli.py gateway/run.py run_agent.py /tmp/hermes-pre-update/
cp gateway/gateway_session_bridge_integration.py /tmp/hermes-pre-update/ 2>/dev/null || true

# 2. Stash pop
git stash pop

# 3. Resolver conflitos manualmente (procurar <<<<<<< Updated upstream)
grep -n "<<<<<<" gateway/platforms/telegram.py model_tools.py
# Editar cada ficheiro, resolver conflitos, git add

# 4. Checkout + pull (para evitar divergent branches)
git checkout -- cli.py gateway/run.py run_agent.py
git pull --rebase origin main

# 5. Restaurar locais (se necessário)
cp /tmp/hermes-pre-update/cli.py ~/.hermes/hermes-agent/cli.py
```

## Fetch de PRs — NousResearch/hermes-agent

O NousResearch/hermes-agent **não expõe refs/pull/** — significa que `git fetch origin pull/727/head:pr-727` NÃO funciona.

**Alternativa que funciona:**
```bash
# Descobrir o branch name do autor via GitHub CLI (mais seguro que curl)
gh pr view 727 --json headRefName --jq '.headRefName'
```
# Fetch direto do branch nomeado
git fetch origin feature/cognitive-memory-system:pr-727
```

**Verificar antes:**
```bash
git ls-remote refs/pull/727/head 2>/dev/null
# Se vazio → repo não expõe PR refs → usar API + branch name
```

---

## Ficheiros Locais Conhecidos do Álvaro (Bianinho OS)

Sempre fazer backup destes antes de reset:
- `gateway/run.py` — hook-modified message integration
- `run_agent.py` — Pre-Compression Save do Bianinho OS
- `gateway/gateway_session_bridge_integration.py` — sessão persistente cross-platform
- `plugins/context_engine/proactive_compressor/` — context engine plugin
- `plugins/rag_context_injector/` — RAG context injector plugin
- `tools/knowledge_vector_tool.py` — knowledge tools (RAG)

**Para descobrir todos os ficheiros modificados/untracked:**
```bash
git status -sb
git diff --name-only
```

## Verificação

```bash
# Confirmar versão nova
git describe --tags --always HEAD

# Confirmar em sync com origin
git describe --tags --always origin/main

# Confirmar gateway ativo
systemctl --user is-active hermes-gateway
```

## Prevenir Futuros Problemas

**ANTES de qualquer update, fazer diagnóstico rápido:**
```bash
cd ~/.hermes/hermes-agent
git stash list  # se retornar algo → clear primeiro
git status -sb  # ?? + M = hard reset approach
```

Se vir `??` (untracked files) + `M` (modified files) ao mesmo tempo, usar abordagem hard reset.

**Após restore, verificar sempre:**
```bash
source venv/bin/activate
python3 -c "import run_agent; print('run_agent OK')"
python3 -c "from gateway.run import GatewayRunner; print('gateway/run OK')"
```

## After Update — Verificar Toolsets (CRÍTICO)

**Nova discovery (22/04/2026):** Local tools em `tools/*.py` não são automaticamente carregados. Precisam de estar no `_HERMES_CORE_TOOLS` em `toolsets.py`.

**Exemplo real:** `knowledge_vector_tool.py` existia e regista 3 tools, mas não apareciam no assistente porque não estavam no `_HERMES_CORE_TOOLS`.

**Diagnóstico:**
```bash
# 1. Verificar se o tool module existe
ls ~/.hermes/hermes-agent/tools/knowledge_vector_tool.py

# 2. Confirmar que se regista mas não carrega
python3 -c "from hermes_agent.tools.knowledge_vector_tool import setup; print(setup())"

# 3. Verificar toolsets.py — secção _HERMES_CORE_TOOLS
grep -n "_HERMES_CORE_TOOLS" ~/.hermes/hermes-agent/toolsets.py

# 4. Listar tools carregados (72 é o normal com knowledge tools)
python3 -c "from hermes_agent.model_tools import _discover_builtin_tools; print(len(_discover_builtin_tools()))"
# 69 = sem knowledge tools | 72 = com knowledge tools
```

**Fix:** Adicionar ao `_HERMES_CORE_TOOLS` em `toolsets.py`:
```python
"knowledge_query",
"knowledge_stats",
"knowledge_process",
```

**Restart:** `systemctl --user restart hermes-gateway` (NOT `pkill` — Álvaro bloqueia pkill).

## Localização dos Backups

```
/tmp/hermes-pre-update/           — ficheiros locais salvos
/tmp/hermes-pre-update-diff.patch — diff completo (243+ lines)
```
