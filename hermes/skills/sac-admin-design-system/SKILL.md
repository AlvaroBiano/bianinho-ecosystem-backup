---
name: sac-admin-design-system
description: CSS Design System para SAC Admin — valores de referência, checklist de consistência e procedimento padrão para nunca mais quebrar o header entre templates.
triggers:
  - SAC admin CSS
  - admin template consistency
  - nav-link styling
  - header design
  - sac-agent templates
---

# SAC Admin — Design System

## ⚠️ ARQUITETURA — DOIS ADMINISTRADORES DISTINTOS

### Porto 5123 — SAC Agent (Flask + sac_agent.py)
Tudo neste skill pertence a este servidor.
**Endpoint**: `http://localhost:5123`
**Rotas admin**: `/admin`, `/kanban`, `/utm-builder`, `/admin/qa`, `/admin/gaps`, `/admin/perfil`
**Templates**: `~/.hermes/sac_agent/templates/` (admin.html, kanban.html, utm-builder.html, admin-qa.html, admin-gaps.html)
**Auth**: mesmo cookie `admin_token` do SAC Bot
**Variáveis de ambiente**: via systemd `Environment=`, NÃO usa .env (sac_agent.py não chama load_dotenv)

### Porto 5124 — Admin Dashboard SEPARADO (Flask + app.py)
**ATENÇÃO**: Este é um Flask app SEPARADO em `~/sac-admin-dashboard-BACKUP/`.
 NÃO é o mesmo servidor do SAC Agent. Apenas gestão de perfil e convites — SEM kanban, SEM UTM, SEM Q&A.
**Se quiseres kanban/UTM/Q&A, acede ao porto 5123 (SAC Agent).**
**Templates**: `~/sac-admin-dashboard-BACKUP/templates/` (admin.html, login.html, perfil.html, convite.html)
**BUG CONHECIDO**: Se .env existe mas `load_dotenv()` não é chamado no início de app.py, `SAC_DB_PATH` fica `None` → `/admin/api/stats` dá 500.
**CORREÇÃO**: garantir `from dotenv import load_dotenv` + `load_dotenv()` no topo de app.py.

## Templates (porto 5123 — SAC Agent)

## REGRAS DE OURO

### Regra 1: CSS compartilhado deve ser IDÊNTICO em todos os templates

Antes de mexer em qualquer CSS, comparar TODOS os templates:
```python
import re

def get_css(selector, path):
    with open(path) as f:
        content = f.read()
    m = re.search(re.escape(selector) + r'\s*\{([^}]+)\}', content)
    return m.group(1).strip() if m else '❌ MISSING'

templates = {
    "admin.html": "/home/alvarobiano/.hermes/sac_agent/templates/admin.html",
    "kanban.html": "/home/alvarobiano/.hermes/sac_agent/templates/kanban.html",
    "utm-builder.html": "/home/alvarobiano/.hermes/sac_agent/templates/utm-builder.html",
    "admin-qa.html": "/home/alvarobiano/.hermes/sac_agent/templates/admin-qa.html",
    "admin-gaps.html": "/home/alvarobiano/.hermes/sac_agent/templates/admin-gaps.html",
}
```

### Regra 2: Checklist de consistência do header

**SEMPRE** verificar estes seletores em **TODOS** os templates antes de qualquer mudança:

```
.site-header   — container do header
.nav-bar       — wrapper dos links de navegação
.nav-link      — cada botão de navegação (inclusive INACTIVE)
.nav-link:hover
.nav-link.active
.site-title    — texto principal do header
.site-subtitle — texto secundário
.btn-sair      — botão de logout
.btn-sair:hover
```

**Nav-links esperados (28/04/2026):** Dashboard · Kanban · UTM Builder · Q&A · Gaps · Sinaergia · Pilares · Perfil (8 links antes do logout)

⚠️ **admin.html é o mais propenso a estar desatualizado** — verificar sempre nele primeiro.

### Regra 3: Valores de referência — ATUALIZADOS 27/04/2026 (single source of truth)

