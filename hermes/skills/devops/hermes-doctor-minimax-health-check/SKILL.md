---
name: hermes-doctor-minimax-health-check
description: Corrigir false warning do hermes doctor para MiniMax API — health check com /v1/models dá 404
triggers:
  - hermes doctor mostra "⚠ MiniMax (HTTP 404)"
  - health check do MiniMax falha no hermes doctor
  - false warning MiniMax no doctor --fix
---

# Corrigir MiniMax Health Check no Hermes Doctor

## Problema
O `hermes doctor --fix` mostra `⚠ MiniMax (HTTP 404)` porque o health check
faz GET a `/v1/models`. O MiniMax **não expõe** esse endpoint — é um falso
warning. A API key e base URL estão configuradas correctamente.

## Causa
Em `hermes_cli/doctor.py`, a entrada do MiniMax na tabela de providers usa:

```python
("MiniMax", ("MINIMAX_API_KEY",), "https://api.minimax.io/v1/models", "MINIMAX_BASE_URL", True),
#                                                                                      ^^^ supports_health_check=True
```

O último parâmetro `True` = tenta fazer GET a esse URL. MiniMax retorna 404.

O base URL do Álvaro é `https://api.minimax.io/anthropic` (documentação oficial
MiniMax), portanto o health check vai a `https://api.minimax.io/anthropic/models`
→ 404.

## Solução Correcta

Mudar `supports_health_check` para `False`, indicando que a API key existe
(configurada em `.env`) mas o health check não é possível:

```python
# MiniMax: /v1/models doesn't exist; skip health check (key is configured in .env).
("MiniMax", ("MINIMAX_API_KEY",), None, "MINIMAX_BASE_URL", False),
#                                                              ^^^^ False = skip
```

Este é o mesmo pattern usado para o OpenCode Go.

**NÃO alterar** `MINIMAX_BASE_URL` no `.env` — o valor actual
`https://api.minimax.io/anthropic` é a documentação oficial e funciona.

## Ficheiro
`~/.hermes/hermes-agent/hermes_cli/doctor.py`, linha ~941

## NÃO FAZER
- Não mudar `MINIMAX_BASE_URL` no `.env`
- Não mudar `MINIMAX_API_KEY`
- Não criar nova variável de ambiente
- Não usar `/v1/text/chatcompletion_v2` como health check — exige POST,
  o health check do doctor usa GET → sempre 404

## Verificação
```bash
hermes doctor --fix
# MiniMax deve mostrar: "✓ MiniMax (key configured)"
```

## Investigação Completa (26/04/2026)

Testei os seguintes endpoints directamente com curl:
- `GET https://api.minimax.io/v1/models` → 404
- `GET https://api.minimax.io/anthropic/models` → 404
- `GET https://api.minimax.io/anthropic/v1/models` → 404
- `POST /v1/text/chatcompletion_v2` → funciona (mas health check usa GET)

O código doctor.py tem lógica para reescrever `/anthropic` para `/v1` usando
`_to_openai_base_url()`, mas isso não resolve porque `/v1/models` também
não existe no MiniMax. A única solução é skippar o health check.

## WhatsApp Bridge — 2 vulnerabilidades críticas residuais

O baileys foi actualizado para `7.0.0-rc.9` (latest), reduzindo de 3 para 2
vulnerabilidades críticas no `protobufjs`. Estas são dependência transitiva do
`@whiskeysockets/libsignal-node` e não têm fix disponível — aguardam patch
upstream.

```
cd ~/.hermes/hermes-agent/scripts/whatsapp-bridge
npm install @whiskeysockets/baileys@latest
npm audit fix  # não resolve — o fix não está disponível
```

## Tool Availability — o que significa "system dependency not met"

Ao investigar porquê `image_gen`, `spotify`, `homeassistant` e `browser-cdp`
mostram "system dependency not met" mesmo depois de instalar packages:

- Estes tools TÊM um `check_fn` que é executado **em runtime** pelo registry
- O `check_fn` retorna `False` porque falta credentials/configuração, não
  porque o package está em falta
- `TOOLSET_REQUIREMENTS` mostra `env_vars=[]` para estes tools — não são
  "missing env vars", são checks de runtime

Exemplos de check_fn:
- `spotify`: `_check_spotify_available()` → verifica `get_auth_status("spotify")`
- `homeassistant`: `_check_ha_available()` → verifica `os.getenv("HASS_TOKEN")`
- `image_gen`: `check_image_generation_requirements()` → verifica FAL_API_KEY
  ou plugin providers
- `browser-cdp`: `_browser_cdp_check()` → verifica se há Chrome com CDP

**Conclusão**: packages Python安装 não resolvem "system dependency not met"
para tools com check_fn — é preciso configurar credentials ou credenciais.
