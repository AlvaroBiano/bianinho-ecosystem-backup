---
name: utm-masked-url-redirect
description: Implementa URLs mascaradas UTM — formato /r/source/campaign que redireciona para landing page com UTMs preservados. Padrão usado no SAC Bot do Método TEN.
version: 1.0.0
author: Bianinho
license: MIT
metadata:
  hermes:
    tags: [UTM, redirect, Flask, marketing, URL-masking]
    created: 2026-04-25
---

# UTM Masked URL Redirect Pattern

Converte URLs longas com UTMs em links curtos e elegantes como:
```
https://dominio.com/r/instagram/lancamento_maio
```
em vez de:
```
https://dominio.com?utm_source=instagram&utm_medium=instagram&utm_campaign=lancamento_maio
```

## Arquitetura

```
/r/<source>/<campaign>
    ↓  Flask route GET /r/<source>/<campaign>
    ↓  redirect(/?utm_source=<source>&utm_medium=<source>&utm_campaign=<campaign>)
    ↓
Landing page (recebe UTMs normalmente)
```

## Implementação

### 1. Rota Flask (`sac_agent.py`)

```python
@app.route("/r/<source>/<campaign>", methods=["GET"])
def utm_redirect(source, campaign):
    """Redireciona URL mascarada /r/source/campaign → landing page com UTMs."""
    medium = request.args.get("medium", source)  # opcional: ?medium=custom
    base = "https://sacbot.masterclasslife.com.br"
    target = f"{base}?utm_source={source}&utm_medium={medium}&utm_campaign={campaign}"
    return redirect(target)
```

### 2. JS do Gerador (UTM Builder)

```javascript
// Gera URL mascarada para exibir/copiar
var maskedUrl = 'https://dominio.com/r/' + plataforma + '/' + campaign;

// Gera URL completa com UTMs (armazenada para reconstrução)
var fullUrl = 'https://dominio.com?utm_source=' + encodeURIComponent(plataforma)
    + '&utm_medium=' + encodeURIComponent(medium)
    + '&utm_campaign=' + encodeURIComponent(campaign);

// Preview mostra URL mascarada (elegante)
document.getElementById('utm-preview').textContent = maskedUrl;

// Copiar copia URL mascarada
async function copyUtmLink(idx) {
    var url = 'https://dominio.com/r/' + utmLinks[idx].source + '/' + utmLinks[idx].campaign;
    await navigator.clipboard.writeText(url);
}

// Salvamento em localStorage guarda source + campaign (não a URL inteira)
utmLinks.unshift({ source: source, campaign: campaign, url: maskedUrl });
localStorage.setItem('sac_utm_links', JSON.stringify(utmLinks));

// Lista reconstrução da URL mascarada
var maskedUrl = 'https://dominio.com/r/' + l.source + '/' + l.campaign;
```

### 3. Validação de Duplicados

```javascript
// Usar source + campaign como chave (não URL completa)
if (utmLinks.some(function(l) { return l.source === source && l.campaign === campaign; })) {
    mostrarToast('Este link já foi salvo.', 'erro');
    return;
}
```

## Padrão Dual-URL

A ideia central é separar **o que o usuário vê** da **estrutura de dados**:

| Campo | Valor |
|-------|-------|
| `source` | `instagram` (plataforma) |
| `campaign` | `lancamento_maio` |
| `medium` | `bio` (opcional, default = source) |
| `masked_url` | reconstruída como `dominio.com/r/{source}/{campaign}` |
| `full_utm_url` | reconstruída no redirect para tracking |

## Extensões Possíveis

- **Custom medium**: aceita `?medium=custom` na URL mascarada
- **Sub-campanhas**: formato `/r/<source>/<campaign>/<subcampaign>`
- **Domínio configurável**: URL base vinda de variável de ambiente
- **Click tracking**: salvar cada redirect no banco antes de redirecionar
