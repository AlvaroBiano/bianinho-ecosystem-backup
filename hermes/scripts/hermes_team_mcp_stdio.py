#!/usr/bin/env python3
"""
Hermes Team MCP Stdio Server

Wrapper MCP stdio que expõe ferramentas de team do AionUI ao Hermes.
O Hermes usa isto como servidor MCP quando é Team Leader.

Protocolo TCP: 4-byte big-endian length header + JSON body
"""

import asyncio
import json
import os
import struct
import sys
from pathlib import Path

# ─── TCP Protocol ──────────────────────────────────────────────────────────────

def read_tcp_message(sock) -> dict:
    """Read a length-prefixed JSON message from TCP socket."""
    header = b""
    while len(header) < 4:
        chunk = sock.recv(4 - len(header))
        if not chunk:
            raise EOFError("Connection closed while reading header")
        header += chunk
    body_len = struct.unpack(">I", header)[0]
    body = b""
    while len(body) < body_len:
        chunk = sock.recv(body_len - len(body))
        if not chunk:
            raise EOFError("Connection closed while reading body")
        body += chunk
    return json.loads(body.decode("utf-8"))


def write_tcp_message(sock, data: dict) -> None:
    """Write a length-prefixed JSON message to TCP socket."""
    body = json.dumps(data).encode("utf-8")
    header = struct.pack(">I", len(body))
    sock.sendall(header + body)


def send_tcp_request(port, payload: dict, token: str) -> dict:
    """Send a request to AionUI TCP server and wait for response."""
    import socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(60)
    try:
        sock.connect(("127.0.0.1", port))
        write_tcp_message(sock, payload)
        return read_tcp_message(sock)
    finally:
        sock.close()


# ─── MCP Stdio Protocol ───────────────────────────────────────────────────────

async def read_json_rpc() -> dict:
    """Read a JSON-RPC message from stdin (blocking)."""
    loop = asyncio.get_event_loop()
    line = await loop.run_in_executor(None, sys.stdin.readline)
    if not line:
        raise EOFError("stdin closed")
    return json.loads(line)


def write_json_rpc(data: dict) -> None:
    """Write a JSON-RPC message to stdout."""
    sys.stdout.write(json.dumps(data) + "\n")
    sys.stdout.flush()


def send_response(req_id, result: dict) -> None:
    """Send a successful JSON-RPC response."""
    write_json_rpc({"jsonrpc": "2.0", "id": req_id, "result": result})


def send_error(req_id, code: int, message: str) -> None:
    """Send a JSON-RPC error response."""
    write_json_rpc({
        "jsonrpc": "2.0",
        "id": req_id,
        "error": {"code": code, "message": message}
    })


# ─── MCP Tools ────────────────────────────────────────────────────────────────

TOOLS = {}


def tool(name, description, schema):
    """Decorator to register an MCP tool."""
    def decorator(func):
        TOOLS[name] = {
            "name": name,
            "description": description,
            "inputSchema": schema,
            "fn": func
        }
        return func
    return decorator


def get_tools_schema() -> list:
    """Return the tools list for MCP initialize."""
    return [
        {"name": t["name"], "description": t["description"], "inputSchema": t["inputSchema"]}
        for t in TOOLS.values()
    ]


# ─── Tool Implementations ─────────────────────────────────────────────────────

@tool(
    "aion_create_team",
    "Create a new team with a leader agent",
    {
        "type": "object",
        "properties": {
            "summary": {"type": "string", "description": "Task summary or initial instruction for the team leader"},
            "name": {"type": "string", "description": "Optional team name"},
            "workspace": {"type": "string", "description": "Absolute path to project workspace directory"}
        },
        "required": ["summary"]
    }
)
def create_team(args: dict) -> dict:
    port = int(os.environ.get("AION_MCP_PORT", "0"))
    token = os.environ.get("AION_MCP_TOKEN", "")
    backend = os.environ.get("AION_MCP_BACKEND", "hermes")
    conversation_id = os.environ.get("AION_MCP_CONVERSATION_ID", "")

    if not port or not token:
        return {"error": "AION_MCP_PORT and AION_MCP_TOKEN environment variables are required"}

    payload = {
        "tool": "aion_create_team",
        "args": args,
        "auth_token": token,
        "backend": backend,
        "conversation_id": conversation_id
    }

    try:
        response = send_tcp_request(port, payload, token)
        return {"result": json.dumps(response.get("result", response))}
    except Exception as e:
        return {"error": str(e)}


