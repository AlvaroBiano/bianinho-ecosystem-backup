# Erros 401 da API MiniMax — Diagnóstico e Resolução

## Sintoma

```
Error code: 401 - {'type': 'error', 'message': 'invalid api key (2049)'}
```

Múltiplos erros 401 consecutivos nos logs.

## Causas Possíveis

1. **API key expirada** — MiniMax Token Plan pode expirar
2. **API key revogada** — removida do dashboard MiniMax
3. **API key mal configurada** — espaços, caracteres extra no .env
4. **Erro temporário** — rate limiting mal interpretado como 401

## Diagnóstico

```bash
# Ver a key no .env (mascarada)
grep MINIMAX_API_KEY ~/.hermes/.env

# Testar a API directamente
curl -s -X POST "https://api.minimax.io/v1/chat/completions" \
  -H "Authorization: Bearer $MINIMAX_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model":"MiniMax-M2.7","messages":[{"role":"user","content":"test"}],"max_tokens":5}' \
  | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('error',{}).get('message','OK'))"
```

## Resolução

1. Obter nova API key em platform.minimaxi.com
2. Editar `~/.hermes/.env`:
   ```
   MINIMAX_API_KEY=eyJhbGc...
   ```
3. Reiniciar o gateway:
   ```bash
   hermes gateway restart
   ```
4. Verificar:
   ```bash
   tail -5 ~/.hermes/logs/errors.log | grep 401
   ```

## Prevenção

- Verificar quota regularmente: `hermes doctor`
- Alerts automáticos quando quality score < 3.0
- A key deve estar mascarada com `***` no .env (não commitar)

## Notas

- Erros 401 antigos nos logs devem ser limpos após correção (`grep -v "401"`)
- O `retry_guard.json` tem `max_retries` para erros 401 — verificar se está activo
- Quality score cai quando há erros 401 em série (dedução de -0.5 por 5+ ocorrências)
