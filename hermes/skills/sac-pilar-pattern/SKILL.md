---
name: sac-pilar-pattern
description: >
  Padrão de implementação de um novo Pilar de conversão no SAC Bot.
  Aplica-se sempre que se implementa um novo pilar (Pilar 3, 4, 5...).
triggers:
  - implementar Pilar no SAC Bot
  - adicionar pilar de conversão
  - novo pilar SAC Bot
  - PILAR 3
  - PILAR 4
  - PILAR 5
---

# SAC Bot — Padrão de Implementação de Novo Pilar

## Arquitectura Existente

O SAC Bot tem 5 pilares de conversão construídos sobre:
- **Schema**: `sac_schema.sql`
- **DB Module**: `sac_db.py`, `sac_db_diagnostico.py`, `sac_db_transformacao.py`
- **Motor**: `sac_persuasao.py` — `get_proximo_passo_pos_diagnostico()` faz o **routing**
- **API**: `sac_agent.py` — rotas Flask, integrado com o webhook `/webhook/sac`
- **Admin UI**: `templates/admin-pilar.html` — tabs para cada pilar

## O Padrão: 7 Passos para Cada Novo Pilar

### Passo 1 — Schema

Adicionar tabela(s) ao `sac_schema.sql` com `CREATE TABLE IF NOT EXISTS` + índices + timestamps `created_at`/`updated_at`.

### Passo 2 — Módulo DB

Criar `sac_db_pilarN.py` com funções: `criar_()`, `get_por_id()`, `listar_todos()`, `actualizar()`, `eliminar()` (soft-delete), `get_estatisticas()`. Usar `get_conn()` do `sac_db.py`.

### Passo 3 — Função Geradora no Motor

Adicionar `gerar_resposta_pilarN()` no final de `sac_persuasao.py`. Estrutura:
1. Buscar dados do pilar
2. Construir resposta com copy framework
3. Fechar com pergunta reflexiva que antecipa o próximo pilar

Fallback obrigatório: se não houver dados, usar os campos do diagnóstico para gerar resposta baseada em templates.

### Passo 4 — Routing

Em `get_proximo_passo_pos_diagnostico()`: adicionar condição **antes** de `return "rag_normal"`.

Ordem: Pilar 2 (transformação, default positivo) → específicos P3/P4/P5 → `rag_normal`.

### Passo 5 — Integração Webhook

Em `sac_agent.py`, após o bloco do Pilar 2:
- Adicionar `import sac_db_pilarN` no topo
- Adicionar bloco `if proximo == "pilarN":` com resposta e `registar_interacao`
- Adicionar rotas CRUD `/admin/api/pilarN` e `/admin/stats/pilarN`

### Passo 6 — Admin UI

Em `templates/admin-pilar.html`:
1. Adicionar botão na navegação dos pilares
2. Adicionar secção `id="pilar-N"` com estatísticas e gestão
3. Adicionar `loadPilarN()` e interceptar `showPilar()`
4. Adicionar modal de criar/editar antes de `</body>`

**Padrão MODAL com cache cliente (OBRIGATÓRIO):**

O modal de edição **nunca** deve fazer `fetch('/api/resource/<id>')` para popular campos —
esse pedido pode falhar com 401 silencioso mesmo com `credentials: 'include'` (o browser
 Cloudflare/browser-session pode não enviar o cookie). Em vez disso:

```
// Variável global para cache (topo do <script>)
window._pilarNCache = {}; // id -> objecto

// Em loadPilarN(), guardar TODOS os items no cache:
window._pilarNCache = {};
items.forEach(function(item) { window._pilarNCache[item.id] = item; });

// Em abrirModal(id), popular instantaneamente a partir do cache:
var item = id ? window._pilarNCache[id] : null;
document.getElementById('campo').value = item ? (item.campo || '') : '';
```

Este padrão foi descoberto a 28/04/2026 quando o modal do Pilar 2 abria mas os campos
ficavam vazios — o fetch devolvia 401 sem erro visível no UI.

### Passo 7 — Seed Data

Criar 3-6 registos iniciais (um por tipo de abolição) para o bot ter conteúdo desde o primeiro dia.

## Ficheiros

| Ficheiro | Acção |
|---|---|
| `sac_schema.sql` | Modified — tabelas novas |
| `sac_db_pilarN.py` | **NOVO** — módulo DB |
| `sac_persuasao.py` | Modified — função + routing |
| `sac_agent.py` | Modified — import + webhook + rotas API |
| `templates/admin-pilar.html` | Modified — tab + JS + modal |
| `sac_leads.db` | **NÃO** commitear — local apenas |

## Armadilhas

