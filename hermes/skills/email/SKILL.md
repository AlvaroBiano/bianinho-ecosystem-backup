---
name: email
description: Email management for bianinhoclaw@gmail.com — send, read, and manage emails autonomously using OAuth2 or App Passwords
category: productivity
tags: [email, gmail, oauth, automation]
---

# Email Manager — bianinhoclaw@gmail.com

## Setup Required

### Option 1: App Password (Simpler)
1. Go to: https://myaccount.google.com/apppasswords
2. Create a new App Password for "Mail"
3. Give it a name (e.g., "Hermes Agent")
4. Copy the 16-character password
5. Tell me the password so I can configure

### Option 2: OAuth2 (More Secure) — Preferred
1. Go to: https://console.cloud.google.com/apis/credentials
2. Create OAuth 2.0 Client ID (Desktop app)
3. Download the JSON file and save as `~/.hermes/email_credentials.json`
4. **CRITICAL STEP:** Go to "OAuth consent screen" and add test users:
   - Click "Add users" in Test users section
   - Add: `bianinhoclaw@gmail.com` and `alvarobiano@gmail.com`
   - OR publish the app immediately
5. Without this step, you'll get: "access_denied - Hermes Agent is in testing mode"
6. Tell me when done so I can complete the setup

**Authorization URL format (for reference):**
```
https://accounts.google.com/o/oauth2/auth?client_id=<ID>&response_type=code&redirect_uri=urn%3Aietf%3Awg%3Aoauth%3A2.0%3Aoob&scope=...&access_type=offline&prompt=consent
```

## Credentials (current setup)
- **Active method:** App Password via GPG-encrypted file
- **GPG file:** `~/.hermes/email_creds.gpg` — contains `{"email": "...", "app_password": "..."}`
- **To decrypt:** `gpg --decrypt ~/.hermes/email_creds.gpg`
- OAuth token file: `~/.hermes/email_token.json` (NOT active — OAuth flow incomplete)

## How to Send Email (App Password method)

The `send_email.py` script uses SMTP with GPG-decrypted App Password. It tries GPG first, then falls back to OAuth. Example using SMTP directly:

```python
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import subprocess
import json

# 1. Decrypt credentials
result = subprocess.run(['gpg', '--decrypt', '/home/alvarobiano/.hermes/email_creds.gpg'],
                        capture_output=True, text=True, timeout=10)
creds = json.loads(result.stdout)
EMAIL = creds['email']
APP_PASSWORD = creds['app_password']

# 2. Send
msg = MIMEMultipart('mixed')
msg['From'] = EMAIL
msg['To'] = to_email
msg['Subject'] = subject
msg.attach(MIMEText(body, 'plain', 'utf-8'))

with smtplib.SMTP('smtp.gmail.com', 587) as server:
    server.starttls()
    server.login(EMAIL, APP_PASSWORD)
    server.send_message(msg)
```

## What I can do with email
- Send emails autonomously
- Read inbox and unread messages
- Search emails
- Mark as read/unread
- Reply to emails
- Receive and validate security codes

## Scripts
- `scripts/email_manager.py` — Python script for email operations
- `scripts/email_oauth_setup.py` — OAuth2 setup wizard
- `scripts/send_email.py` — Simple email sender

## Usage
```bash
# Send email
python3 ~/.hermes/skills/email/scripts/send_email.py --to "example@email.com" --subject "Hello" --body "Message"

# List recent emails
python3 ~/.hermes/skills/email/scripts/email_manager.py --list

# Read specific email
python3 ~/.hermes/skills/email/scripts/email_manager.py --read <message_id>
```
