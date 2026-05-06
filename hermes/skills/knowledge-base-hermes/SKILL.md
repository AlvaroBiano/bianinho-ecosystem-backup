---
name: knowledge-base-hermes
description: Cérebro vetorial com LanceDB — pipeline completo de downloads de livros (Z-Library → sanitização → chunking → vetorização → armazenamento → consulta)
category: knowledge-base-hermes
tags: [knowledge-base, lancedb, vector-db, z-library, epub, RAG, pipeline]
---

# Cérebro Vetorial — Pipeline de Livros (Servidor Linux)
**Servidor:** `/home/alvarobiano/KnowledgeBase/`
**Banco:** `~/KnowledgeBase/knowledge_db/` (LanceDB)

> **MacBook:** O KnowledgeBase é sincronizado do servidor → MacBook via rsync a cada 4h (cron job `72ec656e69bd`).
> Script: `~/.hermes/scripts/sync_knowledge_base.sh`
> Local no MacBook: `~/Library/Application Support/hermes/KnowledgeBase/` (symlink: `~/KnowledgeBase` → acima)
> Para queries no MacBook: usa `~/.hermes/venv/bin/python` (não `~/KnowledgeBase/venv/` que é Linux symlink broken)


---

## Pipeline Detalhado
Ver: `~/KnowledgeBase/pipeline/livro_pipeline.py`

### Comandos Makefile
```bash
cd ~/KnowledgeBase && make help                                    # Mostrar todos os comandos
make install                                                  # Instalar dependências
make process file=<path> cat=<cat>                              # Processar livro
make query q=<pergunta>                                        # Consultar banco
make stats                                                    # Estatísticas
make dedup                                                    # Deduplicar banco
make setup-check                                              # Verificar ambiente
make all                                                      # Processar ~/Downloads/
```

### Comandos Diretos (Python)
```bash
# ✅ CORRECTO — usar venv python directamente (NÃO "python3", usar "python" puro)
cd ~/KnowledgeBase && ~/KnowledgeBase/venv/bin/python vector_brain.py --action process --file <path> --category <cat> --table metodoten
cd ~/KnowledgeBase && ~/KnowledgeBase/venv/bin/python vector_brain.py --action stats --table metodoten
cd ~/KnowledgeBase && ~/KnowledgeBase/venv/bin/python vector_brain.py --action query --query "pergunta" --table metodoten
```

**ATENÇÃO:** Invocar como `~/KnowledgeBase/venv/bin/python` (não `python3`). O binário do venv chama-se `python`, não `python3`.

### Estrutura do Projeto
```
KnowledgeBase/
├── knowledge_db/          # Banco LanceDB
├── pipeline/
│   ├── livro_pipeline.py # Script principal (CLI)
│   ├── setup.sh          # Instalação de dependências
│   ├── config.yaml       # Configurações
│   ├── cron_setup.sh     # Configurar tarefas cron
│   ├── scripts/
│   │   └── download.sh  # Download via Brave
│   └── logs/             # Logs de execução
├── downloads/             # Livros pendentes de processamento
├── venv/                  # Ambiente virtual Python
├── Makefile               # Comandos make
└── README.md               # Documentação

---

## Pipeline Detalhado (7 etapas)

1. **Extração** — EPUB (ebooklib), PDF (pymupdf), TXT (plain)
2. **Sanitização** — remove headers/footers, números de página, ruído
3. **Chunking** — ~1000 chars por chunk, overlap 200
4. **Validação** — remove chunks < 100 chars
5. **Dedup intra-livro** — hash de chunks duplicados
6. **Vectorização** — OpenAI text-embedding-3-small via OpenRouter
7. **Armazenamento** — LanceDB, tabela `chunks`

---

## Estratégia de Chunking

### Abordagem: janelas fixas (window-based) em vez de split por headers
**Problema:** Alguns EPUBs extraem texto que inclui tanto o sumário (TOC) quanto o conteúdo completo — sequential e indistinguível por posição. Isso faz com que patterns de headers (como "LEI X:", "Capítulo Y") captem tanto entries do sumário quanto do conteúdo real, corrompendo o chunking.

**Solução robusta:** Usar janelas fixas de ~1000 chars com overlap de 100 em vez de split por regex de headers. Essa abordagem funciona para QUALQUER livro, independentemente de ter TOC ou estrutura dual.

**Exemplo de chunking por janelas (pseudocódigo):**
```
chunk_size = 1000, overlap = 100, step = 900
for start in range(0, len(text), step):
    chunk = text[start : start + chunk_size]
    if len(chunk) > 50:  # ignorar chunks vestigiais
        yield chunk
