---
name: sac-bot-testing
description: Como testar o SAC Bot — browser console approach e curl fallback. Captura técnicas de browser testing para chatbots com submit via Enter key.
---

# SAC Bot — Testing: Browser Console + Curl

## Contexto

O browser tool (`browser_click`, `browser_type`) falha em alguns cenários com forms SPA:
- `browser_type` não dispara `addEventListener('input')` — botões ficam disabled
- `browser_click` timeout em elementos criados dinamicamente
- Chat submit via `onkeydown="if(event.key==='Enter')..."` — não tem botão submit tradicional

## Abordagem 1: Browser Console (teste visual completo)

### 1. Preencher form init (nome + telefone)

O form usa validação em tempo real via `input` event. `browser_type` não funciona.

```javascript
// Descobrir IDs dos campos
document.querySelectorAll('input')  // mostra IDs

// Preencher e disparar evento input
document.getElementById('campo-nome').value = 'Nome Completo';
document.getElementById('campo-nome').dispatchEvent(new Event('input', {bubbles: true}));
document.getElementById('campo-telefone').value = '(48) 99999-9999';
document.getElementById('campo-telefone').dispatchEvent(new Event('input', {bubbles: true}));

// Clicar botão
document.getElementById('btn-iniciar').click();
```

### 2. Submeter mensagem de chat (textarea + Enter)

O chat usa `<textarea onkeydown="if(event.key==='Enter'...)">` — não há botão submit visível.

```javascript
// Descobrir o elemento
document.getElementById('chat-input')  // é textarea

// Escrever e submeter via Enter
document.getElementById('chat-input').value = 'Mensagem aqui';
document.getElementById('chat-input').dispatchEvent(new KeyboardEvent('keydown', {key: 'Enter', bubbles: true}));
```

### 3. Verificar elementos visíveis após resposta

```javascript
document.getElementById('whatsapp-cta').className     // visivel = presente
document.getElementById('avaliacao-box').className     // visivel = presente
document.getElementById('bottom-actions').className    // visivel = presente
document.getElementById('perguntas-sugeridas').innerHTML  // botões das perguntas

// Verificar typewriter a correr
document.querySelector('.msg-loading') ? 'EM CURSO' : 'TERMINADO'
```

### 4. Esperar resposta do bot

```bash
# No terminal, não no browser
sleep 20  #通常是15-20s
```

### 5. Descobrir IDs de elementos dinâmicos

```javascript
// Quando browser_snapshot não mostra refs
[...document.querySelectorAll('input')].map(i => i.id)
[...document.querySelectorAll('button')].map(b => b.textContent.trim())

// Ver HTML de um container
document.getElementById('chat-input').outerHTML
```

## Abordagem 2: Curl (teste rápido de lógica)

Para validar lógica backend sem esperar pelo browser:

```bash
# Init
RESP=$(curl -s -X POST http://localhost:5123/webhook/sac/init \
  -H 'Content-Type: application/json' \
  -d '{"nome":"Nome Teste","telefone":"(11) 99999-0000","ddd":"11"}')
echo "$RESP" | python3 -c "import json,sys; d=json.load(sys.stdin); print(d.get('lead_id'))"

# Chat — verificar flags
curl -s -X POST http://localhost:5123/webhook/sac \
  -H 'Content-Type: application/json' \
  -d '{"lead_id":ID,"nome":"Nome","telefone":"(11) 99999-0000","ddd":"11","mensagem":"texto","session_id":"sessao"}' \
  | python3 -c "
import json,sys
d=json.load(sys.stdin)
print('CTA:', d.get('mostrar_cta'))
print('EVAL:', d.get('mostrar_avaliacao'))
print('FASE:', d.get('fase'))
print('PERGUNTAS:', d.get('perguntas_sugeridas'))
"
```

## Quando usar qual abordagem

| Abordagem | Use para |
|---|---|
| Browser console | Teste visual, bottom-actions, perguntas sugeridas, typewriter, UX |
| Curl | Debug rápido, verificar lógica, flags, fase, sem esperar |
| Browser snapshot | Ler respostas completas sem esperar pelo UI |

## Notas Importantes

