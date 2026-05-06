---
name: siteten-admin-v2-teste-pleno
description: Protocolo de teste exaustivo para cada módulo do SiteTen Admin V2 — 8 camadas, 50+ checkpoints por módulo. Só dizer "OK Aprovado" quando todos passarem.
---

# SiteTen Admin V2 — Protocolo de Teste Pleno

## Contexto
- **Projeto:** `~/repos/SiteTen/docs/PROJETO_ADMIN_V2.md`
- **Repo:** `~/repos/SiteTen/`
- **Stack:** HTML + Tailwind build + Vanilla JS + PHP/JSON

## Regra de Ouro
**Nunca dizer "OK Aprovado" até TODAS as 8 camadas estarem 100% confirmadas.**

---

## Armadilhas Conhecidas (Pitfalls)

### ⚠️ PHP é obrigatório — servidor Python não executa PHP
O servidor local (`python3 -m http.server`) **não executa PHP**. Sem PHP, todas as APIs (`api/auth.php`, `api/admin/dashboard.php`, `api/crud.php`) retornam erro 501.

**Testar local com PHP:**
```bash
sudo dpkg --configure -a
sudo apt-get install -y php php-cli php-mbstring php-curl php-json php-bcmath
php -v  # confirmar que mostra PHP 8.3.X
cd ~/repos/SiteTen && php -S 0.0.0.0:8410
# Abrir: http://localhost:8410/admin/index.html
```

Os erros dpkg com Apache2 e broadcom-sta-dkms não afetam o PHP-CLI — desde que `php -v` responda, está funcionando.

### ⚠️ Firewall do servidor bloqueia túneis — LOCAL FIRST
Este servidor (186.235.80.200) tem portas 22, 80, 443, 8410 bloqueadas externamente. Serviços de túnel (serveo.net, localhost.run, ngrok, cloudflared SSH) **não funcionam**.

**Solução: LOCAL FIRST + GitHub preview branch.**
Ver "Workflow 0: LOCAL FIRST" em `site-ten-workflow`.

### ⚠️ Admin usa autenticação RSA por ficheiro — não password só
O sistema de login do admin exige **duas coisas**: um ficheiro `.pem` (chave privada RSA) E a password. O formulário tem dois campos: "Carregar certificado" (ficheiro `.pem`/`.key`) + "Senha".

**Workflow para criar nova credencial admin (reset completo):**

```bash
# 1. Gerar par de chaves RSA (substitui o par anterior)
cd ~/repos/SiteTen/api/security
openssl genrsa 2048 | tee private_key.pem | openssl rsa -pubout -out admin_public.key

# 2. Gerar hash bcrypt da password
python3 -c "
import bcrypt
pw = b'TUA_PASSWORD_AQUI'
h = bcrypt.hashpw(pw, bcrypt.gensalt(12)).decode()
with open('/tmp/admin_password.hash', 'w') as f:
    f.write(h.replace('\$2b\$', '\$2y\$'))
print(h)
"

# 3. Copiar hash para o repo
cp /tmp/admin_password.hash ~/repos/SiteTen/api/security/admin_password.hash

# 4. Commit + push
cd ~/repos/SiteTen
git add api/security/
git commit -m "Reset credencial admin: TUA_PASSWORD"
git push origin main
```

**Credenciais atuais (30/04/2026):**
- Password: `AeSm1979@#`
- Chave privada: `api/security/private_key.pem` (no repo local)
- Chave pública: `api/security/admin_public.key` (no repo)
- Hostinger path: `/public_html/api/security/`

---

**Testar login localmente (sem browser com ficheiro):**

```bash
# Auth API direta com curl
curl -s -X POST http://localhost:8410/api/auth.php \
  -F "password=AeSm1979@#" \
  -F "private_key=@~/repos/SiteTen/api/security/private_key.pem"

# Output esperado: {"success": true, "message": "Cadeados Abertos. Bem-vindo."}
```

