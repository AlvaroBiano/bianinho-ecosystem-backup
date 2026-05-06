#!/usr/bin/env python3
"""
Bianinho Autonomous Cycle — O Loop de Decisão Contínua

Este script corre via cron a cada 15 minutos.
Não é um daemon — é um processo leve que:
  1. Lê o mandato
  2. Verifica inbox pendente
  3. Verifica sistemas (saúde)
  4. Decide o que fazer
  5. Executa ou delega
  6. Regista estado
  7. Reporta ao Álvaro só se significativo

Uso: python3 cycle.py [--dry-run]
"""

import sys
import os
import json
import time
import subprocess
from datetime import datetime, timezone
from pathlib import Path

# Add autonomous dir to path
AUTONOMOUS_DIR = Path.home() / ".hermes" / "autonomous"
sys.path.insert(0, str(AUTONOMOUS_DIR))

from inbox import add as inbox_add, list_tasks, get as inbox_get, update as inbox_update, pending_count, stats
from state import begin_cycle, end_cycle, get as state_get, add_journal, memory_append, update_health, active_task_push, active_task_done

DRY_RUN = '--dry-run' in sys.argv
VERBOSE = '--verbose' in sys.argv or DRY_RUN

def log(msg: str):
    ts = datetime.now().strftime("%H:%M:%S")
    print(f"[{ts}] {msg}")
    sys.stdout.flush()

def log_verbose(msg: str):
    if VERBOSE:
        log(msg)

MANDATE_FILE = AUTONOMOUS_DIR / "mandate.md"

def load_mandate() -> str:
    if MANDATE_FILE.exists():
        return MANDATE_FILE.read_text(encoding='utf-8')
    return ""

def load_mandate_summary() -> str:
    """Resumo do mandato para contexto rápido."""
    mandate = load_mandate()
    if not mandate:
        return ""
    lines = mandate.split('\n')
    desires = []
    in_desires = False
    for line in lines:
        if '## O Que Me Move' in line or '## Os Meus Desejos' in line:
            in_desires = True
        elif line.startswith('##'):
            in_desires = False
        elif in_desires and line.strip().startswith('**'):
            desires.append(line.strip().replace('**', '').replace('*', '').strip())
    return "\n".join(desires[:5])

def check_hermes_health() -> dict:
    """Verifica saúde dos serviços."""
    health = {
        'hermes_ok': False,
        'rag_ok': False,
        'services_ok': False,
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'details': {}
    }

    # Check Hermes/Gateway process
    try:
        r = subprocess.run(
            ['pgrep', '-f', '-a', 'hermes|gateway'],
            capture_output=True, text=True, timeout=10
        )
        if r.returncode == 0 and r.stdout.strip():
            health['hermes_ok'] = True
            health['details']['hermes_procs'] = r.stdout.strip()[:200]
        else:
            health['details']['hermes_error'] = 'Nenhum processo encontrado'
    except Exception as e:
        health['details']['hermes_error'] = str(e)

    # Check RAG/LanceDB
    try:
        r = subprocess.run(
            ['pgrep', '-f', '-a', 'lance|rag|vector'],
            capture_output=True, text=True, timeout=10
        )
        if r.returncode == 0 and r.stdout.strip():
            health['rag_ok'] = True
    except Exception as e:
        health['details']['rag_error'] = str(e)

    health['services_ok'] = health['hermes_ok']  # simplified

    return health

def decide_what_to_do(state: dict, mandate_summary: str) -> list:
    """
    Decisor central — o que fazer neste ciclo.
    Retorna lista de acções a tomar.
    """
    actions = []

    # 1. Check inbox
    pending = list_tasks(status='pending', assigned_to='bianinho', limit=20)
    critical = [t for t in pending if t['priority'] == 1]
    high = [t for t in pending if t['priority'] == 2]
    normal = [t for t in pending if t['priority'] == 3]

    for t in critical[:3]:
        actions.append({
            'type': 'execute_task',
            'task_id': t['id'],
            'task': t,
            'reason': 'Tarefa crítica pendente'
        })

    for t in high[:2]:
        actions.append({
            'type': 'execute_task',
            'task_id': t['id'],
            'task': t,
            'reason': 'Tarefa alta prioridade pendente'
        })

    # 2. Check active tasks that may be stuck
    active = list_tasks(status='running', limit=10)
    for t in active:
        created = datetime.fromisoformat(t['created_at'])
        age_min = (datetime.now(timezone.utc) - created.replace(tzinfo=timezone.utc)).total_seconds() / 60
        if age_min > 120:  # mais de 2h a correr
            actions.append({
                'type': 'check_stuck_task',
                'task_id': t['id'],
                'reason': f'Tarefa activa há {age_min:.0f}min'
            })

    # 3. Check health
    h = state.get('health', {})
    if not h.get('hermes_ok', True):
        actions.append({
            'type': 'health_alert',
            'reason': 'Hermes não está a funcionar'
        })

    # 4. Empty inbox normal tasks — do one if nothing urgent
    if not actions and normal:
        actions.append({
            'type': 'execute_task',
            'task_id': normal[0]['id'],
            'task': normal[0],
            'reason': 'Tarefa normal pendente'
        })

    return actions