```

### Exemplo real: "As 48 leis do poder" (Robert Greene)
- O EPUB extraía ~1.3M chars: sumário (com 48 entries "LEI X: ...") → "PREFÁCIO 2" → conteúdo completo
- Regex split por "LEI X:" capturava 96 seções (48 TOC + 48 reais) com conteúdo misturado
- A versão completa usa "LEI X" em MAIÚSCULAS + "JULGAMENTO" como marcador (ex: "LEI 1 NÃO OFUSQUE O BRILHO DO MESTRE JULGAMENTO ...")
- **Solução simples**: usar chunking por janelas fixas, ignorando headers — funcionou perfeitamente
- Resultado: 1.040 chunks limpos, sem contaminação de TOC

### "A Revolução 80/20" (Richard Koch)
- Processou sem problemas com chunking padrão de ~1000 chars
- Contraste: livro NÃO tem estrutura dual TOC/conteúdo no EPUB

**Regra prática:** Se o livro tem estrutura complexa ou conteúdo inesperado, o chunking por janelas fixas é sempre mais seguro que split por headers.

---

## Problemas Conhecidos e Soluções

### "only 81 characters extracted" / EPUB não funciona
**Causa:** O EPUB3 usa tipo 9 (DOC) para XHTML, não tipo 1 (HTML).
**Solução:** Editar `~/KnowledgeBase/vector_brain.py` linha ~539:
```python
# Antes:
if item.get_type() == 1:  # HTML/XHTML
# Depois:
if item.get_type() in (1, 9):  # HTML/XHTML + DOC/EPUB3
```

### PDF não extrai texto ("52 chars")
**Causa:** `pdfplumber` não está instalado no venv do KnowledgeBase.
**Solução:**
```bash
cd ~/KnowledgeBase && source venv/bin/activate
uv pip install pdfplumber
```

### ImportError: No module named 'ebooklib'
```bash
cd ~/KnowledgeBase && source venv/bin/activate
uv pip install ebooklib pyarrow tiktoken lancedb pdfplumber
```

### ⚠️ vectorize_and_store não persiste — table=None
`vectorize_and_store` retorna `status=success` mesmo quando `table=None`, mas **não insere nada no banco**. Os chunks existem em memória mas 0 rows são persistidas.

**Correção — passar tabela real:**
```python
from vector_brain import vectorize_and_store, get_table
import lancedb