```css
/* .site-header — container */
.site-header {
    background: #1e293b;
    padding: 14px 24px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    flex-wrap: wrap;
    gap: 12px;
    border-bottom: 1px solid #334155;
}

/* .site-title e .site-subtitle */
.site-header .site-title { font-size: 15px; color: #00d4ff; font-weight: 700; }
.site-header .site-subtitle { font-size: 12px; color: #94a3b8; }

/* .nav-bar — wrapper dos links */
.nav-bar {
    display: flex;
    align-items: center;
    gap: 6px;
    flex-wrap: wrap;
}

/* .nav-link — botão de navegação (fundo transparente, hover sutil) */
.nav-link {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    height: 32px;
    padding: 0 14px;
    background: transparent;
    color: #94a3b8;
    border: 1px solid transparent;
    border-radius: 6px;
    font-size: 12px;
    font-weight: 600;
    text-decoration: none;
    cursor: pointer;
    transition: all 0.15s;
    white-space: nowrap;
}
.nav-link:hover {
    color: #e2e8f0;
    background: rgba(255,255,255,0.05);
    border-color: #334155;
}
.nav-link.active {
    color: #00d4ff;
    border-color: rgba(0,212,255,0.4);
    background: rgba(0,212,255,0.08);
}

/* .btn-sair — logout (borda vermelha, fundo transparente) */
.btn-sair {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    height: 32px;
    padding: 0 14px;
    background: transparent;
    color: #e74c3c;
    border: 1px solid #e74c3c;
    border-radius: 6px;
    font-size: 12px;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.15s;
}
.btn-sair:hover { background: rgba(231,76,60,0.1); }
```

### Regra 4: Procedimento padrão para mudanças

1. **ANTES**: comparar CSS em todos os 7 templates usando script Node.js (ver abaixo)
2. Identificar qual(is) template(s) estão diferentes
3. Aplicar correção usando os valores de referência acima
4. Aplicar a TODOS os 7 templates de uma vez — nunca apenas a um
5. **NUNCA** fazer `systemctl restart` após cada correção — agrupar todas e reiniciar uma vez só no fim
6. Após reiniciar: navegar em todas as páginas e verificar com `getComputedStyle()` que os valores batem

**Script de aplicação em massa (Node.js):**
```javascript
const fs = require('fs');
const path = '/home/alvarobiano/.hermes/sac_agent/templates';

const NAV_HTML = `    <nav class="nav-bar">
        <a href="/admin"         class="nav-link">Dashboard</a>
        <a href="/kanban"        class="nav-link">Kanban</a>
        <a href="/utm-builder"   class="nav-link">UTM Builder</a>
        <a href="/admin/qa"      class="nav-link">Q&A</a>
        <a href="/admin/gaps"    class="nav-link">Gaps</a>
        <a href="/admin/sinergia" class="nav-link">Sinaergia</a>
        <a href="/pilar" class="nav-link" style="color:#e74c3c;font-weight:700;">Pilares</a>
        <a href="/admin/perfil"  class="nav-link">Perfil</a>
        <form action="/admin/logout" method="POST" style="display:inline;">
            <button type="submit" class="btn-sair">Sair</button>
        </form>
    </nav>`;

const NAV_CSS = `/* ── Site Header ── */
.site-header { ... }
.nav-bar { ... }
.nav-link { ... }
.nav-link.active { ... }
.btn-sair { ... }`;
// (usar valores de referência da Regra 3)

function setActiveLink(html, page) {
    const map = { '/admin':'Dashboard','/kanban':'Kanban',
        '/utm-builder':'UTM Builder','/admin/qa':'Q&A',
        '/admin/gaps':'Gaps','/admin/sinergia':'Sinaergia',
        '/pilar':'Pilares','/admin/perfil':'Perfil' };
    return html.replace(/<nav class="nav-bar">[\s\S]*?<\/nav>/,
        NAV_HTML.replace(`>"${map[page]}"`, `class="nav-link active">${map[page]}"`).replace(`style="color:#e74c3c;font-weight:700;">Pilares`, `class="nav-link active" style="color:#e74c3c;font-weight:700;">Pilares`);
}
// Aplicar a todos os 8 templates
['admin.html','kanban.html','utm-builder.html','perfil.html',
 'admin-gaps.html','admin-qa.html','admin-sinergia.html','admin-pilar.html'].forEach(...);
