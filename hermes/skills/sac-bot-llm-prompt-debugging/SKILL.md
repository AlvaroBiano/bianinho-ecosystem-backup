---
name: sac-bot-llm-prompt-debugging
description: Debugging methodology for SAC Bot LLM responses — fixing wrong terms, duplicated CTAs, and prompt issues via curl testing
---

# SAC Bot — Debugging de Problemas LLM

## Problema Comum
SAC Bot responde com termos errados ("Maria", "Duo/Trio"), duplica CTA, menciona "botão verde" no texto.

## Metodologia de Debug

### Passo 1: Testar via curl (não pelo browser)
```bash
# Init (criar lead)
curl -s http://localhost:5123/webhook/sac/init \
  -X POST -H "Content-Type: application/json" \
  -d '{"nome":"Nome","telefone":"48900000000","ddd":"48"}'

# Chat (ATENÇÃO: endpoint é /webhook/sac, NÃO /webhook/sac/chat)
curl -s http://localhost:5123/webhook/sac \
  -X POST -H "Content-Type: application/json" \
  -d '{"pergunta":"...","nome":"...","telefone":"...","ddd":"..."}'
```

### Passo 2: Identificar o problema no output
- "Maria/Marielena" → termo não banido no prompt
- "Duo/Trio" → termo não banido no prompt
- "botão verde" mencionado no texto → LLM a gerar CTA que duplica com construir_resposta
- Resposta truncada → max_tokens demasiado baixo
- "não tenho essa informação específica" → **prompt defensivo demasiado restritivo** + max_tokens baixo
- Nome errado → lead_id null (não encontrou lead)

**Diagnóstico SQL para "não tenho":**
```bash
sqlite3 ~/.hermes/sac_agent/sac_leads.db "
SELECT c.data, c.mensagem_bot, l.nome, l.telefone FROM conversas c
JOIN leads l ON c.lead_id = l.id
WHERE c.mensagem_bot LIKE '%não tenho%'
ORDER BY c.data DESC LIMIT 10;
```

### Passo 3: Corrigir o prompt do LLM
O prompt fica em `sac_agent.py` → `system_prompt` dentro de `llm_generate_combined`.

**Regras obrigatórias a incluir:**
```
PROIBIÇÃO DE TERMOS: "Maria", "Marielena", "Duo", "Trio", "Dueto"
CTA É TRATADO FORA: O LLM NÃO deve incluir convites para clicar, menções a botão, ou pedidos para "falar com alguém"
```

### Passo 4: Corrigir CTA_POR_FASE em sac_persuasao.py
Se o CTA texto menciona "botão verde" ou "clique aqui", remover. O botão é renderizado pelo frontend — o texto só deve ter a chamada para acção.

## Ficheiros Principais
- `~/.hermes/sac_agent/sac_agent.py` — prompt LLM (system_prompt em llm_generate_combined)
- `~/.hermes/sac_agent/sac_persuasao.py` — CTA_POR_FASE, construir_resposta, PERGUNTAS_SOCRATICAS
- `~/.hermes/sac_agent/templates/index.html` — frontend chat

## Restaurar Backup
```bash
cp ~/.hermes/sac_agent/backups/current_before_restore/sac_agent.py ~/.hermes/sac_agent/
cp ~/.hermes/sac_agent/backups/current_before_restore/sac_persuasao.py ~/.hermes/sac_agent/
cp ~/.hermes/sac_agent/backups/current_before_restore/index.html ~/.hermes/sac_agent/templates/
systemctl --user restart sac-agent
```

## Reiniciar Após Mudanças
```bash
systemctl --user restart sac-agent
```

## Nota: lead_id null
O webhook_sac identifica o lead pelo `telefone` (não por `lead_id` do body).
Se enviar só `lead_id` sem `telefone`, o lead não é encontrado.
O frontend envia `nome + telefone + ddd` — o backend procura por telefone.

## Regras do Botão WhatsApp (implementadas 25/04/2026)

### Regra 1 — "Quero falar com humano/equipe"
O botão aparece IMEDIATAMENTE quando a pessoa pede para falar com alguém.
- Sinal: `quer_falar_humano` em `analisar_mensagem()` em `sac_persuasao.py`
- Detecta: `"quero falar com"`, `"humano"`, `"atendente"`, `"equipe"`, `"time"`
- Texto override em `construir_resposta()`: resposta empática + CTA directo

