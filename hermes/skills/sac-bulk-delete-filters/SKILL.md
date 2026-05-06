---
description: Debug findings from bulk-delete filters - flatpickr failed, native date inputs + JS event listeners fixed it
name: sac-bulk-delete-filters
---

# SAC Bulk Delete Filters - Gotchas e Correções

## Problema
Filtros de exclusão em massa no admin.html não funcionavam:
- Estágio não filtrava
- Data não filtrava

## Causa Raiz
1. **Event listeners**: inline `onchange="loadBulkPreview()"` não disparava (possível conflito com outros scripts)
2. **Flatpickr**: biblioteca não carregava corretamente via CDN, eventos não disparavam

## Solução
```javascript
// Em vez de onchange inline no HTML, usar event listeners no DOMContentLoaded:
window.addEventListener('DOMContentLoaded', function() {
    document.getElementById('bulk-data-inicio').addEventListener('change', loadBulkPreview);
    document.getElementById('bulk-data-fim').addEventListener('change', loadBulkPreview);
    document.getElementById('bulk-ddd').addEventListener('change', loadBulkPreview);
    document.getElementById('bulk-estagio').addEventListener('change', loadBulkPreview);
});
```

## Bug DDD Extraction
Telefones gravados como `(48) 92000-8284` - `substr(telefone,2,2)` retorna `48)` (com parêntese).

**Fix SQL:**
```python
"SELECT DISTINCT(substr(replace(replace(replace(telefone,'(',''),')',''),'-',''),1,2)) as ddd FROM leads"
```

## Conclusão
- Preferir `<input type="date">` nativo em vez de bibliotecas externas
- Adicionar event listeners via JavaScript, não atributos inline HTML
- Testar filtros com dados reais do banco antes de entregar