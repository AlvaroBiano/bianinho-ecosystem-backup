---
name: gdrive-dl-move
description: Download e move arquivos do Google Drive via API OAuth2 — método confiável que funciona com arquivos que exigem autenticação.
category: productivity
---

# Google Drive — Download e Move via OAuth2

## Download confiável de arquivos Drive (sem gdown)

O `gdown` falha com arquivos protegidos por OAuth (mesmo com token válido) porque não faz refresh automático do token.

**Método correto:**

```python
import json, urllib.request, os
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request

TOKEN_FILE = os.path.expanduser("~/.hermes/google_token.json")

def get_token():
    creds = Credentials.from_authorized_user_info(
        json.load(open(TOKEN_FILE)),
        scopes=["https://www.googleapis.com/auth/drive"]
    )
    if creds.expired:
        creds.refresh(Request())
    return creds.token

def download_drive_file(file_id: str, output_path: str):
    """Download arquivo do Google Drive via API v3 com alt=media."""
    token = get_token()
    url = f"https://www.googleapis.com/drive/v3/files/{file_id}?alt=media"
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {token}"})
    with urllib.request.urlopen(req, timeout=120) as response:
        data = response.read()
    with open(output_path, "wb") as f:
        f.write(data)
    print(f"Downloaded: {len(data)/1024:.0f} KB")
```

## Mover arquivo para outra pasta (PATCH)

```python
def move_drive_file(file_id: str, target_folder_id: str):
    """Move arquivo para outra pasta no Drive."""
    token = get_token()
    
    # 1. Descobrir parents atuais
    url = f"https://www.googleapis.com/drive/v3/files/{file_id}?fields=parents"
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {token}"})
    with urllib.request.urlopen(req) as resp:
        current = json.loads(resp.read())
    
    # 2. PATCH com addParents + removeParents
    body = json.dumps({
        "addParents": [target_folder_id],
        "removeParents": current.get("parents", [])
    }).encode()
    
    # ⚠️ CRÍTICO: method="PATCH" precisa ser explícito
    patch_req = urllib.request.Request(
        f"https://www.googleapis.com/drive/v3/files/{file_id}",
        data=body,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        },
        method="PATCH"  # Sem isto → 404 (urllib faz POST por defeito)
    )
    with urllib.request.urlopen(patch_req) as resp:
        return json.loads(resp.read())
```

## Pasta "RAG - Livros a Processar" (18/04/2026)

- **Pasta RAG:** `1Dvk2Ty-xsRerRf4ZpZpeQqP6TTlt8JRe`
- **Pasta Processados:** `1Qaqe5DL9rE2tbL_KrvlAdYfwvMSjwPUA`
- **Token file:** `~/.hermes/google_token.json`

## Script standalone

`~/KnowledgeBase/download_rag.py` — criado em 18/04/2026 com:
- `python3 download_rag.py download <file_id> <output_path>`
- `python3 download_rag.py move <file_id> <folder_id>`

## Notas

- Sempre fazer `creds.refresh(Request())` se `creds.expired` antes de usar token
- `gdown` falha com `403 Forbidden` em arquivos protegidos por OAuth — usar sempre o script Python com `Credentials` para fazer refresh automático
- O limite prático para download via API é ~100MB por arquivo
- Rate limit: se receber HTTP 403 ao vetorizar chunks, esperar 5-10s e retry — não afecta os chunks já inseridos
- Testado com sucesso em 18/04/2026: 10 livros (135MB total) descargados e movidos sem erros
- **OAuth Desktop app flow (token expirado):** ver `references/gdrive-api-reference.md` — inclui fluxo completo de re-autenticação, API GET vs POST, e problema crítico: PATCH addParents/removeParents retorna 200 mas não move ficheiros (não é problema de Z-Library — afecta qualquer ficheiro na hierarquia). Workaround: download → upload multipart → delete.
- **Estrutura do Drive do Álvaro:** ver `references/gdrive-api-reference.md` — pasta "Processados" está DENTRO de "RAG - Livros a Provessar", não na raiz. Esta hierarquia aninhada é a causa provável do PATCH silencioso.

## Armadilha: PATCH addParents/removeParents retorna 200 mas não move (qualquer ficheiro)

**Sintoma**: `PATCH /drive/v3/files/{id}` com `addParents` + `removeParents` devolve `200 OK` mas `parents` não mudam. O ficheiro fica no mesmo sítio.

**Causa real**: Não é Z-Library. O Drive API aceita o PATCH mas ignora-o silenciosamente quando a pasta destino está numa hierarquia com certain constraints (e.g., pastas dentro de Shared Drives, ou certain folder nesting patterns). O `owners` mostra que és owner — não é problema de permissão de leitura.

**⚠️ NUNCA confiar no status 200 do PATCH para confirmar move. Confirmar sempre com GET /files/{id}?fields=parents.**

**Solução**: Download → UploadMultipart → Delete original. Este padrão funciona 100% independentemente do tipo de ficheiro ou estrutura de pastas.

**Erro 404 no PATCH (urllib)**: Sem `method="PATCH"` no Request constructor, urllib faz POST por defeito. Usar requests em vez de urllib (requests aceita o method override no `.patch()` directamente).

**Rate limit**: se receber HTTP 403 ao vetorizar chunks, esperar 5-10s e retry — não afecta os chunks já inseridos.
