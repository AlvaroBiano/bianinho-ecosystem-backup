---
name: session-bridge-integration
description: Implement cross-platform session persistence for Hermes Agent (Telegram ↔ CLI ↔ WhatsApp). Enables context continuity when users switch platforms.
version: 1.1.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [hermes, gateway, session, bridge, cross-platform, persistence]
    related_skills: [hermes-agent]
---

# SessionBridge Integration

Enables cross-platform context persistence for Hermes Agent so users can switch between Telegram, CLI, WhatsApp, and other platforms while maintaining conversation continuity.

## Current Status

| Component | Status | Location |
|-----------|--------|----------|
| `session_bridge.py` core module | ✅ IMPLEMENTED (862 lines) | `~/KnowledgeBase/session_bridge.py` |
| `gateway_session_bridge_integration.py` | 🚫 NOT YET BUILT | `~/.hermes/hermes-agent/gateway/` |
| Gateway integration points in `run.py` | ✅ PATCHED (3 locations) | Integration code exists, needs module |
| CLI bridge support in `cli.py` | ✅ PATCHED | `cli.py` lines ~2990-3058 |

## Architecture

Three-layer design:
1. **UserIdentity layer** — Maps platform-specific IDs to canonical user ID
2. **SessionBridge core** — Maintains user identities, pending work, session linking
3. **Integration hooks** — Gateway (`run.py`) and CLI (`cli.py`) injection points

---

## Implemented: Core SessionBridge Module

**File:** `~/KnowledgeBase/session_bridge.py`

### Dataclasses

**`PlatformSession`** — Uma sessão activa numa plataforma específica.
- `platform: str` — "telegram", "cli", "whatsapp"
- `session_key: str` — agent:main:telegram:dm:435025823 (gateway session key)
- `session_id: str` — 20260416_091234 (state.db id)
- `started_at: str` — ISO datetime
- `last_active: str` — ISO datetime
- `topic: str` — tópico actual da conversa
- `message_count: int` — mensagens trocadas nesta sessão
- `pending_task: str` — descrição da tarefa pendente

**`UserIdentity`** — Identidade unificada do utilizador através de todas as plataformas.
- `canonical_user_id: str` — "435025823" (Telegram user ID do Álvaro)
- `display_name: str` — "Álvaro Biano"
- `platform_sessions: dict[str, PlatformSession]`
- `is_primary_user: bool` — True = é o dono do sistema

**`PendingWork`** — Estado de trabalho activo que persiste entre plataformas.
- `canonical_user_id: str`
- `task: str` — descrição da tarefa em progresso
- `task_detail: str` — detalhes adicionais
- `active: bool`
- `context_summary: str` — max 500 chars
- `conversation_snippet: str` — últimos 3-5 msgs, max 1000 chars
- `parent_session_id: str` — state.db parent session para continuação

### SessionBridge Methods

```python
from session_bridge import SessionBridge, get_session_bridge

sb = get_session_bridge()

# Platform session management
sb.register_primary_user("435025823", "Álvaro Biano")
sb.register_platform_session("435025823", "telegram", "agent:main:telegram:dm:435025823", "20260416_091234")
sb.update_session_activity("435025823", "telegram", message_count=14)
sb.deactivate_platform("435025823", "cli")

# Pending work management
sb.update_pending_work("435025823", task="Revisar método TEN", active=True, last_platform="telegram")
pending = sb.get_pending_work("435025823")
sb.set_task_done("435025823")

# Cross-platform switching
sb.switch_platform("435025823", new_platform="cli")
sb.build_bridge_context("435025823", "cli")

# Discovery
sb.resolve_canonical_id("telegram", session_id="20260416_091234")
sb.get_primary_user()

# Status
sb.get_status()
```

---

## NOT YET BUILT: Gateway Integration Module

**File to create:** `~/.hermes/hermes-agent/gateway/gateway_session_bridge_integration.py`

### Required Functions

The patched integration points in `run.py` and `cli.py` expect these functions:

