---
name: z-library-download
description: Download books from Z-Library using browser automation + curl with session cookies
triggers: [z-library, 1lib, download epub, download pdf]
tags: [z-library, web-scraping, epub, curl, browser-automation]
---

# Z-Library Download — Browser Automation + Curl

## Context
The Z-Library (pt.z-lib.fm / pt.1lib.sk) blocks direct API downloads. Files are served via JavaScript-triggered sessions. This skill documents the working approach discovered through trial and error.

## Cookie-Based Download Method

### Step 1: Login via browser to get cookies
```
Navigate to https://pt.z-lib.fm/login
Fill email: bianinhoclaw@gmail.com
Fill password: @BianinhoZLib2026!xK9
Click login button
Wait for page to load
```

### Step 2: Navigate to book page
Get the book's page (e.g., `https://pt.z-lib.fm/book/zZ2DOmbMgE/title.html`)

### Step 3: Extract download URL
From the page snapshot, find the download link — looks like:
- `/dl/mr5P25e6Dn` (the hash after `/dl/`)

### Step 4: Download with cookies
```bash
curl -L -s \
  -o ~/KnowledgeBase/downloads/book_name.epub \
  -w "HTTP: %{http_code} | SIZE: %{size_download} | TIME: %{time_total}s" \
  -H "Cookie: bsrv=<bsrv>; siteLanguage=pt; remix_userkey=<userkey>; remix_userid=<userid>; selectedSiteMode=books" \
  -H "User-Agent: Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36" \
  "https://pt.z-lib.fm/dl/<hash>"
```

To get fresh cookies from browser console:
```javascript
JSON.stringify({bsrv: document.cookie.match(/bsrv=([^;]+)/)?.[1], userkey: document.cookie.match(/remix_userkey=([^;]+)/)?.[1], userid: document.cookie.match(/remix_userid=([^;]+)/)?.[1]})
```

## Critical: URL May Be Outdated — Always Search First

The link the user shares (e.g. `pt.1lib.sk/book/nvJb9k26vq/...`) is often outdated, broken, or on a domain that's rate-limited (503/522). **DO NOT trust the URL directly.**

**Always do this instead:**
1. Search for the book by title on `https://pt.z-lib.fm`
2. Use the FIRST result from the search — it will have the current correct book ID and domain
3. Use the download link FROM that page (e.g. `/dl/KgrzLR0YM9`)

The book's download hash changes per session — what worked before may not work now. Fresh search = fresh working link.

**Common redirect patterns after login:**
- Clicking book link from library → redirects to homepage (URL stable, content not loaded)
- Clicking book link from search results → same redirect issue
- **Always navigate manually** to the book's URL after login: `https://pt.z-lib.fm/book/<id>/title.html`

### HTTP 503 / 522 (Server overloaded)
- Wait 15-30 seconds and retry
- The Z-Library CDN gets rate-limited; persistence wins
- Try alternate domain: `pt.1lib.sk` vs `pt.z-lib.fm` — one may work when the other is down
- Can retry up to 3-4 times with increasing delays (15s, 20s, 30s)

### HTTP 200 but size ~20KB (HTML — 3 distinct causes, verified in production)
**Cause A — Token expired:** Download hash from previous session is invalid.
**FIX**: Navigate to book page → click download link → capture new `/dl/<hash>` from page URL.

**Cause B — Wrong domain:** Hash from `pt.1lib.sk` fails on `pt.z-lib.fm` and vice versa.
**FIX**: After domain switch, always get fresh download hash from that domain's book page.

**Cause C — Session cookie missing (`remix_userkey`/`remix_userid` absent):** Download returns login HTML.
**FIX**: Login → immediately capture fresh cookies via browser console → navigate to book page → download.

### Reliable workflow (tested across 8+ books, Apr 2026)
1. **Login** → immediately get fresh cookies via browser console (before any navigation)
2. **Search** for book title on Z-Library homepage
3. **Use first result** from search — it always has current book ID and working download hash
4. **Navigate directly** to book's URL: `https://pt.z-lib.fm/book/<id>/title.html`
5. **Download** with fresh cookies + hash from page
6. **Verify** with `file` and `ls -lh`

Why this works: the `/dl/<hash>` changes every login AND every domain. Searching first guarantees you get the correct current book ID + a fresh download hash on the domain you're using.

