# AionUI — Localhost Integration Reference (03/05/2026)

## Arquitectura 100% Local (MacBook)

```
AionUI.app (Electron)
  └─ bianinhoBridge.ts (Electron main process, Electron net module)
        └─ HTTP GET/POST http://127.0.0.1:18743
              └─ bianinho_bridge_server.py (Python HTTP server, PID ~54253)
                    ├─ Hermes (minimax API)
                    ├─ RAG LanceDB (localhost:3101)
                    └─ Skills, Inbox, Memory (~/.hermes/)
```

## Ficheiros-Chave

| Componente | Path |
|---|---|
| BianinhoBridge server | `~/.hermes/scripts/bianinho_bridge_server.py` |
| Bridge logs | `~/.hermes/logs/bianinho_bridge.log` |
| RAG server | `~/KnowledgeBase/rag_server.py` |
| RAG data | `~/KnowledgeBase/knowledge_db/` (sync do servidor a cada 4h) |
| Hermes config | `~/.hermes/config.yaml` |
| AionUI logs | `~/Library/Logs/AionUi/YYYY-MM-DD.log` |
| AionUI app | `/Applications/AionUI.app/` |
| AionUI source (rsynced) | `/tmp/aionui-mac/` |

## Estado dos Serviços (03/05/2026 00:07)

```bash
# Bridge — verificar se está a ouvir
nc -z 127.0.0.1 18743 && echo "bridge OK"

# RAG — verificar se está a ouvir
nc -z 127.0.0.1 3101 && echo "rag OK"

# Testar todos os endpoints do bridge (via execute_code, NÃO curl terminal)
import urllib.request, json
for ep in ["/ping", "/status", "/platform_info", "/check_hermes",
           "/list_skills", "/rag_stats", "/inbox_list", "/cycle_status"]:
    r = urllib.request.urlopen(f"http://127.0.0.1:18743{ep}", timeout=5)
    print(ep, json.loads(r.read()).get("ok", "N/A"))
```

## Erro Hermes Agent ACP — Root Cause

**Log (`~/Library/Logs/AionUi/2026-05-03.log`):**
```
[2026-05-03 00:12:42.045] [error] Failed to parse JSON message: Install them with:  pip install -e '.[acp]' SyntaxError: Unexpected token 'I', "Install th"... is not valid JSON
[2026-05-03 00:12:43.113] [warn]  [ACP hermes] Process exited with code 1 [reason: process_exit]
[2026-05-03 00:12:43.194] [error] [SessionLifecycle] start failed (PROCESS_CRASHED, retryable=true)
 AgentStartupError: Agent exited before initialize completed (code: 1)
```

**Causa:** `pip install -e '.[acp]'` nunca foi executado no repo hermes-agent.

**Fix:**
```bash
cd ~/.hermes/hermes-agent && pip install -e '.[acp]'
```

**Verificação:**
```bash
~/.hermes/venv/bin/hermes acp
# output esperado:
# 2026-05-03 00:19:56 [INFO] acp_adapter.entry: Loaded env from /Users/alvarobiano/.hermes/.env
# 2026-05-03 00:19:56 [INFO] acp_adapter.entry: Starting hermes-agent ACP adapter
# 2026-05-03 00:19:56 [INFO] acp_adapter.server: ACP client connected
```
O `acp_adapter.server: ACP client connected` confirma que o ACP server arrancou e ficou à espera de uma ligação (stdin/stdout do protocolo ACP).

## Como o AionUI Conecta ao Hermes Agent

1. AionUI detecta `hermes` em PATH via `AcpDetector`
2. Configura `cliPath: 'hermes'`, `acpArgs: ['acp']`
3. Faz spawn: `spawn('hermes', ['acp'])`
4. O subprocess executa `acp_adapter.entry.main()` que:
   - Carrega `.env`
   - Importa `acp_adapter.server.HermesACPAgent`
   - Corre `asyncio.run(acp.run_agent(agent))`
   - Comunica via stdio (JSON-RPC sobre aionrs)

Quando o `acp_adapter` não está discoverable → erro → processo termina com code 1.

## Nota sobre o Bridge vs ACP

O **BianinhoBridge** (`localhost:18743`) e o **Hermes Agent ACP** são duas coisas diferentes:
- BianinhoBridge = HTTP server para queries RAG, inbox, skills, status
- Hermes Agent ACP = protocolo de agente conversacional (mensagens, tool calls, sessões)

O AionUI usa ambos para coisas diferentes:
- O separador **Bianinho** (página `/#/bianinho`) → BianinhoBridge HTTP
- O **Hermes Agent** (escolhido como "agente") → ACP subprocess

## Navegação no AionUI (HashRouter)

```
/#/guid           ← página principal (default ao abrir AionUI)
/#/bianinho       ← separador Bianinho (precisa de clique manual na sidebar)
/#/conversation   ← conversas
/#/team/:id      ← equipa
```

O BianinhoPage é carregado via `React.lazy()` — só quando navega para `/#/bianinho` é que os pedidos ao BianinhoBridge são feitos. Por isso `messagesProcessed: 0` no bridge até clicar no separador.