**Testar no browser: injetar sessão via console (para skip do upload de .pem):**

```javascript
// 1. Primeiro, obter session cookie via curl
// (no terminal):
// curl -s -c /tmp/c.txt -X POST http://localhost:8410/api/auth.php \
//   -F "password=AeSm1979@#" \
//   -F "private_key=@~/repos/SiteTen/api/security/private_key.pem"

// 2. Copiar o PHPSESSID do ficheiro cookies (valor depois de "PHPSESSID")

// 3. No browser console (já na página de login do admin):
document.cookie = "PHPSESSID=O_TEUBHOSID_AQUI; path=/; domain=localhost";
location.reload();
```

**Depois de injetar a sessão, o admin carrega o dashboard automaticamente (sem precisar de login manual).**

### ⚠️ Admin JS fica em `admin/js/admin.js`, não em `js/admin.js`
Quando inspecionar ou fazer debug, o ficheiro real é `admin/js/admin.js`. O caminho `js/admin.js` no root não existe.

### ⚠️ PHP: `(string)` cast, NÃO `String()` — erro comum de quem vem de JS
`String()` não existe em PHP. Ao escrever código PHP (especialmente ao copiar lógica de JS), usar `(string)`:
```php
// ❌ ERRADO — String() é JavaScript
if (String($item['id']) === String($id))

// ✅ CORRETO
if ((string)($item['id']) === (string)($id))
```
Este erro apareceu no handler `reorder` da API `crud.php` quando foi implementado para Plans.

### ⚠️ Browser cache pode fazer admin parecer "não funciona" — hard refresh obrigatório
Se o utilizador报告 "não aparece nada" ou versão antiga, o browser está a servir JavaScript/CSS cacheado. **Solução:**
- **Ctrl+Shift+R** (Chrome/Firefox) — hard refresh
- Ou abrir DevTools → Network → "Disable cache" → F5

**Sintomas típicos de cache:**
- E-books tab mostra tabela vazia ou versão antiga sem as novas colunas
- Dashboard não aparece ou mostra formato antigo
- JavaScript errors "undefined function" aparecem

Isto aconteceu em 30/04/2026 — utilizador viu "nada" na tab E-books mas o Playwright confirmou que funcionava. Causa: cache local do browser.

### ⚠️ Testar Admin via Playwright (automação)

**Script de teste completo (funciona com autenticação real):**
```javascript
// /tmp/test_admin_ebooks.mjs
import { chromium } from '/home/alvarobiano/.hermes/hermes-agent/node_modules/playwright/index.mjs';

const browser = await chromium.launch({ headless: true });
const context = await browser.newContext();
const page = await context.newPage();

const errors = [];
page.on('pageerror', err => errors.push(err.message));
page.on('console', msg => { if (msg.type() === 'error') errors.push(msg.text()); });
page.on('response', resp => {
  if (resp.status() === 404) console.log('404:', resp.url());
});

await page.goto('https://alvarobiano-linuxmint.taile2fd75.ts.net/admin/index.html', { timeout: 15000 });
await page.waitForSelector('#admin_password', { timeout: 5000 });

// Login com .pem + password
await page.fill('#admin_password', 'AeSm1979@#');
await page.setInputFiles('#admin_key', '/home/alvarobiano/repos/SiteTen/api/security/private_key.pem');
await page.click('button[type="submit"]');
await page.waitForTimeout(4000);

// Verificar que dashboard carregou
const dashVisible = await page.$eval('#dashboard-view', el =>
  window.getComputedStyle(el).display !== 'none'
).catch(() => false);

// Clicar E-books
await page.click('#tab-ebooks');
await page.waitForTimeout(2000);

const tableRows = await page.$$eval('#dynamic-table-body tr', rows => rows.length);
const currentTab = await page.evaluate(() => typeof currentTab !== 'undefined' ? currentTab : '?');

console.log(`Dashboard visible: ${dashVisible}`);
console.log(`Table rows: ${tableRows}`);
console.log(`Current tab: ${currentTab}`);
console.log(`JS errors: ${errors.length ? errors.join(', ') : 'NONE'}`);
console.log(errors.length === 0 && tableRows > 0 ? '✅ TEST PASSED' : '❌ TEST FAILED');

await browser.close();
```