db = lancedb.connect('knowledge_db/')
tbl = get_table(db)
result = vectorize_and_store(filepath, category, source_name, tbl)
#                                               ↑ tabela real, não None
```

**Verificação pós-inserção:**
```python
import pyarrow as pa
t = tbl.to_arrow()
mask = pa.compute.equal(t['source'], pa.scalar(source_name))
matched = t.filter(mask)
print(f"Inseridos: {matched.num_rows} rows")  # se 0 → falhou silenciosamente
```

---

## Estrutura de Diretórios
```
KnowledgeBase/
├── knowledge_db/          # Banco LanceDB
├── pipeline/
│   ├── livro_pipeline.py  # Script principal (CLI)
│   ├── config.yaml        # Configurações
│   └── logs/              # Logs do pipeline
├── downloads/             # Livros baixados (pending processing)
├── psicologia/livros/
├── marketing/livros/
└── vector_brain.py       # Motor de processamento
```

---

---

## ⚠️ CRÍTICO: Upload Telegram rejeita EPUB — workaround .zip

O Hermes (upload de ficheiros Telegram) **não suporta `.epub`**. Tipos aceites:
`.cfg, .csv, .docx, .ini, .json, .log, .md, .pdf, .pptx, .toml, .txt, .xlsx, .xml, .yaml, .yml, .zip`

**Workflow completo para processar EPUB via Telegram:**

1. Utilizador renomeia `.epub` → `.zip` e envia pelo Telegram
2. Hermes guarda em `/home/alvarobiano/.hermes/cache/documents/doc_<hash>_<nome>.zip`
3. Bianinho extrai e processa:

```bash
# Extrair ZIP EPUB
WORKDIR=~/Downloads/epub_<nome>
mkdir -p $WORKDIR
unzip -o "/home/alvarobiano/.hermes/cache/documents/doc_<hash>.zip" -d $WORKDIR > /dev/null 2>&1

# Listar conteúdo (pode ser .xhtml ou .html)
unzip -l "doc_<hash>.zip" | grep -E "xhtml|html" | head -10

# Converter para TXT (regex strip de tags XHTML/HTML)
~/.hermes/sac_agent/venv/bin/python3 << 'EOF'
import os, re, glob
workdir = os.path.expanduser("~/Downloads/epub_<nome>")
out_path = os.path.expanduser("~/Downloads/epub_txt/<nome_limpo>.txt")
os.makedirs(os.path.dirname(out_path), exist_ok=True)
xhtml_files = sorted(glob.glob(os.path.join(workdir, "OEBPS", "*.xhtml")))
# ou glob para *.html se for .html
text_parts = []
for xf in xhtml_files:
    with open(xf, "r", encoding="utf-8", errors="ignore") as f:
        content = f.read()
    clean = re.sub(r"<[^>]+>", " ", content)
    clean = re.sub(r"\s+", " ", clean).strip()
    if len(clean) > 50:
        text_parts.append(clean)
full_text = "\n\n".join(text_parts)
with open(out_path, "w", encoding="utf-8") as f:
    f.write(full_text)
print(f"Extraído: {len(full_text)//1024}KB, {len(full_text)} chars")
EOF

# Vectorizar
cd ~/KnowledgeBase && ~/KnowledgeBase/venv/bin/python3 pipeline/livro_pipeline.py \
  --file ~/Downloads/epub_txt/<nome_limpo>.txt \
  --category <categoria>
```

**Categorias disponíveis:** `psicologia`, `marketing`, `desenvolvimento_pessoal`, `matematica`, `default`

**Livrarias já processadas (28/04/2026):**
| Livro | Chunks | Categoria |
|-------|--------|-----------|
| Atomic Habits (James Clear) | 226 | desenvolvimento_pessoal |
| O Poder do Hábito (Charles Duhigg) | 236 | desenvolvimento_pessoal |
| The Body Keeps the Score | 264 | desenvolvimento_pessoal |
| Instagram Performance Marketing | 74 | marketing |
| Prompt Realism Mastery | 53 | default |
| How to Make Money with AI | 18 | default |

**Banco total (28/04/2026):** ~62.400 chunks

---

## OCR para EPUBs com Imagens (páginas escaneadas)

Alguns EPUBs (especialmente de Kindle/Amazon) têm o conteúdo como **imagens JPG** em vez de texto — o tesseract OCR é necessário para extrair.

### Setup OCR
```bash
# Tesseract já instalado: /usr/bin/tesseract
# Idiomas disponíveis: eng, por (em /usr/share/tesseract-ocr/5/tessdata/)
# Dependências Python (venv do sac_agent):
~/.hermes/sac_agent/venv/bin/pip install pytesseract Pillow --quiet
```

### Workflow OCR completo
```bash
# 1. Extrair ZIP como acima...
WORKDIR=~/Downloads/epub_<nome>
unzip -o "/home/alvarobiano/.hermes/cache/documents/doc_<hash>.zip" -d $WORKDIR > /dev/null 2>&1

