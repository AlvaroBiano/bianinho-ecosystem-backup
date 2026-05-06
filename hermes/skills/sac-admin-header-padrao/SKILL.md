---
name: sac-admin-header-padrao
description: Header/nav-bar padrão para todas as páginas do SAC Admin — aplicar em qualquer template novo ou modificado.
---

# SAC Admin — Header Padrão

## Quando usar

Sempre que criar ou modificar qualquer template HTML do SAC Admin (`templates/*.html`), o header deve seguir este padrão EXATAMENTE. Aplica-se a todas as 7 páginas: `admin.html`, `kanban.html`, `utm-builder.html`, `perfil.html`, `admin-gaps.html`, `admin-qa.html`, `admin-sinergia.html`.

## Estrutura Obrigatória

### 1. CSS — incluir logo após `body {}`

```css
/* ── Site Header ── */
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
.site-header .site-title {
    font-size: 15px;
    color: #00d4ff;
    font-weight: 700;
}
.site-header .site-subtitle {
    font-size: 12px;
    color: #94a3b8;
}

/* ── Nav Bar ── */
.nav-bar {
    display: flex;
    align-items: center;
    gap: 6px;
    flex-wrap: wrap;
}
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
.btn-sair:hover {
    background: rgba(231,76,60,0.1);
}
```

### 2. HTML do Header — incluir como primeiro elemento dentro de `<body>`

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

## Regras de Atribuição active

A página atual deve ter `class="nav-link active"` — todas as outras `class="nav-link"`.

Mapeamento de páginas:
| Página | Link ativo |
|--------|------------|
| `/admin` | Dashboard |
| `/kanban` | Kanban |
| `/utm-builder` | UTM Builder |
| `/admin/qa` | Q&A |
| `/admin/gaps` | Gaps |
| `/admin/sinergia` | Sinaergia |
| `/pilar` | Pilares |
| `/admin/perfil` | Perfil |

## Regras de Adição de Novos Links

Ao adicionar um novo link ao nav-bar:
1. Adicionar em TODAS as 8 páginas — nunca em apenas uma
2. Manter a ordem: Dashboard → Kanban → UTM Builder → Q&A → Gaps → Sinaergia → Pilares (vermelho) → Perfil → [novo]
3. **Link vermelho:** se o link for uma área especial (ex: Pilares), usar `style="color:#e74c3c;font-weight:700;"` além de `active`
4. Se o novo link for uma página do admin, adicionar o mapeamento active nesta skill
5. **Commit separado** com mensagem a indicar que o header foi atualizado em todas as páginas
6. **Verificação obrigatória** após modificar — confirmar com grep que todas as páginas têm o link:

```bash
for f in admin.html admin-qa.html admin-gaps.html admin-sinergia.html kanban.html perfil.html utm-builder.html admin-pilar.html; do
  echo -n "$f: "; grep -c "href=\"/pilar\"" ~/.hermes/sac_agent/templates/$f
done
# Resultado esperado: 1 em todas as 8 linhas
```

## Ficheiros (8 páginas)

- `/home/alvarobiano/.hermes/sac_agent/templates/admin.html`
- `/home/alvarobiano/.hermes/sac_agent/templates/admin-qa.html`
- `/home/alvarobiano/.hermes/sac_agent/templates/admin-gaps.html`
- `/home/alvarobiano/.hermes/sac_agent/templates/admin-sinergia.html`
- `/home/alvarobiano/.hermes/sac_agent/templates/kanban.html`
- `/home/alvarobiano/.hermes/sac_agent/templates/perfil.html`
- `/home/alvarobiano/.hermes/sac_agent/templates/utm-builder.html`
- `/home/alvarobiano/.hermes/sac_agent/templates/admin-pilar.html`