### HTTP 200 but file is HTML (wrong content) — 3 distinct causes
**Cause A — Token expired (~9-50KB HTML):**
The download hash (`/dl/<hash>`) is session-scoped. If the session changed (new login, different browser), the hash becomes invalid. Even with valid cookies, expired hash returns HTML error page.
**FIX**: Navigate to book page → click download link again → get FRESH download hash from URL → retry with fresh cookies AND fresh hash.

**Cause B — Domain mismatch (~52KB HTML):**
The download hash is domain-specific. A hash from `pt.1lib.sk/dl/XXX` may work on `pt.1lib.sk` but fail (404) on `pt.z-lib.fm`, or vice versa. If one domain returns 503/522, try the other AND use the download hash from that domain's page.
**FIX**: After switching domains, navigate to the book page on the new domain to get a fresh download hash.

**Cause C — Session cookie missing (~52KB HTML):**
After login, the browser needs the `remix_userkey` and `remix_userid` cookies for downloads. If these are missing (e.g., session didn't persist), downloads return login page HTML.
**FIX**: Get fresh cookies via browser console immediately after login, before any navigation.

**Verification always required:**
```bash
file ~/KnowledgeBase/downloads/book.epub
ls -lh ~/KnowledgeBase/downloads/book.epub
```
- Real EPUB: `EPUB document`, typically 500KB-5MB
- HTML error: `HTML document`, <100KB (usually 9-52KB)

### File size too small (bytes)
- Usually means a redirect/error page was downloaded
- Check with `file <filename>` to confirm it's a real EPUB/PDF
- Retry flow: get fresh cookies → navigate to book page → capture new dl hash → curl again

### Session expired mid-download
- Get fresh cookies: navigate to the book page, open browser console and run:
```javascript
JSON.stringify({cookies: document.cookie})
```
- Extract: `bsrv`, `remix_userkey`, `remix_userid`

### Books marked "Descarregados" (Downloaded) — same process required
- Library shows the book but download hash has expired — returns HTML, not the file
- After login: click "A minha biblioteca" → book link redirects to homepage (known bug)
- **FIX**: Manually navigate to the book's URL after login: `https://pt.z-lib.fm/book/<id>/title.html`
- The book's ID is stable; only the `/dl/<hash>` expires
- Verified with: Pai Rico Pai Pobre, O Investidor Inteligente, Quem Pensa Enriquece — all "Descarregados" but required fresh session + fresh hash

### Fast workflow (minimize session expiry)
1. Login → immediately get fresh cookies via browser console
2. Navigate to book page manually
3. Capture download hash from snapshot
4. Execute curl with cookies + hash
5. Verify with `file` command

Session expires in ~1-2 minutes of inactivity. Work fast.

### Session expiration handling
- When session expires: clicking any book link redirects to `/login?redirectUrl=...`
- After login: page often redirects to profile/library instead of the intended book
- **Fix**: manually navigate to the book's URL after login
- The session can expire mid-session if idle for ~1-2 minutes

### EPUB Structure Issue: Books with Duplicate Content

Some EPUB files (notably Robert Greene's titles) contain TWO copies of the book embedded:
1. A short TOC/sample version (first ~100-300 chars per chapter)
2. The full actual content (starts after the 2nd occurrence of "PREFÁCIO")

If you extract text and get suspiciously small chunks (50-300 chars per section), the EPUB likely has this dual-layer structure. **Fix**: After extracting, search for the 2nd occurrence of "PREFÁCIO" (or similar repeating marker) and use that position as the true content start.

Example from "As 48 leis do poder":
- First PREFÁCIO at position ~19K → TOC/summary
- Second PREFÁCIO at position ~39K → FULL CONTENT
- "LEI 1:" appears at positions 106 AND 1.3M — the second is the real chapter start
- "LEI X" headers in the full version are ALL CAPS without colon after number

**Regex pattern for law-book headers (full version, after 2nd PREFÁCIO)**:
```python
lei_pattern = re.compile(r'LEI (\d{1,2})\s+([A-ZÀ-ÚÇÃÕÂÊÎÔÛÄËÏÖÜ\- –.,;:!?\'\"]+?)\s+JULGAMENTO')
```
This captures law number and name up to the "JULGAMENTO" marker. Verified on "As 48 leis do poder" (48 laws).

**Verification**: After chunking, check chunk sizes. Real content produces ~800-1200 char chunks. TOC/sample produces ~50-300 char garbage.

**HTTP 522 (Cloudflare — server overloaded)**:
- Returns SIZE=15 and exit_code=0 (no curl error, but file is HTML error)
- Wait 15-30 seconds, get fresh cookies + navigate to book page again for new hash
- Retry up to 3x with increasing delay

## Verified Working Cookies (as of 2026-04-15)
```
bsrv=9dcf0b42f839f47b77089dc126a26aa6  # changes frequently — always get fresh
siteLanguage=pt
remix_userkey=1e8ad0fcb9799e3f1b2ada7050c1dae3
remix_userid=48157419
selectedSiteMode=books
```
Note: `bsrv` changes on each login. Always get fresh cookies via browser console:
```javascript
JSON.stringify({cookies: document.cookie})
```
Extract: `bsrv`, `remix_userkey`, `remix_userid`.

## Download Limits
- Z-Library allows ~10 downloads/day on free tier
- Monitor usage to avoid hitting limits
- Book marked as "Descarregados" (Downloaded) persists in library

## Verified Books Downloaded (2026-04-15)
| Título | Autor | Formato | Editora / Ano | Notas |
|---|---|---|---|---|
| Pai Rico, Pai Pobre (20 anos) | Kiyosaki | EPUB 4.6MB | Alta Books | "Descarregados" — fresh session required |
| Os segredos da mente milionária | Eker | EPUB 946KB | Sextante | Hash expirou — usar primeiro resultado da pesquisa |
| Como organizar sua vida financeira | Cerbasi | EPUB 2.9MB | Elsevier 2012 | |
| O homem mais rico da Babilônia | Clason | EPUB 1.6MB | Harper Collins 2022 | "Descarregados" |
| O investidor inteligente | Graham | EPUB 3.6MB | | "Descarregados" |
| Quem pensa enrichece - O Legado | Hill | EPUB 2.1MB | 28 de maio 2018 | "Descarregados" — 522 retry funcionou |

## File Verification + Summary Detection
Always verify downloaded file:
```bash
file ~/KnowledgeBase/downloads/book.epub
ls -lh ~/KnowledgeBase/downloads/book.epub
```
- Real EPUB: `EPUB document`, typically 500KB-5MB
- HTML error: `HTML document`, <100KB (usually 9-52KB)
- Summary: `EPUB document`, <200KB or <100K chars total

### ⚠️ Armadilha: Livros que são Resumos/Summaries
Muitos títulos no Z-Library (especialmente não-ficção popular) devolvem **resumos de 30-70 páginas** em vez do livro completo. Isto já aconteceu com:
- "Never Split the Difference" (68 páginas — resumo "in 30 minutes")
- "The Power of Habit" (17 partes, 45K chars — resumo "in 30 minutes")
- "Story Intelligence" (resumo vs. livro completo)

**Como detectar ANTES de processar:**
```python
# Verificar tamanho total
import sys, re, zipfile
sys.path.insert(0, '/home/alvarobiano/KnowledgeBase')

# Para EPUB: usar zipfile directo (mais fiável que ebooklib)
path = '/tmp/book.epub'
texts = []
with zipfile.ZipFile(path) as z:
    for name in z.namelist():
        if name.endswith(('.xhtml', '.html')):
            content = z.read(name).decode('utf-8', errors='ignore')
            text = re.sub(r'<[^>]+>', ' ', content)
            text = re.sub(r'\s+', ' ', text).strip()
            if len(text) > 50:
                texts.append(text)

total = sum(len(t) for t in texts)
parts = len(texts)
print(f"EPUB: {parts} partes, {total} chars total")
# Completo non-fiction: >300K chars. Resumo: <100K chars
if total < 100_000:
    print("⚠️  POSSÍVEL RESUMO — não vectorizar sem confirmar")
```

**Regra prática:** Se um livro parece curto (<100K chars para non-fiction, <50K para paper) E o título é de um livro famoso → verificar se é resumo antes de vectorizar.

## Known Summary Books on Z-Library (2026-04-28)
