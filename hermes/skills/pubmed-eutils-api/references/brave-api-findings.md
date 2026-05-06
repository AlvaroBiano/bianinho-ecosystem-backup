# Brave Search API — findings from session 04/05/2026

## Status

Configured in `~/.hermes/.env` as `BRAVE_SEARCH_API_KEY=BSA46HZI...` — works fine.

## Brave News API (gratuita, 2000 queries/mês)

**Endpoint:** `GET https://api.search.brave.com/res/v1/news/search`

**Funciona com free tier** — retorna notícias reales com `page_age` (ISO date).

```bash
curl -s -H "Accept: application/json" \
     -H "X-Subscription-Token: $BRAVE_SEARCH_API_KEY" \
     "https://api.search.brave.com/res/v1/news/search?q=endometriosis+women+2026&count=10"
```

Retorna JSON com `results[]` — cada item tem:
- `title`, `url`, `description`, `page_age`, `meta_url.netloc`

## Brave Web Search API (requer plano pago)

**Endpoint:** `GET https://api.search.brave.com/res/v1/search`

**Retorna 301 redirect** (location: api-dashboard.search.brave.com) — não funciona no tier gratuito.

## Armadilha: `freshness=pd` não funciona

Testado: com `freshness=pd` → apenas 1 resultado (horóscopo).
Sem `freshness` → 20 resultados relevantes.

**Solução:** buscar sem freshness, filtrar por `page_age` no código.

## Exemplos de queries testadas (04/05/2026)

```python
# News API query para saúde feminina
q = "endometriosis OR breast cancer OR menopause OR PCOS women health 2026"
# Retornou 20 resultados, incluindo BBC, Nature, Yale Medicine, etc.

# Cross-check query (usar título da notícia como query)
q = "endometriosis cancer risk women medical 2026"
```

## Limites da News API

- Max `count` por request: 20
- Rate limit: 2.000 queries/mês (free tier)
- Não permite busca por data específica (só `freshness` que é inútil)
- Filter `page_age` no client-side é suficiente para filtrar notícias < 48h