```python
"""
gateway_session_bridge_integration.py
Gateway integration layer between SessionBridge and Hermes gateway/CLI.
Lazy import of SessionBridge to avoid hard dependency.
"""

import sys
from pathlib import Path

# Add KnowledgeBase to path for session_bridge import
_KB_PATH = Path.home() / "KnowledgeBase"
if str(_KB_PATH) not in sys.path:
    sys.path.insert(0, str(_KB_PATH))

from session_bridge import get_session_bridge, SessionBridge

def get_session_bridge() -> SessionBridge:
    """Get or create the SessionBridge singleton."""
    from session_bridge import get_session_bridge as _get
    return _get()

def register_gateway_session(bridge: SessionBridge, source, session_entry) -> None:
    """
    Register a gateway session with the SessionBridge.
    
    Called from run.py after get_or_create_session().
    source: MessageSource with platform, chat_id, user_id attributes
    session_entry: SessionEntry with session_key, session_id attributes
    """
    try:
        canonical_user_id = str(source.user_id) if source.user_id else None
        if not canonical_user_id:
            return
        
        platform = source.platform.value if hasattr(source.platform, 'value') else str(source.platform)
        session_key = session_entry.session_key
        session_id = session_entry.session_id
        
        bridge.register_platform_session(
            canonical_user_id=canonical_user_id,
            platform=platform,
            session_key=session_key,
            session_id=session_id,
            topic=getattr(source, 'topic', '') or '',
        )
    except Exception:
        pass  # Silently ignore errors

def get_bridge_context(bridge: SessionBridge, source, session_entry) -> str:
    """
    Get cross-platform context to inject into system prompt.
    
    Called from run.py before context_prompt is built.
    Returns context string or empty string if no pending work.
    """
    try:
        canonical_user_id = str(source.user_id) if source.user_id else None
        if not canonical_user_id:
            return ""
        
        platform = source.platform.value if hasattr(source.platform, 'value') else str(source.platform)
        return bridge.build_bridge_context(canonical_user_id, platform)
    except Exception:
        return ""

def update_bridge_pending_work(bridge: SessionBridge, source, session_entry, message_text: str, response: str) -> None:
    """
    Update pending work after agent response.
    
    Called from run.py after agent response is generated.
    Extracts task info from message_text and response to build context_summary.
    """
    try:
        canonical_user_id = str(source.user_id) if source.user_id else None
        if not canonical_user_id:
            return
        
        platform = source.platform.value if hasattr(source.platform, 'value') else str(source.platform)
        
        # Build conversation snippet from message + response
        snippet = f"User: {message_text[:200]}\nAgent: {response[:200]}"
        
        # Check for task indicators in conversation
        task = ""
        if "tarefa" in message_text.lower() or "task" in message_text.lower():
            task = message_text[:100]
        
        bridge.update_pending_work(
            user_id=canonical_user_id,
            task=task,
            last_platform=platform,
            active=bool(task),
            conversation_snippet=snippet,
            message_count=getattr(session_entry, 'message_count', 0) if session_entry else 0,
        )
    except Exception:
        pass

def inject_bridge_context(bridge: SessionBridge, source, session_id: str) -> str:
    """
    Inject bridge context for CLI bridge mode.
    
    Called from cli.py when --bridge flag is used.
    Returns context string to inject into system prompt.
    """
    try:
        canonical_user_id = str(source.chat_id)  # In CLI bridge, chat_id is the canonical user
        platform = source.platform
        
        return bridge.build_bridge_context(canonical_user_id, platform)
    except Exception:
        return ""

def get_auto_bridge_context_for_cli() -> tuple:
    """
    Auto-detect pending work from any platform for CLI.
    
    Called from cli.py when no explicit --bridge specified.
    Returns (source_description: str, context: str) or (None, None) if nothing found.
    """
    try:
        bridge = get_session_bridge()
        active = bridge.pending.list_active()
        
        if not active:
            return (None, None)
        
        # Get the most recent active work
        most_recent = max(active, key=lambda w: w.started_at)
        
        platform = most_recent.last_platform or "unknown"
        source_desc = f"auto:{platform}:{most_recent.canonical_user_id}"
        
        context = bridge.build_bridge_context(most_recent.canonical_user_id, "cli")
        
        return (source_desc, context)
    except Exception:
        return (None, None)
```

