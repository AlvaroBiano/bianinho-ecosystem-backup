#!/usr/bin/env python3
"""Download and move files from Google Drive via OAuth2."""
import json
import subprocess
import sys
import os
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request

TOKEN_FILE = os.path.expanduser("~/.hermes/google_token.json")
SCOPES = ["https://www.googleapis.com/auth/drive"]

def get_access_token():
    creds = Credentials.from_authorized_user_info(
        json.load(open(TOKEN_FILE)),
        scopes=SCOPES
    )
    if creds.expired:
        creds.refresh(Request())
    return creds.token

def download_file(file_id, output_path):
    import urllib.request
    token = get_access_token()
    url = f"https://www.googleapis.com/drive/v3/files/{file_id}?alt=media"
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {token}"})
    with urllib.request.urlopen(req, timeout=120) as response:
        data = response.read()
    with open(output_path, "wb") as f:
        f.write(data)
    print(f"Downloaded: {output_path} ({len(data)/1024:.1f} KB)")
    return len(data)

def move_file_to_folder(file_id, folder_id):
    """Move a file to a different folder."""
    import urllib.request
    token = get_access_token()
    
    # Get current parents
    url = f"https://www.googleapis.com/drive/v3/files/{file_id}?fields=parents"
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {token}"})
    with urllib.request.urlopen(req) as response:
        current = json.loads(response.read())
    
    # Update parents
    body = json.dumps({
        "addParents": [folder_id],
        "removeParents": current.get("parents", [])
    }).encode()
    
    # ⚠️ method="PATCH" must be explicit — urllib defaults to POST otherwise
    patch_url = f"https://www.googleapis.com/drive/v3/files/{file_id}"
    patch_req = urllib.request.Request(
        patch_url, 
        data=body,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        },
        method="PATCH"
    )
    with urllib.request.urlopen(patch_req) as response:
        result = json.loads(response.read())
    print(f"Moved {file_id} to folder {folder_id}")
    return result

if __name__ == "__main__":
    action = sys.argv[1]
    if action == "download":
        file_id = sys.argv[2]
        output_path = sys.argv[3]
        download_file(file_id, output_path)
    elif action == "move":
        file_id = sys.argv[2]
        folder_id = sys.argv[3]
        move_file_to_folder(file_id, folder_id)
