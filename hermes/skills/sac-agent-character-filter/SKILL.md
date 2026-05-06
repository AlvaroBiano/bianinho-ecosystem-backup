---
name: sac-agent-character-filter
category: sac-agent
description: Filtro de saneamento de caracteres não-latinos para SAC Agent — impede que caracteres chineses/japoneses/etc apareçam em respostas em português brasileiro.
---

# SAC Agent — Non-Latin Character Filter

## Context
MiniMax M2.7 e outros LLMs podem retornar caracteres não-latinos (chinês, japonês, árabe, cirílico, coreano) misturados em texto português. Isso é inaceitável para chatbot brasileiro.

## Solution
Aplique `limpar_resposta()` em TODA resposta LLM antes de retornar ao usuário.

## Code (Python)

```python
import re

def limpar_resposta(texto: str) -> str:
    """Remove markdown e caracteres não-latinos de respostas LLM."""
    # Remove markdown
    texto = re.sub(r'\*\*(.*?)\*\*', r'\1', texto)
    texto = re.sub(r'\*(.*?)\*', r'\1', texto)
    texto = re.sub(r'#+\s*', '', texto)
    texto = re.sub(r'\n+', ' ', texto)
    texto = re.sub(r'^\s+|\s+$', '', texto)

    # Remove não-latinos: chinês, japonês, árabe, cirílico, coreano, etc.
    texto = re.sub(
        r'[\u4e00-\u9fff\u3000-\u303f\u3040-\u309f\u30a0-\u30ff'
        r'\uac00-\ud7af\u0400-\u04ff\u0500-\u052f'
        r'\u0600-\u06ff\u0750-\u077f\u08a0-\u08ff]', '', texto
    )

    # Remove símbolos especiais residuais (mantém PT-BR + pontuação)
    texto = re.sub(
        r"[^\w\sáàâãéèêíïóôõúüçÁÀÂÃÉÈÊÍÏÓÔÕÚÜÇ.,!?;:'-]",
        ' ', texto
    )

    # Limpa espaços duplos
    texto = re.sub(r' {2,}', ' ', texto)
    texto = re.sub(r'^\s+|\s+$', '', texto)
    return texto
```

## Trigger
**Sempre aplicar** após receber resposta do LLM e antes de retornar ao frontend/gravar no banco. Aplica-se a qualquer chatbot brasileiro que use MiniMax ou LLM estrangeiro.

## Localização
`~/.hermes/sac_agent/sac_agent.py` — função `limpar_resposta()`.

## Verificação

```bash
python3 -c "
import re
def limpar_resposta(t):
    t = re.sub(r'[\u4e00-\u9fff\u3000-\u303f\u3040-\u309f\u30a0-\u30ff\uac00-\ud7af\u0400-\u04ff\u0500-\u052f\u0600-\u06ff\u0750-\u077f\u08a0-\u08ff]', '', t)
    return t
print(limpar_resposta('合理 isso é um teste 中文 também funciona 日本語'))
"
# Output: 'isso é um teste também funciona'
```