---

## Patched Integration Points

### Gateway run.py — Three Integration Points

**Point 1:** After `get_or_create_session` (grep: `SessionBridge: register gateway session`)
```python
# SessionBridge: register gateway session
try:
    from gateway_session_bridge_integration import (
        get_session_bridge,
        register_gateway_session,
    )
    bridge = get_session_bridge()
    if bridge:
        register_gateway_session(bridge, source, session_entry)
except ImportError:
    pass  # SessionBridge not installed
```

**Point 2:** Before `context_prompt` building (grep: `SessionBridge: inject cross-platform context`)
```python
# SessionBridge: inject cross-platform context
try:
    from gateway_session_bridge_integration import (
        get_session_bridge,
        get_bridge_context,
    )
    bridge = get_session_bridge()
    if bridge:
        bridge_context = get_bridge_context(bridge, source, session_entry)
        if bridge_context:
            context_prompt = bridge_context + "\n\n" + context_prompt
except ImportError:
    pass  # SessionBridge not installed
```

**Point 3:** After agent response (grep: `SessionBridge: update pending work after agent response`)
```python
# SessionBridge: update pending work after agent response
try:
    from gateway_session_bridge_integration import (
        get_session_bridge,
        update_bridge_pending_work,
    )
    bridge = get_session_bridge()
    if bridge:
        update_bridge_pending_work(
            bridge, source, session_entry,
            message_text, response
        )
except ImportError:
    pass  # SessionBridge not installed
```

### CLI cli.py — Bridge Support (lines ~2990-3058)

The CLI is already patched to support `--bridge` parameter:

```python
# In HermesCLI.__init__:
self.bridge = bridge  # New parameter

# In _init_agent() method:
# Explicit bridge: --bridge "telegram:435025823"
if self.bridge:
    from gateway_session_bridge_integration import (
        get_session_bridge,
        inject_bridge_context,
    )
    # Parse "platform:chat_id" or "platform:chat_id:thread_id"
    # Create MockSource and inject context

# Auto-detect: no explicit bridge specified
else:
    from gateway_session_bridge_integration import (
        get_auto_bridge_context_for_cli,
    )
    source, context = get_auto_bridge_context_for_cli()
```

---

## Usage

### CLI with Explicit Bridge
```bash
hermes --bridge "telegram:435025823"
```

### CLI with Auto-Detection
```bash
hermes  # Auto-detects pending work from any platform
```

### Bridge Format
- `platform:chat_id` (e.g., `telegram:435025823`)
- `platform:chat_id:thread_id` (e.g., `telegram:435025823:17585`)

### Manual Testing
```bash
# Test SessionBridge core directly
cd ~/KnowledgeBase
python -c "
from session_bridge import SessionBridge, get_session_bridge

sb = get_session_bridge()
print('Status:', sb.get_status())

sb.register_platform_session(
    '435025823', 'telegram',
    'agent:main:telegram:dm:435025823',
    '20260416_091234'
)
pending = sb.get_pending_work('435025823')
print(f'Pending work: {pending}')

ctx = sb.build_bridge_context('435025823', 'cli')
print(f'Bridge context:\\n{ctx}')
"
```

---

## File Locations

```
~/KnowledgeBase/
├── session_bridge.py              # ✅ Core SessionBridge (862 lines)
├── test_session_bridge.py         # Test suite
└── .session_bridge/               # Runtime data (created on first use)
    ├── user_identities.json
    ├── pending_work.json
    └── bridge_meta.json

~/.hermes/hermes-agent/
├── gateway/
│   ├── run.py                     # ✅ 3 integration points patched
│   └── gateway_session_bridge_integration.py  # 🚫 TO BE CREATED
└── cli.py                         # ✅ Bridge support patched (~lines 2990-3058)
```

---

## Verification Checklist

### Pre-requisites
```bash
# 1. Verify session_bridge.py exists and imports correctly
cd ~/KnowledgeBase
python -c "from session_bridge import SessionBridge, get_session_bridge; print('OK')"

# 2. Check integration points exist in run.py
grep -n "SessionBridge:" ~/.hermes/hermes-agent/gateway/run.py

# 3. Check CLI bridge support in cli.py
grep -n "bridge" ~/.hermes/hermes-agent/cli.py | head -20
```

