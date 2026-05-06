---
name: bianinho-os
description: Sistema operativo de auto-evolução do Bianinho — 3 camadas: Context Memory Router, Workflow Adapter, Self-Evaluation Tracker. Fase 1 completa, Fase 2 completa.
triggers:
  - quando o utilizador pede "como está a tua performance"
  - depois de tarefas complexas (3+ ferramentas)
  - quando se detecta feedback do utilizador
  - monitorização proactiva (a cada 30min)
---

# 🧠 Bianinho OS — Sistema Operativo de Auto-Evolução

## Arquitectura (3 Camadas)

```
┌─────────────────────────────────────────────┐
│  CONTEXT MEMORY ROUTER (Classificação)       │
│  9 tipos: technical, projectual, personal,   │
│  operational, strategic, creative, research, │
│  social, self_improvement                    │
├─────────────────────────────────────────────┤
│  WORKFLOW ADAPTER (Selecção de Template)      │
│  8 templates: Technical, Projectual,          │
│  Strategic, Research, Creative, Self-Evolution│
├─────────────────────────────────────────────┤
│  SELF-EVALUATION TRACKER (Feedback Loop)      │
│  Q-Learning: quality + autonomy = Q-value    │
│  Dimensões: accuracy, efficiency,            │
│  completeness, autonomy, quality, relevance  │
└─────────────────────────────────────────────┘
```

## Componentes

### 1. Context Memory Router
`~/.hermes/scripts/context_memory_router.py`
- Classifica queries em 9 tipos
- Gera routing hints para workflow selection
- Detecta SELF_IMPROVEMENT queries

### 2. Workflow Adapter
`~/.hermes/scripts/workflow_adapter.py`
- 8 templates de workflow
- Complexidade estimada por token count
- Self-Evolution Deep-Loop (6 steps)

### 3. Self-Evaluation Tracker
`~/.hermes/scripts/self_evaluation_tracker.py`
- Registo em `~/.hermes/self_evaluation.jsonl`
- Q-Learning: quality + autonomy = Q-value
- Tendência: improving / stable / declining
- Relatório: `python3 self_evaluation_tracker.py --report`

## FASE 2 — Auto-Log de Avaliações (✅ COMPLETA)

### auto_evaluator.py
`~/.hermes/scripts/auto_evaluator.py`

#### auto_log_eval() — Uso Principal
```python
from auto_evaluator import auto_log_eval

# Após tarefa complexa
auto_log_eval(
    action_taken="criar_relatorio_TEN",
    outcome="auto",        # ou "success"/"partial"/"failure"
    task_type="projectual",
    tool_count=4,
    has_error=False,
    response_text=output_completo,
    user_message=mensagem_do_utilizador,
    notes="Resumo",
    tags=["ten", "relatorio"],
)
```

#### Detecção de Feedback
```python
from auto_evaluator import detect_user_correction, detect_compliment

correction = detect_user_correction(user_message)
compliment = detect_compliment(user_message)
```

### Scoring Automático (auto_log_eval)

| Dimensão | Lógica |
|----------|--------|
| quality | outcome × estimated_tokens (response length) |
| autonomy | 5.0 − penalidades (corrections, errors) |
| efficiency | tool_count: 1-2→5.0, >8→2.5 |
| accuracy | 1.0 success, 0.7 partial, 0.3 failure |
| completeness | outcome × estimated_tokens |
| relevance | fixed 4.5 |

### Integração Proactive Monitor
O `proactive_monitor.py` já regista **1 entry por ciclo** (a cada 30min via systemd timer):
- **ALL OK**: quality=4.5, autonomy=5.0, all dimensions=4-5
- **Partial** (≤1 falha): quality=3.5, dimensions=3.5
- **Failure** (>1 falha): quality=2.5, dimensions=2.5

### CLI — Relatórios
```bash
# Relatório geral
python3 ~/.hermes/scripts/self_evaluation_tracker.py --report

# Avaliações recentes
python3 ~/.hermes/scripts/self_evaluation_tracker.py --recent

# Insights por tipo de acção
python3 ~/.hermes/scripts/self_evaluation_tracker.py --insights

# Auto-log manual
python3 ~/.hermes/scripts/auto_evaluator.py eval \
  --action-taken "pesquisa_rag" \
  --outcome success \
  --task-type research \
  --tool-count 3 \
  --notes "Feito" \
  --tags "research,z-library"
```

## Estado Actual

```
📊 Bianinho OS — FASE 1 ✅ | FASE 2 ✅
Total avaliações: 4
Score médio: ~4.8/5
Autonomy: 5.0/5 (sistema autónomo nas suas operações)
Tendência: stable/declining (esperado com seed=5.0 vs ciclos=4.75)
Próximo: Fase 3 — Integration nas skills
```

##Ficheiros
- `~/.hermes/scripts/context_memory_router.py`
- `~/.hermes/scripts/workflow_adapter.py`
- `~/.hermes/scripts/self_evaluation_tracker.py`
- `~/.hermes/scripts/auto_evaluator.py`
- `~/.hermes/scripts/bianinho_os.py` (motor integrado)
- `~/.hermes/self_evaluation.jsonl` (dados crús)
