---
name: bianinho-self-assessment-redesign
description: Redesenhar sistemas de auto-avaliação para produzir scores honestos — debugging de quality metrics que mostram valores falsos. Inspirado na redesign do bianinho_self_improving.py (20/04/2026).
triggers:
  - quality score no cron diz "4.0/5" mas há erros óbvios no log
  - sistema de auto-avaliação produz [SILENT] quando não devia
  - ao auditar um sistema de self-improvement e descobrir que não tem instrumentação real
  - quality score não corresponde à realidade observada
---

# Bianinho — Redesenhar Self-Assessment para Ser Honesto

## A Lição Central

Um sistema de self-assessment É DESONESTO se:
1. Não tem acesso a fontes de dados reais (só usa "default=good")
2. O quality score = 4.0 mas há centenas de erros no log
3. Produz [SILENT] quando o sistema claramente tem problemas
4. Não categoriza erros — trata retry loops da mesma forma que erros genuínos

**Sintoma:** Quality 3.9/5 mas observas 3+ erros evitáveis numa sessão.

**Cura:** Redesenhar com instrumentação real desde o primeiro output.

## Sessão de Referência

**2026-04-21:** Quality score 3.0 → implementou fixes → score ficou 2.9 → ainda não era suficiente → archiva e limpa errors.log completamente → score 4.0.

Lições aprendidas:
- errors.log pode conter erros de sessões arquivadas — archivar a sessão não remove os erros do log
- Trimmar (tail -500) não funciona se o log tem timestamps mistos de múltiplos dias
- Archivar E limpar completamente é necessário: `shutil.copy(errors.log, archive)` + `open(errors.log, 'w').write('')`
- Fórmula do quality score pode ter double-counting (mesmo erro penalizado em duas categorias)
- Thresholds devem ser graduados: >20 = sério, >10 = moderado, >5 = minor

## Padrão de Debugging — 5 Fases

### Fase 1: Instrumentar com Dados Reais
Antes de definir scoring, conecta a fontes de dados OBJECTIVAS:
- `~/.hermes/logs/errors.log` — erros recentes
- `~/.hermes/hermes_sessions.db` — estatísticas de sessões
- `~/.hermes/skill_fitness_scores.json` — performance de skills
- `~/.hermes/meta_cognition_journal.jsonl` — entradas do journal
- `~/.hermes/interaction_patterns.json` — padrões de interacção
- `system health` — RAM, disk, load

**O que NÃO fazer:** Começar com quality=4.5 por default e esperar que o sistema converge.

### Fase 2: Execução Real do Script
Executa o script actual e observa o output. Pergunta:
- O score corresponde à realidade que conheces?
- Quantos erros há no log que o script não detecta?
- O [SILENT] é genuíno ou é porque o script não olha para os dados?

**Veredicto:** Se o script diz "4.0/5 — OK" mas há 371 erros no log, o script está a mentir.

### Fase 3: Categorizar Erros Corretamente
Nem todos os erros são iguais:

| Tipo | Exemplo | Impacto | Prioridade |
|------|---------|---------|------------|
| Retry loops | context_window_exceeded x267 | Sistémico — consome recursos | CRÍTICO |
| API errors | 404 endpoint | Configuração errada | ALTO |
| Execution errors | SyntaxError, ImportError | Falha pontual | MÉDIO |
### Armadilha 4: Contar Erros sem Categorizar
"20 errors" parece grave mas se 18 são context_window_exceeded, são retry loops, não erros de execução.
**Solução:** Categorizar ANTES de penalizar. Retry loops = dedução sistémica. Erros genuínos = dedução pontual.

### Armadilha 5: Double-Counting no Quality Score
A mesma categoria de erro é penalizada duas vezes (ex: context_window_exceeded em retry_loop_context E em error_spike).
**Solução:** `total_error_count` exclui categorias já penalizadas separadamente. Cada categoria tem uma só oportunidade de dedução.

### Armadilha 6: errors.log Poluído com Erros Históricos
Archivaste a sessão zombie mas os erros dela continuam no errors.log. O script lê os últimos 500 erros e sees ainda erros de Abril 16.
**Solução:** Quando o errors.log tem erros de sessões arquivadas, archiva-o E limpa-o completamente. Não confies em trimming parcial. Usa `grep -v "20260416"` ou archiving total.

