#!/usr/bin/env python3
"""
PROATIVO — Health Monitor
Monitoreia sistemas críticos e age automaticamente quando detecta problemas.
Baseado em: PROBE framework (arxiv 2510.19771) — 3 capacidades:
  1. Buscar problemas não especificados
  2. Identificar bloqueios específicos
  3. Executar resoluções apropriadas
"""
import os, sys, json, time, urllib.request, subprocess
from datetime import datetime

LOG_FILE = "/home/alvarobiano/.hermes/logs/proactive_health.log"
os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)

def log(msg, level="INFO"):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] [{level}] {msg}"
    print(line)
    with open(LOG_FILE, "a") as f:
        f.write(line + "\n")

def http_get(url, timeout=5):
    try:
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read().decode()), None
    except Exception as e:
        return None, str(e)

def check_hermes_gateway():
    data, err = http_get("http://127.0.0.1:3100/api/health")
    if err:
        return False, f"Hermes: ERRO — {err}"
    if data.get("status") != "ok":
        return False, f"Hermes: status={data.get('status')}"
    return True, f"Hermes: OK (v{data.get('version','?')})"

def check_rag_server():
    data, err = http_get("http://127.0.0.1:3101/health")
    if err:
        return False, "RAG server: offline", None
    if not data.get("initialized"):
        return False, "RAG server: initialized=false", "init_rag"
    return True, "RAG server: OK", None

def check_paperclip_issues():
    company_id = "f63fa443-eb1a-4de8-8d61-aebc42dae20f"
    try:
        result = subprocess.run(
            ["curl", "-s", "--max-time", "8", f"http://127.0.0.1:3100/api/companies/{company_id}/issues?status=backlog"],
            capture_output=True, text=True
        )
        data = json.loads(result.stdout)
        unassigned = [i for i in data if not i.get("assigneeAgentId")]
        if unassigned:
            return len(unassigned), f"Paperclip: {len(unassigned)} backlog sem assignee", unassigned[:3]
        return 0, f"Paperclip: {len(data)} issues OK", None
    except Exception as e:
        return None, f"Paperclip: ERRO — {e}", None

def check_disk():
    try:
        result = subprocess.run(["df", "-h", "/"], capture_output=True, text=True, timeout=5)
        parts = result.stdout.strip().split("\n")[1].split()
        used_pct = int(parts[4].replace("%", ""))
        free = parts[3]
        if used_pct > 80:
            return False, f"Disco: {used_pct}% usado ({free} livre) — CRÍTICO"
        return True, f"Disco: {used_pct}% usado ({free} livre)"
    except Exception as e:
        return True, f"Disco: OK (erro na leitura: {e})"

def check_memory():
    try:
        result = subprocess.run(["free", "-h"], capture_output=True, text=True, timeout=5)
        for line in result.stdout.split("\n"):
            if "Mem:" in line:
                parts = line.split()
                return True, f"Memória: {parts[2]}/{parts[1]} usado, {parts[6]} disponível"
    except Exception as e:
        return True, f"Memória: OK (erro na leitura: {e})"
    return True, "Memória: OK"

def check_minimax_api():
    # Load API key
    env_file = "/home/alvarobiano/.hermes/.env"
    api_key = None
    if os.path.exists(env_file):
        with open(env_file) as f:
            for line in f:
                line = line.strip()
                if line.startswith("MINIMAX_API_KEY="):
                    api_key = line.split("=", 1)[1].strip()
                    break
    if not api_key:
        return None, "MiniMax: API key não encontrada"
    try:
        url = "https://api.minimax.io/v1/text/chatcompletion_v2"
        body = json.dumps({
            "model": "MiniMax-M2.7",
            "messages": [{"role": "user", "content": "OK"}],
            "max_tokens": 5
        }).encode()
        req = urllib.request.Request(url, data=body, headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }, method="POST")
        with urllib.request.urlopen(req, timeout=15) as resp:
            result = json.loads(resp.read().decode())
            base = result.get("base_resp", {})
            if base.get("status_code") == 0:
                return True, "MiniMax API: OK"
            return False, f"MiniMax: erro {base.get('status_msg')}"
    except Exception as e:
        return False, f"MiniMax: ERRO — {str(e)[:60]}"

def auto_fix_rag():
    """Tenta reiniciar o RAG server se necessário."""
    log("RAG server não inicializado — tentando resolver...", "WARN")
    try:
        # Try curl POST to /init
        result = subprocess.run(
            ["curl", "-s", "-X", "POST", "--max-time", "5", "http://127.0.0.1:3101/init"],
            capture_output=True, text=True
        )
        time.sleep(3)
        data, _ = http_get("http://127.0.0.1:3101/health")
        if data and data.get("initialized"):
            log("RAG server inicializado com sucesso!", "OK")
            return True
    except Exception as e:
        log(f"Falha ao inicializar RAG: {e}", "ERROR")
    return False

def run_health_check():
    log("=" * 50)
    log("PROATIVO HEALTH CHECK")
    
    issues_found = []
    auto_fixed = []
    
    checks = [
        ("Hermes Gateway", check_hermes_gateway),
        ("RAG Server", check_rag_server),
        ("Paperclip", check_paperclip_issues),
        ("Disco", check_disk),
        ("Memória", check_memory),
        ("MiniMax API", check_minimax_api),
    ]
    
    for name, check_fn in checks:
        try:
            result = check_fn()
            if result is None:
                continue
            
            # Unpack — 2 ou 3 elementos
            if isinstance(result, tuple) and len(result) == 3:
                ok, msg, detail = result
            else:
                ok, msg = result
                detail = None
            
            if name == "Paperclip":
                count = ok if isinstance(ok, int) else 0
                if count and count > 0:
                    issues_found.append((name, msg, detail))
                    log(msg, "WARN")
                else:
                    log(msg, "INFO")
            elif name == "RAG Server":
                if not ok and detail == "init_rag":
                    issues_found.append((name, msg, detail))
                    log(msg, "WARN")
                elif not ok:
                    issues_found.append((name, msg, detail))
                    log(msg, "WARN")
                else:
                    log(msg, "INFO")
            elif not ok:
                issues_found.append((name, msg, detail))
                log(msg, "WARN")
            else:
                log(msg, "INFO")
        except Exception as e:
            log(f"{name}: EXCEPTION — {e}", "ERROR")
            issues_found.append((name, str(e), None))
    
    # Auto-resolution
    for name, msg, detail in issues_found:
        if name == "RAG Server" and detail == "init_rag":
            if auto_fix_rag():
                auto_fixed.append("RAG server")
    
    # Summary
    if not issues_found:
        log("TODOS OS SISTEMAS SAUDÁVEIS", "INFO")
    else:
        if auto_fixed:
            log(f"Auto-corrigidos: {auto_fixed}", "OK")
        log(f"PROBLEMAS: {len(issues_found)}", "WARN")
    
    return len(issues_found), auto_fixed

if __name__ == "__main__":
    run_health_check()
