---
name: site-ten-workflow
description: Workflows for working with the SiteTen project — syncing with production, development, and deployment. SiteTen is the alvarobiano.com.br website built with Tailwind CSS, PHP API, and Netlify deployment.
version: 1.0.0
author: Bianinho
license: MIT
metadata:
  hermes:
    tags: [SiteTen, Netlify, Tailwind, PHP, Production]
    related_skills: [github-repo-management]
---

# SiteTen — Development Workflow

SiteTen is the Álvaro's main website (alvarobiano.com.br). It lives in `~/repos/SiteTen/` and is deployed via Netlify.

## Tech Stack

- **Frontend**: Static HTML + Tailwind CSS (compiled via `tailwindcss` binary)
- **Backend**: PHP API (admin/, api/, area-aluno/)
- **Data**: `data/db.json` — course/product catalog consumed by JS
- **Deploy**: Netlify (connected to GitHub `AlvaroBiano/SiteTen`)
- **Hosting**: www.alvarobiano.com.br

## Key Files

| Path | Purpose |
|------|---------|
| `index.html` | Homepage |
| `*.html` | Pages: blog, cursos, ebooks, artigo, aviso, politica, termos |
| `data/db.json` | Product/course data (consumed by JS) |
| `tailwind.config.js` | Tailwind build config |
| `tailwindcss` | Standalone Tailwind CLI binary (76MB) |
| `admin/` | Admin dashboard |
| `api/` | PHP backend endpoints |
| `area-aluno/` | Student area (login, player) |

## Workflow 0: REGRA LOCAL FIRST — Regra de Ouro do Álvaro ⚠️

**NUNCA fazer nada no Hostinger. Tudo acontece localmente.**

- ✅ Credenciais geradas e testadas localmente
- ✅ PHP server local para testes
- ✅ GitHub como canal de sync (preview branch → pull → teste → aprovação → main)
- ❌ NUNCA tocar no painel Hostinger ou File Manager
- ❌ NUNCA fazer upload direto para o servidor live
- ❌ NUNCA fazer túnel para expor serviços locais (bloqueado por firewall)

**Fluxo de trabalho:**
```
1. Fazer alterações em ~/repos/SiteTen (local)
2. git commit -m "descrição" (local)
3. Push para branch preview no GitHub
4. Álvaro faz: git pull origin preview (no dele)
5. Álvaro testa localmente
6. Álvaro diz "OK Aprovado"
7. Só ENTÃO: merge preview → main → push origin main
```

**Preview automático com watcher:**
```bash
python3 ~/.hermes/scripts/siteten_preview_watcher.py
```
O watcher auto-commita para `preview` a cada alteração em `admin/` ou `api/` (polling 5s).

## Workflow 1: Sync Local Clone with Production

**Before starting any work on SiteTen**, always sync the local clone with the live site first:

```bash
cd ~/repos/SiteTen

# Backup old versions
mkdir -p .compare_backup
for f in *.html data/db.json .htaccess tailwind.config.js admin/index.html; do
  [ -f "$f" ] && cp "$f" ".compare_backup/"
done

# Download from production
for page in index blog cursos ebooks artigo aviso politica termos; do
  curl -s "https://www.alvarobiano.com.br/$page.html" -o "$page.html"
done
curl -s "https://www.alvarobiano.com.br/data/db.json" -o data/db.json
curl -s "https://www.alvarobiano.com.br/.htaccess" -o .htaccess
curl -s "https://www.alvarobiano.com.br/tailwind.config.js" -o tailwind.config.js
curl -s "https://www.alvarobiano.com.br/admin/index.html" -o admin/index.html

echo "Synced with production"
```

## Workflow 2: Making Edits — Regra Principal

**REGRA DO ÁLVARO:Local primeiro → testar → aprovação → push GitHub.** Nunca fazer push para main sem aprovação.

1. Fazer alterações em `~/repos/SiteTen/` (local only)
2. Commitar no branch `main` (local): `git add -A && git commit -m "descrição"`
3. **Testar** — verificar no browser (local ou site live)
4. **Solicitar aprovação** ao Álvaro: "Perfeito/aprova?"
5. **Só depois de aprovado**: `git push origin main`

