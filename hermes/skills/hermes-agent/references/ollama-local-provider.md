# Ollama Local Provider — Hermes Integration

## What this is

Using Ollama (via AnythingLLM desktop app or standalone) as a local LLM provider in Hermes Agent. AnythingLLM runs Ollama's LLM server on `localhost:11434`.

## Models available (May 2026)

| Model | Size | Notes |
|-------|------|-------|
| `gemma4:e4b-it-q4_K_M` | 8B params, 9.6GB | Best quality local |
| `qwen3-vl:4b-instruct` | 4.4B params, 3.3GB | Smaller, vision-capable |

Test with: `curl -s http://localhost:11434/v1/models`

## The Problem

Setting `provider: ollama` alone does NOT work. Hermes registry maps `"ollama"` → `"custom"`, which then looks for a custom provider entry in `config.yaml`. Without it, you get:

```
⚠️ Provider resolver returned an empty API key. Set OPENROUTER_API_KEY or run: hermes setup
```

## The Fix — config.yaml

```yaml
model:
  default: gemma4:e4b-it-q4_K_M
  provider: ollama
  base_url: http://localhost:11434/v1

providers:
  ollama:
    name: Ollama (AnythingLLM)
    base_url: http://localhost:11434/v1
    api_key: ""          # Ollama ignores API keys on localhost
    model: gemma4:e4b-it-q4_K_M
```

**Key insight:** The `providers:` section must contain an entry named `ollama` (matching `model.provider`). The `"ollama"` provider name maps to `"custom"` internally, so Hermes looks up a custom provider definition. Without it, resolution fails.

## Why api_key is empty

Ollama's local API at `localhost:11434` does not validate API keys. Any string is ignored. Setting `api_key: ""` lets Hermes pass through to Ollama without the OpenAI SDK rejecting the request.

## Verify it works

```bash
cd ~/.hermes && ~/.hermes/venv/bin/hermes chat -q "Responde com uma palavra: olá"
# Should respond with "olá" after ~10-20s
```

## Ollama API is OpenAI-compatible

Ollama exposes the standard `/v1/chat/completions` endpoint:

```bash
curl -s http://localhost:11434/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model": "gemma4:e4b-it-q4_K_M", "messages": [{"role": "user", "content": "Olá"}], "max_tokens": 10}'
```

## AnythingLLM ports to know

| Service | Port | Purpose |
|---------|------|---------|
| Ollama LLM server | 11434 | Main API (OpenAI-compatible) |
| AnythingLLM API | 3001 (redwood-broker) | Desktop app management |

Check with: `lsof -i :11434 -i :3001`
