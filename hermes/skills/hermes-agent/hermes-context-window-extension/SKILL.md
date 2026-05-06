---
name: hermes-context-window-extension
version: "1.0"
description: Extender context window for MiniMax M2.7 in Hermes — compression tuning, proactive compressor plugin, and RAG pre-injection via pre_llm_call hook.
triggers:
  - "extend context window minimax"
  - "aumentar contexto hermes"
  - "context compression proactive"
  - "simular ventana mayor minimax"
---

# Hermes Context Window Extension — MiniMax M2.7

## Contexto
MiniMax M2.7 tiene 205K tokens fixed — NO se expande via parámetros de API.
Solo hay 3 вектора reales de optimización:

1. **Compression tuning** (FASE 1 — sin restart)
2. **ProactiveCompressor plugin** (FASE 2 — requiere restart)
3. **RAG pre-injection via pre_llm_call hook** (FASE 3 — sin restart)

## ARQUITECTURA DE PLUGINS HERMES

### Context Engine Plugins
- **Ubicación**: `~/.hermes/hermes-agent/plugins/context_engine/<name>/`
- **Activación**: `context.engine: <name>` en config.yaml
- **Carga**: `load_context_engine()` en `plugins/context_engine/__init__.py`
- **Interfaz**: clase con método `compress(messages)` + propiedades `threshold_tokens`, `context_length`, `name`
- **Extensión**: pueden instanciar internamente el `ContextCompressor` built-in como delegado

### General Plugins (hooks, tools)
- **Ubicación**: `~/.hermes/plugins/<name>/` (NO en el directorio del hermes-agent)
- **Activación**: añadir nombre a `plugins.enabled` en config.yaml
- **Interface**: función `register(ctx)` con `ctx.register_hook("pre_llm_call", callback)`

### Hooks relevantes
- `pre_llm_call`: fire-and-forget, puede retornar `{"context": "..."}` para inyectar en el user message
- Si el hook explota, se loguea y se skip — NO rompe el agent
- El contexto se inyecta en el user message, NO en el system prompt (preserva prompt caching)

## PROACTIVE COMPRESSOR PLUGIN
**Ubicación**: `~/.hermes/hermes-agent/plugins/context_engine/proactive_compressor/`
**Activación**: `context.engine: proactive_compressor` + restart del gateway

Diferencias vs built-in compressor:
- `trigger_threshold`: 0.50 (no 0.70)
- `chunk_size: 60` + `overlap: 10` → summarization rollante
- `protect_last_n: 40` (no 20)
- Delta effective: 143K → ~180K tokens úteis

## RAG PRE-INJECTION PLUGIN  
**Ubicación**: `~/.hermes/plugins/rag_context_injector/__init__.py`
**Activación**: `rag_context_injector` en `plugins.enabled` (sin restart)

Hook `pre_llm_call`:
1. Recibe `session_id`, `user_message`, `conversation_history`
2. Hace query en LanceDB con user_message + recent history
3. Retorna `{"context": ...}` con top-k chunks relevantes
4. Contexto es ephemeral — no se persiste nada

## LO QUE NO FUNCIONA
- **Proxy HTTP** (context_window_extender.py) — requiere cambiar base_url, rompe production, necesita restart
- **SelfExtend / ActivationBeacon** — requieren acceso a los weights del modelo (impossible con API-only)
- **Parámetros extra_body/context_window en API** — MiniMax no tiene tali cosa

## RESTART SOLO CUANDO:
1. Cambio de `context.engine` de `compressor` a `proactive_compressor`
2. Cambio de `base_url` o API settings
3. Upgrade de hermes-agent

## DESCOBERTA POST-UPDATE (29/04/2026)

Estos plugins fueron instalados automaticamente via `hermes update`:
- `plugins/context_engine/proactive_compressor/` — já existe no upstream, não é local
- `plugins/rag_context_injector/` — mesmo caso

**Verificar post-update:**
```bash
ls -la ~/.hermes/hermes-agent/plugins/context_engine/proactive_compressor/
ls -la ~/.hermes/hermes-agent/plugins/rag_context_injector/
# Se existirem com data do update = vieram do upstream
# Se existirem mas não no upstream = são locais
```

## COMPRESSION CONFIG (FASE 1 — sin restart)
`~/.hermes/config.yaml` → `compression:`:
- `threshold: 0.70` (era 0.85)
- `target_ratio: 0.25` (era 0.20)  
- `protect_last_n: 30` (era 20)

El gateway relée esta config en cada request — no requiere restart.
