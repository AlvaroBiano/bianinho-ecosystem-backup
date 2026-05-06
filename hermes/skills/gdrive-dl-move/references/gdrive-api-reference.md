# Google Drive API — Sessão 30/04/2026

## OAuth Desktop App Flow (completo)

Token guardado em `~/.hermes/google_token.json`. Expira ~1h. Refresh Token dura ~7 dias.

**⚠️ Chave do token é `token`, NÃO `access_token`** (OAuth Desktop app devolve `{token: "...", refresh_token: "..."}`).

### Refresh token (sem google-auth lib)

```python
import json, requests

with open('/home/alvarobiano/.hermes/google_token.json') as f:
    t = json.load(f)
with open('/home/alvarobiano/.hermes/google_client_secret.json') as f:
    secret = json.load(f)

r = requests.post('https://oauth2.googleapis.com/token', data={
    'client_id': secret['installed']['client_id'],
    'client_secret': secret['installed']['client_secret'],
    'refresh_token': t['refresh_token'],
    'grant_type': 'refresh_token'
})
nt = r.json()
t['token'] = nt['access_token']
t['expiry'] = nt.get('expiry', t['expiry'])
with open('/home/alvarobiano/.hermes/google_token.json', 'w') as f:
    json.dump(t, f, indent=2)
```

### Re-autenticação completa (refresh token também expirou)

```bash
# 1. Gerar URL
cd ~/KnowledgeBase && source venv/bin/activate
PYTHONPATH=~/.hermes/hermes-agent python3 \
  ~/.hermes/skills/productivity/google-workspace/scripts/setup.py --auth-url

# 2. Álvaro abre link no browser (bianinhoclaw@gmail.com), autoriza
#    URL retorno: http://localhost:1/?code=4/0AeoWuM_RyGjkpk_...

# 3. Extrair código (entre code= e &scope) e trocar por token
PYTHONPATH=~/.hermes/hermes-agent python3 \
  ~/.hermes/skills/productivity/google-workspace/scripts/setup.py \
  --auth-code "4/0AeoWuM_RyGjkpk_..."
```

## Listar ficheiros — API GET

```python
r = requests.get(
    'https://www.googleapis.com/drive/v3/files',
    headers={'Authorization': f'Bearer {token}'},
    params={
        'q': f"'{folder_id}' in parents and trashed=false",
        'pageSize': 50,
        'fields': 'files(id,name,mimeType,size)',
        'orderBy': 'name'
    }
)
files = r.json().get('files', [])
```

⚠️ ERRO COMUM: Usar POST em vez de GET → 400 "Invalid field selection files".
⚠️ ERRO COMUM: No `fields`, escrever `id,name` sem o wrapper `files(...)` → 400.

## PATCH move — SILENCIOSAMENTE IGNORADO (não é Z-Library!)

```python
# PATCH devolve 200 mas NÃO move o ficheiro — confirmado 30/04/2026
r = requests.patch(
    f'https://www.googleapis.com/drive/v3/files/{file_id}',
    headers={'Authorization': f'Bearer {token}'},
    json={
        'addParents': [dest_folder_id],
        'removeParents': [src_folder_id]
    }
)
# Status 200 → IGNORAR. Confirmar sempre:
r_check = requests.get(
    f'https://www.googleapis.com/drive/v3/files/{file_id}?fields=id,parents',
    headers={'Authorization': f'Bearer {token}'}
)
current = r_check.json().get('parents', [])
# Se current continua igual → move falhou silenciosamente
```

**Causa real**: Não é Z-Library. Os ficheiros são de ownership plena (owners=bianinhoclaw@gmail.com). O Drive API ignora `addParents`/`removeParents` silenciosamente quando a hierarquia de pastas envolve certain configurations. O `200 OK` é um false positive.

**⚠️ NUNCA confiar no status 200 do PATCH para confirmar move. Confirmar sempre com GET /files/{id}?fields=parents.**

**Solução definitiva**: Download → UploadMultipart → Delete. Script verificado em produção abaixo.

## UploadMultipart — script verificado (30/04/2026)

Este padrão foi testado e funciona para qualquer ficheiro, qualquer pasta:

