"""
Bianinho Autonomous Inbox — Sistema de Gestão de Tarefas
Dir: ~/.hermes/autonomous/inbox.db (SQLite)
"""

import sqlite3
import json
import uuid
from datetime import datetime, timezone
from pathlib import Path

INBOX_PATH = Path.home() / ".hermes" / "autonomous" / "inbox.db"

def _get_db():
    INBOX_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(INBOX_PATH)
    conn.row_factory = sqlite3.Row
    _init_db(conn)
    return conn

def _init_db(conn):
    conn.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            id          TEXT PRIMARY KEY,
            source      TEXT NOT NULL,       -- 'alvaro', 'system', 'detected', 'delegate'
            content     TEXT NOT NULL,
            priority    INTEGER DEFAULT 3,   -- 1=critical, 2=high, 3=normal, 4=low
            status      TEXT DEFAULT 'pending',  -- pending, running, done, blocked, skipped
            tags        TEXT DEFAULT '[]',   -- JSON array
            created_at  TEXT NOT NULL,
            updated_at  TEXT NOT NULL,
            due_at      TEXT,                -- ISO timestamp or null
            assigned_to TEXT,                -- 'bianinho', 'agent', 'alvaro'
            notes       TEXT DEFAULT '',
            result      TEXT DEFAULT ''
        )
    """)
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_status ON tasks(status)
    """)
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_priority ON tasks(priority)
    """)

def add(content: str, source: str = 'system', priority: int = 3,
         tags: list = None, due_at: str = None, assigned_to: str = 'bianinho',
         notes: str = '') -> str:
    """Adiciona tarefa ao inbox. Retorna task_id."""
    conn = _get_db()
    task_id = str(uuid.uuid4())[:8]
    now = datetime.now(timezone.utc).isoformat()
    tags = tags or []
    try:
        conn.execute("""
            INSERT INTO tasks (id, source, content, priority, status, tags,
                             created_at, updated_at, due_at, assigned_to, notes)
            VALUES (?, ?, ?, ?, 'pending', ?, ?, ?, ?, ?, ?)
        """, (task_id, source, content, priority, json.dumps(tags),
              now, now, due_at, assigned_to, notes))
        conn.commit()
    finally:
        conn.close()
    return task_id

def list_tasks(status: str = None, assigned_to: str = None,
               limit: int = 50, tag: str = None) -> list:
    """Lista tarefas com filtros."""
    conn = _get_db()
    query = "SELECT * FROM tasks WHERE 1=1"
    params = []
    if status:
        query += " AND status = ?"
        params.append(status)
    if assigned_to:
        query += " AND assigned_to = ?"
        params.append(assigned_to)
    query += " ORDER BY priority ASC, created_at DESC LIMIT ?"
    params.append(limit)
    rows = conn.execute(query, params).fetchall()
    conn.close()

    result = []
    for row in rows:
        d = dict(row)
        d['tags'] = json.loads(d['tags'])
        if tag and tag not in d['tags']:
            continue
        result.append(d)
    return result

def get(task_id: str) -> dict | None:
    """Obtém uma tarefa por ID."""
    conn = _get_db()
    row = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
    conn.close()
    if not row:
        return None
    d = dict(row)
    d['tags'] = json.loads(d['tags'])
    return d

def update(task_id: str, status: str = None, priority: int = None,
           result: str = None, notes: str = None) -> bool:
    """Actualiza estado de uma tarefa."""
    conn = _get_db()
    now = datetime.now(timezone.utc).isoformat()
    fields = ['updated_at = ?']
    params = [now]
    if status:
        fields.append('status = ?')
        params.append(status)
    if priority:
        fields.append('priority = ?')
        params.append(priority)
    if result is not None:
        fields.append('result = ?')
        params.append(result)
    if notes is not None:
        fields.append('notes = ?')
        params.append(notes)
    params.append(task_id)
    cur = conn.execute(
        f"UPDATE tasks SET {', '.join(fields)} WHERE id = ?", params)
    conn.commit()
    changed = cur.rowcount > 0
    conn.close()
    return changed

def delete(task_id: str) -> bool:
    """Remove tarefa do inbox."""
    conn = _get_db()
    cur = conn.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
    conn.commit()
    deleted = cur.rowcount > 0
    conn.close()
    return deleted

def pending_count() -> dict:
    """Contagem de tarefas pendentes por prioridade."""
    conn = _get_db()
    rows = conn.execute("""
        SELECT priority, COUNT(*) as cnt
        FROM tasks
        WHERE status = 'pending'
        GROUP BY priority
    """).fetchall()
    conn.close()
    return {row['priority']: row['cnt'] for row in rows}

def stats() -> dict:
    """Estatísticas do inbox."""
    conn = _get_db()
    total = conn.execute("SELECT COUNT(*) FROM tasks").fetchone()[0]
    by_status = {
        r['status']: r['cnt']
        for r in conn.execute(
            "SELECT status, COUNT(*) as cnt FROM tasks GROUP BY status"
        ).fetchall()
    }
    conn.close()
    return {'total': total, 'by_status': by_status}

if __name__ == '__main__':
    import sys
    if len(sys.argv) < 2:
        print("Usage: inbox.py add|list|get|update|delete|stats")
        sys.exit(1)
    cmd = sys.argv[1]
    if cmd == 'list':
        for t in list_tasks():
            print(f"[{t['id']}] {t['status']} P{t['priority']} | {t['content'][:80]}")
    elif cmd == 'stats':
        print(stats())
    elif cmd == 'add' and len(sys.argv) >= 3:
        tid = add(' '.join(sys.argv[2:]))
        print(f"Added: {tid}")
    elif cmd == 'get' and len(sys.argv) >= 3:
        print(get(sys.argv[2]))
    elif cmd == 'update' and len(sys.argv) >= 4:
        print(update(sys.argv[2], status=sys.argv[3]))
    elif cmd == 'delete' and len(sys.argv) >= 3:
        print(delete(sys.argv[2]))