### Regra 2 — 5+ interações sem progresso
Se `interacoes >= 5` e fase ainda é `descoberta` ou `qualificacao`, o botão aparece como escape.
- Condição em `sac_agent.py`: `if interacoes >= 5 and fase in ('descoberta', 'qualificacao'): mostrar_cta = True`

### Timeline completa
| Interações | Fase | Botão? |
|---|---|---|
| 1-2 | descoberta | ❌ Normal |
| 3+ | interesse/decisão | ✅ Normal |
| 5+ | descoberta/qualificação | ✅ Escape |
| qualquer | qualquer | ✅ Se pediu humano |

## Problemas de Output Artifact do LLM

### 1. Separadores `---` repetidos na resposta
**Causa**: O LLM reproduz o padrão de separador que recebe no prompt (ex: `"\n---\n".join(...)` no bloco de Q&As).
**Fix**: Mudar o separador no prompt para um símbolo que o LLM não replique — ex: `◆` em vez de `---`.
```python
# Antes (LLM reproduz):
qa_block = "\n\nRESPOSTAS OFICIAIS JÁ APROVADAS:\n" + "\n---\n".join([...])

# Depois (LLM não reproduz):
qa_block = "\n\nRESPOSTAS OFICIAIS JÁ APROVADAS:\n" + "\n◆\n".join([...])
```
**Ficheiro**: `sac_agent.py` → `llm_generate_combined()` → construção do `qa_block`

### 2. Accent mismatch em pattern matching (Python `in`)
**Causa**: Padrões com acento (`"qual conteúdo"`) não matcham texto sem acento (`"qual conteudo"`). O `in` do Python é literal.
**Fix**: Aplicar `unaccent()` em ambos os lados da comparação:
```python
import unicodedata
def unaccent(t):
    return unicodedata.normalize("NFD", t).encode("ascii", "ignore").decode()

texto_lower = unaccent(texto.lower())
if any(p in texto_lower for p in _p_conteudo):  # _p_conteudo também é pré-normalizado
    sinais["pergunta_concreta_sobre_conteudo"] = True
```
**Ficheiro**: `sac_persuasao.py` → `analisar_mensagem()` → sinais de pergunta concreta

### 3. Diagnóstico double-trigger
**Causa**: `construir_resposta()` chama `deve_entrar_diagnostico()` sem `pergunta_original`, re-avaliando o que o subagente já classificou.
**Fix**: Passar `pergunta_original` e usar `bypass_diag=True`:
```python
# Em sac_agent.py — chamada ao construir_resposta:
resposta_completa, fase = sac_persuasao.construir_resposta(
    result["resposta"], interacoes, sinais, fase_detectada,
    tom_prefixo=tom, regressao=regressao, lead_diag=lead_diag,
    pergunta_original=pergunta,       # ← passar pergunta original
    bypass_diag=(decisao.get("tipo_resposta") == "rag")  # ← bypass se subagente decidiu RAG
)

# Em sac_persuasao.py — construir_resposta():
if bypass_diag:
    deve_diag = False
else:
    deve_diag, _ = deve_entrar_diagnostico(interacoes, sinais, lead_diag, pergunta_original)
```

## Ficheiros
- `sac_agent.py` — `mostrar_cta` com 3 condições (normal + Regra1 + Regra2)
- `sac_persuasao.py` — `quer_falar_humano` em `analisar_mensagem()` e override em `construir_resposta()`

---

## Bugs Comuns Descobertos (28/04/2026)

### Bug 1: fase sempre "descoberta" — contexto_fase hardcoded
**Sintoma**: `fase` no JSON é sempre "descoberta" independentemente do número de interações.
**Causa**: `contexto_fase="descoberta"` hardcoded na chamada a `construir_resposta()`.
**Fix**: `contexto_fase=None` para deixar `detectar_fase()` decidir com lógica actualizada.

```python
# ERRADO:
resposta_completa, fase_detectada = sac_persuasao.construir_resposta(
    ...,
    contexto_fase="descoberta",  # ← hardcoded! ignora detectar_fase()
    ...
)

# CERTO:
resposta_completa, fase_detectada = sac_persuasao.construir_resposta(
    ...,
    contexto_fase=None,  # ← detectar_fase() decide dinamicamente
    ...
)
```

### Bug 2: Todos os early returns sem campos completos
**Sintoma**: Alguns paths do webhook devolvem JSON sem `fase`, `mostrar_avaliacao`, `tom_detectado`, `perguntas_sugeridas`, `retorno`, `historico_resumo`.
**Causa**: Early returns (humano, diagnóstico, guarda) adicionados sem seguir o padrão do retorno final.
**Fix**: Todo early return no webhook deve devolver os 12 campos:

```python
mostrar_avaliacao = sac_db.deve_mostrar_avaliacao(lead_id, interacoes) if lead_id else False
return jsonify({
    "resposta": resposta,
    "fontes": [...],
    "chunks_usados": 0, "tempo_ms": 0,
    "lead_nome": nome, "lead_telefone": telefone, "lead_ddd": ddd,
    "lead_id": lead_id,
    "retorno": bool(lead and lead.get("conversa_count", 0) > 1),
    "historico_resumo": sac_db.get_resumo_anterior(lead_id) if lead_id else "",
    "mostrar_cta": True/False,
    "score": None,
    "mostrar_avaliacao": mostrar_avaliacao,
    "perguntas_sugeridas": [],
    "fase": "descoberta",  # ou "decisao" para humano
    "tom_detectado": "neutro",
}), 200
```

**Linhas críticas a verificar** (procurar `return jsonify({` dentro de `webhook_sac`):
- Override "humano" → fase="decisao", mostrar_cta=True
- Override "diagnostico" → fase="descoberta", mostrar_cta=False
- Guarda pré-RAG → fase="descoberta", mostrar_cta=True
- Diagnóstico in-progress → fase="descoberta", mostrar_cta=False

### Bug 3: tom não definido antes dos early returns
**Sintoma**: `tom` é definido DEPOIS dos early returns (linha ~1390), então early returns que usam `tom or "neutro"` são desnecessários.
**Fix**: Usar `"neutro"` hardcoded directamente nos early returns, não `tom or "neutro"`.

### Padrão: Guarda pré-RAG (transferir_para_equipe)
**Use quando**: o bot não deve responder com RAG a certas perguntas (ex: "como funciona na prática").
**Padrão**: verificar sinal ANTES de chamar `rag_sac()`.

```python
# Em sac_persuasao.py → analisar_mensagem():
"transferir_para_equipe": any(p in texto_lower for p in [
    "como funciona na pratica", "funciona na pratica",
    "e na pratica", "exemplo pratico",
    "me da um exemplo pratico",
    "quem sao os psicologos", "equipe de psicologos",
])

# Em sac_agent.py → webhook_sac, ANTES de result = rag_sac(...):
if sinais.get("transferir_para_equipe"):
    resposta = sac_persuasao.construir_resposta_humano(primeiro_nome)
    resposta = formatar_resposta(resposta)
    if lead_id:
        sac_db.registrar_mensagem(lead_id, "bot", resposta, session_id=session_id)
    return jsonify({
        "resposta": resposta,
        "fontes": [], "chunks_usados": 0, "tempo_ms": 0,
        "lead_nome": nome, "lead_telefone": telefone, "lead_ddd": ddd,
        "lead_id": lead_id,
        "retorno": False, "historico_resumo": "",
        "mostrar_cta": True,
        "score": None, "mostrar_avaliacao": False,
        "perguntas_sugeridas": [],
        "fase": "descoberta", "tom_detectado": "neutro",
    }), 200
```

### Padrão: Lead Return Context (gap > 30 min)
**Use quando**: lead regressa após >30 min e deve ver o último tópico.
```python
if lead_id:
    try:
        from datetime import datetime as dt, timezone as tz
        row = sac_db.get_conn().execute(
            "SELECT ultima_pergunta_data FROM leads WHERE id = ?", (lead_id,)
        ).fetchone()
        sac_db.get_conn().close()
        if row and row[0]:
            last = dt.fromisoformat(row[0].replace("Z", "+00:00"))
            gap_min = (dt.now(tz.utc) - last).total_seconds() / 60
            if gap_min > 30:
                historico_resumo = sac_db.get_resumo_anterior(lead_id) or ""
    except Exception:
        pass
```

### Debug: Verificar se há early returns missing fields
```bash
# Procurar todos os return jsonify no webhook_sac
grep -n "return jsonify" ~/.hermes/sac_agent/sac_agent.py | grep -A5 "webhook_sac"
```
Cada return deve ter: `resposta`, `fontes`, `chunks_usados`, `tempo_ms`, `lead_nome`, `lead_telefone`, `lead_ddd`, `lead_id`, `retorno`, `historico_resumo`, `mostrar_cta`, `score`, `mostrar_avaliacao`, `perguntas_sugeridas`, `fase`, `tom_detectado`.
