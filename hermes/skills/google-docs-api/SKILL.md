---
name: google-docs-api
description: Criar e popular Google Docs via API RESTful — workflow completo com troubleshooting de erros comuns.
category: productivity
tags:
  - google
  - google-docs
  - api
  - rest
---

# Google Docs API — Criar Documento + Inserir Conteúdo

## Descobertas Chave (trial and error)

1. **Criar documento:** API espera `{"title": title}` — NÃO `{"properties": {"title": ...}}`
2. **Inserir texto:** `batchUpdate` com `insertText` aceita payloads até ~1MB num único request
3. **Rate limit:** 429 — adicionar delay 1.5s entre chunks ou inserir tudo num request
4. **Token refresh:** Access token expira em 1h — ter refresh_token pronto

## Fluxo Completo

### 1. Setup — Arquivos Necessários

```
~/.hermes/google_client_secret_final.json  # Desktop app type
~/.hermes/google_token.json                # access_token + refresh_token
```

### 2. Refresh Token (se expirado)

```python
import urllib.request, urllib.parse, json

with open(Path.home() / ".hermes/google_client_secret_final.json") as f:
    cs = json.load(f)["installed"]

data = urllib.parse.urlencode({
    "client_id": cs["client_id"],
    "client_secret": cs["client_secret"],
    "refresh_token": REFRESH_TOKEN,
    "grant_type": "refresh_token",
}).encode()

req = urllib.request.Request(
    "https://oauth2.googleapis.com/token",
    data=data,
    headers={"Content-Type": "application/x-www-form-urlencoded"},
)
# Resposta: {access_token, expires_in, refresh_token, scope, token_type}
```

### 3. Criar Documento

```python
import urllib.request, json

headers = {"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"}

body = {"title": "Título do Documento"}  # ← FLAT, não {"properties": {"title": ...}}

req = urllib.request.Request(
    "https://docs.googleapis.com/v1/documents",
    data=json.dumps(body).encode(),
    headers=headers,
    method="POST",
)

with urllib.request.urlopen(req) as resp:
    result = json.loads(resp.read())
    doc_id = result["documentId"]
    # URL: https://docs.google.com/document/d/{doc_id}
```

### 4. Inserir Texto (request único — evitar rate limit)

```python
requests_payload = [
    {
        "insertText": {
            "location": {"index": 1},
            "text": conteudo_textual,
        }
    }
]

body = {"requests": requests_payload}

req = urllib.request.Request(
    f"https://docs.googleapis.com/v1/documents/{doc_id}:batchUpdate",
    data=json.dumps(body).encode(),
    headers=headers,
    method="POST",
)

with urllib.request.urlopen(req) as resp:
    result = json.loads(resp.read())
    # Sucesso: {'replies': [{}], 'writeControl': {...}, 'documentId': '...'}
```

## Erros Comuns

| Erro | Causa | Solução |
|------|-------|---------|
| 400 "Unknown name properties" | Body errado na criação | Usar `{"title": ...}` flat |
| 429 Too Many Requests | many requests | Inserir tudo num request ou adicionar delay 1.5s |
| 400 "Cannot find field" | Campo inexistente no schema | Verificar estrutura JSON da API |

## Scopes Necessários

```
https://www.googleapis.com/auth/documents      # escrita
https://www.googleapis.com/auth/drive.file     # criar arquivos
```

## Python Script Completo

Ver: `~/.hermes/scripts/create_thyroid_doc.py` (exemplo funcional com 67 artigos)
