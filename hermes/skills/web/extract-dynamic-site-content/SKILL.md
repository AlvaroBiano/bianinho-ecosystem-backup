---
name: extract-dynamic-site-content
description: Extrair conteúdo estruturado de sites com dados carregados via JavaScript/JSON
triggers: [web scraping, extrair site dinamico, dados dinamicos, JSON source]
---
# Extrair Conteúdo de Sites com Dados Dinâmicos (JSON)

## Quando usar
Quando o HTML de um site mostra "Carregando..." ou conteúdo vazio, mas os dados reais são carregados por JavaScript via fetch/XHR.

## Fluxo

1. **Procurar URL do JSON** — Analisar HTML e JS do site:
   ```bash
   curl -s "https://SITE.com/" | grep -i "json\|fetch\|db\.json\|data/"
   curl -s "https://SITE.com/js/main.js" | grep -i "fetch\|json\|db"
   ```
   Padrão comum: `const res = await fetch('data/db.json')`

2. **Testar o JSON** diretamente no browser ou com curl

3. **Mapear estrutura** — Tipicamente tem chaves como: `modules`, `faqs`, `testimonials`, `ebooks`, `plans`, `features`

4. **Extrair com Python** — Ler o JSON, limpar HTML tags (`<b>`, `<p>`, etc.), gerar markdown

## Armadilha
Não fazer scraping do HTML visível — é placeholder. Ir ao JSON fonte que alimenta o JavaScript.

## Caso real: alvarobiano.com.br
- JSON: `https://www.alvarobiano.com.br/data/db.json`
- Conteúdo: 40 cadeiras, 25 FAQs, ebooks, planos, depoimentos
- O HTML principal está quase vazio (placeholder) — os dados vêm do JSON
