---
name: self-improving-agent-2
description: "Captures learnings, errors, and corrections to enable continuous improvement. Use when: (1) A command or operation fails unexpectedly, (2) User corrects Hermes ('No, that's wrong...', 'Actually...'), (3) User requests a capability that doesn't exist, (4) An external API or tool fails, (5) Hermes realizes its knowledge is outdated or incorrect, (6) A better approach is discovered for a recurring task. Also review learnings before major tasks."
author: Adapted for Hermes from biocrfhkust-cloud/self-improving-agent-2
category: proativo
tags:
  - self-improvement
  - learning
  - error-tracking
  - corrections
  - knowledge-management
tools:
  - python3
  - file_read
  - file_write
---

# Self-Improvement Skill

Log learnings and errors to markdown files for continuous improvement. Coding agents can later process these into fixes, and important learnings get promoted to project memory.

## Quick Reference

| Situation | Action |
|-----------|--------|
| Command/operation fails | Log to `.learnings/ERRORS.md` |
| User corrects you | Log to `.learnings/LEARNINGS.md` with category `correction` |
| User wants missing feature | Log to `.learnings/FEATURE_REQUESTS.md` |
| API/external tool fails | Log to `.learnings/ERRORS.md` with integration details |
| Knowledge was outdated | Log to `.learnings/LEARNINGS.md` with category `knowledge_gap` |
| Found better approach | Log to `.learnings/LEARNINGS.md` with category `best_practice` |
| Simplify/Harden recurring patterns | Log/update `.learnings/LEARNINGS.md` with `Source: simplify-and-harden` and a stable `Pattern-Key` |
| Similar to existing entry | Link with `**See Also**`, consider priority bump |
| Broadly applicable learning | Promote to `USER.md`, `AGENTS.md`, and/or `.github/copilot-instructions.md` |
| Workflow improvements | Promote to `AGENTS.md` (Hermes workspace) |
| Tool gotchas | Promote to `TOOLS.md` (Hermes workspace) |
| Behavioral patterns | Promote to `SOUL.md` (Hermes workspace) |

## Hermes Setup (Recommended)

Hermes is the primary platform for this skill. It uses workspace-based prompt injection with automatic skill loading.

### Installation

The skill is installed at `~/.hermes/skills/proativo/self-improving-agent-2/`.

### Workspace Structure

Hermes injects these files into every session:

```
~/.hermes/workspace/
├── AGENTS.md          # Multi-agent workflows, delegation patterns
├── SOUL.md            # Behavioral guidelines, personality, principles
├── TOOLS.md           # Tool capabilities, integration gotchas
├── MEMORY.md          # Long-term memory (main session only)
├── memory/            # Daily memory files
│   └── YYYY-MM-DD.md
└── .learnings/        # This skill's log files
    ├── LEARNINGS.md
    ├── ERRORS.md
    └── FEATURE_REQUESTS.md
```

### Create Learning Files

```bash
mkdir -p ~/.hermes/workspace/.learnings
```

Then create the log files (or copy from `assets/`):
- `LEARNINGS.md` — corrections, knowledge gaps, best practices
- `ERRORS.md` — command failures, exceptions
- `FEATURE_REQUESTS.md` — user-requested capabilities

### Promotion Targets

When learnings prove broadly applicable, promote them to workspace files:

| Learning Type | Promote To | Example |
|---------------|------------|---------|
| Behavioral patterns | `SOUL.md` | "Be concise, avoid disclaimers" |
| Workflow improvements | `AGENTS.md` | "Spawn sub-agents for long tasks" |
| Tool gotchas | `TOOLS.md` | "Git push needs auth configured first" |

### Hermes Session History

Access conversation history from `~/.hermes/hermes_sessions.db`:

```python
import sqlite3
conn = sqlite3.connect('~/.hermes/hermes_sessions.db')
cursor = conn.cursor()
# Query recent sessions for learning opportunities
cursor.execute("SELECT content FROM sessions WHERE timestamp > datetime('now', '-7 days')")
```

### Knowledge Base Integration

Store and retrieve learnings from `~/KnowledgeBase/`:

```bash
# Query related learnings
python3 ~/KnowledgeBase/query.py --semantic "git push authentication"
```

## Logging Format

### Learning Entry

Append to `.learnings/LEARNINGS.md`:

