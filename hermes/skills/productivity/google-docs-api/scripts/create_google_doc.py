#!/usr/bin/env python3
"""Cria Google Doc com referências científicas. Exemplo funcional completo."""
import json, os, re, time, binascii
from pathlib import Path

TOKEN_FILE = Path.home() / ".hermes/google_token.json"
CLIENT_SECRET = Path.home() / ".hermes/google_client_secret_final.json"

def load_token():
    with open(TOKEN_FILE) as f:
        return json.load(f)

def refresh_access_token(refresh_token_str):
    import urllib.request, urllib.parse
    cs = json.loads(open(CLIENT_SECRET).read())["installed"]
    data = urllib.parse.urlencode({
        "client_id": cs["client_id"],
        "client_secret": cs["client_secret"],
        "refresh_token": refresh_token_str,
        "grant_type": "refresh_token",
    }).encode()
    req = urllib.request.Request(
        "https://oauth2.googleapis.com/token",
        data=data,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    with urllib.request.urlopen(req) as resp:
        new = json.loads(resp.read())
        new["refresh_token"] = refresh_token_str
        with open(TOKEN_FILE, "w") as f:
            json.dump(new, f)
        return new["access_token"]

def get_headers():
    token_data = load_token()
    token_mtime = TOKEN_FILE.stat().st_mtime
    if time.time() - token_mtime > token_data.get("expires_in", 3600) - 60:
        access_token = refresh_access_token(token_data["refresh_token"])
    else:
        access_token = token_data["access_token"]
    return {"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"}

def create_document(title):
    import urllib.request
    headers = get_headers()
    body = {"title": title}  # ← FLAT, nao {"properties": {"title": ...}}
    req = urllib.request.Request(
        "https://docs.googleapis.com/v1/documents",
        data=json.dumps(body).encode(),
        headers=headers,
        method="POST",
    )
    with urllib.request.urlopen(req) as resp:
        result = json.loads(resp.read())
        print(f"Documento criado: {result['documentId']}")
        return result["documentId"]

def insert_text(document_id, content, index=1):
    import urllib.request
    headers = get_headers()
    requests_payload = [{"insertText": {"location": {"index": index}, "text": content}}]
    body = {"requests": requests_payload}
    req = urllib.request.Request(
        f"https://docs.googleapis.com/v1/documents/{document_id}:batchUpdate",
        data=json.dumps(body).encode(),
        headers=headers,
        method="POST",
    )
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read())

def parse_markdown_to_text(md_content):
    """Converte markdown para texto simples legível."""
    lines = md_content.split("\n")
    result = []
    for line in lines:
        if line.startswith("# ") or line.startswith("## "):
            result.append("")
            result.append(line.replace("#", "").strip())
            result.append("")
        elif line.startswith("- **"):
            match = re.match(r"- \*\*(.+?)\*\*: (.+)", line)
            if match:
                result.append(f"  {match.group(1)}: {match.group(2).strip()}")
        elif "- **Full Text:**" in line or "- **PubMed:**" in line:
            m = re.search(r"\[(.+?)\]\((.+?)\)", line)
            if m:
                result.append(f"  -> {m.group(1)}: {m.group(2)}")
        elif line.strip():
            result.append(line.strip())
    return "\n".join(result)

def main():
    import sys
    if len(sys.argv) < 3:
        print("Uso: create_google_doc.py <markdown_file> <doc_title>")
        sys.exit(1)
    md_file, doc_title = sys.argv[1], sys.argv[2]
    with open(md_file, encoding="utf-8") as f:
        md_content = f.read()
    text = parse_markdown_to_text(md_content)
    print(f"Texto: {len(text)} caracteres")
    doc_id = create_document(doc_title)
    insert_text(doc_id, text)
    print(f"https://docs.google.com/document/d/{doc_id}")

if __name__ == "__main__":
    main()
