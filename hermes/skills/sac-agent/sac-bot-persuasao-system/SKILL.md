---
name: sac-bot-persuasao-system
description: Arquitectura do sistema de persuasão e perguntas do SAC Bot — RAG, construir_resposta, PERGUNTAS_SOCRATICAS, SEQUENCIA_PERGUNTAS, frontend perguntas sugeridas
category: sac-agent
tags: [sac, persuasion, questions, rag, python]
updated: 2026-04-28
---

# SAC Bot — Sistema de Persuasão e Perguntas

## Arquitectura Actual (25/04/2026)

### RAG → Persuasão → Resposta

```
webhook_sac_chat()
  1. rag_sac()                    → resposta RAG
  2. analisar_mensagem()          → sinais (mencionou_formacao, etc.)
  3. gerar_perguntas_acompanhamento() → 4 perguntas dinâmicas
  4. construir_resposta()         → junta RAG + gatilho + CTA
  5. get_perguntas_sugeridas()    → fallback (se MiniMax falhou)
```

### Ficheiros Principais

| Ficheiro | Papel |
|----------|-------|
| `~/.hermes/sac_agent/sac_persuasao.py` | Lógica de persuasão |
| `~/.hermes/sac_agent/sac_agent.py` | Webhook principal `webhook_sac_chat` |
| `~/.hermes/sac_agent/templates/index.html` | Frontend — renderiza `perguntas_sugeridas` |

### Funções-Chave em sac_persuasao.py

| Função | O que faz |
|--------|-----------|
| `detectar_fase()` | Detecta fase: descoberta/qualificacao/interesse/decisao |
| `analisar_mensagem()` | Extrai sinais da mensagem do lead |
| `construir_resposta()` | **Junta RAG + gatilho + CTA** — não inclui perguntas na resposta |
| `detectar_tópico()` | Detecta tópico da resposta |
| `get_gatilho_por_fase_e_topico()` | Gatilho persuasivo por fase+tópico |
| `get_cta_por_fase()` | CTA por fase |
| `gerar_perguntas_acompanhamento()` | **Gera 4 perguntas dinâmicas via MiniMax** — Jaccard 0.5 para verificar se já existe nas approved_qa. Pending são marcadas para fila de approvação |
| `salvar_perguntas_pendentes()` | Guarda perguntas pending na tabela `pending_qa` |
| `get_perguntas_sugeridas()` | **FALLBACK estático** — só usado quando MiniMax não responde ou devolveu < 4 |

### PERGUNTAS_SOCRATICAS — **FALLBACK** (usado só quando MiniMax não responde)

4 fases × 4 perguntas — fixas por fase, baralhadas aleatoriamente.
Usadas para preencher `perguntas_sugeridas[]` quando `gerar_perguntas_acompanhamento()` devolveu menos de 4 perguntas.

```python
PERGUNTAS_SOCRATICAS = {
    "descoberta": [
        "Como funciona a formação do Método TEN?",
        "Preciso ter experiência prévia pra fazer?",
        "Quanto tempo dura a formação completa?",
        "O que exatamente eu vou aprender?",
    ],
    "qualificacao": [
        "Quanto custa a formação?",
        "Como funciona o suporte durante a formação?",
        "Posso começar a atender ainda durante o curso?",
        "A formação é presencial ou online?",
    ],
    "interesse": [
        "Como funciona a matrícula?",
        "Tem alguma condição de pagamento?",
        "Vocês ajudam com marketing depois que me formar?",
        "Posso falar com alguém da equipe antes de decidir?",
    ],
    "decisao": [
        "Como faço pra me matricular?",
        "Quando posso começar?",
        "Qual é o investimento total?",
        "Tem garantia de satisfação?",
    ],
}
```

### SEQUENCIA_PERGUNTAS (linha 678)

Perguntas que se seguem a perguntas específicas do lead (força o lead a pensar mais fundo):

```python
SEQUENCIA_PERGUNTAS = {
    "Quanto custa": [
        "Tem condição de pagamento?",
        "Posso parcelar?",
        "O valor inclui a extensão universitária?",
    ],
    "Preciso ter experiência": [
        "E se eu vier de outra área?",
        "A formação começa do zero?",
        "E se eu nunca fiz nada disso antes?",
    ],
    "Como funciona a formação": [
        "As aulas são ao vivo ou gravadas?",
        "Quanto tempo preciso dedicar por semana?",
        "Tenho acesso vitalício ao material?",
    ],
    ...
}
```

## Arquitectura Actual (28/04/2026) — Dynamic Questions + PILAR 1

```
webhook_sac_chat()
  1. analisar_mensagem()           → sinais
  2. deve_entrar_diagnostico(pergunta=pergunta_original)  ← PRIMEIRA CHAMADA
  3. Se diagnóstico activo → construir_resposta_diagnostico() → return
  4. rag_sac()                     → resposta RAG
  5. construir_resposta(pergunta_original=pergunta)
     5a. deve_entrar_diagnostico(pergunta=pergunta_original) ← SEGUNDA CHAMADA
     5b. Se impõe diagnóstico → return resposta_diagnostico
     5c. Senão → RAG + gatilho + CTA
  6. gerar_perguntas_acompanhamento()  ← NOVO: 4 perguntas dinâmicas via MiniMax
     - Pending: guardado em pending_qa
     - Static: preenchido com get_perguntas_sugeridas() como fallback
  7. Return JSON com perguntas_sugeridas[]
```

