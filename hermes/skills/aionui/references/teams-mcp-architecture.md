# Teams MCP — Arquitectura e Troubleshooting (03/05/2026)

## Arquitectura Teams MCP

### Componentes

| Ficheiro | Backend | Protocolo | Línguagem |
|----------|---------|------------|-----------|
| `team-mcp-stdio.js` | aionrs, gemini, claude, codex | stdio → TCP bridge | Node.js |
| `hermes_team_mcp_stdio.py` | hermes | stdio → TCP bridge | Python 3 |
| `TeamGuideMcpServer` (interno) | todos | TCP server (porta dinâmica) | Node.js |

Localização no DMG:
```
/Applications/AionUi.app/Contents/Resources/app.asar.unpacked/out/main/
├── team-mcp-stdio.js                    # Para non-Hermes
├── hermes_team_mcp_stdio.py            # Para Hermes
└── team-guide-mcp-stdio.js            # Para non-Hermes (legacy?)
```

### Fluxo de Inicialização (como Team Leader)

1. AionUI inicia processo Hermes com variáveis de ambiente:
   - `TEAM_MCP_PORT=<porta_dinamica>`
   - `TEAM_MCP_TOKEN=<auth_token>`
   - `AION_MCP_BACKEND=hermes`
   - `AION_MCP_CONVERSATION_ID=<conversation_id>`

2. Hermes carrega `hermes_team_mcp_stdio.py` como MCP server stdio

3. `hermes_team_mcp_stdio.py` conecta-se ao `TeamGuideMcpServer` via TCP

4. TeamGuideMcpServer regista as tools `team_spawn_agent`, `team_list_models`, etc.

5. Hermes expõe as tools ao LLM

### Tools Disponíveis (via Teams MCP)

```
team_spawn_agent       - Criar teammate
team_list_models       - Listar modelos disponíveis
team_members           - Listar membros da equipa
team_task_create       - Criar tarefa
team_task_list         - Listar tarefas
team_task_update       - Actualizar tarefa
team_send_message      - Enviar mensagem a teammate
team_shutdown_agent    - Desligar teammate
team_rename_agent      - Renomear teammate
team_describe_assistant - Descrever preset assistant
```

### Como Verificar se Teams MCP Está a Correr

```bash
# 1. Verificar processos
ps aux | grep -E "team-mcp|hermes_team" | grep -v grep

# 2. Verificar logs
grep "TeamGuideMcpServer\|team_mcp\|hermes_team" ~/Library/Logs/AionUi/$(date +%Y-%m-%d).log | tail -20

# 3. TeamGuideMcpServer ativo (porta dinâmica)
grep "TCP server started on port" ~/Library/Logs/AionUi/$(date +%Y-%m-%d).log | tail -5

# 4. Verificar se Hermes foi iniciado com variáveis de Teams
# Ver no log: [ACP hermes STDERR] se mostra AION_MCP_PORT
```

### Erro Comum: EACCES ao Persistir Config

**Log:**
```
[error] [Storage] Failed to persist /Users/alvarobiano/.aionui-config/aionui-config.txt: Error: EACCES: permission denied
[warn] [mcpReadiness] Timed out waiting for MCP ready: slot-xxxxx
```

**Fix:**
```bash
chmod u+w ~/.aionui-config/aionui-config.txt
```

### Equipa Existente vs Equipa Nova

O AionUI mantém múltiplas equipas. Cada Team tem:
- `teamId` (UUID)
- Porta TCP própria (`TeamMcpServer` separado)
- Sessão ACP própria

Se Hermes já está a correr como Team Leader numa sessão, ao criar nova equipa:
- AionUI inicia novo processo Hermes para o Team Leader
- O Hermes "principal" (chat) continua separado

**Conclusão:** Não há comunicação directa entre o Hermes Team Leader e o Hermes principal a não ser via BD SQLite partilhada (só leitura).

### Logs Úteis

| Ficheiro | O que procurar |
|----------|--------------|
| `~/Library/Logs/AionUi/YYYY-MM-DD.log` | TeamGuideMcpServer, team_mcp, EACCES |
| stderr do Hermes (`[ACP hermes STDERR]`) | AION_MCP_PORT, MCP ready, tools |

### Debugging Passo a Passo

1. **Permissão do config** — `chmod u+w ~/.aionui-config/aionui-config.txt`
2. **Logs** — `grep -i "EACCES\|TeamGuide\|mcpReadiness" ~/Library/Logs/AionUi/$(date +%Y-%m-%d).log`
3. **Processos** — `ps aux | grep team-mcp`
4. **Reiniciar AionUI** — fechar e reabrir
5. **Nova sessão Teams** — criar Team novo com Hermes como Leader
