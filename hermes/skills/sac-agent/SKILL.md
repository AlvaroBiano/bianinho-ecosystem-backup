---
name: sac-agent
description: Como implementar features no SAC Admin dashboard — rotas Flask, templates HTML, DB functions, schema SQL
trigger: Implementar nova funcionalidade no dashboard admin do SAC Bot
---

# SAC Admin Dashboard — Como Implementar Features

**Domínio:** sac-agent  
**Quando usar:** Implementar novas funcionalidades no dashboard admin do SAC Bot (Kanban, gráficos, métricas, etc.)

---

## Abordagem

### 1. Investigar o existente antes de mexer
```bash
# Ver colunas atuais do DB
python3 -c "import sqlite3; c=sqlite3.connect('~/.hermes/sac_agent/sac_leads.db').cursor(); print([r[1] for r in c.execute('PRAGMA table_info(leads)')])"

# Ver como leads são criados (buscar_ou_criar_lead em sac_db.py)
# Ver webhook init (webhook_sac_init em sac_agent.py)
```

### 2. Sempre usar migração (não recriar tabela)
```python
# Adicionar coluna se não existir
cols = [r[1] for r in cur.fetchall()]
if 'nova_coluna' not in cols:
    conn.execute("ALTER TABLE leads ADD COLUMN nova_coluna TEXT DEFAULT ''")
```

### 3. UPDATE dinâmico — nunca sobrepor campos não-passados
```python
# CERTO: UPDATE selectivo, só actualiza campos passados (não-None)
def salvar_diagnostico(lead_id, nivel_impacto=None, nivel_clareza=None, ...):
    set_clauses = []
    params = []
    if nivel_impacto is not None:
        set_clauses.append("nivel_impacto = ?")
        params.append(nivel_impacto)
    if nivel_clareza is not None:
        set_clauses.append("nivel_clareza = ?")
        params.append(nivel_clareza)
    if not set_clauses:
        return True
    params.append(lead_id)
    sql = f"UPDATE leads SET {', '.join(set_clauses)} WHERE id = ?"
    conn.execute(sql, params)
    # ERRADO: UPDATE com valores default (sobrescreve campos não-passados com '')
    # conn.execute("UPDATE leads SET nivel_impacto=? WHERE id=?", (nivel_impacto, lead_id))
    # → se nivel_impacto=8 mas nivel_clareza não é passado, clareza volta a 0
```

### 4. Módulo separado para features complexas (não poluir sac_db.py)
```python
# Para features com lógica complexa: criar sac_db_<feature>.py
# ex: sac_db_diagnostico.py, sac_db_pilar2.py, etc.
import sac_db_diagnostico  # novo módulo
# Funções do módulo: get_diagnostico(), salvar_diagnostico(), get_estatisticas_diagnostico()
```

### 5. Após adicionar novo import em sac_agent.py — RESTARTAR sempre
```python
# Quando adiciona "import sac_db_nova_feature" em sac_agent.py
# O módulo é carregado ao fazer import — não há hot reload em produção
systemctl --user restart sac-agent
# Validar: systemctl --user status sac-agent → "active (running)"
```

### 6. Padrão Multi-Pilar (Álvaro workflow)
```bash
# Álvaro implementa pilares um a um — cada pilar:
# 1. Implementar feature
# 2. Testar 100% (curl + browser)
# 3. Admin dashboard actualizado
# 4. Commit + Push ANTES de avançar para próximo pilar
git add -A && git commit -m "feat(pilarN): descrição" && git push origin master

# Para reverter completamente se algo falhar:
git reset --hard <commit_hash_do_backup>
```

