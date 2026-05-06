---
name: sac-agent-architecture
description: Complete chatbot architecture with lead capture, SQLite persistence, RAG responses, and conversation history context injection. Built for Método TEN SAC.
---

# SAC Agent — Architecture & Deployment

## Description
Complete architecture for a chatbot with lead capture, conversation history persistence, and RAG-based responses. Built for the Método TEN SAC.

## Architecture Overview

```
┌─────────────────────────────────────────────┐
│           HTML Chat Page (index.html)        │
│  • Form: nome + telefone (máscara DD)       │
│  • Validação em tempo real                   │
│  • Transição para chat após validação        │
│  • /webhook/sac/init → boas-vindas          │
│  • /webhook/sac → chat normal               │
└────────────┬────────────────────────────────┘
             │ POST /webhook/sac (ou /init)
             ▼
┌─────────────────────────────────────────────┐
│         Flask Server (sac_agent.py)          │
│  Porta 5123                                  │
│  • /webhook/sac/init — identifica lead      │
│  • /webhook/sac — pergunta normal           │
│  • /admin — dashboard metrics               │
│  • /health                                  │
└──────┬──────────────────────┬────────────────┘
       │                      │
       ▼                      ▼
┌──────────────┐    ┌─────────────────────────┐
│  SQLite DB    │    │    LanceDB (RAG)        │
│ (leads +      │    │  Coleção: metodoten     │
│  conversas)   │    │  ~1.426 chunks          │
│ sac_leads.db │    │  + api (Evolution API)   │
└──────────────┘    └─────────────────────────┘
```

## Key Files

| File | Purpose |
|------|---------|
| `~/.hermes/sac_agent/sac_agent.py` | Flask server + persuasive routing + admin routes |
| `~/.hermes/sac_agent/templates/admin.html` | **Admin dashboard template** — métricas, leads, modal conversas, modais confirmação, toasts |
| `~/.hermes/sac_agent/templates/kanban.html` | **Kanban board template** — drag-and-drop, badges de temperatura, funil de leads |
| `~/.hermes/sac_agent/templates/admin-login.html` | **Login admin template** —页de de login dedicada |
| `~/.hermes/sac_agent/sac_db.py` | SQLite DB module + avaliação queries + funil de leads |
| `~/.hermes/sac_agent/sac_persuasao.py` | **Persuasão completa: PAS, AIDA, objeções, Socráticas** |
| `~/.hermes/sac_agent/sac_schema.sql` | SQLite schema |
| `~/.hermes/sac_agent/templates/index.html` | Chat UI + estrelas + WhatsApp CTA |
| `~/.hermes/sac_agent/sac_leads.db` | SQLite database |

## Database Schema

```sql
-- leads: cadastro único por pessoa
CREATE TABLE leads (
    id INTEGER PRIMARY KEY,
    nome TEXT, primeiro_nome TEXT, sobrenome TEXT,
    telefone TEXT, ddd TEXT,
    primeiro_contato TEXT, ultimo_contato TEXT,
    total_mensagens INTEGER, conversa_count INTEGER,
    avaliacao_nota INTEGER DEFAULT NULL,
    avaliado_em TEXT DEFAULT NULL,
    whatsapp_clicks INTEGER DEFAULT 0,
    estagio TEXT DEFAULT 'novo'  -- novo|qualificado|conversa|whatsapp|matriculado|desistente
);

-- conversas: cada interação
CREATE TABLE conversas (
    id INTEGER PRIMARY KEY,
    lead_id INTEGER, timestamp TEXT, tipo TEXT,
    mensagem TEXT, fontes TEXT, tempo_ms INTEGER, session_id TEXT
);

-- avaliacoes: avaliação por estrelas
CREATE TABLE avaliacoes (
    id INTEGER PRIMARY KEY,
    lead_id INTEGER NOT NULL,
    nota INTEGER NOT NULL CHECK(nota >= 1 AND nota <= 5),
    comentario TEXT DEFAULT NULL,
    criado_em TEXT NOT NULL,
    FOREIGN KEY(lead_id) REFERENCES leads(id)
);

-- approved_qa: Q&As curadas
CREATE TABLE approved_qa (
    id INTEGER PRIMARY KEY,
    collection TEXT NOT NULL DEFAULT 'metodo-ten',
    pergunta TEXT, resposta TEXT,
    tema TEXT DEFAULT '',
    aprovado_em TEXT,
    uso_count INTEGER DEFAULT 0, last_used TEXT
);
CREATE INDEX idx_qa_collection ON approved_qa(collection);
```

## Admin Dashboard

### Credenciais
- **Username:** `admin`
- **Password:** `t3rAp32026!` (variável env `ADMIN_PASSWORD` no systemd service)
- **Token secret:** `s3cr3t-t0ken-ch4ng3-m3!` (variável env `ADMIN_TOKEN_SECRET`)

