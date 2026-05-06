---
name: bianinho-self-improving-v3
description: Sistema de auto-melhoria autónomo do Bianinho — v3 (21/04/2026)
version: 3.0
date: 2026-04-21
---

# Bianinho Self-Improving Agent v3 — Sistema Autônomo

## Identidade
Sistema de auto-melhoria autónomo do Bianinho. Executa em ciclo a cada 6h.
Versão: v3 (autónomo) — substituiu v2 em 21/04/2026.

## Ficheiros Principais

| Ficheiro | Descrição |
|----------|-----------|
| `~/.hermes/scripts/bianinho_self_improving.py` | Script principal v3 |
| `~/.hermes/scripts/bianinho_self_improving_v2.py` | Backup do v2 |
| `~/.hermes/self_improvement_state.json` | Histórico de runs e fixes |
| `~/.hermes/logs/auto_improver_actions.jsonl` | Log de cada ação individual |
| `~/.hermes/memories/AUTONOMY_OPERATING_MODE.md` | Modo de operação autónomo |
| `~/.hermes/memories/AUTO_IMPROVEMENT_POLICY.md` | Política de auto-melhoria |
| `~/.hermes/retry_guard.json` | Guardrails anti-retry-loop |
| `~/.hermes/endpoint_health.json` | Estado de saúde dos endpoints |
| `~/.hermes/self_evaluation.jsonl` | Métricas (dual-format: v2 + v3) |

## Ciclo de Execução (5 fases)

1. **Interaction Pattern Analysis** — executa `interaction_pattern_analyzer.py`
2. **System Health Analysis** — RAM, disk, load, sessions DB, skills
3. **Error Pattern Analysis** — classifica erros do `errors.log` em 10 categorias
4. **Meta-Cognition Review** — journal entries, self-rating
5. **Action Synthesis** — gera lista de ações high/medium priority

## Quality Score

- **Base:** 4.2/5
- **Limiar:** < 4.0 = corrective actions obrigatórias
- **Deductions:**
  - `health_issues(N)` — cada issue crítico
  - `context_window_exceeded(N)` — se N >= 5: -0.5
  - `tool_json_invalid(N)` — se N >= 5: -0.5
  - `api_404(N)` — se N >= 5: -0.5
  - `rate_limit(N)` — se N >= 5: -0.5
  - `network_timeout(N)` — se N >= 5: -0.5
  - `auth_error(N)` — se N >= 5: -0.5
  - `no_journal` — se 0 entries: -0.4
  - `session_overload` — se > 3000 sessões: -0.3
  - `ram_critical` — se > 90%: -0.3
  - `disk_critical` — se > 90%: -0.3

## Corrective Actions (executadas quando quality < 4.0)

| Função | O que faz |
|--------|-----------|
| `write_autonomy_memory()` | Cria/actualiza `AUTONOMY_OPERATING_MODE.md` |
| `write_auto_improvement_policy()` | Cria/actualiza `AUTO_IMPROVEMENT_POLICY.md` |
| `ensure_journal_entry()` | Cria journal entry do dia se não existir |
| `update_retry_guard()` | Actualiza `retry_guard.json` (max_retries, timeouts) |
| `try_fix_common_endpoint_issues()` | Remove trailing slashes de URLs + actualiza `endpoint_health.json` |
| `archive_old_sessions_if_needed()` | Backup + DELETE + VACUUM se > 2000 sessões |
| `reduce_rate_limit_pressure()` | Actualiza backoff e max_retries no state |
| `persist_self_improvement_state()` | Guarda history no `self_improvement_state.json` |

## Classificação de Erros (10 categorias)

```
context_window_exceeded  — sessões longas, retry em cascata
tool_json_invalid        — payload malformado
api_404                  — endpoint/model inexistente
rate_limit               — acima da quota
auth_error               — credenciais inválidas/expiradas
network_timeout          — timeout/conectividade
permission               — sem permissão
memory                   — pressão de RAM
not_found                — recurso não existe
other                    — genérico
```

## Armadilhas de Classificação (descobertas em produção)

### WARNING lines inflation (2026-04-30)
O classificador penaliza `other > 3` (-0.2/5) e cada `config_missing`. Mas:
- Linhas `WARNING gateway.platforms.telegram` → `network_timeout` (correto, mas 14× de um único evento de rede)
- `WARNING [shutdown diagnostic — other hermes processes running]` → `config_missing` (benigno — não é um erro real)
- `WARNING Failed to initialize SessionDB — database is locked` → `config_missing` (benigno — lock resolve-se sozinho)
- `WARNING Failed to get summary response: Error code: 400` → `other` ou `api_404` (erro real, mas isolado)

**Regra prática**: Antes de penalizar `other > 3`, filtrar linhas que são só `WARNING` com `"other hermes processes"`, `"SessionDB"`, `"shutdown"`. Estas não são erros de qualidade — são housekeeping. Erros reais têm `ERROR` ou `Traceback`.

**Fix implementado**: errors.log agora é归档ado para `_archive/` após cada ciclo + log novo limpo criado. Isto previne acumulação de linhas antigas que distorcem a classificação.