```

### Regra 5: HTML do header ATUALIZADO — 8 links, Pilares a vermelho, SEM EXCEPCÃO

**ORDEM FIXA**: Dashboard | Kanban | UTM Builder | Q&A | Gaps | Sinaergia | Pilares (vermelho) | Perfil | Sair

```html
<header class="site-header">
    <div>
        <span class="site-title">SAC Método TEN</span>
        <span class="site-subtitle"> · Admin</span>
    </div>
    <nav class="nav-bar">
        <a href="/admin"         class="nav-link">Dashboard</a>
        <a href="/kanban"        class="nav-link">Kanban</a>
        <a href="/utm-builder"   class="nav-link">UTM Builder</a>
        <a href="/admin/qa"      class="nav-link">Q&A</a>
        <a href="/admin/gaps"    class="nav-link">Gaps</a>
        <a href="/admin/sinergia" class="nav-link">Sinaergia</a>
        <a href="/pilar" class="nav-link" style="color:#e74c3c;font-weight:700;">Pilares</a>
        <a href="/admin/perfil"  class="nav-link">Perfil</a>
        <form action="/admin/logout" method="POST" style="display:inline;">
            <button type="submit" class="btn-sair">Sair</button>
        </form>
    </nav>
</header>
```

**REGRA CRÍTICA — Nav bar idêntica em TODOS os templates SEM EXCEPCÃO**:
- Ao criar UM novo template, a nav bar DEVE ser copiada exactamente deste template e aplicada a TODOS os outros
- NUNCA criar template com nav bar incompleta (ex: sem Pilares, sem Perfil, sem UTM Builder)
- Esta é a primeira coisa a verificar quando se abre qualquer template admin para edição
- Se um template não tem esta nav bar exacta, está BUGADO — corrigir imediatamente

**Templates que precisam deste header (8 páginas — TODOS com nav idêntica):**
- `admin.html` — Dashboard
- `kanban.html` — Kanban
- `utm-builder.html` — UTM Builder
- `admin-qa.html` — Q&A
- `admin-gaps.html` — Gaps
- `admin-sinergia.html` — Sinaergia
- `admin-pilar.html` — Pilares
- `perfil.html` — Perfil

**Kanban — valores de referência (larguras fixas):**
- 6 colunas × 215px + 5 gaps × 10px = 1340px (largura total do board)
- `#board` e `#funil-bar`: `width: 1340px` (centrados pelo `.board-wrapper`)

## Armadilhas conhecidas

- **admin.html** é o arquivo mais propenso a estar incompleto — verificar **SEMPRE** nele primeiro
- **perfil.html** é o mais propenso a divergir do design system — verificar SEMPRE nele. Sintoma: nav-links com `background: transparent` e `color: #94a3b8` (cinza) em vez de `background: #0f3460` e `border: 1px solid #00d4ff`. Verificar também que o botão Sair tem `class="btn-sair"` (vermelho) e está DENTRO de `<nav class="nav-bar">`, não num div separado `user-info`.
- CSS inline em HTML (`style="..."`) deve ser evitado — usar classes
- Se um template não tem `<style>` mas tem CSS inline, migrar para classes
- **BUG .env em Flask separado**: Se app.py usa `os.environ.get("VAR")` mas não chama `load_dotenv()` no início, todas as vars do .env ficam como `None`. Sintomas: 500 em rotas de API, vars indefinidas. Correcção: `from dotenv import load_dotenv` + `load_dotenv()` como primeiras linhas do app.py.
- **JS com referências stale ao DOM após refatoração de header**: Quando se refactora o HTML do header (mudar estrutura, remover divs/spans), TODAS as funções JavaScript que referenciam elementos DOM desse header devem ser auditadas ANTES de fazer deploy. Exemplo real: o header do `perfil.html` tinha `user-nome` e `user-role` spans no `.user-info` div; `carregarPerfil()` actualizava esses spans; ao modernizar o header, esses spans foram removidos; a linha `document.getElementById('user-nome')` passou a retornar `null` → TypeError → todo o `try/catch` falha silenciosamente e a página fica sem dados. **Regra**: antes de qualquer refatoração de header, grep todos os `.html` por `getElementById` e `querySelector` com IDs do header para garantir que todos ainda existem na nova estrutura.
- **JS typos que causam falha silenciosa de página inteira**: Erros de sintaxe em scripts inline (ex: `renderQA KPIs` em vez de `renderQAKPIs`) fazem o browser lançar `SyntaxError: Unexpected identifier` → TODAS as funções desse script ficam indefinidas (`typeof renderQAKPIs === 'undefined'`) → tabela vazia, KPIs em `—`, 0 erros visíveis exceto o syntax error no console. **Diagnóstico**: abrir DevTools → Console → procurar `"Unexpected identifier"` ou `"Unexpected token"` E verificar `typeof funcName` para funções que deviam existir. **Regra**: ao adicionar funções JS em templates Flask inline, verificar camelCase e ausência de espaços em nomes de funções.
- **Confusão de portos**: Não confundir o admin do SAC Agent (5123, completo) com o admin-dashboard-BACKUP (5124, incompleto)

