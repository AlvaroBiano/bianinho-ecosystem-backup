---
name: minimax-m2-7
description: MiniMax M2.7 Plus — Chat, TTS, Image Gen, Video (Hailuo), Music, Voice Cloning
---
# MiniMax M2.7 Plus — Guía Completo

## Setup
Chave ja configurada no environment. Bearer token usado em todos os requests.
Base URL: `https://api.minimaxi.com/v1` (OpenAI兼容) ou `https://api.minimaxi.com/anthropic` (Anthropic兼容)

**NOTA:** O dominio e `minimaxi.com` (com "i"), nao `minimax.io`.

---

## ◆ Nous Tool Gateway (Hermes v0.10.0+)

Se tens **pago do Nous Portal** (nousportal.com), o Hermes já tem acesso integrado:

- **Web Search** — busca em tempo real
- **Image Gen** — via MiniMax (mesmo model `image-01`)
- **TTS** — voz natural sem API key separada
- **Browser Automation** — scraping, interações web

**Zero API keys adicionais necessárias.**

Isto é uma alternativa ao uso direto da API MiniMax. Se só precisas de chat, TTS simples ou search, o Tool Gateway pode ser mais rápido de configurar.

---

## Cotas (Plan Plus)
| Recurso | Limite | Janela |
|---------|--------|--------|
| Text Generation (M2.7) | 4.500 | 5h rolling |
| TTS HD (speech-02-hd) | 4.000 | diário |
| Image Generation (image-01) | 50 | diário |
| Video (Hailuo 2.3) | - | - |
| Music (Music-2.6) | 100 | diário |
| Music-cover | 100 | diário |

### Verificar Cotas Atuais

```bash
curl -s -X GET "https://api.minimax.io/v1/query/quota" \
  -H "Authorization: Bearer ***"
```

Resposta inclui `remain`, `limit`, `reset_at` por recurso. Verificar antes de tasks grandes.

---

## 1. TEXT / CHAT

**Endpoint:** `POST /text/chatcompletion_v2`

```bash
curl -s -X POST "https://api.minimax.io/v1/text/chatcompletion_v2" \
  -H "Authorization: Bearer $MINIMAX_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model":"MiniMax-M2.7","messages":[{"role":"user","content":"Olá"}],"max_tokens":1024}'
```

**Models:** `MiniMax-M2.7`, `MiniMax-M2.7-highspeed`, `MiniMax-M2.5`, `MiniMax-M2.5-highspeed`
**Modelo ERRADO:** `MiniMax-Text-01` dá erro 2061 — só funciona no plano pago. Usar sempre `MiniMax-M2.7`.

### ⚠️ CRÍTICO: max_tokens para content aparecer
O M2.7 usa reasoning interno que consome tokens. Se `max_tokens` for baixo (ex: 5-10), o `content` vem **vazio** e o texto aparece só em `reasoning_content`.

**Fix:** usar `max_tokens: 200` mínimo para garantir que `content` é preenchido.

```python
# ✅ CERTO — content aparece
{"model": "MiniMax-M2.7", "messages": [...], "max_tokens": 200}
# ❌ ERRADO — content vazio, texto só no reasoning
{"model": "MiniMax-M2.7", "messages": [...], "max_tokens": 5}
```

**Resposta correta:**
```json
{
  "choices": [{
    "message": {
      "content": "OK",           // ← texto real
      "reasoning_content": "..."  // ← reasoning
    }
  }]
}
```

### Context Window (confirmado 30/04/2026 — documentacao oficial MiniMax)
| Model | Context Window |
|-------|---------------|
| **M2.7** | **204,800 tokens** |
| M2.7-highspeed | 204,800 tokens |
| M2.5 | 204,800 tokens |
| M2.5-highspeed | 204,800 tokens |
| M2.1 | 204,800 tokens |

**IMPORTANTE:** Todos os modelos de texto MiniMax tem exatamente 204,800 tokens. Nao existe 1M de contexto.

### M2.8 — NÃO EXISTE
Como de Abr/2026, **não há registro de M2.8** no site oficial, docs ou release notes. Release mais recente é M2.7 (Mar/2026).

### Diferencial: Modelo de Preço Unlimited
O MiniMax é **raro no mercado** — quase nenhum competitor oferece API unlimited por mensalidade fixa (~$20/mês). A maioria cobra por token (OpenAI, Anthropic, Google, DeepSeek, Grok).

---

## 2. TTS — Text to Speech

**Endpoint:** `POST /t2a_v2`

```bash
curl -s -X POST "https://api.minimax.io/v1/t2a_v2" \
  -H "Authorization: Bearer $MINIMAX_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "speech-2.8-hd",
    "text": "Olá, como vai você?",
    "stream": false,
    "output_format": "hex",
    "voice_setting": {"voice_id": "male-qn-qingse", "speed": 0.95, "vol": 1.0, "pitch": 0},
    "audio_setting": {"sample_rate": 32000, "bitrate": 128000, "format": "mp3", "channel": 1}
  }'
```

