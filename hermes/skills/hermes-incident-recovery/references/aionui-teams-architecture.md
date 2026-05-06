# AionUI Teams — Arquitectura e Integração Hermes

## Resumo Executivo

O sistema Teams do AionUI comunica com agentes via **MCP stdio** (não ACP). O Hermes expõe **ACP**, não MCP stdio — são protocolos incompatíveis à partida. Foi adicionado suporte a `--experimental-acp` no Hermes, mas o AionUI espera MCP stdio.

## Arquitectura do AionUI Teams

### Fluxo de Spawn do Team Leader

```
AionUI → spawn(cliPath="/Users/alvarobiano/.hermes/venv/bin/hermes",
               args=["--experimental-acp"])
    ↓
Hermes recebe --experimental-acp → inicia acp_adapter.entry
    ↓
Mas o AionUI espera: team-guide-mcp-stdio.js como stdio server
```

### O Papel do team-guide-mcp-stdio.js

Ficheiro: `/Applications/AionUI.app/Contents/Resources/app.asar.unpacked/out/main/team-guide-mcp-stdio.js`

Este é um **servidor MCP stdio standalone** que:
- Recebe env vars: `AION_MCP_PORT`, `AION_MCP_TOKEN`, `AION_MCP_BACKEND`, `AION_MCP_CONVERSATION_ID`
- Liga-se ao TCP server interno do AionUI (na porta `AION_MCP_PORT`)
- Expõe ferramentas: `aion_create_team`, `aion_list_models`

```javascript
// Estrutura simplificada
var AION_MCP_PORT = parseInt(process.env.AION_MCP_PORT || "0", 10);
var AION_MCP_TOKEN = process.env.AION_MCP_TOKEN || "";

// Cada tool faz um sendTcpRequest() para o AionUI
function createAionTool(server, toolName, description, schema, tcpPort, authToken) {
    server.tool(toolName, description, schema, async (args) => {
        const payload = {
            tool: toolName,
            args,
            auth_token: authToken,
            backend: AION_MCP_BACKEND,
            conversation_id: AION_MCP_CONVERSATION_ID
        };
        const response = await sendTcpRequest(tcpPort, payload);
        return { content: [{ type: "text", text: response.result || "" }] };
    });
}

async function main() {
    const transport = new StdioServerTransport();
    await server.connect(transport);
}
```

### TCP Server Interno do AionUI

Classe: `TeamGuideMcpServer` em `index.js`

```javascript
// Lista em AION_MCP_PORT, autentica com token, processa pedidos
handleTcpConnection(socket) {
    const reader = createTcpMessageReader(async (msg) => {
        if (request.auth_token !== this.authToken) {
            writeTcpMessage(socket, { error: "Unauthorized" });
            return;
        }
        const result = await this.handleToolCall(toolName, args, backend, conversationId);
        writeTcpMessage(socket, { result });
    });
}
```

### Injeccão do MCP Server no Agente

Em `ensureSession()`:

```javascript
if (await shouldInjectTeamGuideMcp(this.agentConfig.agentBackend)) {
    const aionStdioConfig = getTeamGuideStdioConfig();
    this.agentConfig.presetMcpServers = [
        ...this.agentConfig.presetMcpServers || [],
        {
            name: aionStdioConfig.name,
            command: aionStdioConfig.command,
            args: aionStdioConfig.args,
            env: [
                ...aionStdioConfig.env,
                { name: "AION_MCP_BACKEND", value: this.agentConfig.agentBackend },
                { name: "AION_MCP_CONVERSATION_ID", value: this.conversationId }
            ]
        }
    ];
}
```

## Hermes ACP vs AionUI MCP Stdio

| Aspecto | Hermes ACP | AionUI Teams MCP Stdio |
|---------|-----------|------------------------|
| Protocolo | ACP (Agent Client Protocol) | MCP (Model Context Protocol) |
| Transporte | stdio / network | stdio (child process) |
| Ferramentas | Via ACP SDK | Via JSON-RPC over stdio |
| Bibliotecas | `agent-client-protocol` (Python) | `@modelcontextprotocol/sdk` (Node.js) |
| Integração | Editor (VS Code, Zed, JetBrains) | AionUI Teams |

## Soluções Possíveis

### Opção 1: MCP Stdio Wrapper para Hermes
Criar um processo wrapper que:
1. Inicia o Hermes ACP
2. Expõe um servidor MCP stdio
3. Traduz chamadas MCP → ACP e vice-versa

**Dificuldade:** Alta — requer manter estado entre protocolos diferentes.

### Opção 2: Modificar AionUI para ACP
Alterar o AionUI para aceitar ACP em vez de MCP stdio.
**Dificuldade:** Impossível — código é propietario (app.asar).

### Opção 3: Bridge TCP Custom
Criar um bridge que:
1. Liga ao TCP server do AionUI
2. Expõe um MCP stdio server
3. Encaminha pedidos para o Hermes ACP

**Dificuldade:** Média — o Hermes não tem API ACP pública para tool calls arbitrários.

## Ficheiros Relevantes

### Hermes
- `~/.hermes/hermes-agent/hermes_cli/_parser.py` — adiciona `--experimental-acp`
- `~/.hermes/hermes-agent/hermes_cli/main.py` — handler para `--experimental-acp`
- `~/.hermes/hermes-agent/acp_adapter/entry.py` — entry point ACP

### AionUI (Mac)
- `/Applications/AionUI.app/Contents/Resources/app.asar` — `KNOWN_TEAM_CAPABLE_BACKENDS` modificado
- `/Applications/AionUI.app/Contents/Resources/app.asar.unpacked/out/main/team-guide-mcp-stdio.js` — script MCP stdio
- `~/Library/Application Support/AionUI/aionui/aionui.db` — base de dados com teams

### Base de Dados
```sql
-- Team existente
SELECT * FROM teams;
-- 515f1892-7709-41d7-ac67-7683380b33a8|system_default_user|TEN Team|...|slot-1df887d8|...

-- Schema
CREATE TABLE teams (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    name TEXT NOT NULL,
    workspace TEXT,
    visibility TEXT,
    lead_agent_id TEXT,
    members TEXT,  -- JSON array
    created_at INTEGER,
    updated_at INTEGER
);
```

## Estado Actual (Maio 2026)

- ✅ `--experimental-acp` adicionado ao Hermes
- ✅ `hermes` em `KNOWN_TEAM_CAPABLE_BACKENDS`
- ⚠️ Hermes inicia mas não consegue comunicar com Teams via ACP
- ⚠️ TEN Team existe na BD com `status=pending`
- O Hermes Gateway não tem plataforma Teams activa (só Telegram)

## Comandos de Diagnóstico

```bash
# Ver teams na BD
sqlite3 ~/Library/Application\ Support/AionUI/aionui/aionui.db "SELECT * FROM teams;"

# Ver se Hermes aceita --experimental-acp
~/.hermes/venv/bin/hermes --experimental-acp --help | grep experimental

# Verificar se app.asar tem hermes na lista
strings /Applications/AionUI.app/Contents/Resources/app.asar 2>/dev/null | grep "KNOWN_TEAM_CAPABLE_BACKENDS"

# Ver plataformas activas no gateway
cat ~/.hermes/gateway_state.json
```
