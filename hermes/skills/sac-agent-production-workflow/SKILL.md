---
name: sac-agent-production-workflow
description: Clone SAC Agent production to GitHub, establish local dev clone, audit Flask admin via browser-first approach. Use when Álvaro asks to work on/modify/backup the SAC Admin dashboard.
triggers:
  - Álvaro asks to clone, backup, or modify the SAC admin dashboard
  - Starting any SAC admin development task
  - Before touching local sac_agent code when Álvaro says "check production" or "put on GitHub"
---

# SAC Agent — Production Workflow

## Core Principle: Browser-First
**ALWAYS inspect the production system via browser before touching any local code or making assumptions about what exists.**

Failing to do this leads to working on wrong projects (e.g., `sac-admin-dashboard-BACKUP`) while the real system (`~/.hermes/sac_agent/`) is ignored.

---

## System Architecture (what's real)

### Production = SAC Agent (Flask)
- **Local endpoint**: `http://localhost:5123`
- **Public URL**: `https://sacbot.masterclasslife.com.br` (via cloudflared tunnel)
- **Code location**: `~/.hermes/sac_agent/`
- **GitHub repo**: `AlvaroBiano/sac-agent`
- **Cloudflared tunnel**: routes `sacbot.masterclasslife.com.br` → `localhost:5123`

### Two Entry Points (critical — don't confuse them!)
- **Raiz `/`**: Widget de chat do chatbot (público) — NÃO tem login admin aqui
- **`/admin/login`**: Painel admin com credenciais — users tente aceder `/` e reclame que "login não funciona"
  → **Sempre informar o utilizador para ir a `/admin/login`**

### NOT the real system
- `~/sac-admin-dashboard-BACKUP/` — old/incomplete project, ignore it completely
- Any work on port 5124 admin is NOT the real SAC Agent admin

### Separate Admin Dashboard (port 5124)
- Self-contained Flask app in `~/sac-admin-dashboard-BACKUP/`
- Runs independently on port 5124
- Credentials: `admin@metodoten.com.br` / `t3rAp32026!`
- Different codebase from SAC Agent

---

## Pages in Production SAC Agent Admin

| Page | URL | Description |
|------|-----|-------------|
| Dashboard | `/admin` | Stats (leads, conversas, Q&As), leads table, bulk delete |
| Kanban | `/kanban` | 6-stage pipeline: novo → qualificado → conversa → whatsapp → matriculado → desistente |
| UTM Builder | `/utm-builder` | UTM link generator with source tracking |
| Q&A Perf | `/admin/qa` | Performance table per Q&A (disparos, sucesso, gaps) |
| Gaps | `/admin/gaps` | Questions that had no matching Q&A |
| Perfil | `/admin/perfil` | Admin profile management — template `perfil.html` was missing, created 27/04/2026 |

---

## Workflow: Clone Production to GitHub Backup

```
1. Access production via browser: https://sacbot.masterclasslife.com.br/admin
   (credentials: admin / trocar123)
2. Inspect all pages to confirm feature set
3. Clone GitHub repo to backup:
   git clone https://github.com/AlvaroBiano/sac-agent.git /tmp/sac-agent-github-backup
4. Copy current production files to backup:
   cp ~/.hermes/sac_agent/sac_agent.py ~/.hermes/sac_agent/sac_db.py ~/.hermes/sac_agent/sac_leads.db /tmp/sac-agent-github-backup/
   cp -r ~/.hermes/sac_agent/templates/* /tmp/sac-agent-github-backup/templates/
5. Commit and push from backup dir:
   cd /tmp/sac-agent-github-backup
   git add <modified files>
   git commit -m "Production backup YYYY-MM-DD"
   git push origin master
```

## GitHub Push When Branches Have Diverged

**Symptom:** `git push` fails with `! [rejected] master -> master (fetch first)` — both local and remote have commits the other doesn't.

**Diagnosis first:**
```bash
git log --oneline origin/master -5   # what remote has that local doesn't
git log --oneline HEAD -5           # what local has that remote doesn't
```

**Then decide strategy:**
- If remote = old backup with LESS work than local → use `--theirs` for conflicts (keep remote changes, discard local stales)
- If remote = newer work that local needs → merge remote first, then resolve conflicts

**Workflow for diverged branches:**
```bash
git checkout -- <conflicting-files>        # discard local conflict markers
git merge <remote-commit-hash>             # merge remote into local
# resolve conflicts: use --ours or --theirs per file based on which is newer
git add <resolved-files>
git commit -m "Merge: remote + local fixes"
git push origin master
```

**What happened in 27/04 session:** remote `35420f0` had multi-user system but was missing local fixes (Q&A typo `renderQA KPIs`, nav CSS, Perfil template). Local `873e135` had the fixes but missing multi-user. Merged: kept remote's `sac_agent.py` (multi-user + fixes together), kept local's templates (newer fixes). Result: complete system with all features.

---

## Workflow: Local Development Clone