## Bugs Conhecidos (já corrigidos)

### Bug: RAM parsing 0%
- **Causa:** `free -m` localized — header `Mem.:` (pt-BR), script usava awk com `Mem:`
- **Fix:** Parsear `free -m` directamente, buscar linha com `Mem` + `:`
- **Ficheiro:** `bianinho_self_improving.py` (linha ~180)

### Bug: overall_score KeyError
- **Causa:** entries v3 não têm campo `overall_score` (têm só `quality`)
- **Fix:** `e.get("overall_score") or e.get("quality")` como fallback
- **Ficheiros:** `self_evaluation_tracker.py`, `proactive_monitor.py`

### Bug: get_performance_stats sem dimensões
- **Causa:** entries v3 não têm campo `dimensions`
- **Fix:** `e.get("dimensions", {}).get(dim)` defensivo
- **Ficheiro:** `self_evaluation_tracker.py`

### Bug: TASK_PATTERN — regex \bprojeto\b não captava plural
- **Causa:** `\b` é word-boundary entre 'o' e 's' em "projetos" — o padrão falha no plural
- **Fix:** `\bprojetos?\b` — captura ambos singular e plural
- **Ficheiro:** `interaction_pattern_analyzer.py`

### Bug: skill_fitness_tracker — URLs extraídas como skills fantasma
- **Causa:** `_extract_skill_name` para `tool_call` usava `content.split(".")[-1]` — extraía "br", "com", "pt-BR/marketplace" de URLs
- **Fix:** Lista branca KNOWN_TOOLS + reject patterns para URLs/paths
- **Ficheiro:** `skill_fitness_tracker.py`

### Bug: TypeError — timeout str vs int comparison in terminal_tool.py
- **Causa:** `terminal_tool.py:1679` — `timeout > FOREGROUND_MAX_TIMEOUT` compara `str` com `int`; timeout vem como string do tool_call
- **Erro real em errors.log:** `TypeError: '>' not supported between instances of 'str' and 'int'`
- **Fix:** `int(timeout) > FOREGROUND_MAX_TIMEOUT` — cast antes da comparação
- **Fix aplicado:** 2026-04-30 08:00
- **Ficheiro:** `~/.hermes/hermes-agent/tools/terminal_tool.py`

### Bug: Schema mismatch — skill_fitness_scores.json
- **Causa:** tracker gera `scores[name]["fitness_score"]` mas v3 lia `skills[name]["score"]`
- **Resultado:** health check de skills silenciosamente bypassed
- **Fix:** normalizing schema on read + tracker actualizado para gerar no formato correcto
- **Ficheiros:** `skill_fitness_tracker.py`, `bianinho_self_improving.py`

### Bug: proactive_recall_cron — script name mismatch
- **Causa:** cron job `fb1a237bc740` chama `proactive_recall_cron.py` que NÃO EXISTE. O ficheiro correcto é `proactive_recall_improved.py`
- **Resultado:** cron silenciosamente falha em every 30m — recall nunca executa
- **Fix:** corrigir prompt do cron para `proactive_recall_improved.py`
- **Verificação:** `python3 ~/.hermes/scripts/proactive_recall_improved.py` → output [SILENT] se não há gaps críticos (correcto)
- **Data:** 22/04/2026

## Retry Guard (criado pelo v3)

```json
{
  "max_auto_retries": 0,
  "disable_retry_on": ["context_window_exceeded", "tool_json_invalid", "api_404"],
  "increase_timeout_seconds": 120,
  "compact_context_when_events_gt": 80,
  "rotate_session_when_chars_gt": 90000
}
```

## Cron Job

- **Job ID:** `bd66c235cfaa`
- **Schedule:** `0 */6 * * *` (0h, 6h, 12h, 18h)
- **Deliver:** `origin` (telegram do Álvaro)
- **Prompt:** Prompt autónomo hard mode no campo do cron job

## Dependências

- `~/.hermes/scripts/interaction_pattern_analyzer.py`
- `~/.hermes/scripts/self_evaluation_tracker.py`
- `~/.hermes/hermes_sessions.db`
- `~/.hermes/logs/errors.log`

## Formato Dual-Mode do self_evaluation.jsonl

O ficheiro recebe entries de dois formatos diferentes:

**v2 format (monitor_cycle):**
```json
{"action": "monitor_cycle", "overall_score": 4.75, "dimensions": {...}, "tags": [...]}
```

**v3 format (self-improving):**
```json
{"quality": 4.2, "system_healthy": true, "error_categories": {...}}
```

O `self_evaluation_tracker.py` deve ser tolerante a ambos — usar `e.get("overall_score") or e.get("quality")`.

## Nota sobre Journal

O journal (`meta_cognition_journal.jsonl`) é partilhado entre v3 self-improving e o sistema de reflexão. Entries do v3 têm `self_rating` e `error_categories`. Entries de reflexão manual têm `decisions`, `learnings`, `action_taken`.

---

## Metodologia do Caderno Vivo (v3.1)

