---
name: knowledge-base-content-validation
description: "Debugging de conteúdo destruído pelo sanitizer no pipeline de vetorização de livros. Trigger: chunk count baixo após processamento, sanitizer.clean() remove >90% do texto."
---

# KnowledgeBase Content Validation

## Identificação

**Classe:** Debugging de conteúdo destruído pelo sanitizer no pipeline de vetorização de livros.

**Trigger:** Quando um livro processado retorna contagem de chunks inesperadamente baixa, ou quando `sanitizer.clean()` retorna muito poucos caracteres em relação ao texto original.

## Sintomas

- Livro com 190KB de texto extraído → menos de 5 chunks
- `sanitizer.clean()` remove >90% do texto
- Chunk count muito abaixo do esperado (ex: 3 chunks para um livro de 200KB)
- Livros com "Chapter X:" no conteúdo real estão a desaparecer

## Fluxo de Debug

### Passo 1 — Medir perda por etapa

```python
from vector_brain import extract_text_from_file, sanitizer, chunk_text

text, lang = extract_text_from_file(filepath)
print(f"Original: {len(text)}")

# Etapa 0: copyright
text2, cb = sanitizer._extract_copyright_block(text)
print(f"After copyright: {len(text2)} (removed {len(cb) if cb else 0})")

# Etapa 1-3: linha a linha
lines = text2.split('\n')
cleaned = [l for l in lines if not sanitizer._is_noise_line(l)]
print(f"After noise lines: {len(cleaned)}/{len(lines)}")

# Etapa final
result = sanitizer.clean(text)
chunks = chunk_text(result)
print(f"Final chunks: {len(chunks)}")
```

### Passo 2 — Identificar o culpada

**Causa 1:** NOISE_PATTERNS regex `^\s*(capítulo|chapter|seção|section)\s+\d+` mata TODAS as linhas "Chapter X:"
- **Fix:** `r'^\s*(capítulo|chapter|seção|section)\s+\d+\s*\.?\s*\d*\s*$'` (só se não houver texto real)

**Causa 2:** Estratégia 3 copyright block tem lógica invertida
- `clean_text = normalized[start_idx + len(copyright_text):]` remove ANTES do copyright
- **Fix:** `clean_text = normalized[:start_idx] + normalized[start_idx + len(copyright_text):]`

**Causa 3:** CSS/HTML residual de EPUB mal extraído
- **Fix:** ebooklib para extracção correcta

### Passo 3 — Reprocessar

```bash
# Apagar chunks
~/.hermes/sac_agent/venv/bin/python3 -c "
from vector_brain import db, get_table
t = get_table(db)
t.delete(\"source = 'nome_livro.txt'\")
"

# Reprocessar
~/KnowledgeBase/venv/bin/python3 pipeline/livro_pipeline.py --file ... --category default --force
```

## Ficheiros

- `~/KnowledgeBase/vector_brain.py` — TextSanitizer (NOISE_PATTERNS ~linha 146, copyright ~linha 327)
- `~/KnowledgeBase/pipeline/livro_pipeline.py`
- `~/.hermes/sac_agent/venv/` — venv com ebooklib

## Armadilhas

1. Módulo cacheado — usar novo processo Python após editar vector_brain.py
2. Reprocessar — o pipeline pula livros já processados; usar `--force`
3. EPUB não suportado no Hermes — renomear `.epub` → `.zip`

---

## Problema Separado: OCR Degradado (não é bug do Sanitizer)

**Sintoma:** `unique_ratio < 0.10` — muitos caracteres únicos repetidos ou inexistentes. O texto parece "AAAAA...BBBB...CCCC" com símbolos estranhos. O TextSanitizer NÃO é o culpado — o livro **chegou assim**.

**Verificação rápida:**
```python
~/KnowledgeBase/venv/bin/python3 -c "
import sys
sys.path.insert(0, '/home/alvarobiano/KnowledgeBase')
import lancedb

db = lancedb.connect('/home/alvarobiano/KnowledgeBase/knowledge_db')
tbl = db.open_table('chunks')
df = tbl.to_pandas()

quality = []
for source, grp in df.groupby('source'):
    sample = ' '.join(grp['text'].head(5).tolist())
    total = len(sample)
    unique = len(set(sample))
    ratio = unique / max(total, 1)
    quality.append({'source': source, 'ratio': round(ratio, 3), 'chunks': len(grp)})

import pandas as pd
qdf = pd.DataFrame(quality).sort_values('ratio')
print(qdf[qdf['ratio'] < 0.10].to_string(index=False))
"
```

**Resultado:**
```
unique_ratio < 0.10 → livro com OCR degradado
unique_ratio > 0.15 → livro com texto legível
```

**Livros afectados (28/04/2026):**
| source | ratio | chunks | estado |
|--------|-------|--------|--------|
| atomic_habits.epub | 0.006 | 1267 | 🔴 OCR degradado |
| Dark_Psychology.txt | 0.006 | 396 | 🔴 OCR degradado |
| o_poder_do_habito.epub | 0.060 | 552 | 🔴 OCR degradado |
| as_48_leis_do_poder.epub | 0.089 | 1040 | 🟡 Parcial |
| Multi-Agent_Coordination | 0.076 | 22815 | 🔴 OCR degradado |
| AI_Prompt_Engineering_Bible | 0.095 | 9925 | 🔴 OCR degradado |

**O que fazer com OCR degradado:**
1. **Não tentar limpar com o TextSanitizer** — o sanitizer não consegue recuperar texto corrompido
2. **Tentar obter versão diferente do livro** — buscar PDF digital ou EPUB de outra fonte
3. **Se for o único exemplar disponível**, manter no banco mas com consciência de que as respostas do RAG vão ser ruins

**O TextSanitizer limpa ruído residual** (caracteres de controlo, números de página,版权), mas **não recupera texto que foi destruído pelo OCR**.
