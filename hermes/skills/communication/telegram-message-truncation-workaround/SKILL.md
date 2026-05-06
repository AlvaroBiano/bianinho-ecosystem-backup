---
name: telegram-message-truncation-workaround
description: O que fazer quando mensagens longas do Telegram são truncadas pelo Telegram API antes de chegarem ao gateway Hermes
---

# Telegram Message Truncation Workaround

## Problema
Quando o utilizador envia mensagens longas no Telegram, podem ser truncadas pelo Telegram API antes de chegarem ao gateway Hermes. O utilizador experiencia como "a mensagem é cortada" sempre no mesmo ponto (~300-400 caracteres em mensagens de IA, ou ~4096 em mensagens normais do Telegram API).

O gateway Hermes tem `MAX_MESSAGE_LENGTH = 4096` para envio (`telegram.py` ~linha 988), mas **não há limite equivalente no path de receive** — a truncagem é feita pelo Telegram antes do webhook/gateway receber.

## Solução
**Pedir ao utilizador para enviar em partes curtas** (~500 caracteres por mensagem). Alternativas:
1. Dividir o texto em múltiplas mensagens curtas
2. Usar formato de lista (cada item = uma mensagem)
3. Enviar primeiro parte do conteúdo, depois o resto

## Investigação
- Ficheiro: `~/.hermes/hermes-agent/gateway/platforms/telegram.py`
- `MAX_MESSAGE_LENGTH = 4096` — apenas para envio (send), não receive
- `_flush_text_batch` e lógica de batching é para envio, não receção
- Não há fix de código possível — é limitação da plataforma Telegram