### Armadilha: Botões com classes CSS sem definição (fundo branco)

Botões em templates Flask que usam `class="btn-primary"` ou outra classe sem existir CSS para ela no `<style>` do template — o browser usa o estilo default (fundo branco, texto preto), destruindo o design system. **Sintoma**: botão com aspecto "ridiculamente branco" num admin dark-themed.

**Regra**: todos os botões de acção em templates admin devem ter estilo inline explícito. NUNCA usar classes que não estão definidas no `<style>` do template. Ao adicionar um botão, verificar que existe `style="..."` ou que a classe está no `<style>`.

**Padrão aceite** para botões de acção (baseado no admin-pilar.html):
```html
<!-- Botão primario (outline cyan) -->
<button onclick="..." style="background:#0f3460;color:#00d4ff;border:1px solid #00d4ff;padding:8px 18px;border-radius:6px;cursor:pointer;font-size:13px;font-weight:600;white-space:nowrap;">+ Nova Story</button>

<!-- Botão perigo (outline vermelho) -->
<button onclick="eliminarStory(1)" style="background:rgba(231,76,60,0.1);color:#e74c3c;border:1px solid #e74c3c;padding:3px 10px;border-radius:5px;cursor:pointer;font-size:11px;font-weight:600;">Eliminar</button>

<!-- Botão secundario (fundo transparente, border cinza) -->
<button onclick="fecharModal()" style="padding:10px 20px;border-radius:6px;border:1px solid #334155;background:transparent;color:#94a3b8;cursor:pointer;font-weight:600;">Cancelar</button>
```

### Armadilha: Flex containers sem `flex-wrap` causam overflow horizontal

Quando um container flex tem `display:flex` sem `flex-wrap:wrap`, todos os children ficam numa única linha e ultrapassam o limite do container. **Sintoma**: tags/badges de breakdown "Stories por tipo" ficam encavalados uns nos outros, fora da área visível.

**Regra**: todos os containers que mostram tags dinâmicas ou spans gerados por JavaScript devem ter:
```html
<div style="display:flex; flex-wrap:wrap; gap:6px; align-items:center;">
```

**Verificação no browser console**:
```javascript
var el = document.getElementById('p2-por-tipo');
var r = el.getBoundingClientRect();
var pr = el.parentElement.getBoundingClientRect();
JSON.stringify({ elRight: r.right, parentRight: pr.right, overflow: r.right > pr.right })
// overflow=true significa que o conteúdo está a escapar do container
```

### Armadilha: Célula de acções em tabelas — botões/badge quebram linha

Quando uma célula `<td>` de uma tabela admin contém um badge + botões (ex: "Activa | Editar | Eliminar") e não tem `white-space:nowrap`, o browser quebra os elementos para a linha seguinte se a célula vizinha for estreita ou se o viewport for reduzido.

**Sintoma**: os botões aparecem em 2-3 linhas dentro da mesma célula, destruindo o alinhamento.

**Padrão correcto** — usar `inline-flex gap` dentro de `white-space:nowrap` na célula:
```html
<td style="padding:8px 10px;text-align:center;white-space:nowrap;">
  <div style="display:inline-flex;align-items:center;gap:4px;">
    <span class="badge verde">Activa</span>
    <button onclick="abrirModalStory(1)" style="background:#0f3460;color:#00d4ff;border:1px solid #00d4ff;padding:3px 10px;border-radius:5px;cursor:pointer;font-size:11px;font-weight:600;">Editar</button>
    <button onclick="eliminarStory(1)" style="background:rgba(231,76,60,0.1);color:#e74c3c;border:1px solid #e74c3c;padding:3px 10px;border-radius:5px;cursor:pointer;font-size:11px;font-weight:600;">Eliminar</button>
  </div>
</td>
```

**Regra**: toda a célula de acções de tabela (badge + botões) deve ter `white-space:nowrap` na `<td>` E os elementos dentro de um `<div inline-flex gap:4px>`. NÃO usar `margin-left` entre botões — usar `gap` no flex container.