**Models:** `speech-2.8-hd` ✅ (único que funciona neste plano), `speech-2.8-turbo`, `speech-2.6-hd`, `speech-2.6-turbo`
**Nota:** `speech-02-hd` e `speech-02-turbo` NÃO estão disponíveis — erro 2061.

### System Voice IDs
- `male-qn-qingse` — masculino suave ✅ **← PADRÃO GLOBAL (config.yaml)**
- `female-qn-bella` — feminino alternativo ✅
- `English_expressive_narrator` ✅
- `male-qn-junny` | `female-qn-floral` | `female-qn-yisu` | `male-qn-qingse_4k` — verificar antes de usar

### Emoções (speech-02-hd+)
`happy`, `sad`, `angry`, `fearful`, `disgusted`, `surprised`, `neutral`

### Interjections (speech-2.8-* only)
`(laughs)`, `(chuckle)`, `(coughs)`, `(clear-throat)`, `(groans)`, `(breath)`, `(pant)`, `(inhale)`, `(exhale)`, `(gasps)`, `(sniffs)`, `(sighs)`, `(snorts)`, `(burps)`, `(lip-smacking)`, `(humming)`, `(hissing)`, `(emm)`, `(sneezes)`

### Output
Retorna `hex` encoded. Para salvar como MP3:
```bash
echo "$HEX_RESPONSE" | xxd -r -p > output.mp3
```

### Voz PT-BR
1. **Voice cloning** via console.minimax.io (upload áudio → cria voice_id custom)
2. Usar `male-qn-qingse` ou `male-qn-junny`
3. Ajustar `pitch` e `speed`

---

## 3. IMAGE GENERATION

**Endpoint:** `POST /image_generation`

```bash
curl -s -X POST "https://api.minimax.io/v1/image_generation" \
  -H "Authorization: Bearer $MINIMAX_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model":"image-01","prompt":"A serene portrait of a Brazilian therapist","output_format":"url","output_size":"1k"}'
```

**Models:** `image-01`

**output_size:** `1k` (1024×1024), `2k` (2048×2048), `3k` (3072×3072), `1:1`, `16:9`, `9:16`, `4:3`, `3:4`

**Response:** JSON com `data.image_urls` — é um **array** de URLs, não `image_url` (string única).确认 key 为 `data.image_urls[0]`。

```python
import urllib.request, json, re, os

# Ler MINIMAX_API_KEY do ~/.hermes/.env (chave nao vem do env do terminal)
with open(os.path.expanduser("~/.hermes/.env")) as f:
    for line in f:
        if line.strip().startswith("MINIMAX_API_KEY="):
            api_key = re.split(r"\s+#", line.strip().split("=", 1)[1])[0].strip()
            break

data = json.dumps({
    "model": "image-01",
    "prompt": "your prompt here",
    "output_format": "url",
    "output_size": "1:1"   # 1k|2k|3k|1:1|16:9|9:16|4:3|3:4
}).encode()

req = urllib.request.Request(
    "https://api.minimax.io/v1/image_generation",
    data=data,
    headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
    method="POST"
)
with urllib.request.urlopen(req, timeout=120) as resp:
    result = json.loads(resp.read())
    img_url = result["data"]["image_urls"][0]   # ← array, nao string

    # Baixar imediatamente — URL expira
    img_data = urllib.request.urlopen(img_url, timeout=60).read()
    with open("output.jpg", "wb") as f:
        f.write(img_data)
```

### Download:
```bash
curl -s "URL_DA_IMAGEM" -o imagem.jpg
```

---

## 4. VIDEO GENERATION

**Endpoint:** `POST /v1/video_generation`

**Model:** `MiniMax-Hailuo-2.3` ou `MiniMax-Hailuo-2.3-Fast`

```bash
curl -s -X POST "https://api.minimax.io/v1/video_generation" \
  -H "Authorization: Bearer $MINIMAX_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model":"MiniMax-Hailuo-2.3-Fast","prompt":"A serene beach at sunset"}'
```

**Resolução:** 1080p (6s), 768p (6s/10s), 512p (6s/10s)
**FPS:** 24 fps

Para I2V (image to video), usar `input_image_url` em vez de `prompt`.

---

## 5. MUSIC GENERATION

**Endpoint:** `POST /v1/music_generation`

**Model:** `Music-2.6` (latest), `Music-Cover`, `Music-2.0`, `Music-1.5`

```bash
curl -s -X POST "https://api.minimax.io/v1/music_generation" \
  -H "Authorization: Bearer $MINIMAX_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model":"Music-2.6","prompt":"A calm ambient music track with soft piano"}'
```

**Options:**
- `prompt`: text description
- `lyrics`: lyrics text
- `audio_url`: reference audio for style transfer (Music-Cover)

---

## 6. VOICE CLONING

Via **console.minimax.io** → Voice Clone:
1. Upload 30s-5min de áudio (WAV/MP3, sem ruído)
2. Sistema gera voice_id custom
3. Usa voice_id nos requests TTS

---

---

## ◆ Token Plan Troubleshooting