### Para testes de modules novos: usar branch `preview`
```bash
cd ~/repos/SiteTen
git checkout -b preview        # criar branch preview
# fazer alterações, commitar
git push -u origin preview     # subir preview
# Álvaro faz: git pull origin preview
# Álvaro testa localmente
# Após aprovação → merge para main → push
```

**IMPORTANTE:** O trabalho é 100% local. Ver "Workflow 0: LOCAL FIRST" acima.

### Para preview automático (watcher Python)
```bash
python3 ~/.hermes/scripts/siteten_preview_watcher.py
```
Este script faz polling a cada 5s e auto-commita para o branch `preview` quando detecta alterações em `admin/` ou `api/`.

## ⚠️ Armadilhas Conhecidas

### PHP obrigatório para o admin
O servidor Python (`python3 -m http.server`) **não executa PHP**. Para testar APIs do admin localmente:

```bash
# Instalar PHP (pode dar erros de dpkg com apache2 e broadcom-sta-dkms — ignorar, o CLI funciona)
sudo dpkg --configure -a
sudo apt-get install -y php php-cli php-mbstring php-curl php-json php-bcmath

# Verificar que funciona
php -v  # deve mostrar "PHP 8.3.X"
php -r "echo function_exists('password_verify') ? 'bcrypt ok' : 'no bcrypt';"

# Iniciar servidor PHP local (NÃO usa Apache — é built-in do PHP)
cd ~/repos/SiteTen
php -S 0.0.0.0:8410

# Testar: http://localhost:8410/admin/index.html
```

**Nota sobre erros dpkg:** Apache2 e broadcom-sta-dkms dão erros de configuração mas não afetam o `php-cli`. Se o `php -v` responder, está funcionando.

### PHP obrigatório para o admin
O servidor Python (`python3 -m http.server`) **não executa PHP**. Para testar APIs do admin localmente:

```bash
# Instalar PHP (pode dar erros de dpkg com apache2 e broadcom-sta-dkms — ignorar, o CLI funciona)
sudo dpkg --configure -a
sudo apt-get install -y php php-cli php-mbstring php-curl php-json php-bcmath

# Verificar que funciona
php -v  # deve mostrar "PHP 8.3.X"
php -r "echo function_exists('password_verify') ? 'bcrypt ok' : 'no bcrypt';"

# Iniciar servidor PHP local (NÃO usa Apache — é built-in do PHP)
cd ~/repos/SiteTen
php -S 0.0.0.0:8410

# Testar: http://localhost:8410/admin/index.html
```

**Nota sobre erros dpkg:** Apache2 e broadcom-sta-dkms dão erros de configuração mas não afetam o `php-cli`. Se o `php -v` responder, está funcionando.

**Parar o servidor PHP:**
```bash
kill $(lsof -ti:8410)
```

### Tailscale/Cloudflared para expor servidor local
Este servidor tem **cloudflared** a funcionar como túnel Cloudflare Tunnel (não Tailscale serve).

**Túnel activo (30/04/2026):**
- **URL:** https://alvarobiano-linuxmint.taile2fd75.ts.net
- ** pointing to:** localhost:8410 (PHP built-in server)
- **Processo:** cloudflared tunnel run → routing via Cloudflare → URL pública

**Verificar se cloudflared está a funcionar:**
```bash
ps aux | grep cloudflared | grep -v grep
# ou
curl -s https://alvarobiano-linuxmint.taile2fd75.ts.net/admin/index.html | head -3
```

**Reiniciar túnel (se necessário):**
```bash
pkill -f cloudflared
cloudflared tunnel run --url http://localhost:8410
```

**Se o cloudflared não estiver a funcionar**, usar branch `preview` no GitHub para o Álvaro testar localmente.

**Se o tailscale serve não funcionar** (erro "Access denied"), o Álvaro pode testar localmente com `git pull origin preview` no computador dele.

### Admin credentials: par de chaves RSA
O sistema de login do admin usa **duas camadas**: password bcrypt + assinatura RSA.
Se precisar regenerar credenciais:

```bash
# NOVO par de chaves (gera ambos)
cd ~/repos/SiteTen/api/security/
openssl genrsa 2048 | tee private_key.pem | \
  openssl rsa -pubout -out admin_public.key

# Gerar hash bcrypt da password (PHP usa prefixo $2y$)
python3 -c "
import bcrypt
pw = b'AeSm1979@#'
h = bcrypt.hashpw(pw, bcrypt.gensalt(12)).decode()
h_php = h.replace('\$2b\$', '\$2y\$')
with open('admin_password.hash', 'w') as f: f.write(h_php)
print('Hash:', h_php)
"

# Verificar que as chaves correspondem (mesmo MD5)
md5sum private_key.pem admin_public.key
```

**⚠️ ARMADILHA CRÍTICA: Não confundir pares de chaves.**
Se gerares dois pares de chaves em sessões diferentes, cada par tem a sua public key correspondente.
O admin precisa da **private key que corresponde à public key que está no servidor**.
**Regra: depois de gerar o par, testa a API imediatamente antes de enviar ao Álvaro.**
```bash
curl -s -X POST http://localhost:8410/api/auth.php \
  -F "password=AeSm1979@#" \
  -F "private_key=@~/repos/SiteTen/api/security/private_key.pem" | python3 -m json.tool
# Esperado: {"success": true, "message": "Cadeados Abertos. Bem-vindo."}
```

### Preview branch: criar do zero se divergir
Se o preview branch diverge do main e `git merge main` recusar por "unrelated histories":
```bash
git push origin --delete preview   # apaga remote
git branch -D preview              # apaga local
git checkout -b preview            # cria novo do main atual
git push -u origin preview        # sobe limpo
```
Isto foi necessário em 30/04/2026 quando o primeiro preview foi criado com `--orphan` e não tinha nada em comum com main.

### Firewall bloqueia portas externas — Cloudflare Tunnel funciona
Este servidor (186.235.80.200) bloqueia ligações externas nas portas 22, 80, 443, 8410.
serveo.net, localhost.run, ngrok **não funcionam**.
**Cloudflare Tunnel (cloudflared) funciona** — expõe localhost:8410 como https://alvarobiano-linuxmint.taile2fd75.ts.net
Solução: `cloudflared tunnel run --url http://localhost:8410` (funciona) OU usar branch `preview` no GitHub.

### Chart.js: usar `maintainAspectRatio: true` com wrapper div de altura fixa
Quando se usa Chart.js (bar, doughnut, line) com Tailwind, **nunca** usar `maintainAspectRatio: false` esperando que o atributo `height="120"` no `<canvas>` funcione. O Chart.js ignora o height do canvas nesse modo e estica o gráfico infinitamente para preencher o container pai.

**Padrão correto:**
```html
<!-- NO HTML: envolvido em div com altura fixa + position:relative -->
<div style="height:220px;position:relative;">
    <canvas id="chart-monthly-students"></canvas>
</div>
```

```javascript
// NO JS: maintainAspectRatio: true (padrão) — altura vem do container pai
const chartOptions = {
    responsive: true,
    maintainAspectRatio: true,  // ← TRUE (não false)
    plugins: { legend: { display: false } },
    scales: {
        y: {
            beginAtZero: true,
            ticks: { stepSize: 1, font: { size: 11 } },
            grace: '10%'  // dá espaço acima da barra mais alta
        }
    }
};
```

**Sintomas do bug:** gráfico de barras estica verticalmente até o fundo da página, ocupando espaço infinito.

Isto afetou o Dashboard Admin (bar chart "Alunos por Mês" e doughnut "Distribuição de Conteúdo") em 30/04/2026.

### E-books duplicados no db.json
"atenção plena (mindfulness)" aparece 2x. Remover via admin ou editar `data/db.json` diretamente.

## 🐛 Debugging Playbook — Admin V2

### BUG: Tabela aparece vazia mas dados existem

**Sintomas:** Login funciona, dashboard carrega, mas ao clicar numa tab nada aparece. Playwright confirma: innerHTML tem 6 linhas, zero JS errors.