### 7. Máquina de estados — padrão para features sequenciais
```python
# Estados discretos com transição: IMPACTO → CLAREZA → ABOLIÇÃO → DEPOIS → COMPLETO
FASES = {"nenhum", "impacto", "clareza", "abolicao", "depois", "completo"}

def detectar_fase(lead_diag: dict) -> str:
    if lead_diag.get('diagnostico_completado'):
        return "completo"
    perguntas = lead_diag.get('perguntas_diagnosticas', {})
    if 'impacto' not in perguntas: return "impacto"
    if 'clareza' not in perguntas: return "clareza"
    if 'abolicao' not in perguntas: return "abolicao"
    if 'depois' not in perguntas: return "depois"
    return "completo"

def deve_entrar(interacoes, sinais, lead_diag) -> tuple[bool, str|None]:
    # Regras de gating: primeira msg, objeção, vago
    pass

# No Flask route: se fase_diag != "nenhum" e != "completo"
# → devolver pergunta de diagnóstico, SALVAR a resposta do lead no banco,
# → NÃO chamar RAG até diagnóstico estar completo
```

### 8. Detecção de texto com ordens de grandeza (mais específico → genérico)
```python
# Sempre: mais específico ANTES de genérico
if any(p in texto_lower for p in ["não sei por onde", "não sei como"]):
    return "desconhece"
if any(p in texto_lower for p in ["não sei", "não sei bem"]):
    return "falta_clareza"
# Se "dinheiro" e "tempo" usam "não tenho", detectar dinheiro/tempo ANTES do "não tenho" genérico
if any(p in texto_lower for p in ["não tenho grana", "não tenho condição"]):
    return "dinheiro"
if any(p in texto_lower for p in ["não tenho tempo", "sem tempo"]):
    return "tempo"
```

### 9. Testar endpoint de stats sem autenticação (validar retorno do DB)
```python
# Não precisas de token — testa directamente no Python
python3 -c "
import sac_db_nova_feature
stats = sac_db_nova_feature.get_estatisticas()
print(stats)
"
```
- Funções de DB vão em `sac_db.py`
- Rotas e lógica HTTP vão em `sac_agent.py`
- Templates HTML em `templates/`

### 4. Atualizar schema SQL (sac_schema.sql) após implementar

---

## Gotchas Encontradas

### Flask: redirect "/" vai para o Typebot, não admin
- **Problema:** As rotas admin faziam `redirect("/")` — isso ia para a página do Typebot, não admin
- **Fix:** Mudar para `redirect("/admin/login")` em todas as rotas admin autenticadas
- **Locais afetados:** `admin_page()`, `kanban_page()`, `admin_kanban()`, `admin_lead_estagio()`, etc.

### Flask: send_file() não processa Jinja2
- **Problema:** `admin_page()` usava `send_file("admin.html")` — `{{ username }}` era cru, sem processamento
- **Fix:** Ler arquivo, usar `render_template_string(tmpl, username=username)`
- **Pattern:**
```python
tmpl_path = os.path.join(os.path.dirname(__file__), "templates", "admin.html")
with open(tmpl_path, encoding="utf-8") as f:
    tmpl = f.read()
return render_template_string(tmpl, username=username)
```
- **Também:** Adicionar `render_template_string` ao import do Flask

### Python: usar conn após close()
- **Problema:** Em `buscar_ou_criar_lead`, fechava `conn.close()` e depois tentava usar `conn.execute()`
- **Fix:** Fazer re-fetch ANTES do `conn.close()`:
```python
conn.commit()
lead = dict(conn.execute("SELECT * FROM leads WHERE id=?", (id,)).fetchone())
conn.close()
return lead
```

### Python: `timedelta(minutos=)` → `timedelta(minutes=)` (bug real 26/04/2026)
- `datetime.timedelta` aceita apenas `minutes` (não `minutos` — Portuguese causa TypeError)
- **Sintoma:** `__new__() got an unexpected keyword argument 'minutos'`
- **Fix:** `timedelta(minutes=janela_minutos)` em `sac_db.py` → `marcar_abandono_apos_resposta()`