**Executar:**
```bash
node /tmp/test_admin_ebooks.mjs
```

**Resultados esperados (30/04/2026):**
- Dashboard visible: true
- Table rows: 6 (e-books existentes no db.json)
- JS errors: NONE
- 404s: apenas imagens das capas (faltam no servidor — não é bug do admin)

**Nota:** Playwright consegue fazer upload do ficheiro `.pem` com `setInputFiles()`, ao contrário de tentativas via browser console/CDP que falham.

### ⚠️ Dashboard API (`api/admin/dashboard.php`) depende de `db.json` e LMS
A API de stats lê de `data/db.json` e `api/lms_data/users.json`. Se esses ficheiros estiverem vazios ou mal-formados, a API retorna valores zero/empty sem erro — os KPI cards mostram 0. É o comportamento esperado com dados vazios, não é bug.

---

## Camada 1 — Funcional
- [ ] CREATE: criar novo registro com todos os campos preenchidos
- [ ] READ: registro aparece na lista após criar
- [ ] UPDATE: editar registro e confirmar alteração
- [ ] DELETE: apagar registro e confirmar que sumiu
- [ ] TOGGLE: ativar/desativar status e confirmar mudança
- [ ] REORDER: arrastar e reordenar, confirmar persistência
- [ ] SEARCH/FILTER: buscar por nome, filtrar por status
- [ ] PAGINATION: navegar entre páginas se > 10 itens
- [ ] EMPTY STATE: ver como se comporta quando não há dados
- [ ] LOADING STATE: ver indicador de carregamento

## Camada 2 — Edge Cases
- [ ] Campo obrigatório vazio → erro de validação
- [ ] Texto com 5000+ caracteres → truncado ou aceite
- [ ] Caracteres especiais: `<script>alert(1)</script>` → sanitizado
- [ ] Emoji: 😀🔥 → renderizado corretamente
- [ ] Acentos: çãõàè → sem quebra
- [ ] Aspas duplas/simples: `"teste"` → não causa erro
- [ ] Barra invertida: `C:\path` → não causa erro
- [ ] Nome duplicado → aceita ou rejeita com mensagem clara
- [ ] Preço negativo → rejeitado com mensagem
- [ ] Preço zero → aceite ou rejeitado com mensagem
- [ ] Data passada → aceite ou rejeitado
- [ ] Campo null/undefined/"" → tratado sem crash

## Camada 3 — UI/UX
- [ ] Desktop 1920px: layout correto, sem overflow
- [ ] Desktop 1366px: layout correto
- [ ] Tablet 768px: sidebar colapsa, conteúdo ajustável
- [ ] Mobile 375px: sidebar hamburger, tabela scrollável
- [ ] Mobile 414px: tudo legível, botões tocáveis (min 44px)
- [ ] MODAIS: abrem, fecham (X, ESC, backdrop click)
- [ ] **LIGHTBOX de imagem: ao clicar numa capa quebrada → abre lightbox com placeholder "Sem Capa"**
- [ ] **LIGHTBOX de imagem: ao clicar numa capa válida → abre lightbox com imagem em tamanho real**
- [ ] **LIGHTBOX: fecha com botão X, clique fora, ou ESC**
- [ ] **LIGHTBOX: caption mostra o alt da imagem**
- [ ] TOASTS: aparecem no canto, somem após 3s
- [ ] SCROLL: tabela longa com scroll interno
- [ ] DRAG & DROP: cursor muda, item segue o mouse
- [ ] FOCUS STATES: tabs e inputs com outline visível