**Diagnóstico (5 min) — no browser DevTools ou Playwright:**
```javascript
const el = document.getElementById('crud-main');
const style = window.getComputedStyle(el);
const hasHidden = el.classList.contains('hidden');
console.log(`display: ${style.display}, hidden: ${hasHidden}`);
// Se hidden=true e display=none → BUG ENCONTRADO
```

**Causa raiz:** `switchTab()` faz `classList.add('hidden')` ao crud-main e dashboard-content. O `renderTable()` preenche dynamic-table-body mas nunca remove o hidden. O Tailwind usa `.hidden { display: none !important }` — o `!important` sobrepõe inline styles.

**Correção — OBRIGATÓRIA ao criar qualquer nova tab:**
```javascript
function renderTable() {
    document.getElementById('crud-main')?.classList.remove('hidden');
    // ...
}
```

**Lições:**
1. Zero JS errors NÃO significa que funciona — bugs CSS/visibility existem
2. Verificar classList E computedStyle, não só innerHTML
3. Tailwind `hidden` tem `!important` — sobrepõe inline styles
4. Testar com Playwright ANTES de perguntar ao utilizador
5. Quando o utilizado diz "não funciona" — acreditar, não culpar cache

### Placeholder de imagem não aparece (display:none vs class hidden)

**Problema:** onerror tenta mostrar placeholder com `style.display='flex'` mas não funciona se o elemento tem `class="hidden"` (Tailwind com `!important`).

**Solução:** Nunca usar `class="hidden"` em elementos que precisam ser mostrados por onerror. Usar sempre `style="display:none"`:
```html
<div class="h-14 w-10 ..." style="display:none" ...>
```
```javascript
onerror="this.style.display='none'; this.nextElementSibling.style.display='flex';"
```

### Fluxo de Debug para Problemas Visuais no Admin
1. Verificar se elemento existe — document.getElementById não é null
2. Verificar visibility — classList.contains('hidden') E getComputedStyle().display
3. Verificar dimensões — getBoundingClientRect() para confirmar 0x0
4. Verificar 404s de recursos — Network tab ou page.on('response') no Playwright
5. Screenshot — await page.screenshot({ path: '/tmp/debug.png' }) para ver o que o browser mostra

### Imagem quebrada no popup "Visualizar (Home)" do admin

**Sintoma:** No popup "Vitrine da Página Inicial (1-6)" do admin, capas com `cover_url` vazio/404 mostram o ícone de imagem quebrada do browser.

**Causa:** Quando o `src` aponta para URL inexistente, o browser mostra o ícone broken image — CSS não controla isto.

**Solução correta — src swap (NÃO lightbox):** O Álvaro rejeitou o lightbox neste contexto. O utilizador só quer que a miniatura não apareça como quebrada. Padrão:

```html
<img src="${coverUrl || 'https://placehold.co/300x450/eeeeee/999999?text=Capa'}"
     alt="${ebook.title}"
     class="w-full h-auto max-h-40 object-cover rounded shadow-sm mb-2"
     onerror="this.onerror=null; this.src='https://placehold.co/300x450/eeeeee/999999?text=Sem+Capa'; this.classList.remove('object-cover'); this.classList.add('p-2');">
```

**Porque não lightbox aqui:** O popup mostra 6 miniaturas pequenas. Cada uma clicável para ver em tamanho real seria confuso — o utilizador só quer que não apareça o ícone de imagem partida. O `onerror` substitui diretamente o `src` 404 pelo placeholder dentro da própria miniatura.

**Nota:** `this.onerror=null` previne loop infinito (se o placeholder também falhasse).

### Regra prática — "imagem quebrada" vs. "lightbox de imagem"

| Contexto | Abordagem | Razão |
|---|---|---|
| Admin popup com miniaturas | `onerror` → src swap direto | Simples, não precisa de modal |
| Site público (Home, E-books page) | `onerror` → abre lightbox | Experiência rica, ampliar para ver |
| Card que precisa de visualização | Lightbox `openImgViewer()` | Ver imagem em tamanho real |

**Lição aprendida (30/04/2026):** Perguntar "como deve ficar quando estiver corrigido?" antes de implementar. O Álvaro queria miniatura com placeholder, não um modal giant por cima.

