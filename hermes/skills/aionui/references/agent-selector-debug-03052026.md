# Agent Selector — Hermes Desapareceu (03/05/2026)

## Problema

New Chat → selector de agentes → só aparecem **Aion CLI** e **Gemini CLI**. Hermes desapareceu.

## Arquitectura da Detecção

O AionUI detecta agentes locais via **HTTP bridge** no porto **18743**:

```
GET http://localhost:18743/check_hermes   → {ok, hermes: true}
GET http://localhost:18743/hermes_path    → {path: "/Users/alvarobiano/.hermes/..."}
```

Se estes endpoints não responderem HTTP 200, o Hermes **não aparece** no selector.

## Bridges — TCP vs HTTP

| Ficheiro | Tipo | Serve para AionUI? |
|----------|------|---------------------|
| `~/Library/ApplicationSupport/AionUI/bianinho/bianinho_bridge.py` | **TCP** | ❌ NÃO |
| `~/.hermes/scripts/bianinho_bridge_server.py` | **HTTP** | ✅ SIM |

O bridge TCP é um protocolo binário raw (4-byte length prefix + JSON). O AionUI espera HTTP.

## Iniciar o Bridge Correto

```bash
# Verificar estado actual
lsof -i :18743

# Se nada responder — iniciar HTTP bridge:
~/.hermes/venv/bin/python3 ~/.hermes/scripts/bianinho_bridge_server.py &

# Testar
curl -s --connect-timeout 3 http://localhost:18743/check_hermes
```

## Logs

| Log | Conteúdo |
|-----|----------|
| `~/.hermes/logs/bianinho_http_bridge.log` | HTTP bridge (correcto) |
| `~/.hermes/logs/bridge.log` | TCP bridge (antigo, não usar) |
| `~/.hermes/logs/bridge.err` | Erros TCP bridge |

## Config do AionUI

**Path:** `~/Library/Application Support/AionUI/config/aionui-config.txt`

**Formato:** base64 + URL-encoded JSON (não JSON direto)

```python
import base64, urllib.parse, json
with open('/Users/alvarobiano/Library/Application Support/AionUI/config/aionui-config.txt') as f:
    content = f.read()
data = json.loads(urllib.parse.unquote(base64.b64decode(content)))
```

**Chaves relevantes:**
- `guid.lastSelectedAgent` → agente selecionado (ex: `"aionrs"`)
- `acp.cachedInitializeResult` → capacidades do agente Hermes
- `acp.cachedModels` → modelos disponíveis (MiniMax-M2.7, etc.)
- `assistants` → 21 assistentes (não inclui Hermes)

## DB SQLite

**Path:** `~/Library/Application Support/AionUI/aionui/aionui.db`

Tabelas úteis:
- `acp_session` — sessões ACP
- `remote_agents` — **vazia** — agentes remotos não configurados
- `assistant_plugins` — **vazia** — plugins não configurados

## Teams System (MCP)

O AionUI tem Teams nativo com MCP server:

**Binário:** `app.asar.unpacked/out/main/team-guide-mcp-stdio.js`

**Tool:** `aion_create_team` — cria equipas multi-agente

**Pré-condições (3, todas necessárias):**
1. Utilizador pediu explicitamente OU aceitou proposta de team
2. Apresentaste configuração ao utilizador (roles, agentes)
3. Utilizador confirmou ("ok", "vá", "confirma")

## Processo de Debug

1. `lsof -i :18743` → está algo a ouvir?
2. `curl http://localhost:18743/check_hermes` → responde?
3. Se não, matar bridge errado e iniciar HTTP bridge
4. Reiniciar AionUI ou fazer New Chat
