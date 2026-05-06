---
name: sac-utm-tracking
description: UTM tracking completo para SAC Bot — captura da URL, salvamento em DB, dashboard de origens
tags: [sac-bot, utm, analytics, flask]
authors: Bianinho
created: 2026-04-25
---

# SAC Bot — UTM Tracking (Full-Stack)

## Quando usar

Implementar tracking de origem (UTM) em sistema de captura de leads 100% own (Flask puro, sem Typebot/landing page externa).

## Arquitetura

```
Landing Page (index.html)
  → URLSearchParams → JavaScript extrai utm_source/utm_medium/utm_campaign/primeira_url
  → sessionStorage persiste se lead der refresh
  → POST /webhook/sac/init com payload estendida

Backend (sac_agent.py + sac_db.py)
  → webhook aceita UTMs no body JSON
  → criar_lead() insere UTMs no DB
  → First-touch: se lead existe sem UTMs, preenche
  → get_origens_stats() agrega para dashboard
```

## Passos de Implementação

### 1. Front-end — capturar UTMs da URL

```javascript
function capturarUTMs() {
    const params = new URLSearchParams(window.location.search);
    return {
        utm_source: params.get('utm_source') || '',
        utm_medium: params.get('utm_medium') || '',
        utm_campaign: params.get('utm_campaign') || '',
        primeira_url: window.location.href.split('?')[0]
    };
}

// Salvar no sessionStorage ao iniciar
const utms = capturarUTMs();
sessionStorage.setItem('sac_utm_source', utms.utm_source);
sessionStorage.setItem('sac_utm_medium', utms.utm_medium);
sessionStorage.setItem('sac_utm_campaign', utms.utm_campaign);
sessionStorage.setItem('sac_primeira_url', utms.primeira_url);

// Enviar no webhook
body: JSON.stringify({ nome, telefone, ddd, ...capturarUTMs() })
```

### 2. Backend — aceitar no webhook

No `webhook_sac_init()`:
```python
utm_source = data.get("utm_source", "").strip()
utm_medium = data.get("utm_medium", "").strip()
utm_campaign = data.get("utm_campaign", "").strip()
primeira_url = data.get("primeira_url", "").strip()

lead, is_novo = sac_db.buscar_ou_criar_lead(
    nome, telefone, ddd,
    utm_source=utm_source, utm_medium=utm_medium,
    utm_campaign=utm_campaign, primeira_url=primeira_url
)
```

### 3. DB — colunas na tabela leads

```sql
ALTER TABLE leads ADD COLUMN utm_source TEXT DEFAULT '';
ALTER TABLE leads ADD COLUMN utm_medium TEXT DEFAULT '';
ALTER TABLE leads ADD COLUMN utm_campaign TEXT DEFAULT '';
ALTER TABLE leads ADD COLUMN primeira_url TEXT DEFAULT '';
```

### 4. First-touch attribution

Se lead já existe mas não tem UTMs, preenche (não sobrescreve):
```python
if lead and not lead.get("utm_source") and utm_source:
    conn.execute("""UPDATE leads SET utm_source=?, utm_medium=?,
                       utm_campaign=?, primeira_url=? WHERE id=?""",
                  (utm_source, utm_medium, utm_campaign, primeira_url, lead["id"]))
```

## Verificação

```bash
python3 -c "
import sac_db
s = sac_db.get_origens_stats()
print('UTM sources:', s['por_source'])
"
```

## Notas Importantes

- **Álvaro NÃO USA Typebot** — toda a estrutura SAC Bot é Flask puro (Bianinho construiu)
- UTMs só chegam se link os tiver na URL — ex: `https://sacbot.masterclasslife.com.br/?utm_source=instagram`
- Se não há UTMs, aparece como "direto" (comportamento padrão)
- DDD já existe no schema — não precisa adicionar
