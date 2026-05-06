---
name: gdrive-upload-file
description: Upload files to Google Drive via OAuth2 API (Python) — reliable method for programmatic file delivery.
tags: [gdrive, google, upload, api, oauth2]
version: 1.0
created: 2026-04-22
author: Bianinho
---

# Google Drive — Upload de Arquivos via OAuth2 API

## Quando usar

Enviar arquivos ao usuário via GDrive em vez de anexar na conversa ou deixar no terminal. Sempre que o usuário pedir um arquivo, usar esta skill para fazer upload.

**Regra do Álvaro:** Sempre entregar arquivos via GDrive (nunca anexar na conversa).

## Script de Upload

```python
import json, urllib.request, os

TOKEN_FILE = os.path.expanduser("~/.hermes/google_token.json")

def get_token():
    from google.oauth2.credentials import Credentials
    from google.auth.transport.requests import Request
    creds = Credentials.from_authorized_user_info(
        json.load(open(TOKEN_FILE)),
        scopes=["https://www.googleapis.com/auth/drive"]
    )
    if creds.expired:
        creds.refresh(Request())
    return creds.token

def upload_file(filepath, filename, folder_id=None):
    token = get_token()
    metadata = {"name": filename, "mimeType": "text/markdown"}
    if folder_id:
        metadata["parents"] = [folder_id]

    boundary = "boundary123"
    metadata_json = json.dumps(metadata)
    file_content = open(filepath, "rb").read()

    body = (
        f"--{boundary}\r\n"
        f"Content-Type: application/json\r\n\r\n"
        f"{metadata_json}\r\n"
        f"--{boundary}\r\n"
        f"Content-Type: text/plain\r\n\r\n"
    ).encode() + file_content + f"\r\n--{boundary}--\r\n".encode()

    url = "https://www.googleapis.com/upload/drive/v3/files?uploadType=multipart"
    req = urllib.request.Request(
        url,
        data=body,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": f"multipart/related; boundary={boundary}"
        },
        method="POST"
    )

    with urllib.request.urlopen(req, timeout=60) as resp:
        result = json.loads(resp.read())
        print(f"Uploaded! File ID: {result.get('id')}")
        print(f"Name: {result.get('name')}")
        return result

# Upload
result = upload_file("/path/to/file.md", "nome_do_arquivo.md")
```

## Notas Importantes

1. **Token file:** `~/.hermes/google_token.json` — credentials OAuth2 do GDrive
2. **mimeType:** usar `text/markdown` para .md, `application/pdf` para PDF, `text/plain` para .txt. Para auto-detect: `application/octet-stream`
3. **Pasta optional:** passar `folder_id` para enviar direto para uma pasta específica
4. **Testar auth primeiro:** listar arquivos da root para confirmar que token está válido
5. **`gdown` NÃO funciona** com arquivos protegidos OAuth — sempre usar este script Python com `google.oauth2.credentials.Credentials` + refresh automático

## Rede: execute_code vs terminal vs ctx_execute

`execute_code` (sandbox isolada) **não consegue** alcançar `oauth2.googleapis.com` — timeout. `terminal` e `ctx_execute` (Python do servidor) **conseguem**.

Se o token está válido e não precisa de refresh, `execute_code` funciona. Se o token expirou e precisa de refresh, usar este workaround em 2 passos:

**Passo 1 — Terminal:** obter token fresco e guardar em ficheiro:
```bash
cd ~/.hermes/hermes-agent && source venv/bin/activate && python -c "
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
import json
creds = Credentials.from_authorized_user_file('/home/alvarobiano/.hermes/google_token.json')
creds.refresh(Request())
print(creds.token)
" > /tmp/gdrive_token.txt
```

**Passo 2 — ctx_execute ou terminal com curl:** usar token do ficheiro para upload:
```python
# Em ctx_execute (Python do servidor, tem rede)
import json, urllib.request
token = open('/tmp/gdrive_token.txt').read().strip()
content = open('/path/to/file.md').read()
boundary = 'boundary123xyz'
metadata = json.dumps({'name': 'nome.md', 'mimeType': 'text/plain'})
body = ('--' + boundary + '\r\nContent-Type: application/json\r\n\r\n' + metadata +
        '\r\n--' + boundary + '\r\nContent-Type: text/plain\r\n\r\n' +
        content + '\r\n--' + boundary + '--\r\n')
req = urllib.request.Request(
    'https://www.googleapis.com/upload/drive/v3/files?uploadType=multipart',
    data=body.encode('utf-8'),
    headers={'Authorization': 'Bearer ' + token, 'Content-Type': 'multipart/related; boundary=' + boundary},
    method='POST'
)
with urllib.request.urlopen(req, timeout=30) as resp:
    result = json.loads(resp.read())
    print('OK:', result.get('id'), result.get('name'))
```

**Exceção:** se o token já é válido e não expirou, `execute_code` funciona — testar primeiro antes de usar o workaround dos 2 passos.

## Verificação

```python
# Confirmar auth
token = get_token()
url = "https://www.googleapis.com/drive/v3/files?pageSize=5&fields=files(id,name)"
req = urllib.request.Request(url, headers={"Authorization": f"Bearer {token}"})
with urllib.request.urlopen(req, timeout=15) as resp:
    data = json.loads(resp.read())
    print("Auth OK:", [f['name'] for f in data.get("files", [])])
```

## Armadilhas

- Sem `creds.refresh(Request())` quando token expired → 401 Unauthorized
- Sem `method="POST"` explícito no Request → urllib faz GET por defeito → 405
- Sem `boundary` consistente no multipart body → 400 Bad Request
- Token file corrompido → recriar OAuth token via browser
