---
name: sac-qa-sync-cleanup
description: Protocolo de 3 camadas para manter consistência ao atualizar Q&As do SAC Bot — approved_qa + LanceDB + fonte documental
tags:
  - sac-agent
  - rag
  - lancedb
  - consistency
last_updated: 2026-04-25
---

# SAC Q&A — Sincronização de 3 Camadas ao Atualizar

## Quando usar
Quando o Álvaro aprovar ou corrigir uma Q&A do SAC Bot, este protocolo DEVE ser executado em 3 camadas para garantir consistência. Se a correção envolve **informação que mudou** (não apenas texto/tom), limpar o RAG é obrigatório.

## Camadas (sempre em ordem)

### Camada 1 — approved_qa (SQLite)
Gravar/atualizar a Q&A na tabela `approved_qa`.

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

### Camada 2 — LanceDB (vectores)
Determinar se o chunk problemático está indexado. Buscar por texto ou hash:

```python
import lancedb, os, sys
sys.path.insert(0, os.path.expanduser('~/KnowledgeBase'))
db = lancedb.connect(os.path.expanduser('~/KnowledgeBase/knowledge_db'))
tbl = db.open_table('metodoten')
arrow_table = tbl.to_arrow()

texts = arrow_table['text'].to_pylist()
sources = arrow_table['source'].to_pylist()
chunk_hashes = arrow_table['chunk_hash'].to_pylist()

for i, text in enumerate(texts):
    if 'palavra_chave' in str(text).lower():
        print(f"Row {i} | Hash: {chunk_hashes[i]}")
        print(text[:300])
```

Para deletar chunk específico:
```python
deleted = tbl.delete(f'chunk_hash == "HASH_DO_CHUNK"')
print('Rows deletadas:', deleted)
print('Total rows agora:', tbl.count_rows())
```

### Camada 3 — Fonte documental
Se o chunk veio de um documento indexado (site, apostila), corrigir o fonte para que uma futura re-indexação não reintroduza a informação errada.

Ficheiros típicos:
- Site: `~/.hermes/cache/documents/doc_alvarobiano_site_completo.md`
- Apostilas: `~/.hermes/cache/documents/`

## Exemplo real (Q13 — avaliação)
- **Erro:** Bot dizia "quizzes de múltipla escolha"
- **Fixe:** `~/.hermes/cache/documents/doc_alvarobiano_site_completo.md` linhas 200 e 266
- **Chunk deletado:** Row 1445, hash `98983e2bf128483caf78e84e666d4e94`

## Passo obrigatório — Escanear Q&As existentes

Sempre que limpar informação errada, verificar SE a mesma info existe em OUTRAS Q&As já gravadas:

```python
import sqlite3
conn = sqlite3.connect('sac_leads.db')
cur = conn.cursor()
cur.execute("SELECT COUNT(*) FROM approved_qa WHERE resposta LIKE '%termo_errado%'")
print(f"Q&As com termo errado: {cur.fetchone()[0]}")

cur.execute("SELECT id, pergunta, resposta FROM approved_qa WHERE resposta LIKE '%termo_errado%'")
for row in cur.fetchall():
    print(f"ID {row[0]}: {row[1][:60]}")
    print(f"Trecho: {row[2][:150]}...")
```

Se encontrar, corrigir com UPDATE SET resposta=... WHERE id=X.

## Lição aprendida — 25/04/2026 (membro da equipe → "um membro da equipe")

Quando tens 10+ ocorrências para substituir num ficheiro Python, `sed` é mais rápido que `patch`:

```bash
sed -i "s/texto_antigo/texto_novo/g" ficheiro.py
```

DEPOIS verificar gramática e sintaxe:

```bash
python3 -m py_compile ficheiro.py && echo "OK"
grep -n "texto_novo" ficheiro.py | wc -l
grep -c "texto_antigo" ficheiro.py  # deve ser 0
```

Problema real que ocorreu: substituir "membro da equipe" por "um membro da equipe" criou "a um membro da equipe" (gramática errada) em 3localizações. Corrigi com patches sequenciais. O `replace_all=true` com `patch` não teria funcionado porque a string era diferente em cada sítio.

LanceDB sem FTS: tabelas sem índice invertido não permitem `search("texto")`. Alternativa com `to_arrow()`:

```python
arrow_table = tbl.to_arrow()
texts = arrow_table['text'].to_pylist()
for i, text in enumerate(texts):
    if 'membro da equipe' in str(text):
        print(f"Row {i}: {text[:200]}")
```

Ordem de prioridade: approved_qa (SQLite) > LanceDB. Se approved_qa tem a resposta, ela é usada. LanceDB só entra se approved_qa não tiver match.

## Passo opcional — Actualizar System Prompt

Se a correcção envolve uma palavra em inglês proibida que apareceu na resposta do bot (ex: "pace"), adicionar à lista de banidos em `sac_agent.py` (linha ~170):

```
"pace"
```

Depois reiniciar o SAC Agent: `kill <PID>` + restart com background=true.

## Regra de Ouro

Se a Q&A aprovada existe em Camada 1, ela TEM prioridade sobre LanceDB. Mas se o LanceDB tem chunks com informação contraditória, o LLM pode usar esses chunks como contexto e gerar resposta errada. **Limpar sempre que o facto mudar.**

## Memória HOT — Optimização

Manter entradas curtas (target: <2000 chars). Acima de 90% (1980/2200) é preciso optimizar. Antes de adicionar nota crítica, verificar se entradas redundantes existem e removê-las primeiro.

Ver uso: `memory` tool mostra entries + usage ratio.

## Passo obrigatório — Após mudança global: Push GitHub

Depois de qualquer mudança significativa no SAC Bot, actualizar o cérebro GitHub:

```bash
cd ~/bianinho-cerebro
git add -A
git commit -m "fix: descrição da mudança"
git push origin main
```

Sempre que possível, verificar o push: `git log --oneline -1` deve mostrar o commit mais recente.