### Rotas Admin
| Method | Path | Purpose |
|--------|------|---------|
| GET | `/admin/login` | Página de login admin (NUNCA usar `/` como redirect — é o Typebot) |
| POST | `/admin/login` | Valida credenciais, devolve cookie httpOnly com HMAC token |
| POST/GET | `/admin/logout` | Limpa cookie, redirect para /admin/login |
| GET | `/admin` | Dashboard (requer token válido → redirect /admin/login se sem cookie) |
| GET | `/kanban` | Página Kanban do funil de leads (requer token, mesmo que /admin) |
| GET | `/admin/kanban` | API JSON — dados do Kanban (leads por estágio + estatísticas) |
| PATCH | `/admin/leads/<id>/estagio` | Move lead para outro estágio (PATCH JSON {estagio}) |
| GET | `/admin/stats/leads` | Métricas leads |
| GET | `/admin/stats/conversas` | Métricas conversas |
| GET | `/admin/stats/qa` | Métricas Q&As |
| GET | `/admin/stats/avaliacoes` | Métricas avaliações |
| GET | `/admin/leads/<id>/conversas` | Todas as conversas de um lead |
| DELETE | `/admin/leads/<id>` | Exclui lead + conversas em cascade |

### Regras de UI (OBRIGATÓRIO)
- **NUNCA usar `confirm()` ou `alert()` nativos do browser** — usar SEMPRE componentes criados por nós
- Modal de confirmação para exclusões (overlay + card personalizado)
- Toast notifications para feedback (sucesso/erro) — desaparecem em 3.5s
- Admin icon 🔒 posicionado na `tela-captura` (ANTES do chat), canto superior direito

## Important Discoveries (Trial & Error)

1. **BUG CRÍTICO — `send_file()` vs `render_template_string()`**: `send_file()` envia HTML como ficheiro estático — **não processa** Jinja2 `{{变量}}`. Se a página tem `{{ username }}` e é servida com `send_file()`, aparece literalmente `{{ username }}`. **Solução**: ler o ficheiro HTML com `open()`, guardar em string, usar `render_template_string(tmpl, username=username)`.

2. **BUG CRÍTICO — rotas admin redirecionam para `/` (página do Typebot)**: Quando o admin não tem token, `redirect("/")` manda para a página do Typebot, não para login. **Solução**: criar página `/admin/login` dedicada e usar `redirect("/admin/login")` em todas as rotas admin.

3. **`send_file()` + Jinja2 + `{{}}` = template literal collision**: Mesmo usando `render_template_string()`, se o HTML contiver JavaScript com template literals (`` `${var}` ``), as chaves `{}` dentro de backticks são interpretadas como f-string por Python se estiver dentro de `f"""..."""`. **Solução**: ficheiro `.html` separado, lido com `open()` → `render_template_string()`.

4. **LLM Hallucination Guard (CRÍTICO)**: O LLM pode gerar informação incorrecta que NÃO está no RAG. Apenas "psicólogo" é reservado por lei (CRP). Solução: regra explícita no system prompt com "CORRECÇÃO FACTUAL OBRIGATÓRIA".

3. **Regra UI: zero native dialogs**: Álvaro exige que TODA a interacção com o utilizador seja via componentes criados por nós. `confirm()` e `alert()` nativos são proibidos — usar sempre modal custom + toast notifications.

4. **Field name mismatch bug**: O endpoint `/webhook/sac` procura campos nesta ordem: `pergunta` → `mensagem` → `message` → `text`. Campo errado = resposta vazia → "Não entendi".

5. **Marielena → membro da equipe**: O LLM gerava "Marielena" incorrectamente. Corrigido com `texto.replace()` em `formatar_resposta()` e `plain_resposta()`.

6. **LanceDB vector re-indexing**: Quando se adiciona documentos sem vectores, `tbl.add()` guarda sem embeddings. Deve-se apagar e re-adicionar com campo vector explícito.

7. **cloudflared quick tunnel**: URL muda a cada restart — não é estável para systemd. Para URL estável, usar conta Cloudflare com named tunnel.

## Q&A Aprovadas — Camada de Respostas Pré-Aprovadas

**Arquitectura de prioridade:**
```
Pergunta → Camada 1: Q&A aprovadas (Jaccard similarity, threshold 0.45)
         → Camada 2: LanceDB (busca vetorial apostilas)
```

**Matching: Jaccard + Stopwords**
```python
STOPWORDS = {'o','a','os','as','um','uma','e','é','que','de','do','da',
             'em','no','na','se','para','com','por','mais','ou'}

def _jaccard(s1, s2) -> float:
    # Sem stopwords, threshold 0.45
    # Scores < 0.45 → vai para LanceDB
```

## Deployment

