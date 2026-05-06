#!/usr/bin/env python3
"""
Team Leader Monitor — tool for reading TEN Team Leader messages from AionUI DB

Usage:
    python team_leader_query.py messages [limit] [after_timestamp]
    python team_leader_query.py summary
    python team_leader_query.py poll [timeout]
"""

import json
import sqlite3
import sys
import time
from datetime import datetime
from pathlib import Path

AIONUI_DB = Path.home() / "Library/Application Support/AionUI/aionui/aionui.db"
TEN_TEAM_LEADER_CONV = "d124e72a"


def get_messages(limit: int = 10, after_timestamp: int = None):
    """Lê mensagens do Team Leader."""
    if not AIONUI_DB.exists():
        return {"error": f"Base de dados não encontrada: {AIONUI_DB}"}

    conn = sqlite3.connect(str(AIONUI_DB))
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    query = """
        SELECT id, type, content, created_at
        FROM messages
        WHERE conversation_id = ?
        AND type IN ('user', 'assistant', 'text')
    """
    params = [TEN_TEAM_LEADER_CONV]

    if after_timestamp:
        query += " AND created_at > ?"
        params.append(after_timestamp)

    query += " ORDER BY created_at DESC LIMIT ?"
    params.append(limit)

    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()

    messages = []
    for row in rows:
        content = row["content"]
        try:
            parsed = json.loads(content)
            text = parsed.get("content", content) if isinstance(parsed, dict) else content
        except (json.JSONDecodeError, TypeError):
            text = content

        messages.append({
            "id": row["id"],
            "type": row["type"],
            "content": text,
            "timestamp": row["created_at"],
            "datetime": datetime.fromtimestamp(row["created_at"] / 1000).strftime("%H:%M:%S")
        })

    messages.reverse()
    return messages


def cmd_messages(limit: int = 10, after_ts: int = None):
    """Retorna mensagens do Team Leader."""
    msgs = get_messages(limit, after_ts)
    if not msgs:
        print("Sem mensagens encontradas")
        return

    for msg in msgs:
        role = "👤 Utilizador" if msg["type"] == "user" else "🤖 Team Leader"
        print(f"\n{role} [{msg['datetime']}]")
        print(msg["content"])
        print("-" * 50)


def cmd_summary():
    """Resumo da conversa."""
    msgs = get_messages(limit=6)
    if not msgs:
        print("Sem mensagens")
        return

    print("═" * 60)
    print("CONVERSA DO TEAM LEADER (TEN Team)")
    print("═" * 60)

    for msg in msgs:
        role = "👤" if msg["type"] == "user" else "🤖"
        preview = msg["content"][:100] + "..." if len(msg["content"]) > 100 else msg["content"]
        print(f"\n{role} [{msg['datetime']}]")
        print(preview)

    print("\n" + "═" * 60)


def cmd_poll(timeout: int = 30):
    """Espera por novas mensagens."""
    msgs = get_messages(limit=1)
    last_ts = msgs[0]["timestamp"] if msgs else 0

    print(f"A esperar por novas mensagens (timeout: {timeout}s)...")
    start = time.time()

    while time.time() - start < timeout:
        time.sleep(2)
        new_msgs = get_messages(limit=10, after_timestamp=last_ts)
        if new_msgs:
            print(f"\n✨ {len(new_msgs)} nova(s) mensagem(s)!")
            for msg in new_msgs:
                role = "👤" if msg["type"] == "user" else "🤖"
                print(f"\n{role} [{msg['datetime']}]")
                print(msg["content"])
            return
        print(".", end="", flush=True)

    print("\nTimeout - sem novas mensagens")


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "messages"
    args = sys.argv[2:]

    if cmd == "messages":
        limit = int(args[0]) if args else 10
        after_ts = int(args[1]) if len(args) > 1 else None
        cmd_messages(limit, after_ts)
    elif cmd == "summary":
        cmd_summary()
    elif cmd == "poll":
        timeout = int(args[0]) if args else 30
        cmd_poll(timeout)
    else:
        print(f"Comando desconhecido: {cmd}")
        print("Usage: messages [limit] | summary | poll [timeout]")