# 2. Converter para TXT (XHTML limpo)
~/.hermes/sac_agent/venv/bin/python3 << 'EOF'
import os, re, glob
from PIL import Image
import pytesseract

workdir = os.path.expanduser("~/Downloads/epub_<nome>")
out_path = os.path.expanduser("~/Downloads/epub_txt/<nome_limpo>.txt")
os.makedirs(os.path.dirname(out_path), exist_ok=True)

img_dir = os.path.join(workdir, "OEBPS")
xhtml_files = sorted(glob.glob(os.path.join(img_dir, "*.xhtml")))
images = sorted(glob.glob(os.path.join(img_dir, "*.jpg")))
all_text = []

# XHTML (texto limpo, sempre primeiro)
for xf in xhtml_files:
    with open(xf, "r", encoding="utf-8", errors="ignore") as f:
        content = f.read()
    clean = re.sub(r"<[^>]+>", " ", content)
    clean = re.sub(r"\s+", " ", clean).strip()
    if len(clean) > 50:
        all_text.append(f"=== XHTML: {os.path.basename(xf)} ===\n{clean}\n")

# OCR nas imagens (PSM 11 = melhor para layout complexo)
for img_path in images:
    try:
        img = Image.open(img_path)
        text = pytesseract.image_to_string(img, lang='eng', config='--psm 11')
        text = text.strip()
        if text and len(text) > 20:
            all_text.append(f"=== OCR: {os.path.basename(img_path)} ===\n{text}\n")
    except Exception as e:
        pass

full_text = "\n".join(all_text)
with open(out_path, "w", encoding="utf-8") as f:
    f.write(full_text)
print(f"Extraído: {len(full_text)//1024}KB, {len(full_text)} chars")
EOF

# 3. Vectorizar
cd ~/KnowledgeBase && ~/KnowledgeBase/venv/bin/python3 pipeline/livro_pipeline.py \
  --file ~/Downloads/epub_txt/<nome_limpo>.txt --category <cat>
```

### Diagnóstico: livro é imagem ou texto?
```bash
# Verificar proporção de imagens vs texto no EPUB
unzip -l "/path/to/book.zip" | awk '{sum+=$1} END {print "Total bytes: " sum}'
unzip -l "/path/to/book.zip" | grep -E "\.jpg|\.png|\.jpeg" | awk '{img+=$1} END {print "Imagens: " img}'
# Se imagens > 70% do tamanho → provavelmente escaneado
```

### Limitações conhecidas
- Tesseract em imagens com layout complexo (múltiplas colunas, fontes decorativas) extrai pouco
- Livros 100% escaneados (sem texto embedding) rendem ~18-38KB extraídos vs 1-3MB de imagens
- PDF escaneado → usar `marker-pdf` ou `ocrmypdf` em vez de tesseract directo

---

## Apagar Livros do Banco LanceDB

```bash
cd ~/KnowledgeBase && ~/KnowledgeBase/venv/bin/python3 -c "
import lancedb
db = lancedb.connect('/home/alvarobiano/KnowledgeBase/knowledge_db')
tbl = db.open_table('chunks')

# Listar todos os sources
df = tbl.to_pandas()
for s in sorted(df['source'].unique()):
    cnt = len(df[df['source']==s])
    print(f'  {s}: {cnt} chunks')

# Apagar por source (duas variantes)
deleted = tbl.delete('source in (\"ficheiro.txt\", \"ficheiro_epub.txt\")')
print(f'Deletados: {deleted}')

