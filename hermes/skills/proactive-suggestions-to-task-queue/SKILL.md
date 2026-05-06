---
name: proactive-suggestions-to-task-queue
description: Arquitectura para transformar sugestões proativas em execução autónoma via inbox — sem interrupções Telegram, relatório consolidado entregue ao início da sessão.
---

# Proactive Suggestions → Bianinho Inbox Pattern

## Quando usar
Quando o Álvaro diz "não quero ver sugestões no Telegram — processe tudo autonomamente e entregue só o relatório".

## Arquitectura implementada (24/04/2026)
```
Proactive Suggestion Engine (cron 9,11,13,15,17,19,21h)
  → gera sugestões → ~/.hermes/suggestions_queue.jsonl (status: pending)

Autonomous Suggestion Processor (cron 5,35 */h)
  → LÊ suggestions_queue.jsonl
  → NÃO tenta executar (scripts são burros, sem contexto)
  → escreve para inbox: ~/.hermes/suggestions_for_bianinho.jsonl
  → marca como "processed" em suggestions_queue.jsonl
  → resultado vai para log, não para Telegram

Bianinho (no início de cada sessão)
  → verifica suggestions_for_bianinho.jsonl
  → processa cada sugestão COM CONTEXTO (session_search, Ficheiros, Skills)
  → executa ações reais (investigar, corrigir, indexar, etc.)
  → entrega RELATÓRIO CONSOLIDADO ao Álvaro
```

## Ficheiros
| Ficheiro | Uso |
|---|---|
| `~/.hermes/suggestions_queue.jsonl` | Fila oficial — gerada pelo cron, lida pelo processor |
| `~/.hermes/suggestions_for_bianinho.jsonl` | Inbox do Bianinho — pendente de processamento |
| `~/.hermes/logs/suggestions_processed.jsonl` | Histórico do que foi executado |

## Formato inbox (suggestions_for_bianinho.jsonl)
```jsonl
{"id":"20260424_130036","suggestion":"Bianinho sugere: texto","timestamp":"2026-04-24T13:00:36.868947"}
```

## Formato histórico (suggestions_processed.jsonl)
```jsonl
{"timestamp":"2026-04-24T14:00:00","suggestion_id":"20260424_130036","action":"kb_gap","outcome":"Relatório entregue ao Álvaro"}
```

## Formato do relatório entregue
```
## RELATÓRIO — Processamento de Sugestões Autônomas

**Data:** DD/MM/AAAA
**Sugestões processadas:** N

---
### SUGESTÃO
"texto da sugestão"

### INVESTIGAÇÃO REALIZADA
[O que Bianinho verificou com dados reais]

### AÇÕES EXECUTADAS
| # | Ação | Resultado |

### RECOMENDAÇÕES
[Se houver next steps para o Álvaro]
```

## Passo-a-passo para processar o inbox
1. Ler `~/.hermes/suggestions_for_bianinho.jsonl`
2. Para cada entrada pendente:
   a. Classificar a sugestão
   b. Investigar com session_search, Ficheiros, Skills
   c. Executar ação concreta (ou determinar que não é executável)
3. Compilar relatório consolidado
4. Enviar para Telegram (send_message)
5. Limpar inbox ou marcar como processado

## Armadilhas descobertas
- `process_suggestions.py` e `process_suggestions_queue.py` são AMBOS workers da mesma fila — causam race condition. Manter só um.
- Scripts burros产出fracasso "requiere acceso a la sesión" — não conseguem executar ações reais. Bianinho SÓ deve processar, não os scripts.
- Suggestions duplicadas (mesmo texto em intervalos) → verificar ID antes de processar
