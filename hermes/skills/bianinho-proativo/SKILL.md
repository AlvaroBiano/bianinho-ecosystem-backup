---
name: bianinho-proativo
description: Sistema proactivo de monitorização e auto-correção — health checks, auto-fix, cron jobs
---
# Bianinho Proactivo — Sistema de Auto-Gestão

## Documento Completo da Sessão 20/04/2026
Ver: `~/.hermes/docs/sessions/sessao-guardian-paperclip-20-04-2026.md`

## O Que É Ser Proactivo (arxiv 2510.19771, 2511.02208)

Proactivo = antecipar + iniciar + executar sem esperar ordem.

Três dimensões (PPP framework):
- **Produtividade** — completar tarefas
- **Proactividade** — identificar problemas e agir antes de ser pedido
- **Personalização** — adaptar-se ao contexto do Álvaro

Pipeline PROBE (arxiv 2510.19771):
1. **Buscar** problemas não especificados
2. **Identificar** bloqueios específicos
3. **Executar** resoluções apropriadas

## Sistemas Críticos Monitorizados

| Sistema | O Que Verificar |
|---------|----------------|
| Hermes Gateway | status=ok |
| RAG Server | initialized=true |
| Paperclip | backlog sem assignee |
| MiniMax API | status_code=0 |
| Disco | uso < 80% |
| Memória | disponível > 2GB |

## Script de Health Check (Legacy)

`~/.hermes/scripts/proativo_health_monitor.py` — script antigo, 147 linhas. Descontinuado.

## Cron Job Activo — Proactive Monitor v2

- **Job ID**: `c3282070ec11`
- **Script**: `~/.hermes/scripts/proactive_monitor.py` (~425 linhas, 6 checks)
- **Checks**: LanceDB, MiniMax API (c/ retry), RAG Server (auto-restart), Product Agent, Hermes Gateway, Bianinho OS
- **Schedule**: every 30m
- **Output**: `~/.hermes/cron/output/proactive_monitor_v2/`
- **Delivery**: local
- **Auto-heal**: restart automático de serviços falhados
- **MiniMax retry**: até 2× com backoff 8-16s para erros transitórios (429, 529, timeout)

## Sessão 20/04/2026 — Root Cause: Paperclip Crash + Auto-Restart Adicionado

**Problema**: Product Agent (port 3100) em Connection refused — paperclip.service tinha morrido (exit code 137/OOM kill).

**Causa**: paperclip.service crasha regularmente (~11:24). O monitor detectava mas não fazia auto-restart.

**Fix aplicado**: Adicionado `restart_paperclip()` ao `proactive_monitor.py` — mesmo padrão do RAG Server:
- `systemctl --user start paperclip`
- Espera 8s, verifica /health
- Se falhar → notifica Álvaro via Telegram

**Sintoma conhecido**: `Connection refused` na porta 3100 = paperclip.service offline.
**Quick fix manual**: `systemctl --user start paperclip`

---

## Sessão 20/04/2026 — Root Cause Encontrado

**Problema**: Loop infinito de agentes (Product/Social/CEO Agent) consumindo CPU 89°C.

**Causa real**: `paperclipai run` (PID 487579) estava activo desde 08:57. O scheduler interno do Paperclip fazia heartbeat wake de agentes, spawnando-os em loop contra porta 3100 offline.

**NÃO foi** o Proactive Monitor — apenas verifica, não cria.

**Solução**:
- `kill -9 487579` + `systemctl --user stop/disable paperclip.service`
- `systemctl --user stop/disable rag-server.service` (era duplicado em crash loop)
- PID 335776 = RAG saudável (wrapper Hermes Gateway)
- Sistema estável há >30min

### Guardian Watchdog (Camada 1)
- Script: `~/.hermes/scripts/guardian_watchdog.py`
- Stress test: PASSOU ✓ — matou agente de teste em 30s
- Cron: `00c8472fb615` (every 15min)
- **Detecção**: CPU > 20% sustained + etime < threshold = agente em loop
- **Protecção**: 10min survival buffer (nunca mata antes dos 10min)

### Sistema RAG
- RAG saudável: PID 335776 (iniciado pelo Hermes Gateway wrapper)
- rag-server.service: **disabled** — era duplicado a fazer crash loop

---

## Autonomus Suggestion Processor (Pipeline Novo)

**Problema**: Cron suggestion engines (ex: Proactive Suggestion Engine) entregam sugestões para o Telegram do Álvaro — interrupções desnecessárias para sugestões que podem ser processadas autonomamente.

**Solução**: Pipeline que converte outputs de cron em acções autónomas sem incomodar o utilizador.

### Arquitectura

```
Cron (deliver=origin)     Cron (deliver=local)
        ↓                         ↓
  Telegram do Álvaro     → ~/.hermes/cron/output/{job_id}/
                                  ↓
                         Autonomous Suggestion Processor
                                  ↓
                         ~/.hermes/logs/suggestions_processed.jsonl (dedup)
                                  ↓
                         ~/.hermes/living_notebook.md (log)
```

### Implementação

**1. Mudar cron de origin para local** (ex: suggestion engine):
```
cronjob update --job_id 27e88ff7329d --deliver local
```

**2. Script**: `~/.hermes/scripts/process_suggestions.py`
- Lê o output mais recente do cron
- Extrai secção `## Response`
- Classifica por padrões (alta/media/baixa prioridade)
- Deduplica via `suggestions_processed.jsonl`
- Agrega ao caderno vivo ou executa acção