- **Endpoint webhook**: `/webhook/sac` (NÃO `/webhook/sac/chat`)
- **O botão "Sair"**: `onclick="sairChat()"` no `index.html`
- **WhatsApp CTA visível** = `className` contém `visivel` (não `display`)
- **Telefone no DB**: guardado com mascara `(XX) XXXXX-XXXX`
- **Limpar leads teste**: `DELETE FROM leads WHERE id > 10000` (IDs acima de 10000 são testes)

## Armadilha Comum: field name mismatch JS ↔ Flask

**Sintoma:** Login via widget mostra "Credenciais inválidas", mas `curl` funciona 100%.

**Causa:** O JavaScript envia `{username: u, password: p}` mas o Flask faz `data.get("login")` — `login` está vazio, `username` é ignorado.

**Regra:** Ao testar qualquer endpoint via widget, SEMPRE verifique que os nomes dos campos no `fetch()` body correspondem exatamente ao que o Flask espera via `data.get()`. Exemplo:
```javascript
// ✅ Correto — Flask espera 'login'
body: JSON.stringify({login: u, password: p})

// ❌ Errado — Flask não usa 'username'
body: JSON.stringify({username: u, password: p})
```

**Fix:** `templates/index.html` → acertar field name no JS → `systemctl --user restart sac-agent`.

## Armadilhas Comuns Encontradas em Testes

### 1. Double-Diagnostic Bug (CRÍTICO)
**Sintoma:** O bot faz a mesma pergunta de diagnóstico duas vezes — primeiro não entra (correcto), depois entra (incorrecto).

**Causa:** `construir_resposta()` em `sac_persuasao.py` chama `deve_entrar_diagnostico()` **sem** `pergunta_original`. A segunda chamada tem `pergunta=""` → não há classificação semântica → entra diagnóstico.

**Fix:** `pergunta_original` precisa ser propagada desde `webhook_sac()` → `construir_resposta()` → `deve_entrar_diagnostico()`.

**Como detectar:** Procurar no log duas chamadas consecutivas a `deve_entrar_diagnostico` — a segunda tem `pergunta=''`.

### 2. Classificação Keyword Too Broad (CRÍTICO)
**Sintoma:** "Tem algum módulo sobre ansiedade?" entra em diagnóstico porque a palavra "ansiedade" está numa lista de bloqueio ampla.

**Causa:** A regra `any(keyword in texto for keyword in palavras_problema)` faz match de substring em qualquer posição — "módulo sobre ansiedade" contém "ansiedade" mesmo sendo uma pergunta legítima sobre conteúdo.

**Fix:** Substituir por **padrões de declaração pessoal** (posicionais, no início da mensagem): `"tenho "`, `"sofro "`, `"estou com "`, `"minha "`, `"meu "`, `"pra mim "`. Estes indicam que a pessoa está a declarar que TEM um problema, vs. a perguntar sobre o tema.

### 3. Social Proof Não Detectada no Fallback (MÉDIO)
**Sintoma:** "Minha amiga recomendou, ela já fez" entra em diagnóstico incorrectamente.

**Causa:** A mensagem não tem `?`, embeddings abaixo do threshold, e o fallback não tem padrões de prova social.

**Fix a aplicar:** Adicionar ao fallback: `"já fiz"`, `"já formei"`, `"minha amiga"`, `"meu amigo"`, `"ele/ela fez"`, `"conheci alguém"` — estes indicam lead quente por referência e NÃO devem activar diagnóstico.

### 4. quer_falar_humano Checked AFTER Diagnostic Block (MÉDIO)
**Sintoma:** `mostrar_cta=True` mas a resposta enviada é a pergunta de diagnóstico.

**Causa:** A lógica `quer_falar_humano` override fica **depois** do bloco de diagnóstico — o diagnóstico é executado primeiro e sobrepõe o override.

**Fix:** Mover a detecção `quer_falar_humano` para **antes** do bloco de diagnóstico.

## Ficheiros principais

- `~/.hermes/sac_agent/sac_agent.py` — webhook endpoint
- `~/.hermes/sac_agent/sac_persuasao.py` — persuasão e CTA (aqui vivem os bugs 1-4)
- `~/.hermes/sac_agent/templates/index.html` — frontend chat
