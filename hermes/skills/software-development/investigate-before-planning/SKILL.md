---
name: investigate-before-planning
description: Always investigate the actual state of a system before planning improvements. Use terminal, DB queries, and file inspection to map reality first.
tags:
  - debugging
  - planning
  - architecture
  - workflow
---

# Investigate Before Planning

## When to Use
When given a task that requires understanding or improving a system, process, or architecture — stop and investigate the actual state first. Do not plan based on assumptions. Findings may invalidate the original plan entirely.

## Why
In a recent session, I assumed my memory system was at 98% capacity in a single file. After investigation, I discovered my actual architecture has 5 distinct layers (MEMORY.md, USER.md, hermes_sessions.db, state.db with 84k messages, LanceDB). The bottleneck was different than assumed. This changed the entire plan.

## Steps
1. **Map the actual system** — use terminal, file exploration, and database queries to understand what actually exists
2. **Measure real state** — sizes, counts, actual content
3. **Compare to assumed state** — were you wrong about how it works?
4. **Then plan** — with accurate information

## Example Applied: My Memory System Investigation

### Commands used
```bash
# Find memory-related files
find ~/.hermes -name "*.json" -o -name "*.txt" -o -name "memory*" | grep -i -E "memory|user|profile|notes"

# Inspect SQLite schemas
sqlite3 ~/.hermes/hermes_sessions.db ".schema"
sqlite3 ~/.hermes/state.db ".schema"

# Measure actual sizes
sqlite3 ~/.hermes/hermes_sessions.db "SELECT COUNT(*) FROM sessions;"
sqlite3 ~/.hermes/state.db "SELECT COUNT(*) FROM messages;"

# Read actual memory files
cat ~/.hermes/memories/MEMORY.md
cat ~/.hermes/memories/USER.md
```

### Key Discovery
My memory architecture has 5 layers:
- `MEMORY.md` (~2.1KB) — high-level persistent facts (was thought to be full)
- `USER.md` (~866 chars) — user profile
- `hermes_sessions.db` (1.8MB, 60 sessions) — episodic memory (full session logs)
- `state.db` (117MB, 84,752 messages, FTS indexed) — working memory with full-text search
- `LanceDB` (~118MB) — semantic/vector memory for knowledge base

The MEMORY.md being "98% full" was real but not the bottleneck I assumed. The real power is in state.db + FTS + session_search.

## Principle
> "Debug before you design. Investigate before you plan. Measure before you optimize."