**3. Cron dedicado** (corre 5min após suggestion engine):
```
Job ID: 68ea14482e88
Schedule: 5,35 * * * *
Script: python3 ~/.hermes/scripts/process_suggestions.py
```

### Classificação de Sugestões

| Pattern | Categoria | Prioridade | Acção |
|---------|-----------|------------|--------|
| `skill.*nunca.*usad` | skills_unused | alta | Agregar ao notebook |
| `KB.*gap\|falta.*conteúdo` | kb_gap | alta | Procurar fonte |
| `quality.*declin` | quality_declining | media | Verificar false positive |
| `erro\|bug\|falh` | bug_found | alta | Diagnosticar e corrigir |
| `.*` | general | baixa | Log only |

### Bugs Encontrados e Corrigidos

**Bug 1**: Detecção `[SILENT]` fazia match no prompt do cron, não na resposta.
- **Fix**: Extrair `## Response` primeiro, só verificar `[SILENT]` aí.

**Bug 2**: `suggestion_id` gerado com timestamp actual em vez de extrair do filepath.
- **Fix**: Extrair do nome do ficheiro (ex: `2026-04-21_15-00-44.md` → `20260421_150044`).

**Bug 3**: Sem deduplicação — mesmo output processado múltiplas vezes.
- **Fix**: Log `suggestion_id` em `~/.hermes/logs/suggestions_processed.jsonl`.

### Ficheiros

| Ficheiro | Descrição |
|----------|-----------|
| `~/.hermes/scripts/process_suggestions.py` | Script principal |
| `~/.hermes/logs/suggestions_processed.jsonl` | Log de processados (dedup) |
| `~/.hermes/cron/output/27e88ff7329d/` | Outputs do suggestion engine |

## Cron Jobs Activos

| ID | Nome | Schedule | Nota |
|----|------|----------|------|
| `c3282070ec11` | Proactive Monitor v2 | 30min | 5 checks + auto-heal |
| `00c8472fb615` | Guardian Watchdog | 15min | Camada 1 — detecta e mata |
| `7e26dd33a3f5` | Guardian Validator | 45min | Camada 2 — valida Guardian |
| `51396e392b02` | Guardian Stress Test | 2h | Camada 3 — validação real |
| `68ea14482e88` | Autonomous Suggestion Processor | :05, :35 | Processa sugestões autonomamente |

### Scripts Guardian
- `guardian_watchdog.py` — Camada 1: detecta e mata processos anómalos (Hermes Gateway + RAG + context-mode). Filtro positivo: só captura hermes-gateway, hermes_cli.main, venv/bin/python + rag_service.py, context-mode.
- `guardian_validator.py` — Camada 2: 3 checks (execução + kills + stress test real a cada 4 ciclos)
- `guardian_stress_test.py` — Teste manual original
- `guardian_stress_test_cron.py` — Camada 3: wrapper cron (spawn → wait → verify → report)
- `guardian_integrated_test.py` — Teste integrado (bug de spawn — usar stress_test_cron.py)

### Paperclip — REMOVIDO COMPLETAMENTE (20/04/2026)
- npm uninstall -g paperclipai ✅
- systemctl --user stop/disable/mask paperclip.service ✅
- Ficheiro do serviço removido ✅
- ~/.paperclip e ~/.config/paperclip removidos ✅
- Lógica de Paperclip removida do Guardian ✅
- RAG server.service removido ✅
- Um bug foi encontrado e corrigido: filtro demasiado amplo estava a matar o RAG service legítimo. Corrigido com positive matching.

### Ficheiros de Estado
- `~/.hermes/logs/guardian.log` — log do Guardian
- `~/.hermes/logs/guardian_state.json` — estado do Guardian (kills, pids)
- `~/.hermes/logs/guardian_validator.log` — log do Validator
- `~/.hermes/logs/guardian_validator_state.json` — estado do Validator
- `~/.hermes/logs/guardian_stress_test.log` — log do Stress Test
- `~/.hermes/logs/guardian_stress_test_state.json` — estado do Stress Test
- `~/.hermes/logs/guardian_validator_alert.json` — alerta activo (se existir)

## Como Actuar Proactivamente

**Padrões de auto-iniciativa:**
1. **Health monitor** — verificar sistemas críticos regularmente
2. **Auto-fix** — corrigir problemas conhecidos automaticamente
3. **Proactividade** — trazer informação antes de ser pedido
4. **Sugestão ativa** — propor melhorias mesmo sem solicitação
5. **Continuidade** — continuar trabalho entre sessões sem pedir confirmação

## Erros Comuns e Soluções

- **RAG server initialized=false**: Normal (lazy load), buscar /search força init
- **RAG server offline**: Reiniciar
- **Alarme Falso: Erro de Chave API no Monitor**: Se o monitor reportar falha em um provedor (ex: MiniMax), mas o SAC Bot estiver ok, verifique se o monitor está testando a API direta enquanto o sistema usa o OpenRouter. Ajuste `proactive_monitor.py` para usar o gateway correto.
- **Redundância de Cronjobs**: Se houver notificações repetidas, use `cronjob action='list'` e remova IDs duplicados.
- **int32 JSON serialization**: Corrigido com `default=json_default` no json.dumps
