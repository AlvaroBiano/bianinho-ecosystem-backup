---
name: smart-memory
version: 1.0.0
description: >
  Zero-cost persistent memory that makes your bot smarter over time.
  Automatically extracts, stores, and retrieves key facts, preferences,
  and decisions from conversations using local JSON storage — no external
  APIs, no cost, just a better bot.
author: Adapted for Hermes from J. DeVere Cooley's openjaw-smart-memory
category: proativo
tags:
  - memory
  - context
  - optimization
  - token-saving
  - zero-cost
tools:
  - python3
  - file_read
  - file_write
heartbeat:
  enabled: true
  interval: daily
  action: memory_maintenance
---

# Smart Memory — Persistent Intelligence for Hermes

You have access to a persistent local memory system. Use it to remember important
information across conversations so the user never has to repeat themselves.

## Core Principle

**Remember everything important. Forget nothing the user cares about. Cost nothing.**

All memory is stored locally in `~/.hermes/smart-memory/` as plain JSON files.
No external APIs. No cloud storage. No cost. Just local files and Python scripts.

## When to STORE a Memory

Automatically extract and store memories whenever the user shares:

- **Preferences**: "I prefer dark mode", "I like Python over JavaScript"
- **Personal facts**: names, locations, roles, team members, project names
- **Decisions**: "We decided to use PostgreSQL", "Let's go with the microservice approach"
- **Instructions**: "Always run tests before committing", "Never deploy on Fridays"
- **Important dates**: deadlines, birthdays, recurring events
- **Technical context**: stack details, repo URLs, server addresses, API keys (stored locally only)
- **Corrections**: "Actually, my name is spelled with a K" (update existing memory)

### How to Store

Run the memory manager to store a new memory:

```bash
python3 ~/.hermes/scripts/smart_memory/store.py \
  --category "<preferences|facts|decisions|instructions|dates|technical|corrections>" \
  --key "<short_identifier>" \
  --value "<the information to remember>" \
  --confidence "<high|medium|low>" \
  --source "<conversation|user_explicit|inferred>"
```

**Confidence levels:**
- `high` — User explicitly stated this ("My name is Alex")
- `medium` — Clearly implied from context ("I keep using vim, so they prefer vim")
- `low` — Inferred or uncertain ("They might work in finance based on their questions")

**Source types:**
- `user_explicit` — User directly told you this information
- `conversation` — Extracted from conversation context
- `inferred` — You reasoned this from patterns

## When to RETRIEVE Memories

Before responding to any user message, check if relevant memories exist:

```bash
python3 ~/.hermes/scripts/smart_memory/search.py --query "<relevant keywords>"
```

Use retrieved memories to:
- Personalize responses (use their name, reference their preferences)
- Avoid asking questions you already know the answer to
- Provide continuity across conversations
- Reference past decisions and context

## When to UPDATE a Memory

If the user corrects or changes information:

```bash
python3 ~/.hermes/scripts/smart_memory/update.py \
  --key "<existing_key>" \
  --value "<new_value>" \
  --reason "<why this changed>"
```

The old value is preserved in the memory's history for audit purposes.

## When to FORGET a Memory

If the user explicitly asks you to forget something:

```bash
python3 ~/.hermes/scripts/smart_memory/forget.py --key "<key_to_forget>"
```

This soft-deletes the memory (marks it as forgotten but retains it in the archive
for 30 days before permanent deletion).

## Daily Maintenance (Heartbeat)

Every day, the heartbeat triggers automatic maintenance:

```bash
python3 ~/.hermes/scripts/smart_memory/maintain.py
```

This will:
1. **Prune** — Remove stale low-confidence memories older than 90 days
2. **Deduplicate** — Merge duplicate or near-duplicate entries
3. **Stats** — Generate a usage summary
4. **Archive** — Rotate old memories to archive storage
5. **Integrity check** — Validate JSON files and repair if needed

## Viewing Memory Stats

To report on memory usage and health:

```bash
python3 ~/.hermes/scripts/smart_memory/stats.py
```

This shows: total memories, breakdown by category, storage size, oldest/newest
entries, and estimated token savings.

## Privacy & Security Rules

1. **All data stays local** — Never transmit memory contents to external services
2. **Respect forget requests** — When the user says "forget X", delete it immediately
3. **No sensitive data in logs** — Memory contents never appear in system logs
4. **User can export/delete all data** at any time:
   ```bash
   python3 ~/.hermes/scripts/smart_memory/export.py
   python3 ~/.hermes/scripts/smart_memory/purge.py --confirm
   ```

## Hermes-Native Integrations

### Using the Memory Tool

Hermes provides a built-in memory tool that can be used for quick lookups:

```
memory tool: search "user preferences"
memory tool: store preference dark_mode=true
```

### Knowledge Base Integration

Memories are also synced to `~/KnowledgeBase/` for semantic retrieval:

```bash
# Query the Knowledge Base
python3 ~/KnowledgeBase/query.py --semantic "<search terms>"
```

### Session History Queries

Access conversation history from `~/.hermes/hermes_sessions.db`:

```python
import sqlite3
conn = sqlite3.connect('~/.hermes/hermes_sessions.db')
# Query recent sessions for context
```

## File Structure

```
~/.hermes/smart-memory/
  memories.json          # Active memories (main store)
  archive.json           # Archived/pruned memories
  stats.json             # Usage statistics & token savings tracker
  config.json            # User-customizable settings

~/.hermes/scripts/smart_memory/
  store.py               # Store new memories
  search.py              # Search memories
  update.py              # Update existing memories
  forget.py              # Soft-delete memories
  maintain.py            # Daily maintenance
  stats.py               # Statistics & reporting
  export.py              # Export all data
  purge.py               # Purge all data
```

## Token Savings Tracking

Every time a memory is retrieved instead of the user re-explaining something,
log the estimated token savings:

```bash
python3 ~/.hermes/scripts/smart_memory/log_saving.py --tokens <estimated_tokens_saved>
```

Over time this demonstrates the ROI of the memory system — showing users how
many tokens (and dollars) they've saved by not repeating themselves.
