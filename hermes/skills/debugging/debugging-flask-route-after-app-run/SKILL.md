---
name: debugging-flask-route-after-app-run
description: Flask bug — rotas definidas depois do app.run() são código morto
---

# Flask: Bug — Código Depois do app.run()

## Contexto
Em Python Flask, `app.run()` é **bloqueante**. Código definido depois dele é **código morto** no servidor em execução.

## Sintomas
- Endpoint funciona com `test_client()` mas devolve 404 no servidor real
- Print statements depois do `app.run()` nunca aparecem
- `curl` directa ao endpoint retorna 404

## Causa Raiz
```python
# ❌ DEAD CODE — nunca executado pelo servidor
if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5123)

@app.route("/webhook/sac/avaliar", methods=["POST"])
def webhook_sac_avaliar():  # INACESSÍVEL
    ...
```

## Solução
```python
# ✅ VIVO — executado antes do servidor arrancar
@app.route("/webhook/sac/avaliar", methods=["POST"])
def webhook_sac_avaliar():  # ACESSÍVEL
    ...

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5123)
```

## Porquê o test_client() mascara o bug
`test_client()` processa pedidos **in-process** sem iniciar o servidor HTTP. Nunca chama `app.run()`, por isso rotas registadas depois do `app.run()` são visíveis nos testes mas não no servidor real.

## Como Diagnosticar
```python
# Adicionar JUSTO ANTES do app.run()
print(">>> URL_RULES", [r.rule for r in app.url_map.iter_rules()])
# Se a rota pretendida não aparece aqui → está registada depois do app.run()
```

## WSGI (gunicorn) não resolve
Gunicorn também lê o mesmo `app` object. Se a rota foi registada depois do `app.run()`, o gunicorn também não a vê — porque o código nunca foi executado.

## Padrão Geral
Sempre que uma rota parece não funcionar, verificar: **está o decorador/route registration antes ou depois do `app.run()`?**

## Sintomas Derivados (quando se move código para antes do app.run())

Quando se move rotas de depois para antes do `app.run()`, podem aparecer problemas adicionais:

### 1. Duplicação de rotas (`AssertionError: View function mapping is overwriting an existing endpoint function`)
Se o código original tinha rotas ANTES do `app.run()` E depois, ao mover criam-se duplicados.
**Solução:** Identificar e remover as duplicatas ANTES de mover. Procurar: `grep -n "^@app.route" ficheiro.py`

### 2. `NameError: name 'render_template' is not defined`
Flask só importa `render_template_string` mas o código novo usa `render_template`.
**Solução:** Adicionar `render_template` ao import do Flask:
```python
from flask import ..., render_template_string, render_template
```

### 3. Campo JSON errado no formulário de login (`{ username }` vs `{ login }`)
Se o backend espera `{ login }` mas o HTML envia `{ username }` — login funciona mas redirect não acontece.
**Solução:** Verificar o JSON que o JS envia vs o que `request.get_json()` espera no servidor.

### 4. Verificar com `curl` primeiro, browser depois
O browser pode ter cookies de sessão antigos que mascaram o comportamento real. Sempre testar com `curl -v` limpo.

## Referência
Bug real: `~/.hermes/sac_agent/sac_agent.py` — `webhook_sac_avaliar` definido após `app.run()`. Corrigido 25/04/2026. Commit: `f92d4ab` no repo bianinho-cerebro.
Bug real 27/04/2026: Rotas admin (perfil, convites, users) definidas após `app.run()` + sistema de login duplicado hardcoded vs DB + `render_template` em falta + campo `{username}` vs `{login}` no admin-login.html. Corrigido em ambos `~/.hermes/sac_agent/` e `~/sac-agent-local/`.