@tool(
    "aion_list_models",
    "Query available models for team agent types",
    {
        "type": "object",
        "properties": {
            "agent_type": {"type": "string", "description": "Agent type/backend to query (e.g. gemini, claude, codex)"}
        }
    }
)
def list_models(args: dict) -> dict:
    port = int(os.environ.get("AION_MCP_PORT", "0"))
    token = os.environ.get("AION_MCP_TOKEN", "")
    backend = os.environ.get("AION_MCP_BACKEND", "hermes")
    conversation_id = os.environ.get("AION_MCP_CONVERSATION_ID", "")

    if not port or not token:
        return {"error": "AION_MCP_PORT and AION_MCP_TOKEN environment variables are required"}

    payload = {
        "tool": "aion_list_models",
        "args": args,
        "auth_token": token,
        "backend": backend,
        "conversation_id": conversation_id
    }

    try:
        response = send_tcp_request(port, payload, token)
        return {"result": json.dumps(response.get("result", response))}
    except Exception as e:
        return {"error": str(e)}


# ─── MCP Protocol Handlers ─────────────────────────────────────────────────────

async def handle_initialize(params: dict) -> dict:
    return {
        "protocolVersion": "2024-11-05",
        "capabilities": {"tools": {}},
        "serverInfo": {
            "name": "hermes-team-mcp",
            "version": "1.0.0"
        }
    }


async def handle_tools_list(params: dict) -> dict:
    return {"tools": get_tools_schema()}


async def handle_tools_call(params: dict) -> dict:
    tool_name = params.get("name")
    arguments = params.get("arguments", {})

    if tool_name not in TOOLS:
        raise ValueError(f"Unknown tool: {tool_name}")

    tool_fn = TOOLS[tool_name]["fn"]
    result = tool_fn(arguments)

    if "error" in result:
        raise ValueError(result["error"])

    return {
        "content": [{"type": "text", "text": result.get("result", json.dumps(result))}]
    }


async def handle_request(req: dict) -> None:
    method = req.get("method", "")
    req_id = req.get("id")
    params = req.get("params", {})

    try:
        if method == "initialize":
            result = await handle_initialize(params)
            send_response(req_id, result)

        elif method == "tools/list":
            result = await handle_tools_list(params)
            send_response(req_id, result)

        elif method == "tools/call":
            result = await handle_tools_call(params)
            send_response(req_id, result)

        elif method == "notifications/initialized":
            # Client ready signal - no response needed
            pass

        else:
            send_error(req_id, -32601, f"Method not found: {method}")

    except Exception as e:
        send_error(req_id, -32603, f"Internal error: {e}")


async def main() -> None:
    """Main loop: read JSON-RPC requests from stdin and handle them."""
    sys.stderr.write(
        f"[hermes-team-mcp] Started. PID={os.getpid()}, "
        f"AION_MCP_PORT={os.environ.get('AION_MCP_PORT', 'unset')}, "
        f"BACKEND={os.environ.get('AION_MCP_BACKEND', 'unset')}\n"
    )
    sys.stderr.flush()

    try:
        while True:
            try:
                line = sys.stdin.readline()
                if not line:
                    break
                req = json.loads(line)
                await handle_request(req)
            except json.JSONDecodeError as e:
                sys.stderr.write(f"[hermes-team-mcp] JSON parse error: {e}\n")
                sys.stderr.flush()
            except Exception as e:
                sys.stderr.write(f"[hermes-team-mcp] Error: {e}\n")
                sys.stderr.flush()
    except KeyboardInterrupt:
        pass
    finally:
        sys.stderr.write("[hermes-team-mcp] Shutting down\n")
        sys.stderr.flush()


if __name__ == "__main__":
    asyncio.run(main())
