# E-book Cover Lightbox — Referência de Implementação

**NOTA (30/04/2026):** O admin popup "Visualizar (Home)" NÃO usa lightbox — usa src swap direto. O Álvaro rejeitou o lightbox aí. Ver secção "Admin popup — src swap" abaixo.

---

## Admin popup — src swap direto (NÃO lightbox)

O popup "Visualizar (Home)" no admin mostra 6 miniaturas pequenas. O utilizador só quer que não apareça o ícone de imagem partida — não precisa de modal.

**Código correto (admin):**
```html
<img src="${coverUrl || 'https://placehold.co/300x450/eeeeee/999999?text=Capa'}"
     alt="${ebook.title}"
     class="w-full h-auto max-h-40 object-cover rounded shadow-sm mb-2"
     onerror="this.onerror=null; this.src='https://placehold.co/300x450/eeeeee/999999?text=Sem+Capa'; this.classList.remove('object-cover'); this.classList.add('p-2');">
```

O `onerror` substitui o `src` 404 pelo placeholder diretamente na miniatura. `this.onerror=null` previne loop infinito.

---

## Site público — lightbox (index.html + ebooks.html)

O site público (Home e página E-books) USA lightbox porque o utilizador precisa ver a capa em tamanho real para decidir se compra.

### O modal (HTML)

```html
<div id="img-viewer-modal" class="hidden fixed inset-0 z-[9999] flex items-center justify-center p-4"
    style="background:rgba(0,0,0,0.92);">
    <button onclick="closeImgViewer()"
        class="absolute top-4 right-4 text-white hover:text-gray-300 transition text-4xl z-10 leading-none"
        aria-label="Fechar" style="background:none;border:none;cursor:pointer;padding:8px;line-height:1;">
        <i class="fas fa-times"></i>
    </button>
    <div onclick="closeImgViewer()"
        class="absolute inset-0 w-full h-full cursor-pointer" style="background:none;border:none;" aria-label="Fechar"></div>
    <div class="relative z-10 max-w-5xl w-full flex flex-col items-center" style="pointer-events:none;">
        <img id="img-viewer-content" src="" alt=""
            class="max-h-[85vh] max-w-full object-contain rounded-lg shadow-2xl"
            style="pointer-events:auto;cursor:default;">
        <p id="img-viewer-caption" class="text-white text-center mt-4 text-sm opacity-80 max-w-xl"></p>
    </div>
</div>
```

### Funções JavaScript

```javascript
function openImgViewer(src, alt) {
    const modal = document.getElementById('img-viewer-modal');
    const img = document.getElementById('img-viewer-content');
    const caption = document.getElementById('img-viewer-caption');
    if (!modal || !img) return;
    img.src = src;
    img.alt = alt || '';
    if (caption) caption.textContent = alt || '';
    modal.classList.remove('hidden');
    document.body.style.overflow = 'hidden';
}

function closeImgViewer() {
    const modal = document.getElementById('img-viewer-modal');
    const img = document.getElementById('img-viewer-content');
    if (!modal) return;
    modal.classList.add('hidden');
    document.body.style.overflow = '';
    if (img) img.src = '';
}

document.addEventListener('keydown', function(e) {
    if (e.key === 'Escape') closeImgViewer();
});
```

### Uso nas capas do site público

```html
<img src="${ebook.cover_url || 'https://placehold.co/300x450/eeeeee/999999?text=Capa'}"
     alt="${ebook.title || 'Capa'}"
     class="w-full h-auto object-cover rounded shadow-sm mb-2 cursor-pointer"
     style="cursor:zoom-in;"
     onclick="event.stopPropagation(); openImgViewer(this.src, this.alt);"
     onerror="openImgViewer('https://placehold.co/300x450/eeeeee/999999?text=Sem+Capa', this.alt);">
```

## Placeholders por contexto

| Contexto | Placeholder URL |
|---|---|
| Capa normal (fallback) | `https://placehold.co/300x450/eeeeee/999999?text=Capa` |
| Sem capa (erro) | `https://placehold.co/300x450/eeeeee/999999?text=Sem+Capa` |

## Regra prática — quando usar src swap vs lightbox

| Contexto | Abordagem |
|---|---|
| Admin popup com miniaturas | `onerror` → src swap direto |
| Site público, e-books | Lightbox `openImgViewer()` |

**Lição aprendida (30/04/2026):** O Álvaro rejeitou o lightbox no admin. Antes de implementar, perguntar "como deve ficar quando estiver corrigido?" — resposta esperada: "placeholder na miniatura".
