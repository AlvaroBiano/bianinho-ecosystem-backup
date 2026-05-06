---
name: typebot-self-hosted
description: Complete Typebot v3 self-hosted installation on Linux Mint with Docker, Cloudflare Tunnel, Google OAuth, and PostgreSQL. Includes .env traps, DB access, and OAuth setup.
tags:
  - typebot
  - docker
  - self-hosted
  - chatbot
  - cloudflare
---

# Typebot Self-Hosted Installation — Bianinho Server

## Context
Installing Typebot v3 (baptisteArno/typebot.io) on a local Linux Mint server with Docker, exposed via Cloudflare Tunnel. No billing/limits, full access.

## Server Info
- OS: Linux Mint 22.3 (Zena) = Ubuntu 24.04 (Noble)
- Docker installed: yes (sudo usermod -aG docker $USER done)
- Typebot dir: ~/typebot/
- PostgreSQL password (container): `typebot2026`
- Cloudflared: installed at /usr/local/bin/cloudflared

## Docker Setup (Linux Mint Workaround)

Mint uses "zena" codename but Docker repo needs "noble". Fix:

```bash
sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
sudo chmod a+r /etc/apt/keyrings/docker.asc
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu noble stable" | sudo tee /etc/apt/sources.list.d/docker.list
sudo apt-get update && sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
```

Without re-login: use `sg docker -c "docker compose ..."` or sudo for docker commands.

## .env Required Variables (CRITICAL)

```
ENCRYPTION_SECRET=                    # MUST be exactly 32 characters
DATABASE_URL=postgresql://postgres:typebot2026@typebot-db:5432/typebot
NODE_OPTIONS=--no-node-snapshot
NEXTAUTH_URL=http://localhost:8080
NEXT_PUBLIC_VIEWER_URL=http://localhost:8081
NEXT_PUBLIC_ADMIN_URL=http://localhost:8080
ADMIN_EMAIL=admin@example.com
DISABLE_USER_ACCOUNT_REQUIRED=true
ALLOWED_DOMAINS=*
CHATFlow_INCREASE_USAGE_QUOTA=true
MAX_BOT_INVOCATIONS_PER_MONTH=999999
MAX_ACTIVE_CHATS=999999
S3_BUCKET=typebot-storage             # CANNOT be empty
S3_ENDPOINT=https://s3.amazonaws.com  # CANNOT be empty
S3_REGION=us-east-1
NEXT_PUBLIC_IS_PRO=true
# Google OAuth (Web application type):
GOOGLE_AUTH_CLIENT_ID=...
GOOGLE_AUTH_CLIENT_SECRET=...
```

### Common .env Errors
- `ENCRYPTION_SECRET`: must be exactly ≤32 chars, not more
- `S3_BUCKET` and `S3_ENDPOINT`: empty string → error "Too small: expected string to have >=1 characters"

## Commands

```bash
cd ~/typebot
sg docker -c "docker compose up -d"   # start
sg docker -c "docker compose down"     # stop
sg docker -c "docker compose logs -f typebot-builder"  # logs
sudo docker ps  # check status
```

## Database Access (PostgreSQL inside container)

```bash
sudo docker exec typebot-typebot-db-1 sh -c 'PGPASSWORD=typebot2026 psql -U postgres -d typebot -c "SELECT * FROM \"User\";"'
```

## Cloudflare Tunnel

Quick tunnel (temporary URL, changes on restart):
```bash
cloudflared tunnel --no-autoupdate --url http://localhost:8080 > /tmp/cf.log 2>&1 &
sleep 10 && grep "trycloudflare.com" /tmp/cf.log
```

For permanent URL: need Cloudflare account with named tunnel (free tier works).

## OAuth Setup

Google OAuth requires **Web application** type (NOT Desktop app):
- Desktop app → blocked by Google in automated browsers
- Web app → redirect_uri = `http://localhost:8080/api/auth/callback/google`

Steps:
1. Google Cloud Console → APIs & Credentials → Create OAuth client ID → Web application
2. Add authorized redirect URI: `http://localhost:8080/api/auth/callback/google`
3. Add to .env: GOOGLE_AUTH_CLIENT_ID and GOOGLE_AUTH_CLIENT_SECRET
4. Restart containers

## Direct Database User Creation (if OAuth fails)

```sql
-- Connect:
sudo docker exec typebot-typebot-db-1 sh -c 'PGPASSWORD=typebot2026 psql -U postgres -d typebot'

-- Create user (all NOT NULL fields):
INSERT INTO "User" (id, name, email, "emailVerified", "onboardingCategories", "termsAcceptedAt", "preferredAppAppearance", "graphNavigation")
VALUES ('bianinho', 'Bianinho Admin', 'bianinhoclaw@gmail.com', NOW(), '[]', NOW(), 'light', 'MOUSE');

-- Create workspace:
INSERT INTO "Workspace" (id, name, icon, plan)
VALUES ('bianinho-ws', 'Bianinho Admin', '🤖', 'FREE');

-- Create membership:
INSERT INTO "MemberInWorkspace" ("userId", "workspaceId", role)
VALUES ('bianinho', 'bianinho-ws', 'ADMIN');
```

## Key Files
- ~/typebot/docker-compose.yml
- ~/typebot/.env
- ~/typebot/start.sh (sudo docker compose up -d)

