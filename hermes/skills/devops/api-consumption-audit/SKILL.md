---
name: api-consumption-audit
description: Auditoria profunda de consumo de API em todo o stack — crons, serviços, scripts, Docker
triggers:
  - "audite consumo"
  - "o que está a usar api"
  - "revisão geral api"
  - "quem está a consumir requisições"
  - "análise de custos api"
---

# API Consumption Audit — Full Stack Audit Skill

## Quando Usar
Quando o Álvaro pedir para auditar consumo de API, investigar o que está causando uso excessivo de requisições, ou fazer "revisão geral profunda" em busca de tudo que consome API.

## Metodologia — 5 Camadas de Investigação

### Camada 1: Crons
```
cronjob list
```
Analisar: schedule, modelo usado, se usa skill ou não.
Frequência =/= consumo. Scripts Python puros não chamam API; agentes Hermes sim.

### Camada 2: Serviços systemd activos
```
systemctl --user list-units --type=service --all
systemctl --user status <service>
```

### Camada 3: Scripts Python — procurar padrões de risco
```bash
grep -r "hermes chat\|--yolo\|--source tool\|chatcompletion\|minimax.*01\|AGENT_CMD" \
  ~/.hermes/scripts/ ~/.hermes/cron/ 2>/dev/null | grep -v "__pycache__"
```

**Padrões de risco:**
- `hermes chat --yolo` num cron = AGENTE COMPLETO = múltiplas chamadas LLM
- `AGENT_CMD` = comando que spawna agente consumindo LLM
- `openrouter` = pode ter rate limits diferentes de MiniMax directo

### Camada 4: Docker containers
```
docker ps
```

### Camada 5: Processos activos
```
ps aux --sort=-%cpu
```

## Descobertas Não-Obvias — Confirmadas em Produção

| Descoberta | Impacto Real | Sintoma | Status |
|---|---|---|---|
| Guardian Stress Test (every 120m) | ~36-60 chamadas LLM/dia | `hermes chat --yolo` em AGENT_CMD | ✅ REMOVIDO |
| Proactive Monitor v2 (every 30m) | 48 chamadas LLM/dia via OpenRouter | POST real para openrouter.ai | ✅ Reduzido para 2h |
| Session Summarization durante restart | 5-10 erros 401 em cascata | 401 invalid api key após restart | ⚠️ Normal, auto-correcta |
| 429 insufficient balance (1008) | Queda para OpenRouter free tier | Todas as msgs ficam lentas | ⚠️ Requer credits |

## Comando Único de Screening
```bash
grep -r "hermes chat\|--yolo\|--source tool\|chatcompletion\|minimax.*01\|AGENT_CMD" \
  ~/.hermes/scripts/ ~/.hermes/cron/ 2>/dev/null | grep -v "__pycache__"
```

## Output Esperado
1. Lista categorizada (ALTO/MÉDIO/BAIXO consumo)
2. Para cada fonte: job, schedule, o que realmente faz
3. Número estimado de chamadas LLM/dia
4. Ações recomendadas com ordem de impacto
5. Total antes e depois

## Erros 429 — Distinguir Rate Limit vs Saldo Esgotado

O erro 429 pode ter significados diferentes:

| Código | Significado | Ação |
|--------|-------------|------|
| `429 insufficient balance (1008)` | **Saldo esgotado** | Adicionar créditos MiniMax |
| `429 rate limited` | Rate limit por minuto | Aguardar, não reiniciar |
| `429 via OpenRouter` | Limite do provider free tier | Normal, esperar retry |

**Sintoma típico de saldo esgotado:** após restart do gateway, começa a aparecer 429 e depois cai em cascata para fallback OpenRouter em todas as mensagens.

**Verificação:**
```bash
grep "429\|insufficient\|1008" ~/.hermes/logs/errors.log | tail -20
```

Se aparecer `insufficient balance (1008)` → é saldo, não rate limit.

## Session Summarization 401s — Bug de Startup (Não é Falha Real)

Erros 401 `invalid api key (2049)` no session summarization aparecem durante/após restart do gateway. Causa: o summarization tenta usar a API antes de o auth estar completamente disponível.

**Características:**
- Ocorrem em clusters de 5-10 erros seguidos
- Aparecem quando `gateway restart` acontece
- Cessam automaticamente após gateway ficar 100% operacional
- **Não requerem acção** — auto-correcta-se

**Se persistirem > 5 min após restart**, verificar se o auth.json está acessível.

## Armadilhas
- Não assumir que "scripts Python" não consomem API
- Não confundir frequência com consumo — 288 exec/dia de `ps aux` = 0 API calls
- openrouter pode ter rate limits diferentes de MiniMax directo
- **Erro 401 com `invalid api key` durante restart = normal**, não é chave inválida real
- **Erro 429 com `(1008)` = saldo esgotado**, não rate limit clássico — requer credits, não retry
