#!/usr/bin/env python3
"""
Hermes Team Leader Bridge - Solução Robusta para Mergiar Sessões
================================================================

Esta solução implementa comunicação indirecta entre o main Hermes (Bianinho)
e o Team Leader através de polling da base de dados SQLite do AionUI.

ARQUITECTURA:
  Team Leader → AionUI DB (mailbox/messages) → Bridge File → Main Hermes → Álvaro

Esta abordagem é:
- Robust: Não modifica código do AionUI, sobrevive a updates
- Simple: Não requer comunicação inter-processo complexa
- Reliable: Usa a BD SQLite como intermediário fiável
- Non-blocking: O Team Leader continua a funcionar normalmente

PROBLEMA RESOLVIDO:
  O Team Leader e o main Hermes são processos SEPARADOS. Esta solução
  permite ao Álvaro ver e responder às mensagens do Team Leader.

USO:
  python3 team_leader_session_bridge.py --monitor  (monitorização contínua)
  python3 team_leader_session_bridge.py --status    (estado actual)
  python3 team_leader_session_bridge.py --poll      (verificar novas mensagens)

CRON JOB (recomendado):
  */2 * * * * /Users/alvarobiano/.hermes/venv/bin/python3 /Users/alvarobiano/.hermes/scripts/team_leader_session_bridge.py --cron >> /Users/alvarobiano/.hermes/logs/team_leader_bridge.log 2>&1
"""

import json
import os
import sqlite3
import sys
import time
from datetime import datetime
from pathlib import Path
from threading import Lock
from typing import Optional

# Config
AIONUI_DB = Path.home() / "Library/Application Support/AionUI/aionui/aionui.db"
TEN_TEAM_LEADER_CONV = "d124e72a"
BRIDGE_FILE = Path.home() / ".hermes/team_leader_session_bridge.json"
LAST_SEEN_FILE = Path.home() / ".hermes/team_leader_last_seen.json"
LOG_FILE = Path.home() / ".hermes/logs/team_leader_bridge.log"

# Lock para acesso concorrente
bridge_lock = Lock()

#===============================================================================
# FUNÇÕES DE LOG
#===============================================================================

def log(msg: str, level: str = "INFO"):
    """Log para ficheiro e stdout."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_line = f"[{timestamp}] [{level}] {msg}"

    print(log_line)

    try:
        LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(LOG_FILE, "a") as f:
            f.write(log_line + "\n")
    except Exception:
        pass


#===============================================================================
# FUNÇÕES DE BASE DE DADOS
#===============================================================================

def get_db_connection():
    """Obtém conexão com a base de dados do AionUI."""
    if not AIONUI_DB.exists():
        raise FileNotFoundError(f"Base de dados não encontrada: {AIONUI_DB}")

    conn = sqlite3.connect(str(AIONUI_DB))
    conn.row_factory = sqlite3.Row
    return conn


def get_team_leader_messages(after_timestamp: int = 0, limit: int = 50):
    """
    Obtém mensagens do Team Leader desde o último seen.
    Returns lista de dicts com id, type, content, timestamp.
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, type, content, created_at
        FROM messages
        WHERE conversation_id = ?
        AND type IN ('text', 'user', 'assistant')
        AND created_at > ?
        ORDER BY created_at ASC
        LIMIT ?
    """, [TEN_TEAM_LEADER_CONV, after_timestamp, limit])

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

    return messages


def get_mailbox_messages(after_timestamp: int = 0, limit: int = 20):
    """
    Obtém mensagens da mailbox do Team Leader.
    A mailbox tem: to_agent_id, from_agent_id, content, created_at
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    # Mailbox para o slot do Team Leader
    cursor.execute("""
        SELECT id, to_agent_id, from_agent_id, type, content, created_at
        FROM mailbox
        WHERE to_agent_id = 'slot-1df887d8'
        AND created_at > ?
        ORDER BY created_at ASC
        LIMIT ?
    """, [after_timestamp, limit])

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
            "to": row["to_agent_id"],
            "from": row["from_agent_id"],
            "type": row["type"],
            "content": text,
            "timestamp": row["created_at"],
            "datetime": datetime.fromtimestamp(row["created_at"] / 1000).strftime("%Y-%m-%d %H:%M:%S")
        })

    return messages


