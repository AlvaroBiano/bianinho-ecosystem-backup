#!/usr/bin/env python3
"""Context Helper para cron jobs Hermes.

Obtém contexto da sessão principal via query direta ao hermes_sessions.db.

Schema Hermes:
  sessions: session_id, platform, started_at, ended_at, metadata
  events:  session_id, timestamp, event_type, content, details

Usage:
  python3 get_context.py [limit] [platform]
  python3 get_context.py 20 cli
  python3 get_context.py 50 telegram
"""
import sqlite3
import sys
from pathlib import Path


def get_recent_context(limit=20, platform=None):
    db_path = Path.home() / ".hermes" / "hermes_sessions.db"
    if not db_path.exists():
        return "No session DB found."

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

    # Most recent last (chronological order)
    lines = []
    for event_type, content in reversed(rows):
        preview = content[:250].replace('\n', ' ')
        lines.append(f"[{event_type}] {preview}")

    return "\n".join(lines)


if __name__ == "__main__":
    limit = int(sys.argv[1]) if len(sys.argv) > 1 else 20
    platform = sys.argv[2] if len(sys.argv) > 2 else None
    print(get_recent_context(limit, platform))