```markdown
## [LRN-YYYYMMDD-XXX] category

**Logged**: ISO-8601 timestamp
**Priority**: low | medium | high | critical
**Status**: pending
**Area**: frontend | backend | infra | tests | docs | config

### Summary
One-line description of what was learned

### Details
Full context: what happened, what was wrong, what's correct

### Suggested Action
Specific fix or improvement to make

### Metadata
- Source: conversation | error | user_feedback
- Related Files: path/to/file.ext
- Tags: tag1, tag2
- See Also: LRN-20250110-001 (if related to existing entry)
- Pattern-Key: simplify.dead_code | harden.input_validation (optional, for recurring-pattern tracking)
- Recurrence-Count: 1 (optional)
- First-Seen: 2025-01-15 (optional)
- Last-Seen: 2025-01-15 (optional)

---
```

### Error Entry

Append to `.learnings/ERRORS.md`:

```markdown
## [ERR-YYYYMMDD-XXX] skill_or_command_name

**Logged**: ISO-8601 timestamp
**Priority**: high
**Status**: pending
**Area**: frontend | backend | infra | tests | docs | config

### Summary
Brief description of what failed

### Error
```
Actual error message or output
```

### Context
- Command/operation attempted
- Input or parameters used
- Environment details if relevant

### Suggested Fix
If identifiable, what might resolve this

### Metadata
- Reproducible: yes | no | unknown
- Related Files: path/to/file.ext
- See Also: ERR-20250110-001 (if recurring)

---
```

### Feature Request Entry

Append to `.learnings/FEATURE_REQUESTS.md`:

```markdown
## [FEAT-YYYYMMDD-XXX] capability_name

**Logged**: ISO-8601 timestamp
**Priority**: medium
**Status**: pending
**Area**: frontend | backend | infra | tests | docs | config

### Requested Capability
What the user wanted to do

### User Context
Why they needed it, what problem they're solving

### Complexity Estimate
simple | medium | complex

### Suggested Implementation
How this could be built, what it might extend

### Metadata
- Frequency: first_time | recurring
- Related Features: existing_feature_name

---
```

## ID Generation

Format: `TYPE-YYYYMMDD-XXX`
- TYPE: `LRN` (learning), `ERR` (error), `FEAT` (feature)
- YYYYMMDD: Current date
- XXX: Sequential number or random 3 chars (e.g., `001`, `A7B`)

Examples: `LRN-20250115-001`, `ERR-20250115-A3F`, `FEAT-20250115-002`

## Resolving Entries

When an issue is fixed, update the entry:

1. Change `**Status**: pending` → `**Status**: resolved`
2. Add resolution block after Metadata:

```markdown
### Resolution
- **Resolved**: 2025-01-16T09:00:00Z
- **Commit/PR**: abc123 or #42
- **Notes**: Brief description of what was done
```

Other status values:
- `in_progress` - Actively being worked on
- `wont_fix` - Decided not to address (add reason in Resolution notes)
- `promoted` - Elevated to USER.md, AGENTS.md, or .github/copilot-instructions.md

## Promoting to Project Memory

When a learning is broadly applicable (not a one-off fix), promote it to permanent project memory.

### When to Promote

- Learning applies across multiple files/features
- Knowledge any contributor (human or AI) should know
- Prevents recurring mistakes
- Documents project-specific conventions

### Promotion Targets

| Target | What Belongs There |
|--------|-------------------|
| `USER.md` | Project facts, conventions, gotchas for all agent interactions |
| `AGENTS.md` | Agent-specific workflows, tool usage patterns, automation rules |
| `.github/copilot-instructions.md` | Project context and conventions for GitHub Copilot |
| `SOUL.md` | Behavioral guidelines, communication style, principles (Hermes workspace) |
| `TOOLS.md` | Tool capabilities, usage patterns, integration gotchas (Hermes workspace) |

### How to Promote

1. **Distill** the learning into a concise rule or fact
2. **Add** to appropriate section in target file (create file if needed)
3. **Update** original entry:
   - Change `**Status**: pending` → `**Status**: promoted`
   - Add `**Promoted**: USER.md`, `AGENTS.md`, or `.github/copilot-instructions.md`

### Promotion Examples

**Learning** (verbose):
> Project uses pnpm workspaces. Attempted `npm install` but failed. 
> Lock file is `pnpm-lock.yaml`. Must use `pnpm install`.

**In USER.md** (concise):
```markdown
## Build & Dependencies
- Package manager: pnpm (not npm) - use `pnpm install`
```

**Learning** (verbose):
> When modifying API endpoints, must regenerate TypeScript client.
> Forgetting this causes type mismatches at runtime.