## Sistema de Perguntas Dinâmicas (28/04/2026)

**Ficheiros novos/modificados:**
- `sac_schema.sql` → tabela `pending_qa`
- `sac_db.py` → `salvar_pending_qa()`, `listar_pending_qa()`, `aprobar_pending_qa()`, `rejeitar_pending_qa()`, `buscar_perguntas_por_tema()`, `buscar_perguntas_related()`
- `sac_persuasao.py` → `gerar_perguntas_acompanhamento()`, `salvar_perguntas_pendentes()`
- `sac_agent.py` → integração no webhook após construir_resposta
- `templates/admin-pending-qa.html` → página admin de fila de approvação

**Admin:** `/admin/pending-qa` — lista perguntas pendentes com contexto da conversa. Aprovar cria entrada em `approved_qa`. Rejeitar marca como rejeitada.

**Fluxo:**
```
MiniMax gera 4 perguntas
    ↓
Para cada: Jaccard ≥ 0.5 vs approved_qa?
    ├── SIM  → status='approved'
    └── NÃO  → status='pending' → vai para DB
    ↓
Se < 4 perguntas → preencher com get_perguntas_sugeridas()
    ↓
JSON: perguntas_sugeridas[]
```

```
webhook_sac_chat()
  1. analisar_mensagem()           → sinais
  2. deve_entrar_diagnostico(pergunta=pergunta_original)  ← PRIMEIRA CHAMADA (tem pergunta)
  3. Se diagnóstico activo → construir_resposta_diagnostico() → return
  4. rag_sac()                      → resposta RAG
  5. construir_resposta(pergunta_original=pergunta)        ← SEGUNDA CHAMADA (tem pergunta)
     5a. deve_entrar_diagnostico(pergunta=pergunta_original)  ← verifica de novo
     5b. Se impõe diagnóstico → return resposta_diagnostico
     5c. Senão → RAG + gatilho + CTA
```

### PERIGO CRÍTICO: Double-Call de deve_entrar_diagnostico

`deve_entrar_diagnostico()` é chamada **duas vezes** por mensagem:
- **1ª chamada** (webhook): recebe `pergunta_original` com texto real
- **2ª chamada** (dentro de `construir_resposta`): se `pergunta_original` não for propagada, recebe `""` (string vazia) e toma a decisão errada

**Sintoma**: lead faz pergunta concreta ("Preciso ter experiência prévia pra fazer?") → bot responde conteúdo do RAG → depois retorna pergunta de diagnóstico 0-10. O diagnóstico parece "atravessar" a resposta do RAG.

**Correção obrigatória**: `construir_resposta()` recebe `pergunta_original: str = ""` na assinatura e passa-o a `deve_entrar_diagnostico()`. O caller em `sac_agent.py` passa `pergunta_original=pergunta`.

**Regra**: qualquer função que chame `deve_entrar_diagnostico()` internamente **deve** receber e propagar `pergunta_original`. Nunca chamar `deve_entrar_diagnostico()` sem o texto original do lead.

## Para Activar Perguntas Contextuais

`get_proxima_pergunta(pergunta_anterior, fase)` (linha 717) ainda não está ligada ao fluxo principal. Para ativar:

1. Guardar a última pergunta do lead na sessão/conversa
2. Em `construir_resposta` ou no endpoint, chamar `get_proxima_pergunta(ultima_pergunta, fase)` para contextualizar as perguntas
3. Ou substituir/ complementar `get_perguntas_sugeridas()` com o resultado de `get_proxima_pergunta()`

## Frontend — Renderização de Perguntas (index.html linha 626-638)

```javascript
if (d.perguntas_sugeridas && d.perguntas_sugeridas.length > 0) {
    d.perguntas_sugeridas.forEach(function(perg) {
        var btn = document.createElement('button');
        btn.className = 'perg-sug';
        btn.textContent = perg;
        btn.onclick = function() {
            document.getElementById('chat-input').value = perg;
            enviarMensagem();
            pergBox.classList.remove('visivel');
        };
    });
}
```

## Fluxo de Dados no Webhook (28/04/2026)

```python
# sac_agent.py ~ linha 1037
deve_entrar, tipo_esperado = sac_persuasao.deve_entrar_diagnostico(
    interacoes, sinais, lead_diag, pergunta_original=pergunta  # ← PASSAR SEMPRE
)

# Se diagnóstico activo → return early com construir_resposta_diagnostico()

# Se não → RAG → construir_resposta()
resposta_completa, fase_detectada = sac_persuasao.construir_resposta(
    resposta_rag=result["resposta"],
    interacoes=interacoes,
    sinais=sinais,
    contexto_fase=None,
    tom_prefixo=tom,
    regressao=regressao,
    lead_diag=lead_diag,
    pergunta_original=pergunta,  # ← OBRIGATÓRIO: propaga até deve_entrar_diagnostico
)

response = {
    "resposta": formatar_resposta(resposta_completa),
    "mostrar_cta": interacoes >= 2 and fase_detectada in ("interesse", "decisao"),
    "perguntas_sugeridas": sac_persuasao.get_perguntas_sugeridas(fase_detectada, limite=4),
    "fase": fase_detectada,
    ...
}
```