```python
import json, os, requests, time

TOKEN_FILE = '/home/alvarobiano/.hermes/google_token.json'
SECRET_FILE = '/home/alvarobiano/.hermes/google_client_secret.json'

def get_access():
    with open(TOKEN_FILE) as f: t = json.load(f)
    from datetime import datetime, timezone
    exp = datetime.fromisoformat(t['expiry'].replace('Z', '+00:00'))
    if datetime.now(timezone.utc) > exp:
        with open(SECRET_FILE) as f: secret = json.load(f)
        r = requests.post('https://oauth2.googleapis.com/token', data={
            'client_id': secret['installed']['client_id'],
            'client_secret': secret['installed']['client_secret'],
            'refresh_token': t['refresh_token'],
            'grant_type': 'refresh_token'
        })
        if r.status_code == 200:
            nt = r.json()
            t['token'] = nt['access_token']
            t['expiry'] = nt.get('expiry', t['expiry'])
            with open(TOKEN_FILE, 'w') as f: json.dump(t, f, indent=2)
    return t['token']

def upload_multipart(local_path, file_name, mime_type, dest_folder_id):
    boundary = 'boundary_' + str(os.urandom(16).hex())
    with open(local_path, 'rb') as f:
        file_content = f.read()
    metadata_json = json.dumps({
        'name': file_name,
        'parents': [dest_folder_id],
        'mimeType': mime_type
    }, ensure_ascii=False)
    body = (
        f'--{boundary}\r\n'
        f'Content-Type: application/json; charset=UTF-8\r\n\r\n'
        f'{metadata_json}\r\n'
        f'--{boundary}\r\n'
        f'Content-Type: {mime_type}\r\n\r\n'
    ).encode('utf-8') + file_content + f'\r\n--{boundary}--\r\n'.encode('utf-8')
    r = requests.post(
        'https://www.googleapis.com/upload/drive/v3/files?uploadType=multipart',
        headers={
            'Authorization': f'Bearer {get_access()}',
            'Content-Type': f'multipart/related; boundary={boundary}'
        },
        data=body,
        timeout=300
    )
    if r.status_code == 200:
        return r.json().get('id')
    raise Exception(f'Upload falhou: {r.status_code} {r.text[:200]}')
```

**Testado em produção**: 10 livros (18-32MB cada) — todos movidos com sucesso de "RAG - Livros a Processar" para "Processados".

## Estrutura do Google Drive — Álvaro (pós-limpeza 30/04/2026)

```
Google Drive (bianinhoclaw@gmail.com)
├── 📁 RAG - Livros a Provessar/     ← pasta vazia
├── 📁 Processados/                   ← 10 livros AI (vectorizados no RAG)
├── 📄 💎 PRD: Mentoria Financeira de Sucesso
├── 📄 Referências Científicas — Câncer de Tireoide (67 estudos)
├── 📄 12 Doenças Causadas pelo Relacionamento Abusivo - Café com Terapia
├── 📄 12 Doenças - Relacionamento Abusivo (Formatado)
├── 📄 12 Doenças - Relacionamento Abusivo (Para Formatar)
├── 📄 afiliados_saude_emocional.md
├── 📄 Teste Completo Bianinho
└── 📄 sessao-22-04-2026 (2 ficheiros)
```

**Nota**: A pasta "Processados" com os livros está DENTRO de "RAG - Livros a Provessar". Existe também uma "Processados" na raiz (vazia). A hierarquia aninhada é a causa provável do PATCH silencioso.

**IDs actuais (30/04/2026)**:
- `RAG - Livros a Provessar`: `1Dvk2Ty-xsRerRf4ZpZpeQqP6TTlt8JRe`
- `Processados` (dentro de RAG): `1Qaqe5DL9rE2tbL_KrvlAdYfwvMSjwPUA`

## Como verificar se livro está no RAG (LanceDB)

```python
import lancedb
db = lancedb.connect('/home/alvarobiano/KnowledgeBase/knowledge_db')
all_books = set()
for tbl_name in db.list_tables():
    tbl = db.open_table(tbl_name)
    df = tbl.to_pandas()
    if 'source' in df.columns:
        all_books.update(df['source'].unique())
print(f'{len(all_books)} livros no RAG')
for b in sorted(all_books): print(f'  {b}')
```

**Tabelas**: `api`, `chunks` (64,802 chunks), `default`, `metodoten` (6,559 chunks), `prd_collection`

## Fluxo completo de organização do Drive

```
1. Listar todos os ficheiros (GET /files)
2. Consultar LanceDB — identificar quais livros já estão vectorizados
3. Para livros já no RAG: Download → UploadMultipart para Processados → Delete original
4. Apagar contentores vazios (PaperclipContent, duplicados, Untitled)
5. Verificar resultado final com GET /files
```

⚠️ NUNCA tentar PATCH move — retorna 200 mas não persiste. Usar sempre download-upload-delete.

## Scopes OAuth

```
https://mail.google.com/
https://www.googleapis.com/auth/drive
https://www.googleapis.com/auth/calendar
https://www.googleapis.com/auth/contacts.readonly
https://www.googleapis.com/auth/documents
https://www.googleapis.com/auth/spreadsheets
```
