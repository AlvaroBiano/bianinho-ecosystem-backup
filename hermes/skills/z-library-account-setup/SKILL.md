---
name: z-library-account-setup
description: Create and manage a Z-Library account for the Bianinho agent — registration, email verification via IMAP, and login workflow
category: productivity
tags: [z-library, registration, email-verification, imap]
---

# Z-Library Account Setup — Bianinho

## Account Credentials
- **Email:** bianinhoclaw@gmail.com
- **Senha:** @BianinhoZLib2026!xK9
- **Nickname:** Bianinho
- Email app password (GPG): `ziau riwl ttef fjau` (stored in `~/.hermes/email_creds.gpg`)

## Registration Workflow

### Step 1: Navigate to registration
```
https://pt.z-lib.fm/registration
```
Fill form: email, password, nickname → click "Criar uma conta"

### Step 2: Get verification code via IMAP
```python
import imaplib, email
from email.header import decode_header

app_password = "ziauriwlttefjua"  # no spaces, from GPG

mail = imaplib.IMAP4_SSL("imap.gmail.com")
mail.login("bianinhoclaw@gmail.com", app_password)
mail.select("INBOX")

status, messages = mail.search(None, "ALL")
email_ids = messages[0].split()

for eid in reversed(email_ids):
    status, msg_data = mail.fetch(eid, "(RFC822)")
    msg = email.message_from_bytes(msg_data[0][1])
    if "z-lib" in str(msg).lower():
        # Extract code from HTML body
        if msg.is_multipart():
            for part in msg.walk():
                if part.get_content_type() == "text/plain":
                    body = part.get_payload(decode=True).decode("utf-8", errors="replace")
                    break
        else:
            body = msg.get_payload(decode=True).decode("utf-8", errors="replace")
        
        # Find 4-digit code in HTML
        import re
        match = re.search(r'(\d{4})', body)
        if match:
            code = match.group(1)
            print(f"Code: {code}")
        break
mail.logout()
```

### Step 3: Enter code in browser
- Z-Library uses 4 separate single-digit input fields
- Enter each digit individually in the correct field

### Step 4: Confirm
Click "Confirmar e criar uma conta"

## Download de Livros — Método Confirmado

### O problema critical: Browserbase não salva ficheiros
⚠️ **Browser automation (browser_navigate + browser_click) NÃO funciona para downloads.**
O browser do Browserbase intercepta o download mas NÃO salva no disco. O resultado é sempre HTML.
**SOLUÇÃO**: Usar SEMPRE `curl` via terminal para baixar.

### Passo 1: Login no browser
1. browser_navigate("https://pt.z-lib.fm/login")
2. browser_type email → browser_type senha → browser_click Entrar
3. Verificar que a página mostra ícone de utilizador logado (sem botão "Entrar")

### Passo 2: Obter o link de download
1. browser_navigate à página do livro
2. Identificar o link `/dl/<hash>` no snapshot (ref=eN)
3. NÃO clicar — apenas extrair o hash

### Passo 3: Baixar com curl
```bash
cd ~/Downloads
curl -L -o "<nome_livro>.<ext>" "https://pt.z-lib.fm/dl/<HASH>"
```
O link `/dl/<hash>` содержит toda a autenticação necessária — NÃO precisa de cookies explícitos.

### Passo 4: Verificar
```bash
file ~/Downloads/<nome_livro>.<ext>
# PDF: "PDF document, version X.Y"
# EPUB: "EPUB document"
# HTML: "HTML document" → ERRO
```
- Se HTML → verificar se é "limite esgotado" ou sessão expirada
- Se PDF/EPUB → OK, proceed para processing

### Limite de 10/dia
- **Plano BASIC: 10 downloads por IP por dia** — não é por conta
- Quando atingido: `curl` retorna HTML de 51KB com "O limite diário foi esgotado"
- Não é erro de sessão ou cookies — é o contador de IP
- Testar: `grep -o "O limite[^<]*" ~/Downloads/<ficheiro>`
- **4 livros baixados em sucesso (17/04/2026)**: Atomic Habits, The Body Keeps the Score, O Poder do Hábito, Mindset — depois disso, 6 tentativas resultaram em HTML "limite esgotado"
- O limite resetar às 00:00 UTC — deixar para o dia seguinte

### Sequência confirmada (17/04/2026)
1. Login com sucesso (bianinhoclaw@gmail.com)
2. curl -L com URL `/dl/<hash>` → funciona enquanto IP não atingir 10
3. Após 10: tudo volta HTML "O limite diário foi esgotado"
4. browser_click no botão de download → NÃO ajuda (browser não salva ficheiros)
5. pdfplumber necessário para PDFs: `uv pip install pdfplumber` no venv do KnowledgeBase

### ISBNs de Referência
- `9780857197696` = The Psychology of Money (inglês, Harriman House, Morgan Housel)
- `9788595086257` = A psicologia financeira (PT-BR, HarperCollins Brasil, Morgan Housel)

## Fixes Found During Setup
1. **Email confusion**: Own email is `bianinhoclaw@gmail.com` (not `bianinho@gmail.com`)
2. **App password**: Stored in GPG as `ziau riwl ttef fjau` — join with no spaces = `ziauriwlttefjau`
3. **himalaya email tool**: Not installed on this server
4. **email skill scripts**: Fail due to missing `google` module — use raw imaplib instead
5. **Browser field ref**: Use `browser_navigate` first to get fresh refs when page state is uncertain
6. **Z-Library download via curl**: FUNCIONA quando o IP não atingiu o limite — usar `curl -L -o <ficheiro> "https://pt.z-lib.fm/dl/<HASH>"` (o hash do link de download содержит toda a autenticação necessária)
7. **PDF falhou (52 chars)**: `pdfplumber` não estava no venv do KnowledgeBase → instalar com `uv pip install pdfplumber`
8. **Download limit 10/dia**: plano basic limita a 10 downloads por IP/dia; após isso, ficheiros vêm como HTML (51KB) em vez de EPUB — não é erro de autenticação
9. **Browserbase não salva downloads**: browser_navigate + browser_click NO link de download NÃO funciona — o browser não escreve ficheiros no disco. Usar SEMPRE `curl -L -o` via terminal com o link `/dl/<hash>`