def get_conversation_info():
    """Obtém informação sobre a conversa do Team Leader."""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, name, extra, updated_at
        FROM conversations
        WHERE id = ?
    """, [TEN_TEAM_LEADER_CONV])

    row = cursor.fetchone()
    conn.close()

    if not row:
        return None

    extra = json.loads(row["extra"]) if row["extra"] else {}

    return {
        "id": row["id"],
        "name": row["name"],
        "backend": extra.get("backend", "unknown"),
        "agentName": extra.get("agentName", "unknown"),
        "workspace": extra.get("workspace", "unknown"),
        "updated_at": datetime.fromtimestamp(row["updated_at"] / 1000).strftime("%Y-%m-%d %H:%M:%S")
    }


#===============================================================================
# FUNÇÕES DE BRIDGE STATE
#===============================================================================

def load_bridge_state():
    """Carrega o estado da bridge do ficheiro."""
    if not BRIDGE_FILE.exists():
        return {"messages": [], "last_seen": 0, "last_poll": 0}

    try:
        with open(BRIDGE_FILE, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return {"messages": [], "last_seen": 0, "last_poll": 0}


def save_bridge_state(state: dict):
    """Guarda o estado da bridge no ficheiro."""
    with bridge_lock:
        try:
            BRIDGE_FILE.parent.mkdir(parents=True, exist_ok=True)
            with open(BRIDGE_FILE, "w") as f:
                json.dump(state, f, indent=2)
        except IOError as e:
            log(f"Erro ao guardar estado: {e}", "ERROR")


def update_last_seen(timestamp: int):
    """Actualiza o último timestamp visto."""
    state = load_bridge_state()
    state["last_seen"] = timestamp
    save_bridge_state(state)


def load_last_seen() -> int:
    """Carrega o último timestamp visto."""
    state = load_bridge_state()
    return state.get("last_seen", 0)


#===============================================================================
# FUNÇÕES DE POLLING
#===============================================================================

def poll_new_messages() -> tuple[list, int]:
    """
    Faz polling de novas mensagens do Team Leader.
    Returns: (nova_mensagens, ultimo_timestamp)
    """
    last_seen = load_last_seen()

    # Obter mensagens do Team Leader
    messages = get_team_leader_messages(after_timestamp=last_seen)

    if messages:
        new_last_seen = max(m["timestamp"] for m in messages)
        update_last_seen(new_last_seen)
        log(f"Nova(s) mensagem(ns) do Team Leader: {len(messages)}")
        return messages, new_last_seen

    return [], last_seen


#===============================================================================
# FUNÇÕES DE OUTPUT
#===============================================================================

def format_message(msg: dict, include_sender: bool = True) -> str:
    """Formata uma mensagem para display."""
    content = msg["content"]
    timestamp = msg.get("datetime", "??:??")

    if include_sender:
        sender = msg.get("type", "unknown")
        return f"[{timestamp}] ({sender}):\n{content}"

    return f"[{timestamp}]:\n{content}"


def print_conversation_summary():
    """Imprime resumo da conversa do Team Leader."""
    info = get_conversation_info()

    print("\n" + "=" * 60)
    print("TEAM LEADER CONVERSATION")
    print("=" * 60)

    if info:
        print(f"ID:       {info['id']}")
        print(f"Name:     {info['name']}")
        print(f"Backend:  {info['backend']}")
        print(f"Agent:    {info['agentName']}")
        print(f"Updated:  {info['updated_at']}")
    else:
        print("Informação não disponível")

    print()
    print("-" * 60)

    # Últimas mensagens
    messages = get_team_leader_messages(limit=10)
    if messages:
        print(f"Últimas {len(messages)} mensagem(ns):\n")
        for msg in messages:
            print(format_message(msg))
            print()
    else:
        print("Sem mensagens")

    print("=" * 60)


def print_new_messages():
    """Imprime novas mensagens desde o último polling."""
    messages, _ = poll_new_messages()

    if not messages:
        print("Sem novas mensagens do Team Leader")
        return

    print(f"\n📨 {len(messages)} nova(s) mensagem(ns) do Team Leader:")
    print("-" * 60)

    for msg in messages:
        print(format_message(msg))
        print()


#===============================================================================
# MODO MONITOR
#===============================================================================

def monitor_mode(timeout: int = 0):
    """
    Modo de monitorização contínua.
    Se timeout=0, corre para sempre.
    Se timeout>0, corre por timeout segundos.
    """
    log("A iniciar modo monitor...")
    print("Monitorização do Team Leader (CTRL+C para parar)")

    start_time = time.time()

    while True:
        try:
            messages, _ = poll_new_messages()

            if messages:
                print_conversation_summary()
                log(f"Mostradas {len(messages)} mensagem(ns)")

            if timeout > 0 and (time.time() - start_time) > timeout:
                log(f"Timeout atingido ({timeout}s)")
                break

            time.sleep(10)  # Poll a cada 10 segundos

        except KeyboardInterrupt:
            log("Monitorização interrompida pelo utilizador")
            break
        except Exception as e:
            log(f"Erro no monitor: {e}", "ERROR")
            time.sleep(30)  # Espera mais tempo em caso de erro


#===============================================================================
# MAIN
#===============================================================================

def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="Hermes Team Leader Bridge - Solução Robusta para Mergiar Sessões"
    )

    parser.add_argument(
        "--status",
        action="store_true",
        help="Mostrar estado actual da bridge"
    )

    parser.add_argument(
        "--poll",
        action="store_true",
        help="Verificar e mostrar novas mensagens"
    )

    parser.add_argument(
        "--monitor",
        action="store_true",
        help="Modo de monitorização contínua"
    )

    parser.add_argument(
        "--timeout",
        type=int,
        default=0,
        help="Timeout em segundos para o modo monitor (0=sempre)"
    )

    parser.add_argument(
        "--cron",
        action="store_true",
        help="Modo cron - saída mínima para logging"
    )

    parser.add_argument(
        "--summary",
        action="store_true",
        help="Mostrar resumo da conversa"
    )

    args = parser.parse_args()

    # Verificar se a BD existe
    if not AIONUI_DB.exists():
        print(f"ERRO: Base de dados não encontrada: {AIONUI_DB}")
        sys.exit(1)

    if args.cron:
        # Modo cron - polling simples, saída mínima
        try:
            messages, _ = poll_new_messages()
            if messages:
                log(f"Nova(s) mensagem(ns): {len(messages)}")
                # Guardar para processamento posterior
                state = load_bridge_state()
                state["pending_messages"] = messages
                save_bridge_state(state)
        except Exception as e:
            log(f"Erro no cron: {e}", "ERROR")
            sys.exit(1)

    elif args.status:
        state = load_bridge_state()
        print(f"Bridge State:")
        print(f"  Última mensagem vista: {state.get('last_seen', 0)}")
        print(f"  Mensagens pendentes: {len(state.get('pending_messages', []))}")

    elif args.poll:
        print_new_messages()

    elif args.monitor:
        monitor_mode(timeout=args.timeout)

    elif args.summary:
        print_conversation_summary()

    else:
        # Default: mostrar status e summary
        state = load_bridge_state()
        last_seen = state.get("last_seen", 0)

        print(f"Estado da Bridge:")
        print(f"  Última mensagem vista (timestamp): {last_seen}")

        if last_seen:
            dt = datetime.fromtimestamp(last_seen / 1000)
            print(f"  Última mensagem vista (datetime): {dt.strftime('%Y-%m-%d %H:%M:%S')}")

        print()
        print_new_messages()


if __name__ == "__main__":
    main()
