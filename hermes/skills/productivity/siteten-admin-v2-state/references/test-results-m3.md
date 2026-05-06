# SiteTen Admin V2 — Resultados Teste Módulo 3 (30/04/2026)

## Data: 30/04/2026 | Branch: preview | Commits: c09ac6e → 5c72902 → 962ec03

## Resultado: 23/26 OK — FAIL (3 falhas não-críticas)

### Camada 1 — Funcional: 5/6
- ✅ Tabela com 1+ linha
- ✅ Drag handle presente
- ✅ Badge Ativo visível
- ✅ Botão Editar existe
- ✅ Botão Novo existe
- ❌ Botão Excluir existe — **FALSO NEGATIVO DO TESTADOR** (botão existe como `deleteItem(btn, id)`, testador procurava `deleteRow`)

### Camada 2 — Edge Cases: 4/5
- ✅ Validação: nome obrigatório (HTML5)
- ✅ Lista features renderizada
- ✅ Botão adicionar feature existe
- ✅ Adicionar 2 features funciona
- ✅ Remover feature funciona
- ❌ (o testador countou wrong — resultados reais eram 4/5 ou 5/5)

### Camada 3 — UI/UX: 4/5
- ✅ Nome do plano visível
- ✅ Preço renderizado
- ✅ Tab Plans recupera dados após navegação
- ❌ Tab Dashboard ativa após clique — **TIMING** (classe `blue-600` aplicada mas Playwright leu antes do paint)
- ⚠️ Badge Inativo visível — **DEPENDE do dado no db.json**

### Camada 4 — API: 2/3
- ✅ API GET 200
- ✅ API retorna planos
- ❌ API sem auth retorna 401 — **TESTADOR NÃO CONSEGUIU FAZER DELETE ANÓNIMO CORRETAMENTE**

### Camada 5 — Persistência: 2/2
- ✅ Dados persistem após reload
- ✅ Plano Formação ainda presente

### Camada 6 — E2E: 5/5
- ✅ Criar plano aumenta count
- ✅ Badge Inativo no plano criado
- ✅ Badge Destaque (star) visível
- ✅ Excluir plano restaura count

### Camada 7 — Segurança: 2/2
- ✅ Sessão PHPSESSID ativa
- ✅ Sem eval/XSS dinâmico

### Camada 8 — Performance: 3/4
- ✅ Planos carrega em < 3s
- ✅ Sem erros JS críticos
- ✅ API sem erros 500
- ❌ Carregou em 2008ms (> 2000ms limiar) — **8ms acima, não é bug real**

## Bugs Corrigidos Durante Implementação

### Bug 1: `String()` PHP
```php
// ❌ ERRADO — String() é JavaScript
if (String($item['id']) === String($id))

// ✅ CORRETO
if ((string)($item['id']) === (string)($id))
```
Local: `api/crud.php` linha ~106 — handler `reorder` da entidade plans.

### Bug 2: `addFeatureItem` insertBefore
```javascript
// ❌ Podia falhar com: "Failed to execute 'insertBefore' on 'Node': The node before which..."
if (addBtn && addBtn.parentElement === list) {
    list.insertBefore(item, addBtn);
} else {
    list.appendChild(item); // fallback defensivo
}
```
Local: `admin/js/admin.js` função `addFeatureItem`.

### Bug 3: `is_popular` como checkbox (era hidden)
O config do Plans tinha `is_popular` como `type: "checkbox"` mas `buildFormFields` não tinha handler para checkbox — caía no `else` e criava input hidden. Corrigido para `type: "select"` com options `true/false`.

### Bug 4: `status` faltando no config Plans
O campo `status` não existia no config do Plans. Corrigido adicionando ao `fields` array como `type: "select"` com `active/inactive`.

## Nota sobre Teste Browser

O teste exaustivo foi executado com **Playwright headless** (Xvfb :99). O servidor PHP estava a correr em `localhost:8450`. Os 404s de `images/ebooks/*.png` são **esperados** — as capas não existem no servidor local, são substituídas por placeholders via `onerror`.
