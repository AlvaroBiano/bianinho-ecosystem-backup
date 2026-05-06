---
name: sac-agent-typebot
description: Sub-agente Hermes que recebe webhooks do Typebot e responde via RAG exclusivo em metodoten
triggers: [typebot, webhook, sac, chatbot, suporte]
---

# SAC Agent — Typebot Webhook RAG

## O que é
Sub-agente Hermes que recebe webhooks do Typebot e responde perguntas de SAC usando exclusivamente a colecção `metodoten` no LanceDB.

## Arquitectura
```
Typebot → POST /webhook/typebot → Flask (porto 5123) → LanceDB(metodoten) → MiniMax → JSON
```

## Endpoints
| Endpoint | Método | Descrição |
|---|---|---|
| `http://192.168.2.41:5123/health` | GET | Health check + estatísticas |
| `http://192.168.2.41:5123/webhook/sac` | POST | Pergunta directa SAC |
| `http://192.168.2.41:5123/webhook/typebot` | POST | Integração Typebot |

## Formato POST (Typebot)
```json
{
  "pergunta": "O que é o método TEN?",
  "session_id": "usuario-123"
}
```

## Formato resposta
```json
{
  "resposta": "...",
  "fontes": ["Apostila METODO TEN - Aula 1 a 10a.pdf"],
  "chunks_usados": 5,
  "tempo_ms": 10400
}
```

## Ficheiros
- `~/.hermes/sac_agent/sac_agent.py` — script principal Flask
- `~/.hermes/sac_agent/venv/` — venv com todas as dependências
- `~/.config/systemd/user/sac-agent.service` — serviço systemd

## Comandos
```bash
# Ativar venv
source ~/.hermes/sac_agent/venv/bin/activate

# Reiniciar serviço
systemctl --user daemon-reload && systemctl --user restart sac-agent

# Status
systemctl --user status sac-agent

# Ver logs
journalctl --user -u sac-agent -f

# Testar endpoint
curl -X POST http://192.168.2.41:5123/webhook/sac \
  -H "Content-Type: application/json" \
  -d '{"pergunta": "O que é o método TEN?", "session_id": "teste"}'
```

## Dependências do venv
```
lancedb tiktoken flask openai requests
```

## Tabela LanceDB
- Path: `~/KnowledgeBase/knowledge_db/`
- Colecção: `metodoten` (925 chunks, 1536 dims)
- Embedding: `text-embedding-3-small`

## Problemas resolvidos (histórico)

### `limpar_resposta()` apagava toda a formatação
Função original usava `re.sub(r'\s+', ' ', texto)` + strip de markdown, juntando tudo numa linha.
**Fix**: Dividir em duas funções — `plain_resposta()` para contexto LLM (texto limpo) e `formatar_resposta()` para frontend (HTML).

```python
def plain_resposta(texto):
    """Versão sem markdown para contexto do LLM."""
    import re
    t = re.sub(r'\*\*(.+?)\*\*', r'\1', texto)  # remove bold
    t = re.sub(r'\*(.+?)\*', r'\1', t)           # remove italic
    return t.strip()

def formatar_resposta(texto):
    """Converte markdown para HTML para o frontend."""
    import re
    # 1. Primeiro converter markdown → HTML
    t = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', texto)
    t = re.sub(r'\*(.+?)\*', r'<i>\1</i>', t)
    # 2. SÓ DEPOIS dividir em párágrafos
    partes = [p.strip() for p in t.split('\n\n') if p.strip()]
    return '<p>'.join([''] + partes + ['']) if partes else texto
```

**Ordem de operações CRÍTICA**: sempre markdown → HTML ANTES de inserir marcadores de párágrafo,
caso contrário `__PAR__` ou placeholders com `**` são interpretados como negrito.

### innerHTML vs textContent nas mensagens do bot
As mensagens do bot precisam de `innerHTML` para renderizar tags HTML (`<p>`, `<b>`, `<i>`):
```javascript
// NO FRONTEND (index.html) — usar innerHTML para mensagens do bot:
element.innerHTML = htmlResposta;   // ✅ bot
element.textContent = texto;       // ✅ utilizador
```

### CSS para o chat HTML
Adicionar ao `<style>` do `templates/index.html`:
```css
.msg-bot p {
  margin: 0 0 10px 0;
  padding: 6px 0 0 0;
  border-bottom: 1px solid rgba(255,255,255,0.15);
}
.msg-bot p:last-child { margin-bottom: 0; border-bottom: none; }
.msg-bot b, .msg-bot strong { color: #00d4ff; font-weight: 700; }
.msg-bot i, .msg-bot em { color: rgba(255,255,255,0.75); font-style: italic; }
```

### Separadores visuais feios (----)
O CTA_BOTAO em `sac_persuasao.py` continha `------------------------------------------------------` como separador.
**Remover** — o CSS com `border-bottom` em `<p>` substitui isso elegantemente.

### Número WhatsApp actualizado
Link: `https://wa.me/5548991286513` (actualizado de 5511983030880 em 24/04/2026)

## Notas
- Stateless — cada pergunta é independente (sem memória de sessão)
- Filtro hardcoded para `metodoten` (não consulta `chunks`)
- Tempo médio de resposta: ~10s
- Se Typebot está na cloud (não rede local), usar ngrok:
  ```bash
  ngrok http 5123
  ```