**Skill original:** `minimax-token-plan-troubleshooting`

### O Problema
Erros `HTTP 429: insufficient balance (1008)` com plano MiniMax Token Plan pago ($20/4500 requests-hora), mesmo com quota aparentemente disponível.

### Como o Token Plan funciona (NÃO é como pensas)
- **Text models (M2.7) usam CONTAGEM DE REQUESTS, não tokens.** O erro `insufficient balance (1008)` significa que a quota de requests da janela de 5 horas foi agotada.
- **Janela de 5 horas (rolling):** o sistema calcula uso total dentro das últimas 5 horas. Qualquer request com mais de 5 horas é automaticamente libertado.
- **Keys são incompatíveis:** Token Plan API Key (`sk-cp-...`) é exclusivamente para Token Plan. Não funciona com API standard.

### Verificar quota em tempo real
```bash
curl -s -X GET "https://www.minimax.io/v1/token_plan/remains" \
  -H "Authorization: Bearer $MINIMAX_API_KEY" \
  -H "Content-Type: application/json"
```

Resposta:
```json
{"model_remains": [{"model_name": "MiniMax-M*", "current_interval_usage_count": 404, "current_interval_total_count": 4500}]}
```
**Cálculo rápido:** 4500 - 404 = 4096 requests restantes na janela de 5h.

### Regra de Ouro: Health Checks Devem Verificar CONECTIVIDADE, Não Fazer Calls LLM

**Padrão correcto — HTTP Network Check (NÃO consome quota):**
```python
def check_minimax_connectivity():
    try:
        import urllib.request
        url = "https://api.minimax.io/v1"
        req = urllib.request.Request(url)
        req.add_header("User-Agent", "BianinhoMonitor/1.0")
        with urllib.request.urlopen(req, timeout=8) as resp:
            if resp.status in (200, 404, 405, 400):
                return True
        return False
    except Exception:
        return False
```

### Reduzir frequência dos cron jobs
| Cron Job | Antes | Depois | Impacto |
|---|---|---|---|
| Server Resilience Manager | `*/5 * * * *` | `*/30 * * * *` | -216 chamadas/dia |
| Proactive Monitor | 12x/dia LLM | 12x/dia HTTP only | -100% quota |
| Server Health Check | 1x/hora | 1x/2h | -12 chamadas/dia |

### Armadilhas Comuns
1. **Chave mascarada no .env (`***`)**: health checks não conseguem usar key mascarada — usar apenas HTTP check.
2. **OpenRouter como intermediário**: health check vai pelo OpenRouter consome quota Token Plan da mesma forma.
3. **`/v1/token_plan/remains` precisa de key real**: se a key está mascarada, retorna 403. Não usar para health checks — apenas diagnóstico.
4. **A `.env` production é lida pelo systemd**: cron jobs user-level não herdam — verificar que scripts herdam variáveis correctas.

### Falhas de Formato de API (Mudança de Contrato)
O erro NÃO é HTTP 4xx — é **HTTP 200 com `vectors: null` e `base_resp.status_code`**.

**Sintomas:**
- HTTP 200 OK mas `vectors: null`
- `{"vectors": null, "base_resp": {"status_code": 2013, "status_msg": "invalid params"}}`

**Padrão de debug:**
```python
# Testar endpoint directamente para ver resposta exacta
import json, urllib.request
key = "YOUR_KEY"
payload = {"model": "embo-01", "texts": ["test query"], "type": "db"}
req = urllib.request.Request("https://api.minimax.io/v1/embeddings",
    data=json.dumps(payload).encode(),
    headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
    method="POST")
with urllib.request.urlopen(req, timeout=15) as resp:
    print(resp.read().decode())  # Ver resposta exacta
```

---

## ◆ API Key Types — Token Plan vs Pay-as-you-go

**Skill original:** `minimax-api-key-types`

### Two Different API Key Types

| Key Type | Prefix | Requires | Error if Empty |
|----------|--------|----------|----------------|
| Pay-as-you-go | `sk-api-xxx` | Pre-paid balance | `insufficient balance (1008)` |
| Token Plan | `sk-cp-xxx` | Active plan | Works if plan active |

### How to Identify
- **Pay-as-you-go**: Key starts with `sk-api-`
- **Token Plan**: Key starts with `sk-cp-`

### Troubleshooting Flow
```
1. Test API → 401 Unauthorized → Key invalid/expired
2. Test API → 429 insufficient_balance → Wrong key type (pay-as-you-go without balance)
3. Solution → Use Token Plan key (sk-cp-xxx) instead
```

### Real Example (25/04/2026)
- First API (sk-api-xxx): `401 login fail` → Invalid
- Second API (sk-api-xxx): `429 insufficient balance` → Valid but no balance
- Third API (sk-cp-xxx): `200 OK` → Token Plan works!

---

## Error Codes
| Code | Significado |
|------|-------------|
| 0 | Success |
| 1004 | Authentication failed |
| 2013 | Invalid params |
| 2054 | Voice ID not exist |
| 10001 | Rate limit |