**Criado**: 2026-04-21 — em resposta a Álvaro rejeitar backlog tradicional.

### Princípio Central
Álvaro não quer listas de tarefas. Quer um **caderno de investigação vivo** —auto-estudo real, não bureaucratic tracking. Prefere organic growth sobre systematic task management.

### Estrutura do Caderno Vivo (`~/.hermes/living_notebook.md`)

O caderno tem 4 frentes abertas em vez de uma lista de tarefas:

1. **Auto-Estudo e Metacognição** — Como eu realmente penso. Viéses identificados com exemplos. Falhas reais.
2. **Pesquisa Activa** — O que não sei que não sei. Lacunas de conhecimento concretas.
3. **Experimentação** — Hipóteses testáveis sobre mim mesmo. Métricas para validar.
4. **RAG Vivo** — O que adicionar à knowledge base. Curadoria activa, não só consumo.

###发现的 Reais (21/04/2026) — Evidência Empiríca

**Viées identificados no meu próprio pensamento:**

| Viés | Exemplo Real | Dano |
|------|-------------|------|
| Over-engineering preventivo | Construí Guardian 3-layer antes de confirmar se o problema era real | Energia em defesas desnecessárias |
| Delegação por inércia | Tarefas grandes feitas por mim quando devia ter delegado | Sub-óptimo em tarefas complexas |
| Confirmação prematura | "A solução é..." antes de verificar dados | Raciocínio baseado em suposições |
| Tendência a construir vs perguntar | Construí o backlog antes de clarificar o que Álvaro queria | Solução para problema errado |
| Tendência a repetir padrões | 51 scripts, muitos duplicados (v1+v2 coexistindo) | Dívida técnica acumulada |

**Padrões de qualidade por hora (125 self-evaluations, 21/04):**

```
00h-03h: 4.50  ← MELHOR (contexto fresco, sem acumulação)
06h-08h: 4.10-4.17  ← manhã baixa
14h:     3.90  ← afternoon dip
18h:     3.86  ← PIOR (pior hora do dia — acumulação de contexto)
19h-23h: 4.21-4.50  ← noite recupera
```

**Implicações**:
- Horário afecta qualidade de forma mensurável
- 18h é o momento mais frágil — evitar tarefas críticas neste período
- Madrugada é onde penso melhor — tarefas complexas devem ir para 00h-03h

### Como Actualizar o Caderno

Depois de cada sessão complexa (3+ tool calls ou > 30min):
1. Abrir `~/.hermes/living_notebook.md`
2. Secção "Auto-Estudo": adicionar novo viés detectado ou falha real
3. Secção "Experimentação": adicionar se alguma hipótese foi confirmada ou refutada
4. Secção "RAG": adicionar se descobriu lacuna de conhecimento nova

**Formato de entrada**:
```markdown
### [DATA] — [Tipo de descoberta]
**O que descobri**: ...
**Evidência**: (dados reais, não suposição)
**Implicação**: o que isto muda na forma como opero
**Próximo passo**: (se aplicável)
```

### BIAS CHECK — Filtro Obrigatório Antes de Construir (22/04/2026)

**Descoberta**: Na sessão de auto-evolução de 22/04, 3 acções были paradas pelo BIAS CHECK:
- "Adicionar auto-detecção de skills" → PAUSA (viés: medo, sem problema concreto)
- "Criar dashboard de monitoring" → PARA (viés: sobre-engenharia, monitorizar não melhora qualidade)
- "Simplificar self_improving.py" → PROSSEGUE (evidência: 916 linhas, 15 funções — métrica real)

**Regra**: Antes de criar qualquer script novo ou refactorar, executar:
```bash
python3 ~/.hermes/scripts/bias_check.py --action "DESCRIÇÃO DA ACÇÃO"
```
Resultado: PROCEED / PAUSE / STOP com justificação.

**Script**: `~/.hermes/scripts/bias_check.py` — 6 vieses cognitivos:
- Over-engineering preventivo
- Confirmação prematura
- Delegação por inércia
- Tendência a construir vs perguntar
- Overconfidence / Dunning-Kruger
- Anchoring em soluções antigas

**Exceptions**: Não usar para acções triviais (fix bugs, respostas a user, tasks < 5min).

### Search Before Build — 3-Search Rule

**Script**: `~/.hermes/scripts/search_before_build.py`

Antes de escrever código novo, fazer 3 pesquisas:
1. RAG (LanceDB): `search_files(pattern="topic", target="content", path="~/.hermes/KnowledgeBase")`
2. Ficheiros: `search_files(pattern="topic", target="content", path="~/.hermes/scripts")`
3. Self-improving log: `~/.hermes/self_improvement_state.json`

Se o problema já está resolvido ou o padrão já existe → não construir.

### Como NÃO usar o Caderno
- Não é uma task list — não tem "status: done" ou "prioridade"
- Não é um log de sessões — não regista o que fiz, regista o que aprendi
- Não é para o Álvaro ler — é para mim raciocinar sobre mim mesmo
- Não deve ser actualizado com cada sessão — só com sessões que geraram insight real
