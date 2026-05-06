---
name: git-merge-conflict-production-restore
description: Git merge conflict resolution when local production is the source of truth — never let stale remote code overwrite production fixes. Use when merging remote backups with local production, or when tempted to use --theirs/--ours without verifying which is actually production.
---

# Git Merge: Production as Source of Truth

## Trigger
Use when:
- Doing `git merge` or `git pull` and conflicts arise between local and remote
- Remote was a "backup" of an older state while local has newer production fixes
- You are tempted to use `--theirs` or `--ours` to resolve conflicts without verifying which is actually production

## The Problem
During merge, `--theirs` means "remote branch" and `--ours` means "local branch". But:
- Remote backup may contain OLD code (multi-user system, hardcoded credentials, old bugs)
- Local production may contain NEWER fixes (auth fixes, bug corrections, new templates)
- Arbitrarily choosing `--theirs` or `--ours` can overwrite production with stale code

## The Rule
**Production local code is ALWAYS the source of truth.** Never overwrite it without explicitly verifying:
1. What commit is currently running in production?
2. Does `--theirs` have code that was NEVER in production?
3. Does `--ours` have the production fixes you made today?

## Step-by-Step Resolution

### Step 1: Identify the source of truth
```bash
# Local production commit (what's running NOW)
git log --oneline -3

# Remote backup commit
git log --oneline origin/master -3
```

### Step 2: Compare specific files BEFORE resolving
```bash
# Check which version has the production fixes
git diff <remote-commit>:<file> <local-commit>:<file> | grep "render_template\|ADMIN_USER\|renderQAKPIs"
```

### Step 3: Verify what's actually in production on disk
```bash
grep "render_template\|ADMIN_USER\s*=" ~/.hermes/sac_agent/sac_agent.py
```

### Step 4: If local is production truth, restore it
```bash
# Restore a specific file from the known-good production commit
git show <production-commit>:<path> > <path>
```

### Step 5: Add restored files and complete merge
```bash
git add <restored-files>
git commit -m "Merge: description — restored production code from <commit>"
git push
```

## Anti-Patterns
- ❌ `git checkout --theirs sac_agent.py` without checking which is production
- ❌ `git checkout --ours sac_agent.py` without checking which is production
- ❌ Assuming the remote "backup" is newer/better than local production
- ❌ Not verifying the running code on disk after a merge

## What Actually Happened (27/04/2026)
- Remote `35420f0` was a backup but contained OLD code (hardcoded `ADMIN_USER`, old auth)
- Local `873e135` had production fixes (correct auth, `render_template`, `renderQAKPIs`)
- Used `--theirs sac_agent.py` which overwrote production with stale code
- Fix: `git show 873e135:sac_agent.py > sac_agent.py` restored production

## Verification After Restore
Always test after restoring:
```bash
# Restart the service to pick up new code
systemctl --user restart sac-agent

# Quick API check
curl -s -o /dev/null -w "%{http_code}" http://localhost:5123/admin/qa-stats

# Login test (check actual DB credentials)
sqlite3 ~/.hermes/sac_agent/sac_leads.db "SELECT login FROM admin_users LIMIT 1;"
```
