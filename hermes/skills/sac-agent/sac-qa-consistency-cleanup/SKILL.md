---
name: sac-qa-consistency-cleanup
description: Quando uma Q&A é criada/atualizada na base approved_qa, limpar o mesmo conteúdo errado do LanceDB e dos ficheiros fonte.
triggers: [sac, q&a, rag, lancedb, approved_qa]
---

# SAC Q&A + RAG Consistency Cleanup

## Trigger
Quando uma Q&A é criada, atualizada ou corrigida na base `approved_qa` do SQLite, o mesmo conteúdo errado pode existir no LanceDB E nos ficheiros fonte. Se não limpar ambos, o bot pode usar informação desatualizada como fallback.

## Workflow de 3 camadas

### Passo 1 — Base Approved Q&A (SQLite)
Gravar/atualizar a Q&A aprovada normalmente via `INSERT INTO approved_qa` ou `UPDATE approved_qa SET resposta=? WHERE id=?`.

### Passo 2 — Ficheiros Fonte
Procurar nos ficheiros em `~/.hermes/cache/documents/` o texto errado que foi substituído. Corrigir manualmente.

### Passo 3 — LanceDB (Chunks vetoriais)
Procurar chunks que contêm a informação errada e deletar:

```bash
cd ~/.hermes/sac_agent && venv/bin/python3 -c "
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
        print(str(t)[:200])
"
# Deletar pelo hash:
tbl.delete('chunk_hash == \"HASH_AQUI\"')
```

## Exemplo real

**Q13 — Avaliação:**
- Errado: "quizzes de múltipla escolha", "nota"
- Corrigido: "autoavaliação sem nota"
- Ficheiro: `doc_alvarobiano_site_completo.md` — 2 lugares corrigidos
- LanceDB: chunk Row 1445 deletado (hash: 98983e2bf128483caf78e84e666d4e94)

**Q14 — Preço:**
- Errado: "R$ 490/mês", "12x R$ 778"
- Corrigido: redirecionar para www.alvarobiano.com.br
- Ficheiro: linha de preço removida
- LanceDB: Row 1449 deletada

## Regras de Ouro
1. **SEMPRE** atualizar Approved Q&A E limpar LanceDB E corrigir fonte — nunca apenas um
2. Ao adicionar palavra banida ao system prompt (ex: "pace"), fazer patch imediato
3. Após mudar fonte, não é preciso re-indexar se a Q&A aprovada já cobre o tema (Camada 1 tem prioridade)
4. Reiniciar SAC Agent após mudanças no código (`kill <PID>` + background restart)