### Test After Creating gateway_session_bridge_integration.py

```bash
# 1. Verify gateway integration module imports
cd ~/.hermes/hermes-agent/gateway
python -c "from gateway_session_bridge_integration import get_session_bridge, register_gateway_session, get_bridge_context, update_bridge_pending_work, inject_bridge_context, get_auto_bridge_context_for_cli; print('All imports OK')"

# 2. Test get_session_bridge returns valid instance
python -c "
from gateway_session_bridge_integration import get_session_bridge
bridge = get_session_bridge()
print('Bridge status:', bridge.get_status())
"

# 3. Test auto-detection (with no pending work)
python -c "
from gateway_session_bridge_integration import get_auto_bridge_context_for_cli
result = get_auto_bridge_context_for_cli()
print('Auto-detect result:', result)
"

# 4. Test inject_bridge_context
python -c "
from gateway_session_bridge_integration import inject_bridge_context, get_session_bridge

class MockSource:
    platform = 'telegram'
    chat_id = '435025823'
    thread_id = None

bridge = get_session_bridge()
ctx = inject_bridge_context(bridge, MockSource(), 'test_session')
print('Context:', repr(ctx[:100] if ctx else ''))
"

# 5. Test register_gateway_session (mock integration)
python -c "
from gateway_session_bridge_integration import register_gateway_session, get_session_bridge

class MockSource:
    class platform:
        value = 'telegram'
    user_id = '435025823'
    chat_id = '435025823'

class MockSession:
    session_key = 'agent:main:telegram:dm:435025823'
    session_id = '20260417_120000'

bridge = get_session_bridge()
register_gateway_session(bridge, MockSource(), MockSession())
print('Registered. Status:', bridge.get_status())
"
```

### Integration Verification

```bash
# 1. Verify gateway run.py integration points are reachable
cd ~/.hermes/hermes-agent/gateway
python -c "
import run
# Just importing should not raise errors about missing integration
print('run.py imports OK')
"

# 2. Check that gateway gracefully handles missing integration (ImportError = silent pass)
grep -A2 "except ImportError" ~/.hermes/hermes-agent/gateway/run.py | grep -c "pass"
# Should show "3" (one for each integration point)

# 3. Test CLI with bridge flag (dry run - just check it parses)
cd ~/.hermes/hermes-agent
python -c "
import sys
sys.argv = ['hermes', '--bridge', 'telegram:435025823', '--help']
# The --help should exit before bridge logic runs
" 2>&1 | head -5
```

---

## Troubleshooting

### Gateway can't find integration module
- Ensure `gateway_session_bridge_integration.py` is in `~/.hermes/hermes-agent/gateway/`
- Gateway Python path includes `~/.hermes/hermes-agent/`
- If still failing, check: `python -c "import gateway_session_bridge_integration; print(gateway_session_bridge_integration.__file__)"`

### SessionBridge not working
```bash
# Check data directory exists
ls -la ~/KnowledgeBase/.session_bridge/

# Check permissions
ls -la ~/KnowledgeBase/.session_bridge/*.json 2>/dev/null || echo "No JSON files yet (normal on first run)"

# Reset bridge state (if needed)
python -c "
from session_bridge import get_session_bridge, reset_session_bridge
reset_session_bridge()
sb = get_session_bridge()
print(sb.get_status())
"
```

### API mismatch errors
- The dataclass fields in `session_bridge.py` are the source of truth
- Check `~/KnowledgeBase/session_bridge.py` lines 47-150 for `PlatformSession`, `UserIdentity`, `PendingWork` field definitions
- Update gateway integration code if field names change

### CLI bridge not working
- Verify `cli.py` patch is present: `grep -n "inject_bridge_context\|get_auto_bridge_context_for_cli" ~/.hermes/hermes-agent/cli.py`
- Check bridge format parsing in cli.py (expected: `platform:chat_id` or `platform:chat_id:thread_id`)
- Ensure `gateway_session_bridge_integration.py` can be imported from the gateway path
