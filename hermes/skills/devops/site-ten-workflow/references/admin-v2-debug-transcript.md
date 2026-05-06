# Admin V2 — Bug Debug Transcript (30/04/2026)

## O problema
Usuário reports: "Não está aparecendo bosta nenhuma. Nada ainda. Resolve isso de uma vez."

O sistema parecia funcionar mas a tabela não aparecia.

## Diagnóstico real (herança da sessão)

O browser MOSTRAVA o login, depois do login mostrava o dashboard com as tabs mas quando clicava em E-books não aparecia nada.

**O que NÃO era o problema:**
- Cache do browser (user tentou limpar, não resolveu)
- Incógnito
- Credenciais

**O que ERA o problema:**
`renderTable()` preenchia `dynamic-table-body` com dados mas `crud-main` tinha `class="hidden"` (Tailwind com `!important`).

Evidence do Playwright:
```
crud-main: display=none, hidden=true, width=0, height=0  ← INVISÍVEL
dynamic-table-body: display=table-row-group, hidden=false, width=1214, height=684  ← TEM DADOS
```

## O que foi corrigido

```javascript
// admin/js/admin.js — renderTable()
function renderTable() {
    // ESTA LINHA FALTAVA — REMOVIA O hidden DO crud-main
    document.getElementById('crud-main')?.classList.remove('hidden');

    if (currentEntityData.length === 0) {
        dynamicTableBody.innerHTML = '...';
        return;
    }
    // ... resto
}
```

## Lição

Se zero JS errors E innerHTML tem dados E tabela não aparece → é VISIBILITY bug. Verificar sempre:
1. `classList.contains('hidden')`
2. `getComputedStyle().display`

Nunca culpar cache quando o bug é real.
