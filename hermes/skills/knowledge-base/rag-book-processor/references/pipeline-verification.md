# Pipeline Verification — Bug de Sucesso Falso

## Session Notes (30/04/2026)

**Incidente:** `fracasso_sucesso.pdf` reportou "✅ SUCESSO" e "221 registros inseridos no banco" mas o livro **não estava no banco** quando verificado (0 chunks encontrados).

## Root Cause

O pipeline loga `✅ Removidas entradas anteriores de 'source'` + `N registros inseridos no banco` ANTES de a transacção LanceDB realmente completar. Há um desfasamento entre o log e a realidade.

**Hipótese:** A operação `tbl.add()` pode completar parcialmente (ex: timeout de rede durante vectorização em batch) sem lançar excepção — o log diz sucesso mas o commit não aconteceu.

## Verificação Obrigatória — Sempre

**Nota:** Livros processados para Álvaro usam a tabela `metodoten` (não `chunks`). O argumento `--table metodoten` no vector_brain.py selecciona esta tabela.

Depois de qualquer processamento, **SEMPRE** confirmar:

```python
import sys
sys.path.insert(0, '/home/alvarobiano/KnowledgeBase')
import lancedb

db = lancedb.connect('/home/alvarobiano/KnowledgeBase/knowledge_db')

# Verificar tabela metodoten (tabela principal para livros do Álvaro)
tbl = db.open_table('metodoten')
df = tbl.to_pandas()

source = 'nome_que_aparece_no_log.pdf'
found = df[df['source'].str.contains(source, case=False, na=False)]
print(f"Chips no banco: {len(found)}")
if len(found) == 0:
    # Tentar tabela chunks como fallback
    tbl2 = db.open_table('chunks')
    df2 = tbl2.to_pandas()
    found2 = df2[df2['source'].str.contains(source, case=False, na=False)]
    print(f"Chips em 'chunks': {len(found2)}")
    if len(found2) == 0:
        print("❌ ALERTA: Não está no banco! Reprocessar com --force")
    else:
        print(f"✅ Confirmado em 'chunks': {len(found2)} chips em '{found2['category'].iloc[0]}'")
else:
    print(f"✅ Confirmado em 'metodoten': {len(found)} chips em '{found['category'].iloc[0]}'")
```

## Se 0 Chunks

Reprocessar imediatamente com `--force`:

```bash
cd ~/KnowledgeBase && ./venv/bin/python pipeline/livro_pipeline.py \
  --file "/tmp/nome.pdf" --category auto --force
```

**Regra:** Se o chunk count parecer baixo (< 10 para um PDF > 1MB) ou se o livro simplesmente não aparecer na pesquisa RAG → verificar com o script acima.

## Checklist Pós-Processamento

```
□ Pipeline logou "✅ SUCESSO"
□ Chunk count é razoável (mínimo ~5 para PDFs < 500KB, muito mais para grandes)
□ Categoria não é "default" com score 8-10% (corrigir se aplicável)
□ VERIFICAR: livro existe no banco (script acima)
□ Se 0 chunks → reprocessar com --force
```
