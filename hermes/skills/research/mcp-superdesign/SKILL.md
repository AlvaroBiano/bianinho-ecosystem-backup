---
name: mcp-superdesign
description: Agente AI de design open source para IDEs — MCP servers e CLI do Superdesign
tags: [mcp, design, open-source, ai, ide]
created: 2026-04-23
updated: 2026-04-23
---

# Superdesign MCP — Research Notes

## O que é
Agente AI de design open source que roda dentro de IDEs (Cursor, Windsurf, Claude Code, VS Code).
Repo: github.com/superdesigndev/superdesign | AGPL-3.0 | TypeScript | 6.332 stars
Criadores: @jasonzhou1993 e @jackjack_eth

## MCP Servers Disponíveis
1. `zjohnsonbox/superdesign-mcp-server` — Pacote @superdesign/mcp-server (MIT) — npm
   - Ferramentas: generate_design, create_layout, generate_theme, manage_project, read/write/edit_file, glob_tool, grep_tool, preview_design, list_designs
2. `jonthebeef/superdesign-mcp-claude-code` — MCP alternativo (MIT)
   - Ferramentas: superdesign_generate, superdesign_iterate, superdesign_extract_system, superdesign_list
3. `@superdesign/cli` (npm) — CLI standalone

## Compatibilidade com Hermes Agent
**NÃO compatível nativamente.** O MCP foi projetado para rodar dentro de Claude Code CLI como host. O Hermes Agent é CLI agent standalone sem contexto de IDE.

## Preço
100% gratuito e open source (AGPL-3.0). Não requer API keys próprias — usa a subscription do IDE.
Suporta servidores OpenAI compatíveis locais (LM Studio, etc.).

## Potencial Futuro
Pode ser útil via @superdesign/cli como exec-shell para workflows de design que envolvam código.

## Links
- IDE Extension: https://www.superdesign.dev/ide-extension
- Discord: https://discord.gg/FYr49d6cQ9
- Hackernews: https://news.ycombinator.com/item?id=44376003

---

# Relatório Completo — MCP Servers Gratuitos (23/04/2026)

## Fontes Consultadas
- github.com/modelcontextprotocol/servers (oficial — reference implementations)
- github.com/modelcontextprotocol/servers-archived
- GitHub Search API (repositórios com "mcp-server" + filtro linguagem)
- npm search para @modelcontextprotocol/server-*

## TOP 20 MCP Servers Open Source por Estrelas

| # | Repo | Estrelas | Licença | Descrição |
|---|---|---|---|---|
| 1 | googleapis/mcp-toolbox | 14,784 | Apache-2.0 | Toolbox de databases — query, schema, introspecção |
| 2 | casdoor/casdoor | 13,471 | Apache-2.0 | IAM para agentes LLM — OAuth, OIDC, SAML, LDAP, MFA |
| 3 | webiny/webiny-js | 7,970 | NOASSERTION | CMS serverless AWS com MCP built-in |
| 4 | idosal/git-mcp | 7,966 | Apache-2.0 | Servidor remoto MCP para GitHub — elimina alucinações de código |
| 5 | aipotheosis-labs/aci | 4,753 | Apache-2.0 | 600+ ferramentas via MCP — direct function calling |
| 6 | osaurus-ai/osaurus | 5,116 | MIT | Memory hub macOS — qualquer modelo, execução autônoma |
| 7 | PrefectHQ/fastmcp | 3,055 | Apache-2.0 | Framework TypeScript para construir MCP servers |
| 8 | Gentleman-Programming/engram | 2,782 | MIT | Memory persistente — Go binary + SQLite + FTS5, agent-agnostic |
| 9 | moltis-org/moltis | 2,599 | MIT | Personal agent server em Rust — sandboxed, multi-provider |
| 10 | taylorwilsdon/google_workspace_mcp | 2,197 | MIT | Gmail, Calendar, Docs, Sheets, Slides, Drive via MCP |
| 11 | PleasePrompto/notebooklm-mcp | 2,099 | MIT | Pesquisa documentação via NotebookLM em agentes |
| 12 | agentset-ai/agentset | 1,962 | MIT | RAG platform open source — citações, deep research, 22+ formats |
| 13 | DeusData/codebase-memory-mcp | 1,803 | MIT | Code intelligence — indexa codebases em knowledge graph persistente |
| 14 | stickerdaniel/linkedin-mcp-server | 1,655 | Apache-2.0 | LinkedIn via MCP — profiles, companies, jobs, messages |
| 15 | doobidoo/mcp-memory-service | 1,723 | Apache-2.0 | Memory service para pipelines (LangGraph, CrewAI, AutoGen) |
| 16 | ghostwright/phantom | 1,361 | Apache-2.0 | AI co-worker — memória persistente, credenciais seguras |
| 17 | arabold/docs-mcp-server | 1,260 | MIT | Alternativa open source ao Context7 — docs grounding |
| 18 | brave/brave-search-mcp-server | 932 | MIT | Busca web via Brave Search API (requer API key) |
| 19 | SixHq/Overture | 613 | MIT | Visualiza plano de execução de agente como flowchart/graph |
| 20 | Dataojitori/nocturne_memory | 983 | MIT | Memory server leve com rollback e visualização |

