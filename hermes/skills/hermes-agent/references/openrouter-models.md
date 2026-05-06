# OpenRouter Model Catalog — Free Models

## How `/models` works (curated list)

O `/models` do Hermes **não lista todos os modelos do OpenRouter**. Usa uma **lista curada** de dois fontes:

1. **`OPENROUTER_MODELS`** em `hermes_cli/models.py` — lista hardcoded no código
2. **`model_catalog.py`** (catálogo remoto em `website/static/api/`) — baixado em tempo real

O fluxo em `fetch_openrouter_models()`:
- Busca catálogo remoto → usa como base
- Se catálogo offline → usa `OPENROUTER_MODELS` como fallback
- Filtra por suporte a tools (`_openrouter_model_supports_tools`)
- Marca com badge `"free"` os que têm pricing $0/$0

## Free models currently missing from curated list

Estes existem no OpenRouter mas NÃO estão no catálogo curado do Hermes (30/04/2026):

| Modelo | Context | Badge |
|--------|---------|-------|
| `nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free` | 256k | free |
| `nvidia/nemotron-3-nano-30b-a3b:free` | 256k | free |
| `nvidia/nemotron-nano-12b-v2-vl:free` | 128k | free |
| `nvidia/nemotron-nano-9b-v2:free` | 128k | free |
| `tencent/hy3-preview:free` | — | free |
| `arcee-ai/trinity-large-preview:free` | — | free |

## Workaround: usar modelos fora da lista curada

O modelo não precisa estar na lista curada para ser usado. Basta definir diretamente:

```bash
hermes config set model.default_model "nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free"
```

Ou durante a sessão:
```
/model nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free
```

## Verificar modelos free no OpenRouter

```bash
curl -s "https://openrouter.ai/api/v1/models" | python3 -c "
import json, sys
data = json.load(sys.stdin)
for m in data.get('data', []):
    p = m.get('pricing', {})
    if p.get('prompt') == '0' and p.get('completion') == '0':
        print(m['id'])
"
```

## GitHub Issue aberta

**Issue #17923**: "Feature request: Add free-tier filter to /models and include all free OpenRouter models in curated list"
URL: https://github.com/NousResearch/hermes-agent/issues/17923

---

## gh CLI bug workaround

O `gh` (GitHub CLI) na versão 2.8.9 com Node.js 24 tem bug已知 — comando `gh auth status` dá `TypeError: Cannot read properties of undefined (reading 'options')`.

**Solução**: usar REST API do GitHub via Python em vez do `gh` CLI.

### Criar issue via REST API

```python
import urllib.request, json

# Ler token do .netrc (em modo binário para não truncar)
with open('/home/alvarobiano/.netrc', 'rb') as f:
    content = f.read()
token_start = content.find(b'ghp_')
token_end = content.find(b'\n', token_start)
token = content[token_start:token_end].decode('ascii')

url = "https://api.github.com/repos/NousResearch/hermes-agent/issues"
payload = {
    "title": "Feature request: ...",
    "body": "..."
}

data = json.dumps(payload).encode('utf-8')
req = urllib.request.Request(
    url, data=data,
    headers={
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "Content-Type": "application/json"
    },
    method="POST"
)

with urllib.request.urlopen(req) as resp:
    result = json.loads(resp.read().decode())
    print(result['html_url'])
```

**Nota**: PATs pessoais não têm permissão para criar labels em repos públicos — criar sem labels.

### Ler token do .netrc

```python
# Modo binário — leitura de texto pode truncar tokens
with open('/home/alvarobiano/.netrc', 'rb') as f:
    content = f.read()
token_start = content.find(b'ghp_')
token_end = content.find(b'\n', token_start)
token = content[token_start:token_end].decode('ascii')
```