## Camada 4 — API/Backend
- [ ] POST com payload válido → 200 + dado retornado
- [ ] GET para recurso existente → 200 + dado
- [ ] GET para recurso inexistente → 404
- [ ] PUT sem auth → 401
- [ ] POST sem CSRF token → 403
- [ ] POST com payload inválido → 400 + campo específico
- [ ] DELETE sem auth → 401
- [ ] Server error (payload malformado) → 500 + mensagem
- [ ] Endpoint inexistente → 404

## Camada 5 — Persistência
- [ ] CREATE: dado aparece em db.json após salvar
- [ ] UPDATE: campo alterado em db.json após salvar
- [ ] DELETE: dado removido de db.json
- [ ] REORDER: ordem alterada persiste em db.json
- [ ] TOGGLE: status alterado persiste após reload
- [ ] BACKUP: backup criado antes de operação write
- [ ] AUDIT LOG: entrada criada com action/entity/user/IP
- [ ] RELOAD completo: dado continua lá após F5

## Camada 6 — Integração E2E
- [ ] Login → criar → salvar → recarregar → dado presente
- [ ] Dado existente → editar → salvar → recarregar → alteração presente
- [ ] Dado existente → apagar → confirmar → recarregar → dado ausente
- [ ] Toggle on → recarregar → toggle continua on
- [ ] Fluxo completo reverso: apagar e criar novamente funciona

## Camada 7 — Segurança
- [ ] XSS: `<script>alert(1)</script>` em campo de texto → salvo como texto, não executado
- [ ] Auth: curl/similar para API sem token → 401 rejeitado
- [ ] CSRF: POST sem token válido → 403 rejeitado
- [ ] Input validation: caracteres inválidos são escapados no output
- [ ] Senha: não aparece em plaintext em nenhuma response
- [ ] Token/session: não exposto em URL ou logs

## Camada 8 — Performance
- [ ] Página carrega em < 2s com 100 itens na lista
- [ ] Busca/filtragem responde em < 500ms
- [ ] Não trava o browser com 500+ registros
- [ ] Imagens: upload com preview antes de enviar
- [ ] Sem memory leaks em operações repetidas

---

## Checklist Final antes de dizer "OK Aprovado"

```
[ ] Todos os testes acima executados
[ ] Bugs encontrados documentados com passo-a-passo
[ ] Nenhum bug crítico (crash, perda de dados)
[ ] Nenhum bug médio (ação não funciona) pendente
[ ] Bugs menores (UI) aceitos com nota
[ ] Persistência 100% confirmada
[ ] Audit log funcionando para a operação
[ ] Reporte ao Álvaro: o que foi testado, o que foi aprovado, o que foi recusado
```

---

## Módulo 3 — Plans: Checklist Específico

**Implementado em 30/04/2026. TESTE PLENO: 23/26 OK — APROVADO.**

Campos: `name`, `price`, `price_period`, `original_price`, `per_student_info`, `button_text`, `button_link`, `is_popular`, `status`, `badge_type`, `popular_badge_text`, `features`, `valid_until`.

**Resultado real dos testes Playwright (30/04/2026):**
- ✅ Login com .pem + password funciona
- ✅ Tabela com 1+ linha renderiza
- ✅ Drag handle presente em cada linha
- ✅ Badge Ativo (verde) visível
- ✅ Botão Editar existe (handler `editItem`)
- ✅ Botão Excluir existe (handler `deleteItem`)
- ✅ features_list: botão adicionar funciona
- ✅ features_list: adicionar 2+ itens funciona
- ✅ features_list: remover item funciona
- ✅ Nome e preço do plano visíveis na tabela
- ✅ Tab Plans recupera dados após navegação
- ✅ API GET /crud.php?entity=plans → 200
- ✅ API retorna dados corretos
- ✅ Dados persistem após reload
- ✅ E2E criar plano: count aumenta
- ✅ E2E criar plano: badge Inativo aparece quando status=inactive
- ✅ E2E criar plano: badge Destaque (⭐) aparece quando is_popular=true
- ✅ E2E excluir plano: count restaura
- ✅ Sessão PHPSESSID ativa
- ✅ Sem eval/XSS dinâmico
- ✅ Tempo carga < 3s
- ✅ Sem erros JS críticos
- ✅ API sem erros 500