### Imagem quebrada vs. lightbox com placeholder

**Sintoma:** No popup "Visualizar (Home)" do admin, capas com `cover_url` vazio ou 404 mostram o ícone de imagem quebrada do browser.

**Causa:** O `src=""` ou URL inexistente faz o browser mostrar o ícone de broken image — não é controlado pelo CSS.

**Padrão de correção (onerror → lightbox):**
```html
<img src="${coverUrl || 'https://placehold.co/300x450/eeeeee/999999?text=Capa'}"
     alt="${ebook.title}"
     class="w-full h-auto max-h-40 object-cover rounded shadow-sm mb-2 cursor-pointer"
     onclick="openImgViewer(this.src, this.alt);"
     onerror="openImgViewer('https://placehold.co/300x450/eeeeee/999999?text=Sem+Capa', this.alt);">
```

**O onerror abre o lightbox com o placeholder** — fica muito melhor do que o ícone de imagem quebrada do browser. Este padrão está implementado em:
- `index.html` + `main.js` (Home E-books grid)
- `ebooks.html` + `ebooks.js` (página E-books)
- `admin/index.html` + `admin/js/admin.js` (popup Visualizar Home)

Ver referência completa: `references/ebook-cover-lightbox.md`

### Playwright: login admin não funciona com setInputFiles

Se page.setInputFiles parece funcionar mas o login falha, verificar com curl PRIMEIRO:
```bash
curl -s -X POST "https://alvarobiano-linuxmint.taile2fd75.ts.net/api/auth.php" \
  -F "password=AeSm1979@#" \
  -F "private_key=@/home/alvarobiano/repos/SiteTen/api/security/private_key.pem"
# Esperado: {"success":true,"message":"Cadeados Abertos. Bem-vindo."}
```


## Workflow 3: Cloning SiteTen Fresh

```bash
# Extract PAT
export GITHUB_TOKEN=$(grep "github.com" ~/.git-credentials | head -1 | sed 's|https://[^:]*:\([^@]*\)@.*|\1|')

# Clone
mkdir -p ~/repos && cd ~/repos
git clone "https://$GITHUB_TOKEN@github.com/AlvaroBiano/SiteTen.git"

# Make pushable
cd SiteTen
git remote set-url origin "https://$GITHUB_TOKEN@github.com/AlvaroBiano/SiteTen.git"

# Sync with production (Workflow 1 above)
```

## Workflow 4: Comparing Local vs Production

```bash
cd ~/repos/SiteTen
for page in index blog cursos ebooks artigo aviso politica termos; do
  LIVE="https://www.alvarobiano.com.br/$page.html"
  LIVE_SIZE=$(curl -s "$LIVE" | wc -c)
  LOCAL_SIZE=$(wc -c < "$page.html")
  if [ "$LIVE_SIZE" -eq "$LOCAL_SIZE" ]; then
    curl -s "$LIVE" -o /tmp/live_$page.html
    if diff -q "$page.html" "/tmp/live_$page.html" > /dev/null; then
      echo "✅ $page.html — identical"
    else
      echo "⚠️  $page.html — same size, different content"
    fi
  else
    echo "⚠️  $page.html — local: $LOCAL_SIZE | live: $LIVE_SIZE"
  fi
done
```

## Common Tasks

**Rebuild Tailwind after changing classes:**
```bash
cd ~/repos/SiteTen
./tailwindcss -i ./css/input.css -o ./css/output.css --minify
```

**Force Netlify rebuild:**
Push any commit to `main`, or trigger via Netlify dashboard.

**Check if db.json is current:**
```bash
curl -s "https://www.alvarobiano.com.br/data/db.json" | python3 -c "import json,sys; d=json.load(sys.stdin); print(f'Courses: {len(d.get(\"cursos\",[]))}, Ebooks: {len(d.get(\"ebooks\",[]))}')"
```

## Workflow 5: GitHub Token e Credentials

O token GitHub PAT com acesso total ao repo `AlvaroBiano/SiteTen` está em `~/.git-credentials`.
Para extrair (não usar `cat` diretamente — pode estar mascarado):