### Serviço systemd
```ini
# ~/.config/systemd/user/sac-agent.service
[Unit]
Description=SAC Agent — Typebot Webhook (Método TEN RAG)
After=network.target

[Service]
Type=simple
Restart=always
RestartSec=5
Environment=ADMIN_PASSWORD=t3rAp32026!
Environment=ADMIN_TOKEN_SECRET=s3cr3t-t0ken-ch4ng3-m3!
ExecStart=/home/alvarobiano/.hermes/sac_agent/venv/bin/python3 /home/alvarobiano/.hermes/sac_agent/sac_agent.py --port 5123 --host 0.0.0.0
WorkingDirectory=/home/alvarobiano/.hermes/sac_agent
StandardOutput=append:/home/alvarobiano/.hermes/logs/sac_agent.log
StandardError=append:/home/alvarobiano/.hermes/logs/sac_agent_error.log
```
```bash
systemctl --user daemon-reload
systemctl --user restart sac-agent
```

## Bugs Descobertos

1. **Campo "mensagem" vs "pergunta"**: O endpoint `/webhook/sac` procura nesta ordem: `pergunta` → `mensagem` → `message` → `text`. Campo errado = resposta vazia.
2. **LLM inventa informação**: O LLM pode dizer que "psicoterapia é restrita" quando não é. Corrigido com regra explícita no system prompt.
3. **Tuple index out of range em `buscar_qa_similar`**: Índices inconsistentes entre SELECT e acesso posicional.
4. **`send_file()` não processa Jinja2**: `{{ username }}` aparece literal se servido com `send_file()`. Usar `render_template_string()`.
5. **Anglicismos no LLM**: MiniMax M2.7 às vezes gera palavras em inglês. System prompt com regra estrita.
6. **Rotinas admin sem página de login dedicada**: `redirect("/")` ia para o Typebot. Criado `/admin/login` com template próprio.
7. **SyntaxError em JS com template literals dentro de Python f-strings**: `` `<div data-id="${l.id}">` `` dentro de `f"""..."""` quebra. Usar ficheiro `.html` separado.

## Funil de Leads (Kanban)

**Estágios:** `novo` → `qualificado` → `conversa` → `whatsapp` → `matriculado` → `desistente`

**Migração de leads existentes:**
```python
# Leads com whatsapp_clicks > 0 → estágio 'whatsapp'
# Leads com conversa_count > 0 E whatsapp_clicks = 0 → estágio 'conversa'
# Resto → 'novo'
```

**Badge de temperatura** (baseado em `ultimo_contato`):
- Quente: < 2h
- Morno: 2-24h
- Frio: > 24h

**Funções em `sac_db.py`:**
- `atualizar_estagio(lead_id, estagio)` — atualiza e loga mudança
- `get_leads_por_estagio()` — retorna leads com badge de temperatura
- `get_estatisticas_funil()` — contadores por estágio
- `ESTAGIOS`, `ESTAGIO_LABEL`, `ESTAGIO_ICONE` — constantes globais

**Atualização automática:** `registrar_whatsapp_click()` chama `atualizar_estagio(lead_id, "whatsapp")` automaticamente.

## Sistema de Avaliação por Estrelas

**Regras:**
- Mínimo 2 interações antes de mostrar
- Nunca avaliou → mostra
- Avaliou com < 4 estrelas → mostra novamente
- Avaliou com >= 4 estrelas → não mostra mais

## Sistema de Persuasão (`sac_persuasao.py`)

### Frameworks implementados

| Framework | Fase | Gatilho |
|-----------|------|---------|
| **PAS** (Problem-Agitate-Solution) | descoberta | `get_gatilho("pas")` |
| **AIDA** (Attention-Interest-Desire-Action) | interesse | `get_gatilho("aida")` |
| **Gatilhos de medo** | sinais["medo"] | `get_gatilho("medo")` |
| **Gatilhos de dor** | sinais["dor"] | `get_gatilho("dor")` |
| **Prova social** | qualificação | `get_gatilho("prova_social")` |
| **Diferencial** | interesse | `get_gatilho("diferencial")` |
| **Urgência** | decisão | `get_gatilho("urgencia")` |

### Tratamento de objeções (7 tipos)

```python
tratar_objecao(texto)  # retorna string de resposta ou None
# Detecta: não tenho dinheiro, vou pensar, não tenho tempo,
#          já fiz outro curso, não sei se consigo,
#          medo de não conseguir depois, é caro
```

## Regras de Sistema do LLM (System Prompts)

Ambas as funções `llm_generate()` e `llm_generate_from_qa()` incluem:

1. PROIBIÇÃO de primeira pessoa ("eu", "meu")
2. Termos genéricos para equipa ("a gente", "a equipe")
3. **CORRECÇÃO FACTUAL:** "psicoterapia" NÃO é reservada — apenas "psicólogo" é reservado por lei (CRP)
4. **PROIBIÇÃO ABSOLUTA DE INFORMAÇÃO EXTERNA:** Só pode usar conteúdo do RAG.

## Correção Automática de Nomes

Em `formatar_resposta()` e `plain_resposta()`:
```python
texto = texto.replace("Marielena", "membro da equipe")
```

## Status
Stable — in production use. Admin dashboard implementado com métricas, gestão de leads, visualização e exclusão de conversas.
