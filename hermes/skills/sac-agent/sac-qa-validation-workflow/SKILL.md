# SAC Q&A Validation — Workflow Completo

## Quando usar
Validação de respostas do SAC Bot contra a lista de 50 perguntas de qualificação.

---

## Workflow de 1 pergunta

### 1. Testar
```bash
cd ~/.hermes/sac_agent && venv/bin/python3 -c "
import requests, time
start = time.time()
r = requests.post('http://localhost:5123/webhook/sac', json={
    'pergunta': 'PERGUNTA_AQUI',
    'lead_id': 999,
    'session_id': 'test-qN'
}, timeout=90)
elapsed = int((time.time() - start) * 1000)
data = r.json()
print(f'Status: {r.status_code} | Tempo: {elapsed}ms')
print(f'Resposta:\n{data.get(\"resposta\", data)}')
"
```

### 2. Mostrar ao Álvaro
Aguardar "Perfeito" ou correção.

### 3. Se Álvaro aprovar → Gravar
```python
import sqlite3
from datetime import datetime
conn = sqlite3.connect('sac_leads.db')
cur = conn.cursor()
resposta = '''RESPOSTA COMPLETA AQUI'''
cur.execute('''
INSERT INTO approved_qa (pergunta, resposta, tema, aprovado_em, collection)
VALUES (?, ?, ?, ?, ?)
''', (
    'PERGUNTA',
    resposta,
    'TEMA',
    datetime.now().isoformat(),
    'metodo-ten'
))
conn.commit()
```

---

## REGRA DE OURO: Consistência multi-camada

Quando uma Q&A é corrigida, SEMPRE atualizar TODAS as camadas:

1. **Camada 1 (approved_qa)** — INSERT ou UPDATE na tabela `sac_leads.db`
2. **Camada 2 (LanceDB)** — Se o erro também existe nos chunks:
   - Identificar e deletar: `tbl.delete('chunk_hash == "HASH"')`
3. **Ficheiro fonte** — Corrigir para não ser reintroduzido na re-indexação

### Padrões de erros e limpeza

| Erro | Camada | Como identificar | Ação |
|---|---|---|---|
| Quiz/múltipla escolha | LanceDB + Site | 'quiz' + 'múltipla escolha' | Deletar chunk + patch site |
| Preço | LanceDB + Site | 'R$' + '490' + '778' | Deletar chunk + patch site |
| Termos em inglês | System prompt | "pace", "feedback", etc. | Adicionar à lista negra |

### Buscar chunks no LanceDB
```python
import lancedb, os, sys
sys.path.insert(0, os.path.expanduser('~/KnowledgeBase'))
db = lancedb.connect(os.path.expanduser('~/KnowledgeBase/knowledge_db'))
tbl = db.open_table('metodoten')
arrow_table = tbl.to_arrow()
texts = arrow_table['text'].to_pylist()
chunk_hashes = arrow_table['chunk_hash'].to_pylist()
for i, t in enumerate(texts):
    if 'TERMO_ERRADO' in str(t):
        print(f'Row {i} | Hash: {chunk_hashes[i]}')
```

### Deletar chunk
```python
deleted = tbl.delete('chunk_hash == "HASH_AQUI"')
```

---

## System Prompt — Palavras em inglês proibidas
"familiarity", "feedback", "upgrade", "knowing", "helpful", "thank you", "pace"
Local: `~/.hermes/sac_agent/sac_agent.py` → system_prompt em `llm_generate()`

## Retry MiniMax
10 tentativas com 2s sleep. Funções `llm_generate` e `llm_generate_qa`.

## Limite Telegram
Se mensagem chega cortada → ler de `~/.hermes/cache/documents/doc_*_NOME.txt`
