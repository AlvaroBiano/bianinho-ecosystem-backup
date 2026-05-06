#!/usr/bin/env python3
"""
Fix de categorização do RAG — Bianinho
Método: ler tudo → modificar df → drop table → recreate → add
Execute: ~/KnowledgeBase/venv/bin/python /tmp/rag_cleanup.py
"""
import sys
sys.path.insert(0, '/home/alvarobiano/KnowledgeBase')

from pathlib import Path
import lancedb
import pandas as pd
import pyarrow as pa

DB_PATH = Path('/home/alvarobiano/KnowledgeBase/knowledge_db')

SCHEMA = pa.schema([
    pa.field("vector", pa.list_(pa.float32(), 1536)),
    pa.field("text", pa.string()),
    pa.field("source", pa.string()),
    pa.field("category", pa.string()),
    pa.field("chunk_index", pa.int32()),
    pa.field("total_chunks", pa.int32()),
    pa.field("filepath", pa.string()),
    pa.field("language", pa.string()),
    pa.field("chunk_hash", pa.string()),
    pa.field("processed_at", pa.string()),
])

db = lancedb.connect(str(DB_PATH))

# PASSO 1: Ler
print("📖 Lendo banco...")
df = tbl = db.open_table('chunks').to_pandas()
total_before = len(df)
print(f"   {total_before} chunks, {df['source'].nunique()} livros")

# PASSO 2: Modificar — Remover duplicados TXT vs EPUB
duplicates = [
    'the_body_keeps_the_score.txt',
    'o_poder_do_habito.txt',
    'atomic_habits.txt',
]
for src in duplicates:
    n = (df['source'] == src).sum()
    if n > 0:
        print(f"   🗑️  '{src}' ({n} chunks)")
        df = df[df['source'] != src].reset_index(drop=True)

# PASSO 2b: Remover não-livros
non_book_mask = (
    df['source'].str.startswith('consolidation-', na=False) |
    df['source'].isin([
        'incidente-2026-04-23.txt', 'MEMORY-migration-16-04-2026',
        'estudo_50mil_canais', 'teste_sanitizacao.txt',
        'doc_alvarobiano_site_completo.md',
        'marketing-para-terapeutas.md', 'criacao-cursos-online.md',
    ])
)
for src in df[non_book_mask]['source'].unique():
    print(f"   🗑️  '{src}' ({(df['source']==src).sum()} chunks)")
df = df[~non_book_mask].reset_index(drop=True)

# PASSO 2c: Recategorizar livros mal classificados
recat = {
    # IA
    'Multi-Agent_Coordination.epub': 'inteligencia_artificial',
    'AI_Prompt_Engineering_Bible.epub': 'inteligencia_artificial',
    'Your_Creative_Brain_and_AI.epub': 'inteligencia_artificial',
    'Autonomous_Minds.pdf': 'inteligencia_artificial',
    'Natural_General_Intelligence.pdf': 'inteligencia_artificial',
    'Artificial_Intelligence_of_Neuromorphic_Systems.pdf': 'inteligencia_artificial',
    'Mind_Brain_Quantum_AI.pdf': 'inteligencia_artificial',
    'Principles_of_Building_AI_Agents.pdf': 'inteligencia_artificial',
    'doc_b7f7a038a7f1_RAG_with_Python_Cookbook_Learn_principles_of_RAG_with_LLM_and_agentic.pdf': 'inteligencia_artificial',
    'Neural_Marketing_Hack.epub': 'inteligencia_artificial',
    'Prompted_How_to_Create_and_Communicate_with_AI.pdf': 'inteligencia_artificial',
    'money_ai_stepbystep.txt': 'inteligencia_artificial',
    'How_to_Make_Money_with_AI.txt': 'inteligencia_artificial',
    'doc_695a26a9105e_AI_Profit_Playbook_Unleash_Proven_Tactics_for_Massive_AI_Driven.pdf': 'inteligencia_artificial',
    # Comunicação
    'as_48_leis_do_poder.epub': 'comunicacao',
    'Never_Split_the_Difference.txt': 'comunicacao',
    'Dark_Psychology.txt': 'comunicacao',
}
for source, new_cat in recat.items():
    mask = df['source'] == source
    if mask.sum() > 0:
        old = df.loc[mask, 'category'].iloc[0]
        n = mask.sum()
        if old != new_cat:
            print(f"   🔄 '{source}': '{old}' → '{new_cat}' ({n} chunks)")
            df.loc[mask, 'category'] = new_cat

# PASSO 3: Drop + Recreate
print("\n🗑️  Dropping table...")
db.drop_table('chunks')
print("➕ Recreating + inserting...")
db.create_table('chunks', schema=SCHEMA, mode='create')
tbl_new = db.open_table('chunks')
tbl_new.add(df)
print(f"   ✅ {len(df)} chunks (removidos: {total_before - len(df)})")

# PASSO 4: Relatório
print("\n RESULTADO:")
df2 = tbl_new.to_pandas()
print(df2.groupby('category').agg(
    chunks=('text','count'), livros=('source','nunique')
).sort_values('chunks', ascending=False).to_string())