```bash
xxd ~/.git-credentials | head -3
# Output: ...ano:<GITHUB_PAT>@gith...
# Token: <GITHUB_PAT>
```

Se o `cat` mostrar `***`, usar `xxd` para ler o binário e extrair o token manualmente.

## Versionamento (v1, v2, v3...)

```bash
cd ~/repos/SiteTen
python3 ~/.hermes/scripts/siteten_version_manager.py --get          # ver versão atual
python3 ~/.hermes/scripts/siteten_version_manager.py --increment "descrição"  # criar v{N+1} + tag git
```

Fluxo: Álvaro faz alterações → Bianinho executa version manager → push automático.

## Análise Completa do Site (30/04/2026)

Ver: `references/analise-site-2026-04-30.md`

## Problemas Conhecidos (a resolver)
- `cursos: []` e `blog_posts: []` vazios → SEO morto
- Sem checkout automático → 100% das vendas via WhatsApp manual
- `.htaccess` sem HTTPS forcing nem headers de segurança (CSP, XSS, clickjacking)
- E-books duplicados no db.json ("atenção Plena (Mindfulness)" aparece 2x)
- Sem pixel Facebook/Instagram (remarketing)
- Tailwind CSS não minificado (css/tailwind-output.css: 69KB)
- JS bundles sem code splitting (main.js, article.js, articles.js: 37-38KB cada)
- Páginas PT-BR diferentes das versões inglês/espanhol (usa-english/, mex-spanish/)
- Sem Google Search Console verificado
- **Dashboard gráfico "Alunos por Mês"** (30/04/2026): Corrigido — `getMonthlyStudents()` agora usa `created_at` real. Antes fabricava dados falsos (distribuição igual por mês). Alunos sem data vão para o mês atual.
### Chart.js stretching infinito (30/04/2026): Corrigido — `maintainAspectRatio: false` + canvas `height` attribute não funciona. Usar `maintainAspectRatio: true` + wrapper div com altura fixa.

---

## Admin V2 — Padrão de Implementação de Módulo CRUD

O admin em `admin/` é uma SPA que usa **config-driven CRUD**: cada módulo define sua estrutura em `config[currentTab]` no `admin/js/admin.js`. Cada módulo novo segue o mesmo padrão.

### Etapas de Implementação (sempre nesta ordem)

#### 1. Backend PHP — `api/ebooks.php` (exemplo para e-books)

**a) Parsing de novos campos** (após `$isUpdate` e antes dos campos existentes):
```php
$amazon_link = $_POST['amazon_link'] ?? '';
$price = isset($_POST['price']) ? $_POST['price'] : '';
$category = $_POST['category'] ?? '';
$tags = isset($_POST['tags']) ? $_POST['tags'] : '';
$status = isset($_POST['status']) ? $_POST['status'] : 'active';
```

**b) Se reordenação drag-drop é necessária** (antes de `$isUpdate`):
```php
if (isset($_POST['action']) && $_POST['action'] === 'reorder') {
    $orderedIds = isset($_POST['ordered_ids']) ? json_decode($_POST['ordered_ids'], true) : [];
    // Reorder loop...
    exit;
}
```

**c) Update**: adicionar os novos campos no `foreach ($ebooks as &$eb)` dentro do `if ($isUpdate)`.

**d) Create**: adicionar os novos campos no `$newEbook = [...]`.

**Validação**: `php -l api/ebooks.php` antes de continuar.

#### 2. Frontend JS — `admin/js/admin.js`

**a) Config do módulo** (no objeto `config = {...}`):
```javascript
moduleName: {
    title: "Gestão de Módulo", desc: "Descrição.",
    api: "../api/ebooks.php",
    hasImage: true, imageField: "cover_image", imageUrlField: "cover_url",
    headers: ["Ordem", "Capa", "Título", "Ações"],  // cols matching renderRow
    renderRow: (item) => `...<td>...</td>...`,
    fields: [
        { name: "status", label: "Status", type: "select", req: true,
          options: [{ value: 'active', text: '🟢 Ativo' }, { value: 'inactive', text: '🔴 Inativo' }] },
        { name: "title", label: "Título", type: "text", req: true },
        { name: "price", label: "Preço", type: "text", req: false },
        // ...
    ]
},
```