### SQL: schema duplicado `);` causa syntax error
- **Problema:** `sac_schema.sql` tinha `);` duplicado na linha 32 da tabela `leads` — `init_db()` falhava com `near ")": syntax error`
- **Sintoma:** `init_db()` dá syntax error mas a tabela já existe no DB — confunde
- **Fix:** Verificar linha 32 do schema, remover `);` extra
- **Verificação:** `~/.hermes/sac_agent/venv/bin/python3 -c "import sac_db; sac_db.init_db()"` — se não imprimir erro, schema está OK

### PRD-driven multi-phase implementation
- Quando o Álvaro apresenta um PRD com fases (Fase 1, 2, 3...), seguir a ordem e pedir aprovação entre fases
- Antes de cada fase: rever o PRD, identificar deps, confirmar scope
- Após cada fase: commitar + push antes de avançar
- Commit pattern: `"Fase N — descrição"` (ex: `"Fase 2 — Sinaergia: endpoints Flask + página admin-sinergia.html"`)

### Multi-template coordination (rewriting existing templates)
- admin.html, admin-qa.html, admin-gaps.html partilham a mesma nav bar — adicionar novos links em todos
- Ao reescrever um template existente (em vez de patch): fazer replace completo, depois verificar AST/sintaxe
- Nav bar pattern obrigatório:
  - CSS: `.nav-link{min-width:110px,h:34px,bg:#0f3460,color:#00d4ff,border:1px solid #00d4ff,br:6px,fw:600}`
  - HTML: `<a href="/admin/link" class="nav-link">🔗 Nome</a>`
- Client-side status: quando endpoints não devolvem `status`, calcular no JS antes de renderizar

### Verificar endpoints Flask sem autenticação (testar sintaxe)
- **Problema:** Login real pode falhar (password diferente) mas precisamos validar que os endpoints estão registados
- **Fix:** Usar venv do sac_agent para importar o app e iterar as rotas:
```bash
~/.hermes/sac_agent/venv/bin/python3 -c "
from sac_agent import app
for r in app.url_map.iter_rules():
    if 'sinergia' in r.rule or 'gap' in r.rule:
        print(r.rule)
"
```

### API key: o .env do projeto tem a chave real?
- **Problema:** Variáveis de ambiente do Docker/Linux sobrepõem o `.env` local — `MINIMAX_API_KEY` em prod pode ser diferente
- **Fix:** No testar endpoints, verificar sempre com `venv/bin/python` para apanhar imports de Flask do venv

### Client-side status calculation (quando DB não devolve `status`)
- **Problema:** `get_qa_performance_stats()` não devolve campo `status` — `admin-qa.html` precisa calcular
- **Fix:** Calcular no JavaScript antes de filtrar/renderizar:
```javascript
var taxa = q.taxa_sucesso_pct || 0;
var gapsTotal = (q.gaps_puros||0) + (q.gaps_parciais||0);
if ((q.gaps_puros||0) === 0 && (q.gaps_parciais||0) === 0 && taxa >= 80) {
    q.status = 'saudavel';
} else if (taxa < 50 || gapsTotal >= 3) {
    q.status = 'critico';
} else {
    q.status = 'atencao';
}
```

### Standalone cron scripts (sem Flask)
- **Problema:** Scripts em `~/.hermes/scripts/` para cron não devem importar Flask (pode não estar disponível fora do venv)
- **Fix:** Imports só de `sac_db`:
```python
#!/usr/bin/env python3
import sys
sys.path.insert(0, os.path.expanduser('~/.hermes/sac_agent'))
from sac_db import sync_gap_registry, get_sinergia_panel
```
- Executar sempre com venv: `~/.hermes/sac_agent/venv/bin/python3 ~/.hermes/scripts/sac_gap_conference.py sync`

### JS: concatenação com aspas dentro de aspas
- **Problema:** `'>''` em string JavaScript (erro de sintaxe "Invalid or unexpected token")
- **Fix:** `'</div>' + '<div class="coluna-body"...>'` — fechar string antes de abrir nova

