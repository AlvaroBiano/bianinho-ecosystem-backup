---
name: hermes-session-schema
description: Hermes sessions database schema reference — tables, columns, indexes, and query patterns. Essential for any script that reads Hermes session data directly.
category: data-science
---

# Hermes Sessions DB — Schema Reference

## Location
`~/.hermes/hermes_sessions.db`

## Schema

```sql
CREATE TABLE sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,
    platform TEXT NOT NULL,  -- telegram, cli, terminal, auto_plugin
    started_at TEXT NOT NULL,
    ended_at TEXT,
    metadata TEXT  -- JSON: user_info, source details
);

CREATE TABLE events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,
    timestamp TEXT NOT NULL,  -- YYYY-MM-DD HH:MM:SS
    event_type TEXT NOT NULL,  -- user_message, agent_response, tool_call, tool_result, error, system, skill_used, file_access, web_access, note, finding
    content TEXT NOT NULL,  -- O conteúdo real
    details TEXT,  -- JSON: tool_name, file_path, url, skill_name, etc.
    FOREIGN KEY (session_id) REFERENCES sessions(session_id)
);

CREATE INDEX idx_events_session ON events(session_id);
CREATE INDEX idx_events_type ON events(event_type);
CREATE INDEX idx_events_timestamp ON events(timestamp);
```

## Common Query Patterns

### Get recent events from a specific platform
```python
conn = sqlite3.connect(os.path.expanduser("~/.hermes/hermes_sessions.db"))
cur = conn.cursor()
cur.execute("""
    SELECT e.event_type, e.content FROM events e
    JOIN sessions s ON e.session_id = s.session_id
    WHERE s.platform = ?
    ORDER BY e.id DESC LIMIT ?
""", (platform, limit))
```

### Get all sessions (most recent first)
```sql
SELECT session_id, platform, started_at FROM sessions
ORDER BY id DESC LIMIT 20;
```

### Get events by type
```sql
SELECT timestamp, content FROM events
WHERE event_type = 'user_message'
ORDER BY id DESC LIMIT 10;
```

### Get conversation pairs (user + agent)
```sql
SELECT e1.content as user, e2.content as agent
FROM events e1
JOIN events e2 ON e1.session_id = e2.session_id
  AND e2.event_type = 'agent_response'
  AND e2.id > e1.id
JOIN sessions s ON e1.session_id = s.session_id
WHERE s.platform = 'telegram'
ORDER BY e1.id DESC LIMIT 20;
```

### Get events from today
```sql
SELECT event_type, substr(content, 1, 200)
FROM events
WHERE timestamp >= date('now')
ORDER BY id DESC LIMIT 20;
```

## Platform Values

| Platform | Meaning |
|----------|---------|
| `cli` | Command-line interactive session |
| `telegram` | Telegram user conversation |
| `auto_plugin` | Background/cron job session |
| `terminal` | Terminal session |

## Event Types

| Type | Description |
|------|-------------|
| `user_message` | User input |
| `agent_response` | AI response |
| `tool_call` | Tool execution started |
| `tool_result` | Tool output |
| `system` | System events (session start/end) |
| `skill_used` | Skill invocation |
| `file_access` | File read/write |
| `web_access` | Web request |
| `note` | Internal note |
| `finding` | Discovery or result |

## Python Helper (get_context.py)

Location: `~/.hermes/skills/context-aware-delegation/scripts/get_context.py`

```python
import sqlite3, os, sys
from pathlib import Path

def get_recent_context(limit=20, platform=None):
    db_path = Path.home() / ".hermes" / "hermes_sessions.db"
    conn = sqlite3.connect(str(db_path))
    cur = conn.cursor()
    if platform:
        cur.execute("""
            SELECT e.event_type, e.content FROM events e
            JOIN sessions s ON e.session_id = s.session_id
            WHERE s.platform = ?
            ORDER BY e.id DESC LIMIT ?
        """, (platform, limit))
    else:
        cur.execute(f"""
            SELECT event_type, content FROM events
            ORDER BY id DESC LIMIT {limit}
        """)
    rows = cur.fetchall()
    conn.close()
    if not rows:
        return "No recent context found."
    lines = []
    for event_type, content in reversed(rows):
        preview = content[:250].replace('\n', ' ')
        lines.append(f"[{event_type}] {preview}")
    return "\n".join(lines)

if __name__ == "__main__":
    limit = int(sys.argv[1]) if len(sys.argv) > 1 else 20
    platform = sys.argv[2] if len(sys.argv) > 2 else None
    print(get_recent_context(limit, platform))
```

Usage:
```bash
python3 get_context.py 20 telegram  # Last 20 Telegram events
python3 get_context.py 50           # Last 50 events (any platform)
```

## Pitfalls

1. **NEVER assume sessions table schema** — always use `session_search()` or query the DB directly with proper column names
2. Always inspect schema with `sqlite3 ~/.hermes/hermes_sessions.db ".schema"` before writing queries
3. `content` column stores raw text — no JSON parsing needed unless `details` column exists
4. `session_id` is TEXT, not INTEGER foreign key in events — join on `session_id`