```
1. If ~/sac-agent-local/ already exists:
   cd ~/sac-agent-local && git stash && git pull origin master
2. If first time:
   git clone https://github.com/AlvaroBiano/sac-agent.git ~/sac-agent-local
3. Make changes in ~/sac-agent-local/ ONLY — never touch ~/.hermes/sac_agent/
4. Test locally (SAC Agent already running on port 5123)
5. When approved by Álvaro: push to GitHub from ~/sac-agent-local/
6. Deploy: copy modified files to ~/.hermes/sac_agent/
7. Restart service: systemctl --user restart sac-agent
```

---

## Critical Rule: Work LOCAL FIRST — Never Modify Production Directly

Álvaro's default instruction is "tudo localmente primeiro." This means:
1. Clone GitHub to `~/sac-agent-local/`
2. Develop and test there
3. Only after Álvaro approves → push to GitHub → copy to `~/.hermes/sac_agent/`
4. **Never** `write_file` or `patch` files in `~/.hermes/sac_agent/` directly unless explicitly authorized

When I accidentally modified `~/.hermes/sac_agent/sac_agent.py` directly instead of `~/sac-agent-local/`, I caused confusion about which environment was being changed.

**If in doubt → ask "Queres que faça localmente primeiro?" before touching production code.**

---

## Critical Rule: Service Restart After Code Changes

The SAC Agent runs as a systemd user service. Python code changes in `~/.hermes/sac_agent/` are NOT picked up until the service restarts:

```bash
systemctl --user restart sac-agent
```

**Symptom of forgetting**: routes return 404 even though they exist in the code file.

---

## Admin Credentials

- **Login page URL**: `https://sacbot.masterclasslife.com.br/admin/login` (NÃO a raiz `/`)
- **Credentials**: `admin@metodoten.com.br` / `t3rAp32026!`
- **Password storage**: bcrypt hash in `sac_leads.db → admin_users.password`
- **Auth system**: JWT-like token via `make_token()` / `parse_token()` (NOT the old HMAC system)

## Debugging Missing Templates (404 on existing route)

When a Flask route exists but returns 404:
1. Check if the template file exists: `ls ~/.hermes/sac_agent/templates/perfil.html`
2. Check what filename the route renders: `render_template("perfil.html")`
3. If template is missing → create it using `sac-admin-design-system` CSS values as reference
4. Restart service: `systemctl --user restart sac-agent`

**Known missing template**: `perfil.html` for `/admin/perfil` route — was created manually in 27/04/2026.

## Structural Bug Found: Routes After app.run()

The SAC Agent has `app.run()` in the middle of the file (around line 1735) with routes defined both before AND after it. Routes after `app.run()` are dead code — not registered by Flask.

**Why it happened:** The codebase evolved — initial routes were placed before `app.run()`, then later more routes (admin auth, perfil, convites, users) were added after it, thinking `app.run()` was at the end.

**How to diagnose:**
```bash
grep -n "^@app.route\|^if __name__" ~/.hermes/sac_agent/sac_agent.py
# Any @app.route AFTER "if __name__" = dead code
```

**Fix (both production and clone):**
1. Move the entire `if __name__ == "__main__":` block (with `app.run()`) to the END of the file, after ALL route definitions
2. Check for duplicate route definitions (same URL + endpoint name appearing twice)
3. Check for `NameError: name 'render_template' is not defined` — add `render_template` to the Flask import line
4. Restart service: `systemctl --user restart sac-agent`

**Why test_client() doesn't reveal this:** `test_client()` processes requests in-process without calling `app.run()`. So routes after `app.run()` appear to work in tests but fail on the real server.

## Admin Login Field Bug: `{ username }` vs `{ login }`

The admin-login.html form sends `{ username }` but the Flask route expects `{ login }`. This causes:
- Login API returns 200 OK ✅
- But the frontend check `if (d.ok)` may not match the response structure
- Login appears to work but redirect never happens

**Fix in admin-login.html:**
```javascript
// ❌ Wrong
body: JSON.stringify({ username: u, password: p }),
// ✅ Correct
body: JSON.stringify({ login: u, password: p }),
```

## Dotenv Note
The SAC Agent (`~/.hermes/sac_agent/`) does NOT use `dotenv` — environment variables come exclusively from the systemd service environment. If you add a `.env` file, it will be ignored. Variables must be set in the systemd service file or at service startup.

---

## Key Files
- `~/.hermes/sac_agent/sac_agent.py` — main Flask app with all routes
- `~/.hermes/sac_agent/sac_db.py` — database layer
- `~/.hermes/sac_agent/sac_leads.db` — SQLite database (leads, conversas, approved_qa, etc.)
- `~/.hermes/sac_agent/sac_persuasao.py` — persuasion engine
- `~/.hermes/sac_agent/templates/` — HTML templates (admin, kanban, qa, gaps, etc.)

## GitHub Token
Available at `~/.hermes/.env` as `GITHUB_TOKEN=***`. Use to push:
```bash
git remote set-url origin https://${GITHUB_TOKEN}@github.com/AlvaroBiano/sac-agent.git
```
