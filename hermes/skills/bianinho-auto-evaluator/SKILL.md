---
name: bianinho-auto-evaluator
description: Auto-avaliação de tarefas e performance do Bianinho OS — log automático após tarefas complexas, detecção de feedback do utilizador, e relatório de performance.
triggers:
  - após completar tarefa complexa (3+ ferramentas)
  - quando o utilizador dá feedback (correção ou elogio)
  - quando se pede relatório de performance
  - integração com proactive_monitor (já activo, 1 entry/ciclo)
---

# bianinho-auto-evaluator — Auto-Avaliação do Bianinho OS

## Conceito
Inspirado em Q-Learning: cada tarefa completada gera sinais de reward.
O sistema infere automaticamente quality e autonomy scores — sem input manual.

## Uso Principal

### Auto-log após tarefa complexa
```python
from auto_evaluator import auto_log_eval

auto_log_eval(
    action_taken="criar_relatorio_TEN",
    outcome="auto",
    task_type="projectual",
    tool_count=4,
    has_error=False,
    response_text=output_completo,
    user_message=mensagem_do_utilizador,
    notes="Relatório do Método TEN",
    tags=["ten", "relatorio"],
)
```

### Detectar feedback do utilizador (no fluxo)
```python
from auto_evaluator import detect_user_correction, detect_compliment

correction = detect_user_correction(user_message)
compliment = detect_compliment(user_message)
# adjustment: se correction=True, autonomy -= 1.0
```

### CLI — Relatórios
```bash
# Relatório geral
python3 ~/.hermes/scripts/self_evaluation_tracker.py --report

# Avaliações recentes
python3 ~/.hermes/scripts/self_evaluation_tracker.py --recent

# Insights por tipo de acção
python3 ~/.hermes/scripts/self_evaluation_tracker.py --insights

# Log manual
python3 ~/.hermes/scripts/auto_evaluator.py eval \
  --action-taken "pesquisa_rag" \
  --outcome success \
  --task-type research \
  --tool-count 3 \
  --notes "Pesquisa Z-Library completada" \
  --tags "research,z-library"
```

## Integração com Proactive Monitor
O `proactive_monitor.py` já faz log automático de cada ciclo (a cada 30min):
- 1 entry por ciclo, consolidado
- Scores: quality=4.5, autonomy=5.0 para ciclos OK
- Tags: `["monitor_cycle", "auto", ...failed_checks]`

## Scoring Automático

| Dimensão | Como é calculada |
|----------|-----------------|
| quality | outcome × response_length |
| autonomy | 5.0 − penalidades (corrections, errors) |
| efficiency | tool_count: 1-2 tools=5.0, >8 tools=2.5 |
| accuracy | 1.0 success, 0.7 partial, 0.3 failure |
| completeness | outcome × estimated_tokens |
| relevance | fixed 4.5 |

## Deteção de Feedback
Padrões de **correcção**: "não", "errado", "espera", "oops", "volta atrás"
Padrões de **elogio**: "perfeito", "muito bem", "adorei", "top"

## Armadilhas e Bugs Encontrados

### Bug 1: `log_evaluation()` sobrescreve `dimensions`
`log_evaluation()` chamava internamente `_score_dimension()` que recalculava todas
as dimensões a partir do `quality`, destruindo scores pré-calculados.

**Solução**: Adicionado parâmetro `dimensions=dict` em `log_evaluation()`.
Se fornecido, usa directamente — não recalcula.

```python
# ✅ CERTO: passar dimensões pré-calculadas
dim_scores = {"accuracy": 5.0, "efficiency": 4.5, ...}
log_evaluation(action, outcome, quality, autonomy, dimensions=dim_scores)

# ❌ ERRADO: dimensões são sobrescritas por _score_dimension()
log_evaluation(action, outcome, quality, autonomy)
```

### Bug 2: `_score_dimension()` usava escala errada
`_score_dimension()` fazia `quality / 5.0` — convertendo scores 1-5 para 0-1,
quando devia retornar directamente `quality` na escala 1-5.

**Solução**: `base = float(quality)` sem divisão.

### Bug 3: Múltiplas entries por ciclo no monitor
Primeira versão: 6 entries por ciclo (1 por check) → 288 entries/dia.
Resultado: tendência falseamente "declining", dados diluídos.

**Solução**: 1 entry consolidada por ciclo, com scores fixos de sistema autónomo.
Design pattern: 1 entry por "unidade de trabalho" ou "sessão", não por sub-operação.

### JSONL Cleanup Procedure
Se os dados ficarem corrompidos (entries duplicadas, valores errados):
```bash
# Backup antes de limpar
cp ~/.hermes/self_evaluation.jsonl ~/.hermes/self_evaluation_backup.jsonl

# Verificar estado
python3 -c "import json; [print(json.loads(l)['action'], json.loads(l)get('overall_score')) for l in open('~/.hermes/self_evaluation.jsonl')]"

# Reescrever com só as entries válidas
python3 -c "
import json
entries = [json.loads(l) for l in open('/home/alvarobiano/.hermes/self_evaluation.jsonl')]
valid = [e for e in entries if isinstance(e.get('dimensions', {}).get('accuracy'), float) and e['dimensions']['accuracy'] > 1.0]
with open('/home/alvarobiano/.hermes/self_evaluation.jsonl', 'w') as f:
    for e in valid: f.write(json.dumps(e, ensure_ascii=False) + '\n')
print(f'Kept {len(valid)}/{len(entries)} entries')
"
```

## Ficheiros
- `~/.hermes/scripts/auto_evaluator.py` — módulo de auto-avaliação
- `~/.hermes/scripts/self_evaluation_tracker.py` — sistema de registo + relatório
- `~/.hermes/self_evaluation.jsonl` — dados crús (JSONL)