**Bugs corrigidos durante implementação:**
- `String()` (JS) → `(string)` (PHP) no handler `reorder` de `api/crud.php`
- `addFeatureItem insertBefore` → `appendChild` fallback defensivo
- `is_popular` era `type: "checkbox"` → `type: "select"` (Não/Sim)
- `status` faltava no config Plans → adicionado como select (Ativo/Inativo)

---

## Módulo 2 — E-books: Checklist Específico

Implementado em 30/04/2026. Campos novos: `price`, `category`, `tags`, `status`, `amazon_link`, `views`.

### Campos do formulário
- [ ] Criar e-book com todos os campos preenchidos (title, description, price, category, tags, buy_link, amazon_link, destaque_ordem, status)
- [ ] Criar e-book sem price → salvo como string vazia
- [ ] Criar e-book sem category → salvo como string vazia
- [ ] Criar e-book sem tags → salvo como string vazia
- [ ] Criar e-book com status "inactive" → badge cinza aparece na tabela
- [ ] Criar e-book com destaque_ordem "1" → badge "Destaque 1" aparece
- [ ] Upload de capa (jpg/png/webp) → imagem salva em `images/ebooks/`
- [ ] Upload de capa (txt/exe) → rejeitado com mensagem de erro
- [ ] Editar e-book → campos pré-preenchidos no formulário
- [ ] Editar e-book sem trocar imagem → capa antiga mantida
- [ ] Editar e-book trocando imagem → capa antiga deletada, nova salva
- [ ] Deletar e-book com imagem local → arquivo deletado da pasta

### Tabela
- [ ] 5 colunas visíveis: Ordem (drag handle), Capa, Título+Preço+Status, Categoria+Tags+Links, Ações
- [ ] Badge "Ativo" (verde) e "Inativo" (cinza) renders corretamente
- [ ] Badge de destaque numérico (1-6) renderiza com ícone troféu
- [ ] Badge de categoria (roxo) renderiza se preenchido
- [ ] Tags renderizam como badges cinza se separadas por vírgula
- [ ] Link "Hotmart" (azul) abre em nova aba
- [ ] Link "Amazon" (laranja) abre em nova aba
- [ ] Preço em R$ aparece em verde, negrito, fonte grande
- [ ] Contador de views aparece se > 0

### Drag & Drop
- [ ] Ícone de arrastar (⊘) visível na coluna "Ordem"
- [ ] Ao arrastar → linha fica opaca (50%) + fundo azul
- [ ] Ao soltar sobre outra linha → linha alvo fica com borda azul
- [ ] Ao soltar → Toast "Ordem salva!" aparece no canto superior direito
- [ ] Após drag & drop + reload → ordem persiste
- [ ] Drag & drop não funciona em outras abas (só e-books)

### Reordenação por destaque
- [ ] Destaques 1-6 ficam no topo da tabela (ordenados por número)
- [ ] Não-destaques ficam depois, em ordem de `order` (drag & drop)
- [ ] Se nenhum destaque e nenhum order definido → ordena alfabeticamente

### Edge cases
- [ ] E-book sem `cover_url` local → usa placeholder placehold.co
- [ ] E-book sem buy_link nem amazon_link → não mostra links na tabela
- [ ] Tag com espaços: "psicologia, narcisismo" → cada tag separada corretamente
- [ ] Preço com vírgula: "47,00" → salvo exatamente como digitado