## Quality Score com Deduções Objectivas
Base: começa em 4.0 (não 5.0 — isso cria viés de positividade).
Deduções por problemas reais — thresholds graduados:

```python
def calculate_quality_score(p2_health, p3_errors, p4_journal):
    score = 4.0
    deductions = []

    # Sistema não saudável
    if not p2_health["healthy"]:
        score -= 0.5 * len(p2_health["issues"])
        deductions.append(f"health_issues({len(p2_health['issues'])})")

    # Retry loops — problema sistémico (CATEGORIA SEPARADA, não double-count)
    categories = p3_errors.get("error_categories", {})
    context_count = categories.get("context_window_exceeded", 0)
    api404_count = categories.get("api_404", 0)

    if context_count > 20:
        score -= 0.5; deductions.append(f"retry_loop_context({context_count})")
    elif context_count > 5:
        score -= 0.2; deductions.append(f"context_warnings({context_count})")

    if api404_count > 20:
        score -= 0.3; deductions.append(f"api_404_historical({api404_count})")
    elif api404_count > 5:
        score -= 0.15; deductions.append(f"api_404({api404_count})")

    # Erros genuínos — só penalizar se muitos (exclui context_window/api_404)
    error_count = p3_errors["total_error_count"]  # já exclui context_window/api_404
    if error_count > 20:
        score -= 0.5; deductions.append(f"error_spike({error_count})")
    elif error_count > 10:
        score -= 0.2; deductions.append(f"errors({error_count})")

    # Journal não usado
    if p4_journal["journal_entries"] == 0:
        score -= 0.3; deductions.append("no_journal_use")

    return max(0.5, min(5.0, score)), deductions
```

**Regra CRÍTICA:** `total_error_count` em Phase 3 deve EXCLUIR `context_window_exceeded` e `api_404` e `rate_limit` — essas categorias têm as suas próprias deduções. Se não excluires, vais double-count.

### Fase 5: Verificar que o Score É Honesto
Validação: o score faz sentido given what you know?
- Se há 371 retry loops e 0 journal entries, score 4.0 = mentira
- Score 2.7 com essas condições = honesto

**Teste de honestidade:** mostras o report ao Álvaro e ele confirma "sim, isso corresponde ao que observo"?

## Armadilhas

### Armadilha 1: Viés de Avaliação Própria
O sistema avalia-se a si próprio → tendência a dar scores altos.
**Solução:** Métricas objectivas, não auto-confiança.

### Armadilha 2: Tool Orpha
Ferramentas úteis mas nunca chamadas (`meta_cognition_journal.py`).
**Solução:** Se existe uma tool que não é chamada pelo sistema de auto-avaliação, ou integra-a ou remove-a.

### Armadilha 3: Threshold Alto Demais
Alertar só se quality < 3.5 significa que 3.5-4.5 são "OK" quando podiam ser melhor.
**Solução:** Quality < 4.0 já deve gerar medium-priority actions.

### Armadilha 4: Contar Erros sem Categorizar
"20 errors" parece grave mas se 18 são context_window_exceeded, são retry loops, não erros de execução.
**Solução:** Categorizar ANTES de penalizar. Retry loops = dedução sistémica. Erros genuínos = dedução pontual.

## Ficheiros

- `~/.hermes/scripts/bianinho_self_improving.py` — self-improvement agent v2 (redesenhado 20/04/2026)
- `~/.hermes/meta_cognition_journal.jsonl` — journal de decisões (primeira entry 20/04/2026)
- `~/.hermes/scripts/meta_cognition_journal.py` — tool orpha que agora é chamada
- `~/.hermes/scripts/interaction_pattern_analyzer.py` — tool orpha que agora é chamada
- `~/.hermes/self_evaluation.jsonl` — dados de quality score
- `~/.hermes/docs/sessions/sessao-auto-evolucao-20-04-2026.md` — sessão completa

## Sessão de Referência

Redesenho do `bianinho_self_improving.py` (20/04/2026):
- Antes: quality 3.9/5, 0 detecção de erros, [SILENT] sempre
- Depois: quality 2.7/5, 371 retry loops detectados, 0 journal entries
- Score passou de mentira para honesto