### SQLite: LEAD não tem REGRESSÃO se UPDATE não mudou nada
- **Problema:** `atualizar_estagio()` retorna `False` se estágio já é o mesmo — bom, mas significa que o Kanban client-side não deve mostrar "moveu" se não mudou
- **Importante:** No frontend, re-renderizar o board após todo PATCH, mesmo se `mudou: false`

### Lead migration: WhatsApp clicks existentes
- Quando adicionar Kanban a DB já populado, migrar leads manualmente:
```sql
UPDATE leads SET estagio='whatsapp' WHERE whatsapp_clicks > 0;
UPDATE leads SET estagio='conversa' WHERE conversa_count > 0 AND whatsapp_clicks = 0;
```

---

## Padrão de Feature Completa

### DB (sac_db.py)
```python
# 1. Função de stats
def get_feature_stats() -> dict:
    conn = get_conn()
    try:
        rows = conn.execute("SELECT campo, COUNT(*) FROM leads GROUP BY campo").fetchall()
        return {r["campo"]: r[1] for r in rows}
    finally:
        conn.close()

# 2. Função de update (se needed)
def atualizar_feature(lead_id: int, valor: str) -> bool:
    ...
```

### Rotas (sac_agent.py)
```python
@app.route("/admin/stats/feature", methods=["GET"])
def admin_stats_feature():
    ok, _ = verify_admin_token()
    if not ok: return jsonify({"erro": "Não autenticado"}), 401
    stats = sac_db.get_feature_stats()
    return jsonify(stats)
```

### Template (admin.html)
```html
<!-- Card UI -->
<div class="card">
    <h2>📌 Feature</h2>
    <canvas id="chart-feature"></canvas>
</div>

<!-- JS -->
async function loadFeatureChart() {
    var r = await fetch('/admin/stats/feature', {credentials:'include'});
    var data = await r.json();
    // render Chart.js
}
window.addEventListener('DOMContentLoaded', loadFeatureChart);
```

### Padrão: Admin Approval Queue (pending_qa pattern)

Quando precisas de um sistema onde o bot gera conteúdo dinamicamente mas Álvaro quer aprovar antes de ficar oficial:

### 1. Schema SQL — tabela `pending_qa`
```sql
CREATE TABLE IF NOT EXISTS pending_qa (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    pergunta        TEXT NOT NULL,
    resposta        TEXT NOT NULL DEFAULT '',
    tema            TEXT NOT NULL DEFAULT '',
    contexto_lead   TEXT NOT NULL DEFAULT '',
    lead_id         INTEGER,
    lead_nome       TEXT DEFAULT '',
    status          TEXT NOT NULL DEFAULT 'pending',  -- 'pending'|'approved'|'rejected'
    admin_nota      TEXT DEFAULT '',
    criado_em       TEXT NOT NULL,
    aprovado_rejeitado_em TEXT
);
CREATE INDEX IF NOT EXISTS idx_pending_status ON pending_qa(status);
```

### 2. Funções DB (sac_db.py)
```python
def salvar_pending(item: dict) -> int:
    """Guarda item pendente. Retorna ID."""
    conn = get_conn()
    cur = conn.execute("""INSERT INTO pending_qa (pergunta, resposta, tema,
                       contexto_lead, lead_id, lead_nome, status, criado_em)
                       VALUES (?,?,?,?,?,?,'pending',?)""",
        (item['pergunta'], item.get('resposta',''), item.get('tema',''),
         item['contexto'], item.get('lead_id'), item.get('lead_nome',''),
         datetime.now().isoformat()))
    pend_id = cur.lastrowid
    conn.commit(); conn.close()
    return pend_id

def aprobar_pending(pend_id: int) -> int | None:
    """Approva — cria em approved_qa, marca pending. Retorna novo ID."""
    ...

def rejeitar_pending(pend_id: int) -> bool:
    """Marca como rejeitado."""
    ...
```