## Reference Servers Oficiais MCP (Arquivados)

Disponíveis em servers-archived. Todos open source mas alguns requerem API keys:

| Server | Descrição | API Key? |
|---|---|---|
| brave-search | Busca web e local | ✅ Brave API key |
| everart | Geração de imagens AI | ✅ API key |
| github | Gestão repos, ficheiros, API | ✅ GitHub token |
| gitlab | API GitLab | ✅ GitLab token |
| gdrive | Acesso Google Drive | ✅ Google OAuth |
| google-maps | Localização, direções | ✅ Google API |
| postgres | Acesso read-only a PostgreSQL | ❌ Gratuito |
| puppeteer | Browser automation | ❌ Gratuito |
| redis | Key-value store | ❌ Gratuito |
| sentry | Issues do Sentry | ✅ Sentry DSN |
| slack | Channel management | ✅ Slack token |
| sqlite | Interação SQLite | ❌ Gratuito |
| aws-kb-retrieval | AWS Knowledge Base + Bedrock | ✅ AWS |

## Análise: Mais Relevantes para o Hermes Agent

### Categoria: Memória Persistente
1. **engram** (MIT, 2,782 stars) — Go binary + SQLite + FTS5. Agent-agnostic. Uma binary, zero deps. Potencial alto para memória de longo prazo do Bianinho.
2. **codebase-memory-mcp** (MIT, 1,803 stars) — Indexa codebases em knowledge graph. Útil para código intelligence.
3. **mcp-knowledge-graph** (MIT, 840 stars) — Graph database local para memória.
4. **memora** (MIT, 394 stars) — Persistent memory simples.

### Categoria: Databases
1. **mcp-toolbox** (Apache-2.0, 14,784 stars) — Google Cloud only (BigQuery, Spanner, etc.). Menos relevante.
2. **postgres** (referência) — Read-only PostgreSQL. Poderia conectar ao Hermes sessions DB.
3. **sqlite** (referência) — Poderia expor sac_leads.db, Hermes sessions, etc.

### Categoria: Integração Web/Produtividade
1. **google_workspace_mcp** (MIT, 2,197 stars) — Gmail, Calendar, Docs, Sheets. Alto valor para workflows do Álvaro.
2. **linkedin-mcp-server** (Apache-2.0, 1,655 stars) — LinkedIn automation.
3. **brave-search-mcp-server** (MIT, 932 stars) — Web search. Requer Brave API key (gratuita disponível).

### Categoria: Código/Git
1. **git-mcp** (Apache-2.0, 7,966 stars) — Servidor remoto para GitHub. Reduz alucinações em código.
2. **mcp-puppeteer** — Browser automation (arquivado).

### Categoria: RAG/Conhecimento
1. **agentset** (MIT, 1,962 stars) — RAG platform open source com 22+ formatos.
2. **docs-mcp-server** (MIT, 1,260 stars) — Alternativa Context7 para docs grounding.

## Recomendação de Prioridade para o Hermes Agent

**Alta prioridade:**
- `engram` — memory persistente (Go binary, SQLite, FTS5, MIT)
- `google_workspace_mcp` — Gmail/Calendar/Docs (MIT, alto valor prático)
- `sqlite` reference server — expor Hermes sessions DB e sac_leads.db
- `postgres` reference server — se usar PostgreSQL

**Média prioridade:**
- `git-mcp` — GitHub integration (reduz alucinações em código)
- `codebase-memory-mcp` — code intelligence
- `brave-search-mcp-server` — web search (requer Brave API key gratuita)

**Baixa prioridade:**
- `superdesign` — já documentado, não compatível nativamente
- LinkedIn MCP — útil para social media automation
- `Overture` — flowchart de agentes (interessante mas cedo)

## NOTA: Servidor MCP vs Integração Direta
MCP servers são desenhados para IDEs/clients que suportem o protocolo. O Hermes Agent é Python-based. Para usar um MCP server com Hermes, seria necessário:
1. O Hermes suportar nativamente o protocolo MCP (não suporta atualmente)
2. Ou usar um wrapper/adapter
3. Ou executar o MCP como subprocesso e коммуницировать via stdio

Verificar se o Hermes Agent tem suporte MCP antes de tentar integração.

## Links Úteis
- Lista oficial de servers: https://github.com/modelcontextprotocol/servers
- MCP Registry: https://registry.modelcontextprotocol.io/
- Awesome MCP Servers: https://github.com/punkpeye/awesome-mcp-servers
- MCP Servers Org (glama): https://glama.ai/mcp/servers
- MCP Servers (mcpservers.org): https://mcpservers.org