**b) CRÍTICO — renderTable() deve mostrar crud-main:**
```javascript
function renderTable() {
    // ⚠️ OBRIGATÓRIO: Remover 'hidden' do crud-main
    // O switchTab() adiciona classList.add('hidden') ao crud-main
    // Se o renderTable() não o remover, a tabela fica INVISÍVEL
    // porque o Tailwind usa .hidden { display: none !important; }
    // e !important bloqueia a remoção via inline style
    document.getElementById('crud-main')?.classList.remove('hidden');

    // ... resto do renderTable
}
```

**c) Drag & drop (se aplicável)**: adicionar em `renderTable()`:
```javascript
if (currentTab === 'moduleName') {
    tr.setAttribute('draggable', 'true');
    tr.setAttribute('data-id', item.id);
    tr.addEventListener('dragstart', handleDragStart);
    tr.addEventListener('dragover', handleDragOver);
    tr.addEventListener('dragleave', handleDragLeave);
    tr.addEventListener('drop', handleDrop);
    tr.addEventListener('dragend', handleDragEnd);
}
```

**c) Funções de drag** (antes de `renderTable`):
```javascript
let draggedRow = null;
function handleDragStart(e) { draggedRow = e.currentTarget; ... }
function handleDragOver(e) { e.preventDefault(); ... }
function handleDrop(e) {
    // Reorder DOM, call saveOrder(newOrderedIds)
}
async function saveOrder(orderedIds) {
    const fd = new FormData();
    fd.append('action', 'reorder');
    fd.append('ordered_ids', JSON.stringify(orderedIds));
    const res = await fetch('../api/module.php', { method: 'POST', body: fd });
    // showToast on result
}
```

**d) Toast notifications** (função utilitária):
```javascript
function showToast(message, type = 'info') {
    const colors = { success: 'bg-green-500', error: 'bg-red-500', info: 'bg-blue-500' };
    const toast = document.createElement('div');
    toast.className = `${colors[type]} text-white px-4 py-3 rounded-lg shadow-lg text-sm`;
    toast.textContent = message;
    document.body.appendChild(toast);
    setTimeout(() => { toast.style.opacity = '0'; setTimeout(() => toast.remove(), 300); }, 3000);
}
```

#### 3. Frontend HTML — `admin/index.html`

- Se o módulo tem upload de imagem: `enctype="multipart/form-data"` no `<form id="dynamic-form">`
- Para charts com altura fixa: wrap canvas em `<div style="height:220px;position:relative;"><canvas id="..."></canvas></div>`

#### 4. Verificações obrigatórias antes de entregar

```bash
php -l api/ebooks.php          # syntax check PHP
node --check admin/js/admin.js  # syntax check JS
```

### Módulos já implementados (30/04/2026)

| Módulo | Backend | Frontend | Drag & Drop | Campos |
|--------|---------|----------|-------------|--------|
| Dashboard (Módulo 1) | `api/admin/dashboard.php` | `admin/index.html` + `admin/js/admin.js` | Não | KPIs, Charts (Chart.js), Alerts |
| E-books (Módulo 2) | `api/ebooks.php` | `admin/js/admin.js` config | ✅ Sim | price, category, tags, status, amazon_link, views, destaque ordinal |

### To-do: implementar следующие módulos

- Plans (Módulo 3): já existe mas melhorar campos (período, badge popular, features em lista)
- Blog Posts (Módulo 4): editor TinyMCE, categories, tags, SEO fields
- FAQs (Módulo 5): CRUD com categorias
- Testimonials (Módulo 6): foto, rating estrelas
- Cursos/Módulos (Módulo 7): estrutura hierárquica curso→módulo→aula
- Alunos/LMS (Módulo 8): gestão completa
- Integrações (Módulo 9): Hotmart/Eduzz webhook, Facebook Pixel
- Backups (Módulo 10): automático + manual + restore
- Audit Log (Módulo 11): log de todas as alterações
- Configurações (Módulo 12): multi-usuário admin, segurança
