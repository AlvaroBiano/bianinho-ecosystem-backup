"""
Bianinho Autonomous State — Persistência de Estado Entre Ciclos
Dir: ~/.hermes/autonomous/state.json
"""

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

STATE_FILE = Path.home() / ".hermes" / "autonomous" / "state.json"

def _load() -> dict:
    if STATE_FILE.exists():
        try:
            with open(STATE_FILE) as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            pass
    return _default()

def _default() -> dict:
    return {
        'version': 1,
        'cycle_id': None,
        'last_cycle_at': None,
        'last_cycle_duration_s': None,
        'cycles_total': 0,
        'last_cycle_summary': '',
        'active_tasks': [],         # task_ids currently running
        'pending_decisions': [],     # things to decide on next cycle
        'memory_snapshot': {
            'wins': [],
            'concerns': [],
            'ongoing': []
        },
        'health': {
            'rag_ok': True,
            'hermes_ok': True,
            'services_ok': True,
            'last_check': None
        },
        'flags': {},                # arbitrary key-value flags
        'journal': []              # recent significant events
    }

def _save(state: dict):
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(STATE_FILE, 'w') as f:
        json.dump(state, f, indent=2, ensure_ascii=False)

def begin_cycle() -> dict:
    """Inicia novo ciclo. Retorna state com novo cycle_id."""
    state = _load()
    state['cycle_id'] = str(uuid.uuid4())[:8]
    state['last_cycle_at'] = datetime.now(timezone.utc).isoformat()
    _save(state)
    return state

def end_cycle(cycle_id: str, duration_s: float, summary: str = '',
              decisions_made: list = None):
    """Finaliza ciclo e guarda resultado."""
    state = _load()
    if state['cycle_id'] != cycle_id:
        return  # wrong cycle, ignore
    state['cycles_total'] += 1
    state['last_cycle_duration_s'] = duration_s
    state['last_cycle_summary'] = summary
    state['active_tasks'] = []
    state['pending_decisions'] = decisions_made or []
    _save(state)

def get() -> dict:
    """Retorna estado actual."""
    return _load()

def set_flag(key: str, value: Any):
    """Define flag arbitrária."""
    state = _load()
    state['flags'][key] = value
    _save(state)

def get_flag(key: str, default: Any = None) -> Any:
    """Obtém flag."""
    return _load().get('flags', {}).get(key, default)

def add_journal(event_type: str, message: str, data: dict = None):
    """Adiciona entrada ao journal."""
    state = _load()
    entry = {
        'ts': datetime.now(timezone.utc).isoformat(),
        'type': event_type,
        'message': message,
        'data': data or {}
    }
    state['journal'].insert(0, entry)
    state['journal'] = state['journal'][:50]  # keep last 50
    _save(state)

def update_health(health: dict):
    """Actualiza estado de saúde."""
    state = _load()
    state['health'] = health
    _save(state)

def memory_append(memory_type: str, text: str):
    """Adiciona à memória do estado. Types: wins, concerns, ongoing."""
    state = _load()
    entry = {
        'ts': datetime.now(timezone.utc).isoformat(),
        'text': text
    }
    if memory_type not in state['memory_snapshot']:
        state['memory_snapshot'][memory_type] = []
    state['memory_snapshot'][memory_type].insert(0, entry)
    state['memory_snapshot'][memory_type] = state['memory_snapshot'][memory_type][:10]
    _save(state)

def active_task_push(task_id: str):
    """Marca tarefa como activa (em execução)."""
    state = _load()
    if task_id not in state['active_tasks']:
        state['active_tasks'].append(task_id)
    _save(state)

def active_task_done(task_id: str):
    """Remove tarefa das activas."""
    state = _load()
    if task_id in state['active_tasks']:
        state['active_tasks'].remove(task_id)
    _save(state)

if __name__ == '__main__':
    import sys
    if len(sys.argv) < 2:
        print(json.dumps(_load(), indent=2, ensure_ascii=False))
    elif sys.argv[1] == 'begin':
        print(begin_cycle())
    elif sys.argv[1] == 'stat':
        s = _load()
        print(f"Ciclos: {s['cycles_total']}")
        print(f"Último: {s['last_cycle_at']} ({s['last_cycle_duration_s']}s)")
        print(f"Resumo: {s['last_cycle_summary']}")
