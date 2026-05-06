---
name: sac-bot-html-formatting
description: Formatação HTML do SAC Bot — markdown para HTML, CSS das mensagens, debugging de formatação
---

# SAC Bot — HTML Formatting

## Arquitectura de formatação

O SAC Bot usa duas funções em `sac_agent.py` para formatar texto:

### `formatar_resposta(texto)` → HTML para o frontend
Converte markdown em HTML para renderização no chat (`innerHTML`):
- `**negrito**` → `<b>negrito</b>`
- `*itálico*` → `<i>itálico</i>`
- `\n\n` → párágrafos separados (`<p>...</p>`)
- `- item` → `<ul><li>item</li></ul>`

### `plain_resposta(texto)` → plain text para contexto LLM
Remove markdown e caracteres não-latinos. Usada para o contexto interno do LLM (não deve ter HTML).

### `limpar_resposta()` → DEPRECADA
Função antiga que destruía toda a formatação. **Substituída** por `formatar_resposta` e `plain_resposta`.

## CSS crítico para párágrafos visíveis

O `.msg-bot p` **PRECISA** de `border-bottom` senão os párágrafos parecem um bloco único:

```css
.msg-bot p {
    margin: 0 0 10px 0;
    padding: 6px 0 0 0;
    border-bottom: 1px solid rgba(255,255,255,0.08);  /* LINHA SEPARADORA */
}
.msg-bot p:first-child { padding-top: 0; border-top: none; }
.msg-bot p:last-child { margin-bottom: 0; border-bottom: none; }
.msg-bot b, .msg-bot strong { color: #00d4ff; font-weight: 700; }
.msg-bot i, .msg-bot em { font-style: italic; color: #b8c5d6; }
.msg-bot br { display: block; content: ""; margin: 6px 0; line-height: 1.4; }
```

## Bug crítico: regex concatenadas no shell

**NUNCA** fazer `re.sub()` com ranges Unicode concatenados em múltiplas linhas no shell:
```python
# ERRADO — não funciona
texto = re.sub(r'[\u4e00-\u9fff\u3000-\u303f...]', '', texto)

# CERTO — cada range em chamada separada
texto = re.sub(r'[\U00010000-\U0010ffff]', '', texto)
texto = re.sub(r'[\u4e00-\u9fff]', '', texto)
texto = re.sub(r'[\u3000-\u303f\u3040-\u309f\u30a0-\u30ff]', '', texto)
texto = re.sub(r'[\uac00-\ud7af]', '', texto)
texto = re.sub(r'[\u0400-\u04ff\u0500-\u052f]', '', texto)
texto = re.sub(r'[\u0600-\u06ff\u0750-\u077f\u08a0-\u08ff]', '', texto)
```

Isto acontece porque no shell o backslash é consumido antes de chegar ao Python.

## innerHTML vs textContent

No `index.html`, as mensagens do bot **DEVEM** usar `innerHTML`:
```javascript
msgBot.innerHTML = dados.mensagem;   // ✅ renderiza HTML
msgBot.textContent = dados.mensagem;  // ❌ mostra HTML como texto
```

## Debugging

### Verificar HTML no DOM
```javascript
document.getElementById('chat-mensagens').innerHTML
```

### Verificar se párágrafos estão a renderizar
```javascript
document.querySelectorAll('.msg-bot p').length  // deve ser > 0
```

### Verificar CSS aplicado
```javascript
getComputedStyle(document.querySelector('.msg-bot p')).marginBottom
```

## Ficheiros

| Ficheiro | Papel |
|---|---|
| `~/.hermes/sac_agent/sac_agent.py` | Backend — `formatar_resposta()`, `plain_resposta()` |
| `~/.hermes/sac_agent/sac_persuasao.py` | Gatilhos de persuasão e CTA |
| `~/.hermes/sac_agent/templates/index.html` | Frontend — CSS das mensagens + `innerHTML` |
