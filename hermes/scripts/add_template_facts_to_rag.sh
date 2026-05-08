#!/bin/bash
# Adicionar facts do template PDF científico ao RAG LanceDB
# Executar quando o servidor Linux estiver online

echo "📦 Facts do template PDF científico para adicionar ao RAG:"
echo ""

FACTS='[
  {
    "text": "Template de Relatorio Cientifico PDF: template HTML/CSS profissional em tons de azul (#0d3b66, #1a5f7a) e verde (#2d8a7b, #3da935). Guardado em ~/.hermes/templates/scientific_report_template.html. Gera PDFs profissionais com Chrome headless.",
    "source": "template-scientific-report",
    "category": "templates",
    "filepath": "~/.hermes/templates/scientific_report_template.html"
  },
  {
    "text": "Template PDF cientifico: estrutura completa inclui header com gradiente azul-verde, sections com h3 e borda verde, callout boxes (verde, azul, warning), tables com header gradiente, article cards em grid 2 colunas, flowchart com steps e setas, conclusion grid 2x2 com glass effect, footer com gradiente.",
    "source": "template-scientific-report",
    "category": "templates",
    "filepath": "~/.hermes/templates/scientific_report_template.html"
  },
  {
    "text": "Template relatorio cientifico: paleta de cores - Azul escuro #0d3b66, Azul medio #1a5f7a, Azul claro #2d8a7b, Verde #3da935, Verde claro #7ed957. Backgrounds: #f8fbfc, #f0f9f6, #f0f7fc.",
    "source": "template-scientific-report",
    "category": "templates",
    "filepath": "~/.hermes/templates/scientific_report_template.html"
  },
  {
    "text": "Skill para gerar relatorios PDF cientificos: skill scientific-report-template em ~/.hermes/skills/scientific-report-template/. Usa Chrome headless: /Applications/Google Chrome.app/Contents/MacOS/Google Chrome --headless --no-sandbox --disable-gpu --print-to-pdf.",
    "source": "skill-scientific-report-template",
    "category": "templates",
    "filepath": "~/.hermes/skills/scientific-report-template/SKILL.md"
  },
  {
    "text": "TemplateHTML cientifico: placeholders para substituicao dinamica - TITULO, SUBTITULO, DATA, NUM_ARTIGOS, SECTIONS_HTML. Callout boxes: class=callout, callout blue, callout warning. Article cards: class=article-card com score badge, pmid, title, journal.",
    "source": "template-scientific-report",
    "category": "templates",
    "filepath": "~/.hermes/templates/scientific_report_template.html"
  },
  {
    "text": "Relatorio fibromialgia 07/05/2026: relatorio cientifico Fibromialgia Origem Emocional e Diagnostico Exclusivamente Clinico gerou PDF ~/Documents/FIBROMIALGIA_Relatorio_Cientifico_2026-05-07.pdf. 52 artigos PubMed, 18 com abstract valido.",
    "source": "fibromyalgia-report-07-05-2026",
    "category": "relatorios",
    "filepath": "~/Documents/FIBROMIALGIA_Relatorio_Cientifico_2026-05-07.pdf"
  }
]'

echo "$FACTS" | python3 -c "
import sys, json, os, sys
sys.path.insert(0, os.path.expanduser('~/Library/Application Support/hermes/KnowledgeBase'))
from vector_brain import get_table, embedder, db
import hashlib
from datetime import datetime

facts = json.load(sys.stdin)
table = get_table(db)
texts = [f['text'] for f in facts]
vectors = embedder.generate_text_embeddings(texts)

rows = []
for i, f in enumerate(facts):
    chunk_hash = hashlib.sha256(f['text'].encode()).hexdigest()[:16]
    rows.append({
        'vector': vectors[i]['embedding'],
        'text': f['text'],
        'source': f.get('source', 'unknown'),
        'category': f.get('category', 'general'),
        'chunk_index': 0, 'total_chunks': 1,
        'filepath': f.get('filepath', 'memory-migration'),
        'language': 'pt-BR', 'chunk_hash': chunk_hash,
        'processed_at': datetime.now().isoformat(),
    })

table.add(rows)
print(f'✅ {len(rows)} facts adicionados ao RAG')
for r in rows:
    print(f'  [{r[\"category\"]}] {r[\"text\"][:70]}...')
"

echo ""
echo "📊 Stats do RAG:"
python3 -c "
import os, sys
sys.path.insert(0, os.path.expanduser('~/Library/Application Support/hermes/KnowledgeBase'))
from vector_brain import get_stats
stats = get_stats()
print(f'   Total chunks: {stats[\"total_chunks\"]}')
print(f'   Categorias: {stats[\"categories\"]}')
"
