---
name: sac-bot-debugging
description: SAC Bot debugging patterns — counter bugs, classifier patching, server restart, message truncation
tags: [sac-bot, debugging, python, troubleshooting]
---

# SAC Bot — Debugging Patterns

Coleção de padrões de debugging descobertos durante o desenvolvimento do SAC Bot. Cada padrão representa uma lição aprendida que se aplica a problemas futuros.

---

## ◆ Off-by-One em Contadores

**Skill original:** `off-by-one-counter-debugging`

### Problema Real
O SAC Bot usa `interacoes` para contar trocas de mensagens. O utilizador pediu "aparecer após a 3ª troca". patches iniciais usaram `interacoes >= 3`. O teste revelou que na 3ª troca real, `interacoes=2`.

### Lição
Contadores em código podem ser **0-indexed** (começam em 0) ou **1-indexed** (começam em 1). Nunca assumes — **testa sempre**.

### Como Diagnosticar
```python
# Adicionar TEMPORARIAMENTE ao response JSON
"interacoes": interacoes,

# Depois testar com 3 trocas reais
# Troca 1: interacoes=0 → 1-indexed seria 1
# Troca 2: interacoes=1 → 1-indexed seria 2
# Troca 3: interacoes=2 → 1-indexed seria 3
# Resultado: 0-indexed (interacoes=N-1)
```

### Regra Prática
Quando o código usa `if interacoes < X` ou `>= X`, verificar:
1. Onde é que `interacoes` é definido/incrementado?
2. Qual é o valor na primeira iteração?
3. Testar com 3 casos: troca 1, 2, 3 para confirmar

### Referência
SAC Bot: `~/.hermes/sac_agent/sac_agent.py` (linha ~800) — `interacoes` começa em 0 na primeira troca.

---

## ◆ Patching Classifiers — Padrão de Correção de if/elif

**Skill original:** `classifier-patching-pattern`

### O Problema
Ao fazer patch de uma função classificadora com if/elif/else, as condições são avaliadas top-to-bottom com short-circuit booleano. Ao adicionar novas regras, a ordem é crítica.

```python
# ERRADO — o primeiro disjuncto "A in s" dispara primeiro
if ("A" in s or ("A" in s and "B" in s)):
    return "specific"
if "timeout" in s:
    return "timeout"
```

Mais insidioso: quando tens `if "httpx" in s: return "network_timeout"` ANTES da nova regra Telegram, e a linha Telegram contém `httpx.ReadError`, a regra genérica `httpx` dispara primeiro.

### O Padrão Correto
Usar variável intermédia para o prefixo do módulo, e colocar padrões mais específicos ANTES dos genéricos:

```python
# CORRETO — variável intermédia + ordem correta
telegram_module_present = "gateway.platforms.telegram" in s
if (("gateway.platforms.telegram_network" in s)
        or (telegram_module_present and ("reconnect" in s or "httpx.readerror" in s))):
    return "config_missing"
if "timeout" in s or "httpx" in s or "connection" in s:
    return "network_timeout"
```

### Princípios Chave
1. **Padrões mais específicos (com prefixos longos) devem vir ANTES de padrões genéricos** na cadeia if/elif
2. **Condições compostas com `and` devem usar variáveis intermédias** para evitar short-circuit
3. **Ao combinar `prefixo_modulo AND conteudo`, sempre extrair o prefixo como variável separada**

### Verificação
```python
import sys
for m in list(sys.modules.keys()):
    if 'your_module' in m:
        del sys.modules[m]

sys.path.insert(0, '/path/to/scripts')
from your_module import classify_error_line

tests = [
    ('padrão específico com prefixo e conteúdo', 'expected_category'),
    ('padrão genérico que deve funcionar', 'expected_category'),
]
all_ok = True
for line, expected in tests:
    result = classify_error_line(line)
    if result != expected:
        all_ok = False
        print(f'FAIL [{expected}] got [{result}]: {line[:60]}')
print('All passed!' if all_ok else 'SOME FAILED')
```

---

## ◆ Server Restart After Code Change

**Skill original:** `server-restart-after-code-change`

### Sintomas
- Fix de código aplicado mas comportamento não muda
- `test_client()` funciona mas `curl` ao servidor real não
- Mudanças funcionam no dev mas não em produção

### Causa Raiz
Iniciar o servidor manualmente (ex: `python3 sac_agent.py --port 5123`) cria um processo que o systemd não rastreia. Um `systemctl restart sac-agent` subsequente tenta iniciar um novo processo mas o antigo continua a correr na mesma porta.

### Como Diagnosticar
```bash
# Ver start time do processo vs file modification time
ps aux | grep sac_agent | grep -v grep
stat ~/.hermes/sac_agent/sac_agent.py

# Verificar qual código o servidor real está a usar
curl -s http://localhost:5123/webhook/sac/init \
  -X POST -H "Content-Type: application/json" \
  -d '{"nome":"Test","telefone":"(00) 00000-0000","ddd":"00"}' | \
  python3 -c "import sys,json; d=json.load(sys.stdin); print('mostrar_cta:', d.get('mostrar_cta'))"
```

### Como Corrigir
```bash
# 1. Matar TODOS os processos com o código antigo
pkill -f sac_agent.py

# 2. Verificar que a porta está livre
lsof -i :5123

# 3. Iniciar fresco via systemd
systemctl --user start sac-agent

# 4. Verificar novo PID e start time
systemctl --user status sac-agent --no-pager
ps aux | grep sac_agent | grep -v grep
```

### Distinção Crítica
| Scenario | Sintoma | Causa |
|----------|---------|-------|
| Código mudou, servidor não reiniciou | Comportamento igual após restart | Processo antigo ainda a correr |
| Código mudou, servidor reiniciou | Comportamento ainda errado | Bug está no código |
| test_client() funciona, servidor real não | Endpoint 404 ou resposta errada | Código depois do app.run() ou processo antigo |

### Referência
SAC Bot PID 18771 (08:41) ainda a correr quando systemd tentou reiniciar (09:33). Kill + restart corrigiu.

---

## ◆ Debug de Mensagens Truncadas no Telegram

**Skill original:** `session-debug-message-truncation`

### O Problema
O Álvaro recebe mensagens longas do Telegram truncadas. A causa é o character filter que remove caracteres não-latinos — o texto em português com acentos é destruído antes de chegar ao modelo.

### Solução
O character filter (`.replace()` chains) remove acentos e caracteres especiais. Estas substituições destroem o texto antes do processamento:

```python
# NÃO usar em texto que vai ser enviado ao Telegram
# Estas substituições destroem texto em português:
text = text.replace('á', 'a').replace('ã', 'a')...
```

O fix está em manter o texto original intacto para logging/display e aplicar sanitização apenas onde necessário (ex: na resposta do modelo, não na mensagem original).

### Referência
Skill: `sac-agent-character-filter` — o filtro de saneamento de caracteres.