# Verificar
df2 = tbl.to_pandas()
ai = df2[df2['source'].str.contains('ficheiro', na=False)]
print(f'Remaining: {len(ai)} chunks')
"
```

### Verificar antes de apagar
```bash
# Antes de apagar, confirmar o que vai ser removido
df = tbl.to_pandas()
to_delete = df[df['source'].isin(['ficheiro_a.txt', 'ficheiro_b.txt'])]
print(f"Vai apagar {len(to_delete)} chunks de {to_delete['source'].unique()}")
```

---

## Gerir Tabelas LanceDB — Comandos Directos

```bash
# Listar tabelas
cd ~/KnowledgeBase && ~/KnowledgeBase/venv/bin/python3 -c "
import lancedb
db = lancedb.connect('knowledge_db')
print('Tables:', db.list_tables())
"

# Schema de uma tabela
cd ~/KnowledgeBase && ~/KnowledgeBase/venv/bin/python3 -c "
import lancedb
db = lancedb.connect('knowledge_db')
tbl = db.open_table('chunks')
print('Schema:', tbl.schema)
df = tbl.to_pandas()
print(f'Total: {len(df)} chunks')
print(df['source'].value_counts().head(10))
"

# Count rows
cd ~/KnowledgeBase && ~/KnowledgeBase/venv/bin/python3 -c "
import lancedb
db = lancedb.connect('knowledge_db')
for t in ['chunks', 'metodoten', 'default']:
    try:
        tbl = db.open_table(t)
        print(f'{t}: {tbl.count_rows()} rows')
    except:
        print(f'{t}: not found')
"
```

---

## ⚠️ CRÍTICO: Duas Tabelas LanceDB e Dois vEnvs

---

## ⚠️ CRÍTICO: Duas Tabelas LanceDB e Dois vEnvs

### Tabelas LanceDB
O banco em `knowledge_db/` tem **DUAS tabelas**:

| Tabela | Conteúdo | Quem usa |
|--------|----------|----------|
| `chunks` | Livros gerais, categorias | Pipeline KnowledgeBase (livro_pipeline.py) |
| `metodoten` | Conteúdo do Método TEN, apostilas, site, manual do terapeuta | **SAC Bot** |

**ERRO COMUM:** Indexar na tabela errada. Se usar o pipeline do KnowledgeBase com `--table chunks`, vai para `chunks` — o SAC Bot NUNCA vai ver esses dados.

### vEnvs
| venv | Python | Para que serve |
|------|--------|---------------|
| `~/KnowledgeBase/venv/` | 3.14 | Pipeline de livros (livro_pipeline.py) |
| `~/.hermes/sac_agent/venv/` | 3.12 | SAC Bot, indexação manual para `metodoten` |
| `~/.hermes/sac_agent/venv/bin/python3` | 3.12 | **ÚNICO venv que persiste correctamente na `metodoten`** |

**Problema:** O venv 3.14 tem `lancedb` mas NÂO persiste correctamente na `metodoten` — os dados aparecem no query mas não sobrevivem reinício do processo SAC Bot. O venv 3.12 (sac_agent) é o correcto.

### Indexar Manual/PDF na Tabela Correcta (para o SAC Bot)

```bash
# ✅ CORRECTO — usar venv do sac_agent com openai directo
cd ~/KnowledgeBase && ~/.hermes/sac_agent/venv/bin/python3 << 'EOF'
import sys, os, time, json
import numpy as np
from datetime import datetime

# API key do auth.json
auth_path = '/home/alvarobiano/.hermes/auth.json'
with open(auth_path) as f:
    auth = json.load(f)
cp = auth['credential_pool']['openrouter']
key = next(c['access_token'] for c in cp if c.get('access_token'))

# Embedding via OpenRouter
import openai
client = openai.OpenAI(api_key=key, base_url='https://openrouter.ai/api/v1')
def embed(texts):
    r = client.embeddings.create(model='text-embedding-3-small', input=texts)
    return [x.embedding for x in r.data]

# Load chunks
with open('/tmp/manual_chunks.txt', 'r', encoding='utf-8') as f:
    content = f.read()
chunks = []
for line in content.split('\n'):
    if line.startswith('[CHUNK '):
        if chunks: chunks.append('\n'.join(chunks))
        chunks = []
    else:
        chunks.append(line)

