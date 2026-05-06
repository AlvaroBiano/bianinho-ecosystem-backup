---
name: llm-output-auto-correction
category: mlops
tags: [llm, hallucinations, output-layer, correction]
description: Corrigir alucinações consistentes do LLM via camada de auto-correcção no código, não no prompt.
---

# LLM Output Auto-Correction Layer

## Quando usar
Quando um LLM gera consistentemente a mesma resposta errada (nome errado, facto errado, expressão proibida) e não se corrige via prompt. A correcção é aplicada na **camada de saída** do código, não no prompt.

## Como funciona
Em qualquer função que formata/limpa a saída do LLM antes de guardar ou enviar, adicionar `str.replace()` para correcções de erros conhecidos.

## Implementação em Python

```python
def formatar_resposta(texto: str) -> str:
    if not texto:
        return ""
    # Corrigir nomes próprios conhecidos
    texto = texto.replace("Marielena", "membro da equipe")
    # ... resto do código ...
    return texto

def plain_resposta(texto: str) -> str:
    if not texto:
        return ""
    texto = texto.replace("Marielena", "membro da equipe")
    # ... resto do código ...
    return texto
```

## Regras
- Aplicar a correcção **EM AMBAS** funções (UI + contexto LLM)
- A correcção vem **ANTES** de qualquer outra transformação de texto
- Manter a lista de correcções no topo da função

## Como adicionar uma nova correcção
1. Identificar o erro consistente na conversa/banco
2. `grep -rni "erro" ...` para encontrar origem
3. Se é alucinação do LLM: adicionar `replace` na `formatar_resposta()` E `plain_resposta()`
4. Corrigir histórico no banco: `UPDATE tabela SET col = REPLACE(col, 'erro', 'correcto') WHERE col LIKE '%erro%'`
5. Testar Ctrl+Shift+R

## Se o erro é factual (não só nome)
- Adicionar regra no **SYSTEM PROMPT**: `CORRECÇÃO FACTUAL: [afirmação errada] — [facto correcto]`
- PLUS: corrigir também no código como belt-and-suspenders

## Ficheiros de referência
- SAC Bot: `~/.hermes/sac_agent/sac_agent.py`
  - `formatar_resposta()` — ln ~430 (saída UI/HTML)
  - `plain_resposta()` — ln ~519 (contexto LLM)
- Correccções activas: `"Marielena" → "membro da equipe"`
- Banco histórico: `~/.hermes/sac_agent/sac_leads.db`
  - Corrigir: `UPDATE conversas SET mensagem = REPLACE(mensagem, 'A', 'B') WHERE mensagem LIKE '%A%';`
