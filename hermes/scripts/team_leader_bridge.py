#!/usr/bin/env python3
"""
Team Leader Bridge — permite comunicação entre Bianinho e o Team Leader
via ficheiro partilhado.

O Team Leader escreve neste ficheiro quando recebe mensagens.
O Bianinho pode ler e também escrever mensagens para o Team Leader.
"""

import json
import os
import sqlite3
import sys
import time
from datetime import datetime
from pathlib import Path
from threading import Lock

BRIDGE_FILE = Path.home() / ".hermes/team_leader_bridge.json"
AIONUI_DB = Path.home() / "Library/Application Support/AionUI/aionui/aionui.db"
TEN_TEAM_LEADER_CONV = "d124e72a"
LOCK_FILE = Path.home() / ".hermes/team_leader_bridge.lock"

lock = Lock()


def read_bridge():
    """Lê o estado actual da bridge."""
    if not BRIDGE_FILE.exists():
        return {"messages": [], "last_read": 0}

    try:
        with open(BRIDGE_FILE, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return {"messages": [], "last_read": 0}


def write_bridge(data):
    """Escreve o estado da bridge."""
    with lock:
        with open(BRIDGE_FILE, "w") as f:
            json.dump(data, f, indent=2)


def get_new_team_leader_messages():
    """Obtém mensagens novas do Team Leader desde o último read."""
    bridge = read_bridge()
    last_read = bridge.get("last_read", 0)

    if not AIONUI_DB.exists():
        return [], last_read

    conn = sqlite3.connect(str(AIONUI_DB))
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, type, content, created_at
        FROM messages
        WHERE conversation_id = ?
        AND type IN ('text', 'assistant')
        AND created_at > ?
        ORDER BY created_at ASC
    """, [TEN_TEAM_LEADER_CONV, last_read])

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
            "content": text,
            "timestamp": row["created_at"],
            "datetime": datetime.fromtimestamp(row["created_at"] / 1000).strftime("%H:%M:%S")
        })

    if messages:
        new_last_read = max(m["timestamp"] for m in messages)
        bridge["last_read"] = new_last_read
        write_bridge(bridge)

    return messages, last_read


def write_message_to_team_leader(content: str):
    """Escreve uma mensagem para o Team Leader processar."""
    bridge = read_bridge()
    bridge["messages"].append({
        "from": "bianinho",
        "content": content,
        "timestamp": int(time.time() * 1000),
        "datetime": datetime.now().strftime("%H:%M:%S"),
        "status": "pending"
    })
    write_bridge(bridge)
    return {"success": True, "message": "Mensagem escrita para Team Leader"}


def get_pending_messages():
    """Obtém mensagens pendentes de resposta do Team Leader."""
    bridge = read_bridge()
    return [m for m in bridge.get("messages", []) if m.get("from") == "team_leader" and m.get("status") == "pending"]


def mark_message_read(message_id: str):
    """Marca uma mensagem como lida."""
    bridge = read_bridge()
    for msg in bridge.get("messages", []):
        if msg.get("id") == message_id:
            msg["status"] = "read"
    write_bridge(bridge)


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "read"

    if cmd == "read":
        msgs, _ = get_new_team_leader_messages()
        if msgs:
            print(f"📨 {len(msgs)} nova(s) mensagem(s) do Team Leader:")
            for m in msgs:
                print(f"\n[{m['datetime']}]")
                print(m["content"][:200] + "..." if len(m["content"]) > 200 else m["content"])
        else:
            print("Sem novas mensagens")

    elif cmd == "write":
        if len(sys.argv) < 3:
            print("Usage: team_leader_bridge.py write <mensagem>")
            sys.exit(1)
        result = write_message_to_team_leader(sys.argv[2])
        print(result)

    elif cmd == "poll":
        timeout = int(sys.argv[2]) if len(sys.argv) > 2 else 30
        start = time.time()
        while time.time() - start < timeout:
            msgs, _ = get_new_team_leader_messages()
            if msgs:
                print(f"📨 {len(msgs)} nova(s) mensagem(s)!")
                for m in msgs:
                    print(f"\n[{m['datetime']}]")
                    print(m["content"])
                break
            time.sleep(2)
            print(".", end="", flush=True)
        else:
            print("\nTimeout - sem novas mensagens")

    elif cmd == "status":
        bridge = read_bridge()
        pending = [m for m in bridge.get("messages", []) if m.get("status") == "pending"]
        print(f"Bridge: {BRIDGE_FILE}")
        print(f"Mensagens pendentes: {len(pending)}")
        print(f"Último read timestamp: {bridge.get('last_read', 0)}")