**Verificação no browser console:**
```javascript
var cell = document.querySelector('#p3-stories-body tr:first-child td:last-child');
var r = cell.getBoundingClientRect();
var row = cell.closest('tr');
JSON.stringify({ cellW: r.width, buttonsInLine: cell.querySelectorAll('button').length, wrapping: r.height > 40 })
// wrapping=true = altura >40px significa que os botões estão em mais de uma linha
```

### Armadilha: Encoding UTF-8 partido em placeholders (caracteres chineses no texto português)

Quando placeholders são definidos em strings Python (ex: no código Flask que gera HTML), caracteres não-ASCII podem ser serializados incorrectamente e aparecer como caracteres chineses/japoneses no browser. **Sintoma**: placeholder mostra `"sentindo-se绝望ado"` em vez de `"sentindo-se desesperado"`.

**Regra**: ao definir placeholders em strings Python que geram HTML inline, usar apenas ASCII ou garantir que o ficheiro Python está guardado como UTF-8 e a string é uma literal Unicode (`u"..."` ou `"""..."""` com coding declaration).

**Verificação**: verificar o ficheiro com `grep -n "绝望\| рус\| 简体" templates/admin-pilar.html` após criar placeholders com texto não-ASCII.

## Kanban — Layout (full-width + scroll interno)

O Kanban tem 6 colunas de 215px + gap de 10px = 1340px de largura total. A barra de background (funil-bar) vai de ponta a ponta; os cards têm scroll interno.

**Estrutura:**
```html
<!-- No body -->
<div class="board-wrapper">
    <div id="funil-bar"></div>
    <div id="board"></div>
</div>
```

**CSS:**
```css
body { overflow-x: hidden; }

/* Wrapper full-width, flex column */
.board-wrapper {
    display: flex;
    flex-direction: column;
    width: 100%;
}

/* Funil-bar: FULL WIDTH da página */
#funil-bar {
    width: 100%;
    padding: 12px 0;
}

/* Board: scroll horizontal INTERNO, colunas left-aligned */
#board {
    display: flex;
    gap: 10px;
    padding: 12px 0;
    min-height: calc(100vh - 110px);
    align-items: flex-start;
    justify-content: flex-start;
    min-width: 0;          /* CRÍTICO: permite overflow em flex children */
    overflow-x: auto;      /* scroll interno no board */
}
```

**Resultado**: funil-bar 100% da página, board começa em x=0, scroll interno para ver colunas 4-5-6, sem scroll na página.

## Tabelas com Paginação + Overflow Scroll

Quando uma tabela admin tem mais de ~20 linhas, usar paginação client-side com overflow scroll no wrapper.

### Estrutura HTML
```html
<div class="qa-table-wrap">
    <table class="qa-table">
        <thead>...</thead>
        <tbody id="qa-tbody">...</tbody>
    </table>
    <div class="table-fade-right"></div>
</div>
<div class="qa-pagination" id="qa-pagination">
    <span class="qa-pagination-info" id="qa-pagination-info"></span>
    <div class="qa-pagination-controls" id="qa-pagination-controls"></div>
</div>
```

### CSS
```css
/* Wrapper: scroll horizontal interno, NÃO na página */
.qa-table-wrap {
    overflow-x: auto;
    position: relative;
    border-radius: 8px;
}

/* Tabela: min-width grande o suficiente para colunas */
.qa-table {
    min-width: 947px;
    width: 100%;
    border-collapse: collapse;
}

/* Fade à direita quando há overflow */
.table-fade-right::after {
    content: '';
    position: absolute;
    top: 0; right: 0; bottom: 0;
    width: 40px;
    background: linear-gradient(to right, transparent, #0f172a);
    pointer-events: none;
}

/* Paginação */
.qa-pagination {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 12px 4px;
    gap: 12px;
}
.qa-pagination-info { font-size: 12px; color: #94a3b8; }
.qa-pagination-controls { display: flex; gap: 4px; flex-wrap: wrap; }
.qa-page-btn {
    min-width: 34px; height: 34px;
    padding: 0 8px;
    background: #0f3460; color: #00d4ff;
    border: 1px solid #00d4ff; border-radius: 6px;
    font-size: 12px; font-weight: 600;
    cursor: pointer;
}
.qa-page-btn:hover { background: rgba(0,212,255,0.15); }
.qa-page-btn.active { background: #00d4ff; color: #0f172a; }
.qa-page-btn:disabled { opacity: 0.35; cursor: default; }
```