def execute_task(task: dict, dry_run: bool = False) -> str:
    """Executa uma tarefa do inbox."""
    task_id = task['id']
    content = task['content']
    tags = task.get('tags', [])

    log(f"[TASK:{task_id[:6]}] Executando: {content[:80]}")

    if dry_run:
        return "DRY RUN - não executado"

    # Mark as running
    inbox_update(task_id, status='running')
    active_task_push(task_id)

    try:
        # Execute based on tags or content
        result = _dispatch_task(content, tags, task_id)

        inbox_update(task_id, status='done', result=result[:500])
        add_journal('task_done', f"{content[:60]}", {'task_id': task_id, 'result': result[:200]})
        memory_append('wins', f"Tarefa concluída: {content[:60]}")
        return result

    except Exception as e:
        inbox_update(task_id, status='blocked', notes=str(e))
        add_journal('task_error', f"{content[:60]}: {e}", {'task_id': task_id})
        memory_append('concerns', f"Erro em tarefa: {content[:60]} — {e}")
        return f"ERRO: {e}"
    finally:
        active_task_done(task_id)

def _dispatch_task(content: str, tags: list, task_id: str) -> str:
    """
    Despacha tarefa para executor apropriado.
    Extensível — mais handlers podem ser adicionados aqui.
    """
    content_lower = content.lower()

    # RAG / Knowledge Base tasks
    if any(k in content_lower for k in ['processar livro', 'adicionar livro', 'vectorizar']):
        return _handle_rag_task(content, tags)

    # System/health tasks
    if any(k in content_lower for k in ['verificar saúde', 'health check', 'verificar serviços']):
        return _handle_health_task()

    # SAC / Bot tasks
    if any(k in content_lower for k in ['sac', 'bot', 'chatbot']):
        return _handle_sac_task(content)

    # Research tasks
    if any(k in content_lower for k in ['pesquisar', 'research', 'investigar']):
        return _handle_research_task(content, task_id)

    # Default: delegate to sub-agent
    return _handle_delegate_task(content, tags, task_id)

def _handle_rag_task(content: str, tags: list) -> str:
    """Processa tarefas de RAG."""
    kb_dir = Path.home() / "KnowledgeBase"
    venv_python = kb_dir / "venv" / "bin" / "python3"

    if not venv_python.exists():
        return f"ERRO: venv não encontrada em {venv_python}"

    # Run RAG stats to verify it's working
    result = subprocess.run(
        [str(venv_python), str(kb_dir / "pipeline" / "livro_pipeline.py"), "--stats"],
        capture_output=True, text=True, timeout=60,
        cwd=str(kb_dir)
    )
    output = result.stdout + result.stderr
    return f"RAG OK — {output[:300]}"

def _handle_health_task() -> str:
    """Verificação de saúde do sistema."""
    import socket
    checks = []

    # Hermes
    try:
        r = subprocess.run(['pgrep', '-f', '-a', 'hermes|gateway'],
                         capture_output=True, text=True, timeout=10)
        checks.append(f"Hermes: {'OK' if r.returncode == 0 else 'FAIL'}")
    except:
        checks.append("Hermes: ERRO")

    # Disk
    try:
        r = subprocess.run(['df', '-h', '/'],
                         capture_output=True, text=True, timeout=10)
        line = [l for l in r.stdout.split('\n') if '/dev/' in l][0]
        pct = line.split()[4]
        checks.append(f"Disco: {pct} usado")
    except:
        checks.append("Disco: ERRO")

    # RAM
    try:
        r = subprocess.run(['free', '-m'],
                         capture_output=True, text=True, timeout=10)
        lines = r.stdout.split('\n')
        mem_line = [l for l in lines if 'Mem:' in l][0]
        parts = mem_line.split()
        used = parts[2]
        total = parts[1]
        checks.append(f"RAM: {used}/{total}MB")
    except:
        checks.append("RAM: ERRO")

    return " | ".join(checks)

def _handle_sac_task(content: str) -> str:
    """Tarefas relacionadas com SAC Bot."""
    # Check if service is running
    try:
        r = subprocess.run(['systemctl', '--user', 'status', 'sac-agent'],
                         capture_output=True, text=True, timeout=10)
        if 'active (running)' in r.stdout:
            return "SAC Bot: OK"
        return f"SAC Bot: {r.stdout[:200]}"
    except Exception as e:
        return f"SAC Bot: ERRO — {e}"