---

## ◆ Google OAuth Setup — Labeled Subsection

**Source**: `typebot-self-hosted-auth/` + `typebot-self-hosted-oauth/`

### Key Requirement: Web Application OAuth Client
OAuth client must be type **"Web application"** (NOT Desktop app — Desktop gives `disallowed_useragent` error).

### Critical env vars
```
NEXTAUTH_URL=https://PUBLIC_TUNNEL_URL   # Must be public URL, NOT localhost
GOOGLE_AUTH_CLIENT_ID=...
GOOGLE_AUTH_CLIENT_SECRET=...
```

### Docker Compose — Critical: extra_hosts
Container needs `extra_hosts` for internet access:
```yaml
x-typebot-common: &typebot-common
  extra_hosts:
    - "host.docker.internal:host-gateway"
```
WITHOUT this, the container cannot reach `accounts.google.com` and OAuth fails with `fetch failed`.

### Troubleshooting OAuth
| Problem | Cause | Fix |
|---------|-------|-----|
| `fetch failed` | Container no internet | Add `extra_hosts: host-gateway` |
| `redirect_uri_mismatch` | Wrong redirect URI in Google Cloud | Add `https://TUNNEL_URL/api/auth/callback/google` |
| OAuth popup blocked | Desktop app type | Recreate as Web application |
| `NEXTAUTH_URL` wrong | Using localhost in production | Set to public tunnel URL |

### Direct DB User Creation (when OAuth works but callback fails)
```sql
-- Connect:
sudo docker exec typebot-typebot-db-1 psql -U postgres -d typebot

-- Create user:
INSERT INTO "User" (id, name, email, "emailVerified", "onboardingCategories", "termsAcceptedAt", "preferredAppAppearance", "graphNavigation")
VALUES ('bianinho', 'Bianinho Admin', 'bianinhoclaw@gmail.com', NOW(), '[]', NOW(), 'light', 'MOUSE');

-- Create workspace:
INSERT INTO "Workspace" (id, name, icon, plan)
VALUES ('bianinho-ws', 'Bianinho Admin', '🤖', 'FREE');

-- Create membership:
INSERT INTO "MemberInWorkspace" ("userId", "workspaceId", role)
VALUES ('bianinho', 'bianinho-ws', 'ADMIN');
```

---

## ◆ Troubleshooting — Labeled Subsection

**Source**: `typebot-self-hosted-troubleshooting/`

### Docker Container Connectivity Test
```bash
sudo docker exec typebot-typebot-builder-1 node -e "
const https = require('https');
['accounts.google.com','www.google.com','oauth2.googleapis.com'].forEach(d => {
  const req = https.get({hostname:d, path:'/', method:'GET', timeout:8000}, r => {
    console.log(d,'status:',r.statusCode); r.destroy();
  });
  req.on('error', e => console.log(d,'error:',e.message));
  req.on('timeout', () => { console.log(d,'TIMEOUT'); req.destroy(); });
  req.setTimeout(8000);
});
"
```

### Network Isolation Pattern
If `accounts.google.com` times out from container but works from host:
- Add `extra_hosts: - "host.docker.internal:host-gateway"` to docker-compose
- DO NOT use `network_mode: host` — breaks inter-container communication

### PostgreSQL Direct Access (via Docker)
```bash
sudo docker exec typebot-typebot-db-1 sh -c 'PGPASSWORD=typebot2026 psql -U postgres -d typebot -c "SELECT * FROM \"User\";"'
```

---

## ◆ Typebot API (v6.x) — Labeled Subsection

**Source**: `typebot-self-hosted-api/`

### Endpoints
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/typebots` | List typebots |
| GET | `/api/v1/typebots/:id` | Get typebot |
| POST | `/api/v1/typebots` | Create typebot |
| POST | `/api/v1/typebots/:id/import` | Import flow |
| PATCH | `/api/v1/typebots/:id` | Update typebot |
| POST | `/api/v1/typebots/:id/publish` | Publish |

Base URL: `https://typebot.alvarobiano.com.br`

### Auth
```bash
curl -H "Authorization: Bearer <TOKEN>" https://typebot.alvarobiano.com.br/api/v1/typebots
```

### Block Schema Requirements (v6 — very strict)
All blocks require `label`. Type discriminator must be exact:

| Block | Type Value |
|-------|-----------|
| Message | `"text"` |
| Text Input | `"text input"` |
| Choice Input | `"choice input"` |
| Webhook | `"Webhook"` |
| End | `"end"` |

### PATCH Pitfalls
- `label` is required on ALL blocks
- `events` must be `null` or omitted — array causes error
- Type discriminator: `"text"` not `"message"`, `"text input"` not `"TextInput"`

### RAG Webhook Agent
```bash
~/.hermes/agent-sac-venv/bin/python ~/.hermes/scripts/agent_sac_typebot.py
# Port: 3102
```

### OpenRouter Preferred over MiniMax
Use OpenRouter (google/gemini-3-flash-preview) instead of MiniMax for chat — MiniMax has rate limit issues.

---

## Containers
- typebot-typebot-builder-1 (port 8080)
- typebot-typebot-viewer-1 (port 8081)
- typebot-typebot-db-1 (PostgreSQL 16, port 5432 internal)
- typebot-typebot-redis-1 (Redis, port 6379 internal)