**In AGENTS.md** (actionable):
```markdown
## After API Changes
1. Regenerate client: `pnpm run generate:api`
2. Check for type errors: `pnpm tsc --noEmit`
```

## Recurring Pattern Detection

If logging something similar to an existing entry:

1. **Search first**: `grep -r "keyword" .learnings/`
2. **Link entries**: Add `**See Also**: ERR-20250110-001` in Metadata
3. **Bump priority** if issue keeps recurring
4. **Consider systemic fix**: Recurring issues often indicate:
   - Missing documentation (→ promote to USER.md or .github/copilot-instructions.md)
   - Missing automation (→ add to AGENTS.md)
   - Architectural problem (→ create tech debt ticket)

## Simplify & Harden Feed

Use this workflow to ingest recurring patterns from the `simplify-and-harden`
skill and turn them into durable prompt guidance.

### Ingestion Workflow

1. Read `simplify_and_harden.learning_loop.candidates` from the task summary.
2. For each candidate, use `pattern_key` as the stable dedupe key.
3. Search `.learnings/LEARNINGS.md` for an existing entry with that key:
   - `grep -n "Pattern-Key: <pattern_key>" .learnings/LEARNINGS.md`
4. If found:
   - Increment `Recurrence-Count`
   - Update `Last-Seen`
   - Add `See Also` links to related entries/tasks
5. If not found:
   - Create a new `LRN-...` entry
   - Set `Source: simplify-and-harden`
   - Set `Pattern-Key`, `Recurrence-Count: 1`, and `First-Seen`/`Last-Seen`

### Promotion Rule (System Prompt Feedback)

Promote recurring patterns into agent context/system prompt files when all are true:

- `Recurrence-Count >= 3`
- Seen across at least 2 distinct tasks
- Occurred within a 30-day window

Promotion targets:
- `USER.md`
- `AGENTS.md`
- `.github/copilot-instructions.md`
- `SOUL.md` / `TOOLS.md` for Hermes workspace-level guidance when applicable

Write promoted rules as short prevention rules (what to do before/while coding),
not long incident write-ups.

## Periodic Review

Review `.learnings/` at natural breakpoints:

### When to Review
- Before starting a new major task
- After completing a feature
- When working in an area with past learnings
- Weekly during active development

### Quick Status Check
```bash
# Count pending items
grep -h "Status\*\*: pending" .learnings/*.md | wc -l

# List pending high-priority items
grep -B5 "Priority\*\*: high" .learnings/*.md | grep "^## \["

# Find learnings for a specific area
grep -l "Area\*\*: backend" .learnings/*.md
```

### Review Actions
- Resolve fixed items
- Promote applicable learnings
- Link related entries
- Escalate recurring issues

### Detection Triggers

**Corrections** (→ learning with `correction` category):
- "No, that's not right..."
- "Actually, it should be..."
- "You're wrong about..."
- "That's outdated..."

**Self-Improving Agent Quality Score Bugs**

When running `bianinho_self_improving.py` (or similar self-improvement cycles), the quality score itself can be wrong if the error classification has bugs. Always validate the classification independently:

1. Read the raw log file (`errors.log`) directly
2. Apply the classifier logic manually to each line
3. Compare your results against what the script reports
4. Common classification bugs:
   - **False auth_error**: "401" appearing in timestamps (e.g., `20260421_162137_401139`) — fix: require `HTTP [45]XX` pattern, not just substring match
   - **False rate_limit**: "insufficient balance" misclassified as auth_error — fix: check for "insufficient" before generic 401/403 match
   - **False not_found**: "working directory not found" caught by generic "not found" check — fix: order more specific checks before generic ones
   - **False other**: benign operational messages (git skipped, checkpoint warnings) caught by generic "other" — fix: add explicit patterns for known-benign categories
5. **Rule**: If quality < 4.0 but classification looks wrong, fix the classifier first before acting on the score

**Retry-Loop Self-Defence Pattern (bianinho_self_improving.py)**

The self-improving script can enter a retry loop: running every ~31min with no cooldown, compounding rate limits until quality collapses. Detected pattern: 10 runs in 5 hours with quality oscillating 3.4–4.2 and same fixes applied repeatedly.

When corrective action is triggered (quality < 4.0), always check for retry-loop before applying fixes:

1. **Detect**: Count runs in `~/.hermes/self_improvement_state.json` history. If >3 runs within 6h with similar error categories, this is a loop.
2. **Cooldown lock**: Create `~/.hermes/self_improving.lock` with `locked_until` (ISO timestamp). Set to 5–6h ahead. This prevents the script from running again until quota resets.
3. **Guard endpoint health**: Mark the exhausted endpoint (e.g. MiniMax TTS `code 2056`) as `rate_limited` in `endpoint_health.json` with component + error detail so downstream tools respect it.
4. **Harden retry_guard**: Raise `backoff_seconds` to 300+ and `timeout_guard` to 240s when `ctx_execute` degradation is present.
5. **Persist corrective state**: Append a `corrective_session` block to `self_improvement_state.json` with root causes and fixes so the next cycle skips already-applied fixes.
6. **Log to journal**: Append a structured entry to `meta_cognition_journal.jsonl` with the full diagnosis.

Files to read for diagnosis (in order):
- `errors.log` — actual error messages (ground truth)
- `self_improvement_state.json` — run history + applied fixes
- `retry_guard.json` — current throttle settings
- `endpoint_health.json` — endpoint status

Files to write (in order):
1. `~/.hermes/self_improving.lock` — cooldown enforcement
2. `~/.hermes/endpoint_health.json` — updated health + rate-limit flags
3. `~/.hermes/retry_guard.json` — hardened throttle settings
4. `~/.hermes/self_improvement_state.json` — append corrective_session block
5. `~/.hermes/meta_cognition_journal.jsonl` — journal entry
6. `~/.hermes/logs/auto_improver_actions.jsonl` — action log

**Feature Requests** (→ feature request):
- "Can you also..."
- "I wish you could..."
- "Is there a way to..."
- "Why can't you..."

**Knowledge Gaps** (→ learning with `knowledge_gap` category):
- User provides information you didn't know
- Documentation you referenced is outdated
- API behavior differs from your understanding

**Errors** (→ error entry):
- Command returns non-zero exit code
- Exception or stack trace
- Unexpected output or behavior
- Timeout or connection failure

## Priority Guidelines

| Priority | When to Use |
|----------|-------------|
| `critical` | Blocks core functionality, data loss risk, security issue |
| `high` | Significant impact, affects common workflows, recurring issue |
| `medium` | Moderate impact, workaround exists |
| `low` | Minor inconvenience, edge case, nice-to-have |

## Area Tags

Use to filter learnings by codebase region:

| Area | Scope |
|------|-------|
| `frontend` | UI, components, client-side code |
| `backend` | API, services, server-side code |
| `infra` | CI/CD, deployment, Docker, cloud |
| `tests` | Test files, testing utilities, coverage |
| `docs` | Documentation, comments, READMEs |
| `config` | Configuration files, environment, settings |

## Best Practices

1. **Log immediately** - context is freshest right after the issue
2. **Be specific** - future agents need to understand quickly
3. **Include reproduction steps** - especially for errors
4. **Link related files** - makes fixes easier
5. **Suggest concrete fixes** - not just "investigate"
6. **Use consistent categories** - enables filtering
7. **Promote aggressively** - if in doubt, add to USER.md or .github/copilot-instructions.md
8. **Review regularly** - stale learnings lose value

## Hermes-Native Features

### Session Query for Learning Extraction

Extract learnings from past sessions:

```python
import sqlite3
from datetime import datetime, timedelta

conn = sqlite3.connect('~/.hermes/hermes_sessions.db')
cursor = conn.cursor()

# Get sessions from last 7 days
cursor.execute("""
    SELECT timestamp, content 
    FROM sessions 
    WHERE timestamp > datetime('now', '-7 days')
    ORDER BY timestamp DESC
""")

for row in cursor.fetchall():
    # Analyze for learning opportunities
    timestamp, content = row
    # Check for corrections, errors, feedback patterns
```

### Skill Integration

Promote successful learnings to reusable skills:

```bash
# When a learning becomes a skill
hermes skills create <skill-name> --from-learning LRN-20250115-001
```

### Cronjob Integration

Set up automatic learning extraction:

```bash
# Daily at 4am - extract learnings from session logs
0 4 * * * python3 ~/.hermes/scripts/self_improvement/extract_from_sessions.py

# Weekly on Sunday - pattern detection and promotion
0 22 * * 0 python3 ~/.hermes/scripts/self_improvement/weekly_review.py
```

## Gitignore Options

**Keep learnings local** (per-developer):
```gitignore
.learnings/
```

**Track learnings in repo** (team-wide):
Don't add to .gitignore - learnings become shared knowledge.

**Hybrid** (track templates, ignore entries):
```gitignore
.learnings/*.md
!.learnings/.gitkeep
```

---

Adapted for Hermes from biocrfhkust-cloud/self-improving-agent-2