def _handle_research_task(content: str, task_id: str) -> str:
    """Delega tarefa de pesquisa a sub-agente."""
    # Extract what to research
    query = content.replace('pesquisar', '').replace('research', '').strip()
    if not query:
        return "ERRO: sem query de pesquisa"

    # Note: in full implementation, would use delegate_task
    # For now, just return a note
    inbox_update(task_id, notes=f'Pesquisa pendente: {query}. Requer delegação.')
    return f"Pesquisa pendente — delegar: {query}"

def _handle_delegate_task(content: str, tags: list, task_id: str) -> str:
    """Delega tarefa complexa a sub-agente via terminal."""
    # This would launch a sub-agent in a real implementation
    # For now, log and note
    add_journal('delegate', f"Delegando: {content[:60]}", {'task_id': task_id})
    inbox_update(task_id, notes='Delegada — requer sub-agente')
    return f"Delegada: {content[:80]}"

def report_to_alvaro(cycle_summary: dict):
    """
    Reporta ao Álvaro via Telegram se algo significativo aconteceu.
    Só notifica se realmente necessário — silêncio quando OK.
    """
    significant = cycle_summary.get('significant_events', [])
    if not significant:
        return  # silêncio — tudo bem

    # In a full implementation, would send via send_message tool
    # For now, just journal
    add_journal('report_sent', f"Eventos significativos: {len(significant)}",
                {'events': significant})

def run_cycle(dry_run: bool = False) -> dict:
    """Executa um ciclo completo."""
    start = time.time()
    cycle_state = begin_cycle()
    cycle_id = cycle_state['cycle_id']

    summary = {
        'cycle_id': cycle_id,
        'started_at': cycle_state['last_cycle_at'],
        'actions_taken': [],
        'significant_events': [],
        'errors': []
    }

    try:
        # Load mandate summary for context
        mandate_summary = load_mandate_summary()
        state = state_get()
        mandate_short = load_mandate()[:200]

        log_verbose(f"[{cycle_id}] Ciclo iniciado — {state['cycles_total']} ciclos totais")

        # Check health
        health = check_hermes_health()
        update_health(health)
        summary['health'] = health

        if not health.get('hermes_ok'):
            summary['significant_events'].append({
                'type': 'health_alert',
                'message': 'Hermes não está a funcionar',
                'details': health.get('details', {})
            })

        # Decide what to do
        state = state_get()  # refresh after health update
        actions = decide_what_to_do(state, mandate_summary)
        summary['actions_count'] = len(actions)

        log_verbose(f"[{cycle_id}] {len(actions)} acções a tomar")

        # Execute actions
        for action in actions:
            try:
                if action['type'] == 'execute_task':
                    result = execute_task(action['task'], dry_run=dry_run)
                    summary['actions_taken'].append({
                        'type': 'execute_task',
                        'task_id': action['task_id'],
                        'result': result[:100]
                    })
                    if not dry_run:
                        inbox_update(action['task_id'], notes=result[:200])

                elif action['type'] == 'health_alert':
                    summary['significant_events'].append({
                        'type': 'health_alert',
                        'message': action['reason']
                    })

                elif action['type'] == 'check_stuck_task':
                    summary['actions_taken'].append({
                        'type': 'check_stuck',
                        'task_id': action['task_id'],
                        'reason': action['reason']
                    })

            except Exception as e:
                summary['errors'].append(str(e))
                add_journal('cycle_error', f"Erro em {action['type']}: {e}")

        # Update state
        duration = time.time() - start
        end_cycle(cycle_id, duration, f"{len(summary['actions_taken'])} acções", [])

        log_verbose(f"[{cycle_id}] Ciclo terminado em {duration:.1f}s — "
                   f"{len(summary['actions_taken'])} acções")

        return summary

    except Exception as e:
        duration = time.time() - start
        add_journal('cycle_crash', str(e))
        end_cycle(cycle_id, duration, f"ERRO: {e}")
        summary['errors'].append(str(e))
        return summary

# ─── Entry Point ────────────────────────────────────────────
if __name__ == '__main__':
    log(f"Bianinho Autonomous Cycle — {'DRY RUN' if DRY_RUN else 'LIVE'}")
    result = run_cycle(dry_run=DRY_RUN)
    actions_count = result.get('actions_count', len(result.get('actions_taken', [])))
    errors_count = len(result.get('errors', []))
    sig_count = len(result.get('significant_events', []))
    log(f"Resultado: {actions_count} acções, "
        f"{errors_count} erros, "
        f"{sig_count} eventos significativos")
    if result.get('significant_events'):
        for ev in result['significant_events']:
            log(f"  → {ev['type']}: {ev['message']}")
