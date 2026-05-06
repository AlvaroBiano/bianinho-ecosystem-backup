#!/usr/bin/env python3
"""
Busca RAG BM25 no banco LanceDB — tabela metodoten.
Uso: ~/KnowledgeBase/venv/bin/python ~/.hermes/scripts/rag_search.py "sua pergunta" [top_k]

Dependências: lancedb, pandas (via ~/KnowledgeBase/venv)
"""
import sys, re
from collections import Counter
import lancedb

DB_PATH = "/home/alvarobiano/KnowledgeBase/knowledge_db"
TOP_K_DEFAULT = 5

def build_index():
    db = lancedb.connect(DB_PATH)
    tbl = db.open_table("metodoten")
    df = tbl.to_pandas()
    k1, b = 1.5, 0.75
    N = len(df)
    corpus, doc_lens, doc_freqs = [], [], Counter()
    for text in df['text']:
        tokens = re.findall(r'\b\w+\b', str(text).lower())
        corpus.append(tokens)
        doc_lens.append(len(tokens))
        for term in set(tokens):
            doc_freqs[term] += 1
    avgdl = sum(doc_lens) / max(N, 1)
    return df, corpus, doc_lens, doc_freqs, avgdl, k1, b, N

def bm25_search(query, df, corpus, doc_lens, doc_freqs, avgdl, k1, b, N, top_k=5):
    query_tokens = re.findall(r'\b\w+\b', query.lower())
    scores = []
    for i, doc in enumerate(corpus):
        score = 0.0
        for term in query_tokens:
            if term not in doc_freqs:
                continue
            df_val = doc_freqs[term]
            idf = max(0, (N - df_val + 0.5) / (df_val + 0.5))
            tf_val = sum(1 for t in doc if t == term)
            numerator = tf_val * (k1 + 1)
            denominator = tf_val + k1 * (1 - b + b * doc_lens[i] / max(avgdl, 0.001))
            score += idf * numerator / max(denominator, 0.001)
        scores.append((i, score))
    ranked = sorted(scores, key=lambda x: x[1], reverse=True)[:top_k]
    return [(df.iloc[i]['source'], df.iloc[i]['text'], df.iloc[i]['category'], score)
             for i, score in ranked if score > 0]

def search(query, top_k=5):
    df, corpus, doc_lens, doc_freqs, avgdl, k1, b, N = build_index()
    return bm25_search(query, df, corpus, doc_lens, doc_freqs, avgdl, k1, b, N, top_k)

if __name__ == "__main__":
    query = sys.argv[1] if len(sys.argv) > 1 else "vitamina D"
    top_k = int(sys.argv[2]) if len(sys.argv) > 2 else TOP_K_DEFAULT
    results = search(query, top_k)
    print(f"\n🔍 Busca: '{query}' — {len(results)} resultados\n")
    for i, (source, text, category, score) in enumerate(results, 1):
        print(f"[{i}] 📖 {source} (score={score:.2f}) [{category}]")
        print(f"    {text[:300]}...")
        print()