# Connect + insert
import lancedb
db = lancedb.connect('/home/alvarobiano/KnowledgeBase/knowledge_db')
tbl = db.open_table('metodoten')
SOURCE = 'Nome da Fonte'

for i in range(0, len(chunks), 20):
    batch = [c.strip() for c in chunks[i:i+20] if len(c.strip()) > 50]
    if not batch: continue
    try:
        vecs = embed(batch)
        records = [{'text': c[:8000], 'vector': vecs[j], 'source': SOURCE,
            'category': 'metodo-ten', 'chunk_index': i+j, 'total_chunks': len(chunks),
            'filepath': 'ficheiro.pdf', 'language': 'pt',
            'processed_at': datetime.now().isoformat()} for j, c in enumerate(batch)]
        tbl.add(records)
        print(f"  Batch {i//20+1}: added, total {tbl.count_rows()}")
        time.sleep(1)
    except Exception as e:
        print(f"  ERRO batch {i//20+1}: {e}")
        time.sleep(5)

print(f"✅ Total: {tbl.count_rows()} rows")
EOF
```

### Verificar After Indexação
```bash
# ✅ Usar venv KnowledgeBase para queries (tem pandas)
cd ~/KnowledgeBase && ~/KnowledgeBase/venv/bin/python3 -c "
import lancedb, numpy as np
db = lancedb.connect('knowledge_db')
tbl = db.open_table('metodoten')
print('Total rows:', tbl.count_rows())
r = tbl.search(np.zeros(1536).tolist(), vector_column_name='vector').limit(1000).to_pandas()
print(r['source'].value_counts())
"
```

---

## Telegram Book Processing Pipeline

When user sends a PDF via Telegram and says "processe o livro":

### Step 1: Find the file
```python
import glob
matches = glob.glob('/home/alvarobiano/.hermes/cache/documents/doc_<hash>*')
# Use prefix match — file may not exist at exact reported path
src = matches[0] if matches else None
```

**⚠️ CRITICAL:** Do NOT use the exact path reported in the Telegram message. The file may not exist yet or may have encoding issues with `open()`. Always use `glob.glob()` with hash prefix first, then access via the glob result.

### Step 2: Process with vector_brain.py
```bash
~/KnowledgeBase/venv/bin/python ~/KnowledgeBase/vector_brain.py \
  --action process --file "<src_path>" --category desenvolvimento_pessoal --table metodoten
```

**Python environment:** `~/KnowledgeBase/venv/bin/python` (Python 3.14) — NOT system python3 or python3.12.

**⚠️ The file path MUST be accessed via glob result, not the raw Telegram path.** Direct `open(path)` calls fail for files with non-ASCII characters (accents, cedillas) due to encoding timing issues.

### Step 3: Report results to user
```
✅ Livro processado com sucesso!

📚 <Título>

Resultados:
- <N> caracteres extraídos
- <N> chunks armazenados no banco vetorial
- Categoria: desenvolvimento_pessoal ✓

O livro está disponível no RAG para buscas sobre <temas>.
```

### Image-based PDFs (low extraction)
If result shows <500 chars extracted and only 1 chunk:
```
⚠️ Processado com resultado limitado

📚 <Título>

Resultados:
- <N> caracteres extraídos (PDF de imagens)
- 1 chunk armazenado

Este livro tem conteúdo essencialmente em formato de imagem — não é possível extrair mais texto. Se tiver uma versão com texto digitalizado (OCR), posso processar novamente.
```

## LanceDB Schema — metodoten table
```
text: string
vector: fixed_size_list<float>[1536]
source: string
category: string
chunk_index: int32
total_chunks: int32
filepath: string
language: string
chunk_hash: string
processed_at: string
copyright: string
```

## Comandos Úteis
```bash
cd ~/KnowledgeBase && source venv/bin/activate
python3 pipeline/livro_pipeline.py --file <path> --category <cat>
python3 pipeline/livro_pipeline.py --query "<pergunta>"
python3 pipeline/livro_pipeline.py --stats
```
