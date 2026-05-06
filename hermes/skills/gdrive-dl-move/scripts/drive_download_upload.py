#!/usr/bin/env python3
"""
Google Drive: Download → UploadMultipart → Delete original.
Workaround para PATCH addParents/removeParents que retorna 200 mas não move.
Verificado em produção 30/04/2026: 10 livros movidos (18-32MB cada).

Uso:
    python3 drive_download_upload.py                    # move todos da RAG para Processados
    python3 drive_download_upload.py --list             # apenas listar
    python3 drive_download_upload.py --single <file_id> # mover um ficheiro específico
"""
import json, os, requests, time, argparse

WORKDIR = '/tmp/books_work'
os.makedirs(WORKDIR, exist_ok=True)

TOKEN_FILE  = '/home/alvarobiano/.hermes/google_token.json'
SECRET_FILE = '/home/alvarobiano/.hermes/google_client_secret.json'

# IDs do Drive (30/04/2026)
RAG_FOLDER_ID   = '1Dvk2Ty-xsRerRf4ZpZpeQqP6TTlt8JRe'
PROCESSADOS_ID  = '1Qaqe5DL9rE2tbL_KrvlAdYfwvMSjwPUA'

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

def list_folder(folder_id):
    r = requests.get(
        'https://www.googleapis.com/drive/v3/files',
        headers={'Authorization': f'Bearer {get_access()}'},
        params={
            'q': f"'{folder_id}' in parents and trashed=false",
            'pageSize': 50,
            'fields': 'files(id,name,mimeType,size)'
        }
    )
    return [f for f in r.json().get('files', [])
            if 'folder' not in f['mimeType']]

def download_file(file_id, local_path):
    r = requests.get(
        f'https://www.googleapis.com/drive/v3/files/{file_id}?alt=media',
        headers={'Authorization': f'Bearer {get_access()}'},
        timeout=300, stream=True
    )
    if r.status_code != 200:
        raise Exception(f'Download falhou: {r.status_code}')
    with open(local_path, 'wb') as f:
        for chunk in r.iter_content(chunk_size=131072):
            f.write(chunk)

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
        data=body, timeout=300
    )
    if r.status_code != 200:
        raise Exception(f'Upload falhou: {r.status_code} {r.text[:200]}')
    return r.json().get('id')

def delete_file(file_id):
    r = requests.delete(
        f'https://www.googleapis.com/drive/v3/files/{file_id}',
        headers={'Authorization': f'Bearer {get_access()}'}
    )
    return r.status_code in [200, 204]

def move_one(item):
    file_id, file_name, mime_type = item['id'], item['name'], item['mimeType']
    safe_name = file_name.replace('/', '_')
    local_path = os.path.join(WORKDIR, safe_name)
    print(f'>>> {file_name}')
    print(f'    Download...', end=' ', flush=True)
    download_file(file_id, local_path)
    print(f'OK ({os.path.getsize(local_path)/1024/1024:.1f}MB)')
    print(f'    Upload...', end=' ', flush=True)
    new_id = upload_multipart(local_path, file_name, mime_type, PROCESSADOS_ID)
    print(f'OK (ID: {new_id})')
    print(f'    Delete original...', end=' ', flush=True)
    ok = delete_file(file_id)
    print('OK' if ok else f'FALHOU {ok}')
    os.remove(local_path)
    print(f'    Feito: {file_name}\n')
    time.sleep(0.5)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--list', action='store_true')
    parser.add_argument('--single')
    args = parser.parse_args()

    if args.list:
        items = list_folder(RAG_FOLDER_ID)
        print(f'Livros na pasta RAG: {len(items)}\n')
        for it in items:
            print(f'  {it["name"]}')
        return

    items = list_folder(RAG_FOLDER_ID)
    print(f'A processar {len(items)} livros...\n')
    for item in items:
        try:
            move_one(item)
        except Exception as e:
            print(f'    ERRO: {e}\n')

    import shutil
    shutil.rmtree(WORKDIR, ignore_errors=True)
    print('=== CONCLUÍDO ===')

if __name__ == '__main__':
    main()