### JavaScript — Variáveis e Constantes
```javascript
var qaCurrentPage = 1;
const QARowsPerPage = 15;
var qaAllData = []; // dados completos carregados uma vez
```

### JavaScript — Render com Slice
```javascript
function renderQATable() {
    var filtered = qaAllData.filter(...);
    var start = (qaCurrentPage - 1) * QARowsPerPage;
    var pageData = filtered.slice(start, start + QARowsPerPage);
    // renderizar pageData em #qa-tbody
    renderQAPagination(filtered.length);
}

function renderQAPagination(total) {
    var totalPages = Math.ceil(total / QARowsPerPage);
    var start = (qaCurrentPage - 1) * QARowsPerPage + 1;
    var end = Math.min(qaCurrentPage * QARowsPerPage, total);
    document.getElementById('qa-pagination-info').textContent =
        'Mostrando ' + start + '-' + end + ' de ' + total + ' Q&As';

    var controls = document.getElementById('qa-pagination-controls');
    controls.innerHTML = '';
    // Botão «
    controls.innerHTML += '<button class="qa-page-btn" onclick="qaGoPage(0)" ' + (qaCurrentPage===1?'disabled':'') + '>«</button>';
    // Botões numéricos
    for (var p = 1; p <= totalPages; p++) {
        controls.innerHTML += '<button class="qa-page-btn ' + (p===qaCurrentPage?'active':'') + '" onclick="qaGoPage(' + p + ')">' + p + '</button>';
    }
    // Botão »
    controls.innerHTML += '<button class="qa-page-btn" onclick="qaGoPage(' + (totalPages+1) + ')" ' + (qaCurrentPage===totalPages?'disabled':'') + '>»</button>';
}

function qaGoPage(page) {
    if (page < 1 || page > Math.ceil(qaAllData.length / QARowsPerPage)) return;
    qaCurrentPage = page;
    renderQATable();
}
```

### CRÍTICO — Reset ao Filtrar/Pesquisar
Sempre que o utilizador digitar no search ou mudar filtro:
```javascript
// No oninput do search E no onchange do filtro
qaCurrentPage = 1;
renderQATable();
```

### Verificação
```javascript
var rows = document.querySelectorAll('#qa-tbody tr').length;
var info = document.getElementById('qa-pagination-info').textContent;
var wrap = document.querySelector('.qa-table-wrap');
JSON.stringify({ rows: rows, info: info, wrapScroll: wrap.scrollWidth, wrapClient: wrap.clientWidth })
// Esperado: rows=15, info="Mostrando 1-15 de 92 Q&As", wrapScroll > wrapClient
```

**Verificação (browser console):**
```javascript
var b = document.getElementById('board');
var f = document.getElementById('funil-bar');
var cols = document.querySelectorAll('.coluna');
JSON.stringify({
  windowW: window.innerWidth,
  funilLeft: Math.round(f.getBoundingClientRect().left),   // deve ser 0
  funilRight: Math.round(f.getBoundingClientRect().right), // deve ser ~780
  boardLeft: Math.round(b.getBoundingClientRect().left),    // deve ser 0
  firstColLeft: Math.round(cols[0].getBoundingClientRect().left), // deve ser 0
  lastColRight: Math.round(cols[cols.length-1].getBoundingClientRect().right), // > windowW
  canScroll: b.scrollWidth > b.clientWidth
})
```

**Armadilha CSS (não usar `align-items: center` no wrapper):**
`align-items: center` no wrapper força o flex child (board, 1340px) a centrar dentro do wrapper (780px) — isso cria overflow simétrico nos dois lados MAS o espaço à esquerda fica maior que à direita porque o browser arredonda pixels. Solução: não usar `align-items: center`, usar `justify-content: flex-start` no board e `overflow-x: auto` no board.

## Verificação pós-mudança

Após qualquer mudança de CSS:
```javascript
JSON.stringify({
  navLink: (() => {
    const n = document.querySelector('.nav-link');
    const s = getComputedStyle(n);
    return {minW: s.minWidth, h: s.height, pad: s.padding, bg: s.backgroundColor};
  })(),
  btnSair: (() => {
    const b = document.querySelector('.btn-sair');
    const s = getComputedStyle(b);
    return {bg: s.backgroundColor, h: s.height};
  })()
})
```
