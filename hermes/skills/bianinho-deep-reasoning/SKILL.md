---
name: bianinho-deep-reasoning
description: >
  Sistema de raciocínio profundo inspirado em ACT-Halting do OpenMythos.
  Classifica queries por complexidade e activa reflexão explícita quando necessário.
triggers:
  - quando o utilizador pede algo estratégico, auto-evolução, ou arquitectura
  - quando a query contém múltiplas Keywords de alta complexidade
---

# Bianinho Deep Reasoning — SKILL

## Origem

Inspirado no ACT-Halting do OpenMythos (kyegomez/OpenMythos, MIT License).
O conceito original: modelos com profundidade recorrente adaptativadecidem
quantos loops de raciocínio cada query necessita. Transposto para arquitectura
de agente: queries simples = resposta directa; queries complexas = reflexão
explícita antes de agir.

## Arquitectura

```
Query → ComplexityClassifier → [deep | moderate | simple]
                                    ↓
                         deep  → PENSAMENTO PROFUNDO prefix
                         moderate → PENSAMENTO REFLECTIDO prefix
                         simple → sem modificação
```

## Implementação

### Hook: `~/.hermes/hooks/deep_reasoning/`

- **Ficheros**: `HOOK.yaml` + `handler.py`
- **Eventos**: `agent:start`, `agent:end`
- **Integração**: Não modifica o Hermes core — usa o sistema de hooks existente
- **Estado**: `/tmp/deep_reasoning/session_state.json` (por sessão)

### Padrões de Classificação

**DEEP (razão profunda activada)** — 2+ matches ou 1 match + 2+ palavras de pergunta:
- auto-evolução, self-improvement, metacognição
- estratégia, planeamento, arquitectura, decisões
- implementação de sistemas, refactor, design
- OpenMythos/OpenMight, multi-agent, loops de raciocínio
- "como poderia", "o que fazer para"
- Keywords: `complexo`, `análise profunda`, `avaliação crítica`

**MODERATE (razão refleitiva activada)** — 1+ match ou >30 palavras:
- Código, debugging, implement, configure, setup
- SAC, Typebot, LanceDB, RAG, Docker
- Projectos, testes, configurações

**SIMPLE** — tudo o resto. Sem modificação ao prompt.

## Componentes

| Componente | Ficheiro | Função |
|---|---|---|
| Hook handler | `~/.hermes/hooks/deep_reasoning/handler.py` | Classifica e prepende prefixo |
| Estado por sessão | `/tmp/deep_reasoning/session_state.json` | Regista modo activo por session_id |
| Skill doc | `~/.hermes/skills/proativo/bianinho-deep-reasoning/SKILL.md` | Esta documentação |

## Prefixos injetados

**Deep**:
```
[PENSAMENTO PROFUNDO ATIVADO]

Esta é uma query Complexa/Estratégica. Antes de responder:
1. Identifica exactamente o que está a ser pedido
2. Considera 2-3 abordagens alternativas
3. Antecipa problemas ou falhas na tua resposta
4. Verifica se tens contexto suficiente — se não tens, diz
5. Estrutura a tua resposta de forma clara

Não respondas imediatamente. Pensas primeiro, responde depois.
```

**Moderate**:
```
[PENSAMENTO REFLECTIDO ATIVADO]

Esta query requer atenção moderada. Antes de responder:
1. Verifica factos e comandos antes de os executar
2. Se há ambiguidade, clarifica antes de agir
3. Para código/configuração: prova antes de aplicar
```

## Teste

```bash
# Verificar se o hook está carregado
hermes logs 2>/dev/null | grep deep_reasoning

# Testar classificação manualmente
python3 -c "
import re
from pathlib import Path
import sys
sys.path.insert(0, '/home/alvarobiano/.hermes/hooks/deep_reasoning')
from handler import _classify

tests = [
    'Como poderia melhorar a minha auto-evolução?',
    'ls -la',
    'Configura o Typebot para o SAC Agent',
    'O que achas do OpenMythos para usar no Bianinho OS?',
    'oi',
    'Quanto custa a formação?',
]
for t in tests:
    mode, reason, conf = _classify(t)
    print(f'[{mode.upper()}] conf={conf:.2f} | {reason} | {t}')
"
```

## Logs

O hook imprime no stdout (visível via `hermes logs`):
```
[deep_reasoning] [DEEP] session=abc123... conf=0.85 | deep=3 mod=0 q=2
[deep_reasoning] [SIMPLE] session=def456... (no prefix injected)
[deep_reasoning] [END] session=abc123... mode=deep elapsed=12.3s
```

## Limitações

- O prefixo é injectado na mensagem do utilizador — funciona porque o Hermes
  adiciona o contexto do utilizador ao final do prompt de sistema
- O impacto real depende de como o modelo responde ao prefixo com texto
  em caixa alta — ajuste os prefixos se o efeito for insuficiente
- Estado em ficheiro = não persiste entre reinícios do gateway