### 3. Rotas Flask (sac_agent.py)
```python
@app.route("/admin/pending-qa", methods=["GET"])
def admin_pending_qa_page():
    ok, username = verify_admin_token()
    if not ok: return redirect("/admin/login")
    pendentes = sac_db.listar_pending_qa("pending")
    ...
    return render_template_string(tmpl, username=username, pendentes=pendentes, ...)

@app.route("/admin/pending-qa/<int:pend_id>/aprovar", methods=["POST"])
def admin_pending_qa_aprovar(pend_id):
    ...
    sac_db.aprobar_pending_qa(pend_id, admin_nota)
    return redirect("/admin/pending-qa")

@app.route("/admin/pending-qa/<int:pend_id>/rejeitar", methods=["POST"])
def admin_pending_qa_rejeitar(pend_id):
    ...
```

### 4. Template admin-pending-qa.html
- Ver `templates/admin-pending-qa.html` como referência
- Incluir: badge status (pending=amarelo, approved=verde, rejected=vermelho)
- Contexto da conversa que gerou o item
- Botões Aprovar / Rejeitar via POST forms

---

## Padrão: Dynamic Generation + Static Fallback

Quando queres gerar conteúdo dinâmico via MiniMax mas manter fallback se a API falhar:

```python
def gerar_conteudo_dinamico(api_key: str, contexto: dict) -> list:
    # 1. Tentar MiniMax
    candidatas = minimax_gerar(api_key=api_key, ...)
    if not candidatas:
        return STATIC_FALLBACK  # retorna pool estático

    # 2. Verificar se já existe (Jaccard > 0.5)
    resultado = []
    for item in candidatas:
        if jaccard_score(item, approved_db) >= 0.5:
            resultado.append({"item": item, "status": "approved", "qa_id": match_id})
        else:
            resultado.append({"item": item, "status": "pending", "qa_id": None})
    return resultado

# No caller (sac_agent.py):
if dinamicas and lead_id:
    salvar_pendentes(dinamicas, ...)  # só as pending

# Preencher com estáticas se < 4:
if len(dinamicas) < 4:
    estaticas = get_estaticas_fallback(fase, limite=4 - len(dinamicas))
    for ep in estaticas:
        dinamicas.append({"pergunta": ep, "status": "static", "qa_id": None})
```

---

## Gotcha: separadores `---` no prompt LLM

**Problema:** Quando juntas itens de contexto com `\n---\n`, o LLM por vezes replica o padrão na resposta, causando `---` na resposta final.

**Fix:** Usar separador que o LLM não reproduza naturalmente — `◆` ou `\n---\n` → `◆`.

```python
# ERRADO: LLM vê "---" e reproduz
qa_block = "\n---\n".join([...])

# CERTO: separador não-replicável
qa_block = "\n◆\n".join([...])
```

---

## Commit
```bash
git add -A && git commit -m "SAC Bot: feature name implementada (data)"
git push
```

---

## Padrão de Cron Job para SAC Bot

### Script wrapper em `~/.hermes/scripts/`
```python
#!/usr/bin/env python3
"""SAC Abandono Cron — detecta leads que abandonaram após resposta."""
import sys
sys.path.insert(0, "/home/alvarobiano/.hermes/sac_agent")
from sac_db import get_conn, marcar_abandono_apos_resposta

# Itera sobre todas as qa_performance com abandono_marcado=0
# e chama marcar_abandono_apos_resposta(conversa_id, janela_minutos=30)
```

### Cron job (via `cronjob create`)
```
schedule: "*/30 * * * *"
prompt: "python3 ~/.hermes/scripts/sac_abandono_cron.py"
```

### Verificação
```bash
python3 ~/.hermes/scripts/sac_abandono_cron.py
# Output esperado: {"total_checados": N, "marcados": M, "erros": 0}
```

---

## Verificação
1. `systemctl --user restart sac-agent`
2. Login em `/admin/login`
3. Verificar que não há erros no console do browser
4. Testar fluxo completo (criar lead → verificar no DB → ver no dashboard)
5. Atualizar roadmap: `[ ]` → `~~P1~~ ✅ IMPLEMENTADO`