1. Routing order: específicos (P3/P4/P5) **depois** de Pilar 2, **antes** de `rag_normal`
2. Soft-delete: usar `ativa = 0`, nunca `DELETE` directo
3. Fallback obrigatório: resposta dinâmica se não houver dados
4. Sem import circular: só `sac_persuasao` → `sac_db_pilarN`, nunca o contrário
5. Usar `get_conn()` do `sac_db.py` para connections
6. **Modal fetch 401**: nunca fazer `fetch('/api/resource/<id>')` dentro de `abrirModal()` — usar cache global (`window._pilarNCache`) populated por `loadPilarN()` na abertura da página. Fetch dentro de modal falha silenciosamente com 401 em produção (Cloudflare/sessão browser).
7. **Botões sempre com estilo inline**: usar `style="background:#0f3460;color:#00d4ff;border:1px solid #00d4ff;padding:8px 18px;border-radius:6px;..."` — nunca `class="btn-primary"` ou outras classes CSS sem definição no template. O admin-pilar.html não tem CSS externo; todos os estilos devem ser inline.
8. **Tags de breakdown com flex-wrap**: o container de tags (ex: "Stories por tipo") precisa de `style="display:flex;flex-wrap:wrap;gap:6px;"` senão as tags ficam encavaladas em ecrãs pequenos.
9. **Encoding de caracteres não-latinos**: o LLM por vezes insere caracteres chineses/japoneses (ex: "聊聊") em texto português. O pipeline MiniMax → Python → SQLite pode não detectar isto se o charset estiver mal configurado. Corrigir manualmente no conteúdo das stories antes de inserir na DB — verificar visualmente com `SELECT titulo FROM ancoragem_stories` após seed.

## ⚠️ Armadilha DB PATH — CRÍTICO (descoberto em 28/04/2026 Pilar 4)

**O erro mais grave ao criar um novo módulo DB:**

O `sac_db.py` usa `sac_leads.db` como DB_PATH. Se o novo módulo DB definir o seu próprio `DB_PATH = "sac_bot.db"` (ou qualquer string hardcoded), as tabelas serão criadas num ficheiro SQLite SEPARADO que o Flask em produção não vê — resultando em 500 Internal Server Error sem traceback visível.

**Sintomas:**
- API funciona via `python3` directo mas falha com 500 via Flask (serviço em produção)
- `SELECT COUNT(*)` no DB directo devolve dados mas a API devolve 500
- O serviço Flask está a usar um DB diferente do script de seed

**Solução OBRIGATÓRIA:**
```python
# NOVO sac_db_pilarN.py — FAZER ASSIM:
from sac_db import get_conn   # ✅ Usa sac_leads.db

# NAO FAZER ISTO:
# DB_PATH = "sac_bot.db"       ❌ Ficheiro errado
# DB_PATH = "minha_tabela.db"  ❌ Outro ficheiro
```

**Verificação depois de criar tabelas e fazer seed:**
```bash
# Confirmar que estão no DB certo
sqlite3 sac_leads.db ".tables" | grep pilarN
# NAO usar sac_bot.db
```

## Routing por Tipo de Abolição (Pilar 3+)

O `get_proximo_passo_pos_diagnostico()` em `sac_persuasao.py` usa `abolicao_tipo` para seleccionar o pilar:

```
dinheiro         → pilar3_ancoragem
medo             → pilar5_risco
inercia          → pilar4_urgencia
tempo            → pilar3_ancoragem  (ou pilar4_urgencia conforme implementação)
falta_clareza    → pilar2_transformacao
desconhece       → pilar2_transformacao ou rag_normal
```

**Routing real (28/04/2026):**
```
nivel_clareza >= 7 AND nivel_impacto >= 7  →  pilar2_transformacao
abolicao_tipo == 'dinheiro'                →  pilar3_ancoragem
abolicao_tipo == 'inercia'                  →  pilar4_urgencia
abolicao_tipo == 'medo'                    →  pilar5_risco
default                                   →  rag_normal
```

Para Pilar 4 (urgência), a condição de trigger é `abolicao_tipo == 'inercia'`. Para Pilar 5 (risco), `abolicao_tipo == 'medo'`.

## Padrão de Resposta do Pilar 3 (Ancoragem de Valor)

O `gerar_resposta_pilar3()` usa 5 blocos randomizados:
- **Bloco A — Frase âncora**: contextualiza o valor antes do preço ("Este programa já ajudou centenas...")
- **Bloco B — Pergunta de valor**: muda referencial de "preço" para "valor/transformação"
- **Bloco C — Custo da inacção**: âncora de custo real (dinheiro + tempo + oportunidades perdidas)
- **Bloco D — Prova social**: reduz percepção de risco ("arrependimento mais comum é não ter começado antes")
- **Bloco E — Ancoragem de preço**: preço como custo da transformação vs. custo da inacção
- **Bloco F — Pergunta reflexiva**: move o lead para a decisão

4 fases internas: `valor → custo → decisao → conversao`

Routing pós-Pilar 3:
- `custo_estimado >= 7` → Pilar 4
- `decisao_confirmada` → Pilar 5
- default → RAG normal
