"""
Team Leader Monitor — lê mensagens do Team Leader da BD do AionUI
"""

import json
import sqlite3
import time
from datetime import datetime
from pathlib import Path

AIONUI_DB = Path.home() / "Library/Application Support/AionUI/aionui/aionui.db"
TEN_TEAM_LEADER_CONV = "d124e72a"


def get_messages(limit: int = 10, after_timestamp: int = None) -> dict:
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
            "datetime": datetime.fromtimestamp(row["created_at"] / 1000).strftime("%Y-%m-%d %H:%M:%S")
        })

    messages.reverse()
    return {"messages": messages, "count": len(messages)}


def get_conversation_summary() -> dict:
    """Resumo da conversa do Team Leader."""
    result = get_messages(limit=6)
    if "error" in result:
        return result

    messages = result.get("messages", [])
    if not messages:
        return {"summary": "Sem mensagens", "messages": []}

    summary_parts = []
    for msg in messages[-4:]:
        role = "👤" if msg["type"] == "user" else "🤖"
        preview = msg["content"][:80] + "..." if len(msg["content"]) > 80 else msg["content"]
        summary_parts.append(f"{role} [{msg['datetime']}] {preview}")

    return {
        "summary": "Conversation do Team Leader (últimas 4 trocas):\n\n" + "\n\n".join(summary_parts),
        "message_count": result["count"],
        "messages": messages
    }


def poll_for_new_messages(timeout: int = 30) -> dict:
    """Espera por novas mensagens do Team Leader."""
    if not AIONUI_DB.exists():
        return {"error": f"Base de dados não encontrada: {AIONUI_DB}"}

    # Obter timestamp atual
    result = get_messages(limit=1)
    if "error" in result:
        return result

    messages = result.get("messages", [])
    last_timestamp = messages[0]["timestamp"] if messages else 0

    start_time = time.time()
    while time.time() - start_time < timeout:
        time.sleep(2)
        result = get_messages(limit=10, after_timestamp=last_timestamp)
        new_messages = result.get("messages", [])

        if new_messages:
            return {
                "new_messages": new_messages,
                "count": len(new_messages),
                "elapsed": round(time.time() - start_time, 1)
            }

    return {"new_messages": [], "count": 0, "message": "Timeout - sem novas mensagens"}
