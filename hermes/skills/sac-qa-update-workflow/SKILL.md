---
name: SAC Q&A Update Workflow
description: Workflow completo para atualizar Q&As do SAC Bot — Approved DB + LanceDB + fonte. Garante que não haja inconsistência entre camadas RAG.
category: sac-agent
tags: [sac, rag, lancedb, approved-qa]
---

# SAC Q&A Update Workflow

## Quando usar
Quando uma Q&A aprovada é criada, atualizada ou corregida, este workflow GARANTE que o sistema não gere respostas erradas em nenhuma circunstância.

## O Problema
O SAC Bot tem 2 camadas RAG:
- **Camada 1:** Approved Q&A (SQLite `approved_qa`) — PRIORIDADE MÁXIMA
- **Camada 2:** LanceDB (apostilas/indexadas) — usada só se Camada 1 não responder

Se a Camada 2 tiver informação ERRADA sobre um tema, e a Camada 1 não tiver resposta aprovada para esse tema, o bot vai gerar resposta ERRADA a partir dos chunks do LanceDB.

**Solução simples:** basta gravar a Q&A aprovada na Camada 1 que ela tem prioridade. MAS se o chunk do LanceDB CONTINÉM informação errada, quando re-indexar (ex: novo download do site), a info errada volta ao LanceDB e pode contaminar respostas futuras.

## Workflow Completo (3 etapas)

### Etapa 1: Atualizar Approved Q&A
```python
import sqlite3
from datetime import datetime

conn = sqlite3.connect('sac_leads.db')
cur = conn.cursor()
cur.execute('''
    INSERT INTO approved_qa (pergunta, resposta, tema, aprovado_em, collection)
    VALUES (?, ?, ?, ?, ?)
''', (pergunta, resposta, tema, datetime.now().isoformat(), 'metodo-ten'))
conn.commit()
```

### Etapa 2: Deletar chunks errados do LanceDB

**Passo 2.1 — Encontrar o chunk errado:**
```python
import lancedb, os, sys, pyarrow as pa
sys.path.insert(0, os.path.expanduser('~/KnowledgeBase'))

db = lancedb.connect(os.path.expanduser('~/KnowledgeBase/knowledge_db'))
tbl = db.open_table('metodoten')
arrow_table = tbl.to_arrow()

texts = arrow_table['text'].to_pylist()
chunk_hashes = arrow_table['chunk_hash'].to_pylist()

for i, text in enumerate(texts):
    if 'palavra_errada' in str(text).lower():
        print(f'Row {i} | Hash: {chunk_hashes[i]}')
        print(f'Texto: {str(text)[:300]}')
```

**Passo 2.2 — Deletar pelo hash:**
```python
deleted = tbl.delete(f'chunk_hash == "HASH_DO_CHUNK"')
print('Deletadas:', deleted.num_deleted_rows)
print('Total rows agora:', tbl.count_rows())
```

### Etapa 3: Corrigir o ficheiro fonte
Encontrar e corrigir o texto no ficheiro fonte original (ex: `~/.hermes/cache/documents/doc_alvarobiano_site_completo.md`) para que um futuro re-index não reintroduza a informação errada.

```bash
# Encontrar o texto
grep -n "palavra_errada" ~/.hermes/cache/documents/doc_alvarobiano_site_completo.md
```

## Notas Importantes
- **Retry MiniMax:** O código tem retry de 10 tentativas com `time.sleep(2)` entre tentativas. Se todas falharem, usa fallback da Q&A aprovada.
- **Aprovada = Prioridade Absoluta:** Qualquer Q&A na tabela `approved_qa` SEMPRE sobrepõe o LanceDB. Mas se o fonte tiver info errada e for re-indexado sem estar corrigido, volta a contaminar.
- **Não precisa re-indexar após corrigir Approved Q&A:** A Camada 1 já tem prioridade máxima. Só precisa limpar o LanceDB + fonte se houver risco de re-index.
