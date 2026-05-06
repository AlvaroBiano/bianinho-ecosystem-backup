#!/usr/bin/env python3
"""
Recategorização rápida de um livro já vectorizado.
Não re-vectoriza — só muda a categoria no banco.
Execute: ~/KnowledgeBase/venv/bin/python /tmp/recategorize.py <source_name> <new_category>

Exemplo: ~/KnowledgeBase/venv/bin/python /tmp/recategorize.py fracasso_sucesso.pdf desenvolvimento_pessoal
"""
import sys
sys.path.insert(0, '/home/alvarobiano/KnowledgeBase')
from pathlib import Path
import lancedb
import pandas as pd
import pyarrow as pa

source = sys.argv[1] if len(sys.argv) > 1 else input("source: ").strip()
new_cat = sys.argv[2] if len(sys.argv) > 2 else input("nova categoria: ").strip()

db = lancedb.connect('/home/alvarobiano/KnowledgeBase/knowledge_db')
tbl = db.open_table('chunks')
df = tbl.to_pandas()

mask = df['source'] == source
if mask.sum() == 0:
    print(f"NÃO ENCONTRADO: '{source}'")
    sys.exit(1)

old_cat = df.loc[mask, 'category'].iloc[0]
n = mask.sum()
if old_cat == new_cat:
    print(f"JÁ ESTÁ: '{source}' é '{new_cat}' ({n} chunks)")
else:
    print(f"{source}: '{old_cat}' → '{new_cat}' ({n} chunks)")
    df.loc[mask, 'category'] = new_cat
    tbl.delete(f"source = '{source}'")
    # LanceDB aceita pandas DataFrame directamente
    tbl.add(df[mask])
    print("✅ Recategorizado")

    # Verificação: confirmar que está no banco
    tbl_verify = db.open_table('chunks')
    df_v = tbl_verify.to_pandas()
    found = df_v[df_v['source'] == source]
    print(f"  Verificação: {len(found)} chunks no banco")

print("\nEstado actual:")
df2 = tbl.to_pandas()
print(df2.groupby('category').agg(chunks=('text','count'), livros=('source','nunique')).sort_values('chunks', ascending=False).to_string())
