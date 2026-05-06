---
name: sac-bot-qa-validation
description: Workflow para validar respostas do SAC Bot contra as 100 perguntas oficiais do Método TEN
triggers: [testar sac bot, validar qa sac, pergunta sac]
---

# SAC Bot Q&A Validation Workflow

## Quando usar
Validação de respostas do SAC Bot contra as 100 perguntas da lista oficial do Método TEN.

## Fluxo (sempre neste ordem)

### 1. Testar a pergunta
```python
import requests, time
start = time.time()
r = requests.post('http://localhost:5123/webhook/sac', json={
    'pergunta': 'PERGUNTA COMPLETA',
    'lead_id': 999,
    'session_id': 'test-qN'
}, timeout=60)
elapsed = int((time.time() - start) * 1000)
data = r.json()
print(f'Status: {r.status_code} | Tempo: {elapsed}ms')
print(f'Resposta:\n{data.get("resposta", data)}')
```

### 2. Mostrar resultado ao Álvaro
- Apresentar a resposta completa
- Fazer análise: conteúdo, tom, velocidade, erros
- Aguardar aprovação

### 3. Gravação (após aprovação)
```python
import sqlite3
from datetime import datetime
conn = sqlite3.connect('sac_leads.db')
cur = conn.cursor()
resposta = '''RESPOSTA COMPLETA APÓVADA'''
cur.execute('''
INSERT INTO approved_qa (pergunta, resposta, tema, aprovado_em, collection)
VALUES (?, ?, ?, ?, ?)
''', (
    'PERGUNTA COMPLETA',
    resposta,
    'TEMA',
    datetime.now().isoformat(),
    'metodo-ten'
))
conn.commit()
print('Q<N> gravada com ID:', cur.lastrowid)
```

### 4. Atualização de Q&A existente
Se o Álvaro fornecer uma versão corrigida:
```python
cur.execute('UPDATE approved_qa SET resposta=? WHERE id=<ID>', (resposta_corrigida,))
conn.commit()
```

## Notas importantes

- **Timeout**: usar sempre `timeout=60` (o SAC Agent pode demorar >30s)
- **Se timeout**: verificar se o processo está ativo (`ss -tlnp | grep 5123`) e tentar novamente
- **Se resposta incompleta no chat**: verificar ficheiro em cache em `/home/alvarobiano/.hermes/cache/documents/` — pode estar a versão completa truncada no Telegram
- **Termo "mentoria"**: não usar neste contexto — usar "atendimento em grupos do Telegram"
- **Q&As aprovadas** têm prioridade sobre LanceDB (Camada 1 > Camada 2). Atualizar SQLite é suficiente — não precisa reindexar RAG

## Temas por grupo
1. O que é o Método TEN (Q1-Q5)
2. Para quem é (Q6-Q7)
3. Estrutura e formato (Q8-Q9)
4. Certificação (Q10+)
