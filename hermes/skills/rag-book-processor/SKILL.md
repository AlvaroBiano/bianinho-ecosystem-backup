---
name: rag-book-processor
description: Pipeline completo de processamento de livros para o RAG LanceDB — extracção, higienização, chunking, vectorização, categorização e armazenamento. Sistema em ~/KnowledgeBase/.
triggers:
  - usuário envia arquivo epub pdf zip
  - usuário diz "processar livro"
  - vectorizar livro para RAG
  - Bianinho processa livro automaticamente
  - banco RAG livro novo
related_skills:
  - rag-query            # consulta proativa do RAG
  - pesquisa-automatica-rag  # busca automática em todas as conversas
---

# RAG Book Processor — Bianinho
**Versão: 2.6 — 01/05/2026**

**Changelog 2.6:**
- EPUB: Calibre (`ebook-convert`) como primeira opção. Se não instalado, extracção Python manual via OPF spine (NÃO `sorted(os.listdir)` — ignora ordem de leitura)
- Regra EPUB: nunca perguntar, converter e processar automaticamente
- Bug 20: `filepath.stat()` crasha pipeline — copiar para `/tmp/` e passar caminho `/tmp/` ao `--file`
- Quando o Álvaro estranhar o título de um livro processado, explicar que vem do metadata interno do EPUB (campo `<dc:title>` no OPF) — não é inventado

**Changelog 2.5:**
- Workflow Telegram Document adicionado — fluxo completo para processar livros enviados via Telegram
- `metodoten` table como target padrão para livros do Método TEN
- `rag-query` skill adicionado como related_skill

**Changelog 2.4:**
- Bug 16: `python3` no Hermes = Python 3.14 sem pdfminer/lancedb — usar sempre `~/KnowledgeBase/venv/bin/python` para LanceDB e `python3.12` para pdfminer directo
- Bug 17: Ficheiro existe no `ls` mas Python não abre — Unicode normalization (NFC vs NFD) com caracteres especiais. Usar `glob.glob()` com hash doc_ como âncora, nunca o caminho literal com acentos.
- Bug 18: `db.list_tables()` devolve pydantic model com atributo `.tables` — não itera directamente
- Bug 19: `scripts/_archive/process_book.py` tem schema incompatível com LanceDB (campo `id` vs `vector`). NUNCA usar para inserção — usar `~/KnowledgeBase/vector_brain.py`

---

## ⚡ Quick Reference: Telegram Document → RAG
## ⚡ Quick Reference: Telegram Document → RAG

**When user sends a PDF or EPUB via Telegram and says "processe o livro":**

```bash
# 1. Encontrar o ficheiro (sempre glob — caracteres especiais podem falhar)
python3.12 -c "
import glob
matches = glob.glob('/home/alvarobiano/.hermes/cache/documents/doc_<hash>*')
print('Matches:', matches)
"

# 2. Se EPUB (verificar com: unzip -l <file> | grep -E 'mimetype|OEBPS|META-INF'):
#    OPÇÃO A — Calibre (preferido):
#    ebook-convert /tmp/book.epub /tmp/book.pdf 2>&1 | tail -3
#    cd ~/KnowledgeBase && ./venv/bin/python pipeline/livro_pipeline.py \
#      --file "/tmp/book.pdf" --category <cat> --force
#
#    OPÇÃO B — Extracção Python para TXT (se Calibre não instalado):
#    python3 ~/KnowledgeBase/scripts/extract_epub.py /tmp/book.epub /tmp/book.txt
#    cd ~/KnowledgeBase && ./venv/bin/python pipeline/livro_pipeline.py \
#      --file "/tmp/book.txt" --category <cat> --force
#
#    Se PDF:
#    Copiar para /tmp/ e processar directamente

# 3. VERIFICAÇÃO OBRIGATÓRIA — confirmar chunks no banco
~/KnowledgeBase/venv/bin/python -c "
import lancedb
db = lancedb.connect('/home/alvarobiano/KnowledgeBase/knowledge_db')
df = db.open_table('chunks').to_pandas()
found = df[df['source'].str.contains('book_name', na=False)]
print(f'Chunks: {len(found)}')
"
```

**⚠️ CRITICAL:** Never use the Telegram path directly. Always copy to `/tmp/` first. For EPUB: Calibre first, Python extraction if unavailable.

**Report format:**
- Success (>10 chunks): ✅ Livro processado com sucesso! + char count + chunk count + category
- Image PDF (<500 chars, 1 chunk): ⚠️ Processado com resultado limitado + aviso de PDF de imagens
- EPUB: inform always o título extraído do metadata para o Álvaro confirmar

---

**Pipeline correcto (sempre):**
```bash
cd ~/KnowledgeBase && ~/venv/bin/python vector_brain.py \
  --action process --file "/tmp/book.pdf" --category <cat> --table metodoten
```
- **NÃO** usar `scripts/_archive/process_book.py` para LanceDB (schema incompatível)
- **SEMPRE** usar `~/KnowledgeBase/venv/bin/python` (Python 3.14 do venv com lancedb)
- Target padrão: `--table metodoten` (conteúdo do Método TEN / desenvolvimento pessoal)

**Changelog 2.3:**
- PASSO 0 de pré-verificação adicionado ao workflow: MD5 check, EPUB-ZIP detection, size check
- `references/epub-zip-workaround.md` adicionado: fluxo completo para EPUB disfarçado de ZIP (padrão Captivate)

**Changelog 2.2:****
- Bug 12: Telegram "document too large" — limite 20 MB + workaround
- Bug 13: find -name com caracteres especiais falha
- Bug 14: Threshold borderline — 10% vai para default (floating point)
- Bug 11 (renamed from previous): Duplicate detection via MD5

**Changelog 2.1:**
- Bug 8: Pipeline pode reportar SUCCESS sem inserir (verificação obrigatória)
- Bug 9: `to_arrow()` não existe — usar `pa.Table.from_pandas()`
- Bug 10: ZIP pode ser EPUB estruturalmente (extração manual necessária)
- Padrão inline de recategorização documentado
- Detecção de duplicados via MD5

Pipeline de processamento completo de livros para o banco vetorial LanceDB. Tudo o que precisas de saber para operar, debugar e manter o sistema.

---

## Arquitectura do Sistema

```
FICHEIRO (ZIP|PDF|EPUB|TXT)
    │
    ▼
┌──────────────────────────────────────────┐
│  1. EXTRAÇÃO DE TEXTO                  │
│  extract_text_from_file()                │
│  · PyMuPDF (fitz)  → PDF              │
│  · ebooklib         → EPUB             │
│  · Encoding fallback → TXT              │
└────────────────────┬───────────────────┘
                     ▼
┌──────────────────────────────────────────┐
│  2. HIGIENIZAÇÃO (TextSanitizer)        │
│  clean() — 8 etapas                     │
│  · Copyright block (extracção)          │
│  · Control chars, ruído, whitespace    │
│  · Pontuação normalizada                │
└────────────────────┬───────────────────┘
                     ▼
┌──────────────────────────────────────────┐
│  3. CHUNKING                             │
│  chunk_text()                            │
│  · tiktoken cl100k_base (512 tokens)   │
│  · 64 tokens overlap                    │
│  · Validação por chunk                  │
└────────────────────┬───────────────────┘
                     ▼
┌──────────────────────────────────────────┐
│  4. DEDUPLICAÇÃO                        │
│  compute_chunk_hash() → MD5 normalizado  │
│  · Intra-livro                          │
│  · Campo chunk_hash no banco             │
└────────────────────┬───────────────────┘
                     ▼
┌──────────────────────────────────────────┐
│  5. VECTORIZAÇÃO                         │
│  OpenAIEmbeddingsWrapper                 │
│  · text-embedding-3-small (1536 dims)   │
│  · OpenRouter proxy                      │
│  · Batch size 100                       │
└────────────────────┬───────────────────┘
                     ▼
┌──────────────────────────────────────────┐
│  6. ARMAZENAMENTO (LanceDB)             │
│  Tabela única "chunks"                   │
│  · 10 campos por registro               │
│  · Full-text search                      │
└──────────────────────────────────────────┘
```

---

## Componentes do Sistema

### Ficheiros Principais

| Ficheiro | Papel |
|----------|-------|
| `~/KnowledgeBase/vector_brain.py` | Motor: extracção, sanitização, chunking, vectorização |
| `~/KnowledgeBase/pipeline/livro_pipeline.py` | CLI e pipeline de orquestração |
| `~/KnowledgeBase/knowledge_db/` | Directório do banco LanceDB (tabelas: `api`, `chunks`, `default`, `metodoten`, `prd_collection`) |
| `~/.hermes/cache/documents/` | Onde Telegram guarda ficheiros recebidos |
| **`~/KnowledgeBase/venv/bin/python3`** | **Python interpreter — SEMPRE usar este** |

### Tabela LanceDB — Schema

```
Campo          Tipo               Descrição
────────────────────────────────────────────────────────────────
vector         list[float32]     Embedding 1536-dim (text-embedding-3-small)
text           string             Texto do chunk já limpo
source         string             Nome do ficheiro origem
category       string             Categoria: ia|psicologia|marketing|etc
chunk_index    int32              Posição do chunk neste livro
total_chunks  int32              Total de chunks do livro
filepath       string             Caminho completo do ficheiro
language       string             Idioma ("pt")
chunk_hash     string             MD5 normalizado do chunk (dedup)
processed_at   string             ISO timestamp
```

**Tabelas existentes:** `chunks` (principal, 70k+ chunks), `metodoten` (6k+ chunks, usa schema idêntico + campo extra `copyright`), `api`, `default`, `prd_collection`. Livros processados pelo pipeline `vector_brain.py` vão para a tabela especificada por `--table` (default: `chunks`). A tabela `metodoten` é populada separadamente (mesmo schema mas sem o campo `copyright`).

---

## Formatos de Ficheiro — Como Processar

### `.zip` — EPUB disfarçado (renomeado pelo utilizador)

**REGRA CRÍTICA (01/05/2026 — Álvaro):** **NUNCA renomear o ficheiro.** EPUB que chega como `.zip` deve ser extraído e convertido para `.txt` (não para `.epub`). O pipeline processa `.txt` — esse é o formato intermediário.

**Detecção:** `unzip -l <file.zip> | head` — se contiver `OEBPS/`, `mimetype`, `META-INF/` → é EPUB.

**Fluxo completo:**

```bash
# 1. Copiar via bytes (evita Unicode normalization no caminho)
python3 -c "
import glob
src = glob.glob('/home/alvarobiano/.hermes/cache/documents/doc_<hash>*')[0]
with open(src, 'rb') as f:
    data = f.read()
with open('/tmp/book_name.epub', 'wb') as f:
    f.write(data)
"

# 2. Extrair texto do EPUB para TXT
python3 << 'PYEOF'
import zipfile, re, os, xml.etree.ElementTree as ET

epub_path = '/tmp/book_name.epub'
txt_path = '/tmp/book_name.txt'

ns = {'opf': 'http://www.idpf.org/2007/opf', 'dc': 'http://purl.org/dc/elements/1.1/'}
with zipfile.ZipFile(epub_path, 'r') as z:
    opf_files = [f for f in z.namelist() if f.endswith('.opf')]
    opf_path = opf_files[0]
    opf_dir = os.path.dirname(opf_path)
    opf_root = ET.fromstring(z.read(opf_path))
    
    title = opf_root.find('.//dc:title', ns)
    title_text = title.text if title is not None else 'Unknown'
    
    manifest = opf_root.find('opf:manifest', ns)
    spine = opf_root.find('opf:spine', ns)
    item_by_id = {}
    for item in manifest.findall('opf:item', ns):
        item_id = item.get('id'); href = item.get('href'); mt = item.get('media-type')
        if href: item_by_id[item_id] = (href, mt)
    
    reading_order = []
    if spine is not None:
        for ir in spine.findall('opf:itemref', ns):
            idref = ir.get('idref')
            if idref in item_by_id: reading_order.append(item_by_id[idref])
    
    all_text = []
    for href, mt in reading_order:
        if 'html' in (mt or '') or 'xhtml' in (mt or ''):
            fp = os.path.join(opf_dir, href).lstrip('/')
            try:
                root = ET.fromstring(z.read(fp))
                def extract_text(elem):
                    texts = []
                    if elem.text: texts.append(elem.text.strip())
                    for ch in elem:
                        texts.extend(extract_text(ch))
                        if ch.tail: texts.append(ch.tail.strip())
                    return [t for t in texts if t]
                texts = extract_text(root)
                if texts: all_text.append('\n'.join(texts))
            except: continue
    
    result = f'TÍTULO: {title_text}\n\n' + '\n\n'.join(all_text)
    with open(txt_path, 'w', encoding='utf-8') as f:
        f.write(result)
    print(f'Título: {title_text}')
    print(f'Arquivos: {len(reading_order)}, Texto: {len(result)} chars')
PYEOF

# 3. Processar como TXT
cd ~/KnowledgeBase && ./venv/bin/python pipeline/livro_pipeline.py \
  --file "/tmp/book_name.txt" --category <cat> --force
```

**⚠️ ERRO CRÍTICO A EVITAR:** Nunca usar `sorted(os.listdir())` para extrair capítulos — isso ignora a ordem de leitura do livro. Muitos EPUBs têm capítulos fora de ordem alfabética. **Usar SEMPRE o OPF spine** como faz o script acima.

**Caso especial — Capítulos em XHTML separados (padrão Captivate/Vanessa Van Edwards):**
Quando `OEBPS/xhtml/` existe com múltiplos `.xhtml` files, o pipeline não processa diretamente.
Extrair e concatenar manualmente:
### Passo 4 — Extrair texto dos XHTML pela ordem do spine (CORRETO)

⚠️ **Erro comum:** Usar `sorted(os.listdir())` — ordem alfabética ignora a ordem de leitura do livro. Muitos EPUBs têm capítulos fora de ordem alfabética (ex: "Chapter 10" antes de "Chapter 2"). **Usar sempre o OPF spine.**

```python
import zipfile, xml.etree.ElementTree as ET, re, os

epub_path = "/tmp/book.epub"          # INPUT: EPUB original
txt_path  = "/tmp/book_name.txt"       # OUTPUT: TXT combinado

ns = {'opf': 'http://www.idpf.org/2007/opf',
      'dc':  'http://purl.org/dc/elements/1.1/'}

with zipfile.ZipFile(epub_path, 'r') as z:
    # 1. Achar o OPF (tabela de contents)
    opf_files = [f for f in z.namelist() if f.endswith('.opf')]
    opf_path  = opf_files[0]
    opf_dir   = os.path.dirname(opf_path)

    opf_root = ET.fromstring(z.read(opf_path))

    # 2. Construir mapa id → (href, media_type)
    manifest = opf_root.find('opf:manifest', ns)
    item_by_id = {item.get('id'): (item.get('href'), item.get('media-type'))
                  for item in manifest.findall('opf:item', ns)
                  if item.get('href')}

    # 3. Ler spine na ordem correcta
    spine      = opf_root.find('opf:spine', ns)
    reading_order = [item_by_id[itemref.get('idref')]
                     for itemref in spine.findall('opf:itemref', ns)
                     if itemref.get('idref') in item_by_id]

    # 4. Extrair texto de cada capítulo XHTML
    all_text = []
    for href, media_type in reading_order:
        if 'xhtml' in (media_type or ''):
            full = os.path.join(opf_dir, href).lstrip('/')
            try:
                root = ET.fromstring(z.read(full))
            except ET.ParseError:          # mal-formed XML → envolver
                try:
                    root = ET.fromstring(z.read(full) + b'</html>')
                except:
                    continue

            def extract_text(elem):
                t = []
                if elem.text: t.append(elem.text.strip())
                for ch in elem:
                    t.extend(extract_text(ch))
                    if ch.tail: t.append(ch.tail.strip())
                return [x for x in t if x]

            texts = extract_text(root)
            if texts:
                all_text.append('\n'.join(texts))

    # 5. Guardar TXT — primeiro chunk pode ter prefixo TÍTULO: do EPUB metadata
    #    Remover após processamento se necessário (verificar primeiro chunk no banco)
    result = '\n\n'.join(all_text)
    with open(txt_path, 'w', encoding='utf-8') as f:
        f.write(result)

    print(f"OK: {len(result):,} chars de {len(reading_order)} capítulos")
```

**Exemplo real:** `Como_Ouvir_As_Criancas_E_Responder.epub` (184.859 chars, 84 capítulos, 119 chunks). Execute antes de copiar para `/tmp/`:
```bash
cp "/home/alvarobiano/.hermes/cache/documents/doc_e336d6a9ff93_Como_Ouvir_As_Criancas_E_Responder.epub.zip" \
   /tmp/book.epub
```

## ⚠️ Pitfall: Prefixo "TÍTULO:" no primeiro chunk

O pipeline EPUB→TXT extrai o OPF metadata e pode concatenar o título do livro no início do primeiro chunk como `TÍTULO: Nome do Livro Cover`. Isso polui o embedding.

**Como detectar:**
```python
df[df['source'].str.contains('nome_livro')]['text'].iloc[0][:50]
# → 'TÍTULO: Nome do Livro Cover ...'  ← problema
```

**Como corrigir** (inline, sem reprocessar):
```python
import lancedb, pyarrow as pa
db = lancedb.connect('/home/alvarobiano/KnowledgeBase/knowledge_db')
tbl = db.open_table('chunks')
df = tbl.to_pandas()
mask = df['source'] == 'nome_livro.txt'
texts = df.loc[mask, 'text'].tolist()
for i, t in enumerate(texts):
    if t.startswith('TÍTULO:') or t.startswith('TITULO:'):
        # encontrar segundo parágrafo real
        parts = t.split('\n\n', 2)
        if len(parts) >= 2:
            texts[i] = parts[1] if len(parts[1].strip()) > 50 else parts[2] if len(parts) > 2 else t
        break
df.loc[mask, 'text'] = texts
tbl.delete("source = 'nome_livro.txt'")
tbl.add(pa.Table.from_pandas(df[mask]))
```

**Prevenir** (futuro): O pipeline deveria detectar e skipar o bloco `TÍTULO:` na extração. Por agora, corrigir manualmente após inserção.
# 4. Processar como TXT
# cd ~/KnowledgeBase && ./venv/bin/python pipeline/livro_pipeline.py \
#   --file "/tmp/book_name.txt" --category auto --force
```

**Estruturas EPUB comuns:**
**Estruturas EPUB comuns:**
- `OEBPS/xhtml/` — capítulos XHTML separados (ex: Captivate)
- `OEBPS/content.xhtml` — capítulos em ficheiros separados
- `OEBPS/part0001.html` — partes numeradas
- `text/` — estrutura alternativa

### `.pdf` — Processamento directo

```bash
cd ~/KnowledgeBase && ./venv/bin/python pipeline/livro_pipeline.py \
  --file "<path.pdf>" --category auto
```

Usa **PyMuPDF (fitz)**. Preserva espacinhos em encoding não-padrão (superior a pdfplumber).

**Heurísticas PDF (in-build em `extract_pdf`):**
- Inserção de `[FIM-PAGINA]` entre páginas (evita concatenação sem delimitação)
- Remoção de números de página isolados: `re.match(r'^\[\[\]\d\s\.\-]+$')`
-上下文 `[pagina N/M]`注入livros > 5 páginas

### `.epub` — Direct (via ebooklib)

```bash
cd ~/KnowledgeBase && ./venv/bin/python pipeline/livro_pipeline.py \
  --file "<path.epub>" --category auto
```

Ebooklib extrai items tipo 1 (HTML) e 9 (XHTML). Remove: `<script>`, `<style>`, entidades HTML.

### `.txt` — Plain text

```bash
cd ~/KnowledgeBase && ./venv/bin/python pipeline/livro_pipeline.py \
  --file "<path.txt>" --category auto
```

Fallback de encoding: `utf-8 → latin-1 → cp1252 → iso-8859-1`.

---

## Sistema de Higienização — TextSanitizer

O `TextSanitizer` em `vector_brain.py` é a camada de limpeza crítica. Funciona em **8 etapas** antes do chunking.

### clean() — 8 Etapas

```
Etapa 0: _extract_copyright_block()    EXTRAI copyright legal (preserva conteúdo)
Etapa 1: remove control chars           \x00-\x08, \x0b, \x0c, \x0e-\x1f, \x7f-\x9f
Etapa 2: normaliza \n{3,} → \n\n     Remove quebras de linha excessivas
Etapa 3: _is_noise_line() por linha    Filtra ruído linha a linha
Etapa 4: normaliza whitespace         \s+ → espaço
Etapa 5: trim()                        Remove espaços início/fim
Etapa 6: _normalize_punctuation()       Normaliza aspas, travessões, pontuação
Etapa 7: remove linhas < 3 chars       Limpeza final de fragmentos
Etapa 8: replace('"','"'), etc.       Aspas tipográficas → ASCII
```

### NOISE_PATTERNS — O que é Removido por Linha

Compilados num único regex `IGNORECASE | MULTILINE` e aplicados linha a linha:

| # | Padrão Regex | Remove | NÃO Remove |
|---|-------------|--------|-----------|
| 1 | `^\[\s*\d+\s*\]$` | `[123]` | `[1] See page 5` |
| 2 | `^\d+\.\s*\d+\s*$` | `123. 456` | |
| 3 | `^—\s*\d+\s*—$` | `— 123 —` | |
| 4 | `^\|\s*\d+\s*\|$` | `\| 123 \|` | |
| 5 | `^\s*\d{1,4}\s*$` | `123` | |
| 6 | `^[-_=]{10,}\s*$` | `____________` | |
| 7 | `^\*+\s*$` | `***` | |
| 8 | `^(capítulo\|chapter\|seção\|section)\s+\d+\s*\.?\s*\d*\s*$` | `Chapter 1` | `Chapter 1: Title` |
| 9 | `^(continua\|continued\|to be continued)` | `continued` | |
| 10 | `^\s*©\s*\d{4}` | `© 2024` | |
| 11 | `^\s*todos\s+os\s+direitos\s+reservados` | `Todos os direitos reservados` | |
| 12 | `^\s*publisher\s+information` | `Publisher information` | |
| 13 | `^\s*isbn\s*[\d\-]+` | `isbn 978-3-16` | |
| 14 | `^\s*generated\s+by\s+\w+` | `Generated by calibre` | |
| 15 | `^\s*http[s]?://\S+` | `http://example.com` | |

### _is_noise_line() — Lógica Completa

```python
def _is_noise_line(line):
    if not stripped: return True               # linha vazia
    if len(stripped) < 3: return True         # < 3 chars
    if noise_re.match(stripped): return True   # matches NOISE_PATTERNS
    if header_footer_re.match(stripped): return True
    if re.match(r'^[\d\s\.\,\-\:\;]+$'): return True  # só números/pontuação
    if numbers_ratio > 0.5 and len < 20: return True  # curto + >50% números
    return False
```

### _extract_copyright_block() — 3 Estratégias

Chamada **ANTES** de qualquer processamento. Detecta e extrai o bloco legal para não poluir os chunks.

```
Input: "TODOS OS DIREITOS RESERVADOS...SEM PERMISSÃO POR ESCRITO\n\nCapítulo 1..."

Estratégia 1 — Lei 9.610/98 (Brasil):
  → Remove de "TODOS OS DIREITOS RESERVADOS" até "SEM PERMISSÃO POR ESCRITO"
  → Mantém tudo antes + tudo depois do bloco

Estratégia 2 — Marcadores GRUPO BRAGA / BIANO:
  → Padrão: r'(?:GRUPO\s+BRAGA|BIANO|IDEALIZADORES)[\s\.](?:DESTE| deste)'
  → Remove até ao marcador

Estratégia 3 — Copyright curto (fallback):
  → r'[^.]+\.' — primeira frase completa
  → Mantém texto ANTES + texto DEPOIS do copyright
```

**Padrões de copyright capturados:**
```
TODOS OS DIREITOS RESERVADOS E PROTEGIDOS PELA LEI 9.610 DE 19/02/1998...SEM PERMISSÃO POR ESCRITO
Copyright © 2024 ... reservados (até ~200 chars)
```

O bloco copyright é **extraído** (não apagado) — o texto real do livro é preservado.

### COMMON_HEADER_FOOTER — Headers/Footers comuns

```
^\s*editorial\s+\w+       → "editorial Planeta"
^\s*publicado\s+por       → "Publicado por Editora"
^\s*impresso\s+por         → "Impresso por Gráfica"
^\s*edição\s+\d+          → "Edição 3"
```

### is_valid_chunk() — Validação Final

Após o chunking, cada chunk é validado e **descartado** se:

```
· < 50 caracteres
· < 10 palavras
· > 30% números (provável página/número)
· Casa com FORBIDDEN_PATTERNS (notas, figuras, páginas)
· Caixa alta inteira E > 10 chars (provável header)
· < 100 chars E < 20% caracteres únicos (repetitivo)
```

### _normalize_punctuation() — Regras

```
Espaços antes de pontuação:   "foo ." → "foo."
Espaços depois de pontuação:   "foo. Bar" → "foo. Bar"
Consecutivos pontos:           "foo.." → "foo."
Consecutivos espaços:          "foo  bar" → "foo bar"
Aspas tipográficas:              " ' → ASCII
Travessões:                    – — → -
Reticências:                   ... → …
```

---

## Chunking

```python
CHUNK_SIZE = 512     tokens por chunk
CHUNK_OVERLAP = 64   tokens de sobreposição entre chunks
```

- Usa `tiktoken` encoding `cl100k_base` (mesmo do modelo de embeddings)
- Fallback: split por palavras se tiktoken falhar
- Cada chunk passa por `sanitizer.clean()` antes de ser aceite
- Deslocamento: `start += 512 - 64 = 448` tokens (overlap preserva contexto entre chunks)

---

## Deduplicação

```python
compute_chunk_hash(chunk)
  → Normaliza: chunk.lower().strip()
  → MD5 hexadecimal
  → Usado em: dedup intra-livro + campo chunk_hash no banco
```

`SEEN_CHUNKS` global é resetado entre livros diferentes (para permitir chunks iguais em livros diferentes).

---

## Vectorização

```
Modelo:       text-embedding-3-small (OpenAI)
Dimensões:    1536
Provider:     OpenRouter (proxy API)
Endpoint:     https://openrouter.ai/api/v1/embeddings
Batch size:   100 chunks por request HTTP
Timeout:      60 segundos
Token count:  tiktoken cl100k_base (fallback: len/4)
```

Erro de batch: preenche vectors com zeros `[0.0]*1536` e continua.

---

## Sistema de Categorização

### 8 Categorias + default

| Categoria | Livros | Keywords (amostra) |
|-----------|--------|--------------------|
| `inteligencia_artificial` | 15 | llm, gpt, rag, agentic, neural network, embedding... |
| `marketing` | 9 | marketing, funnel, copywriting, roi, seo... |
| `metodo-ten` | 1 | método ten, terapia emocional, Álvaro Braga... |
| `desenvolvimento_pessoal` | 3 | habit, productivity, mindset, atomic habits... |
| `psicologia` | 3 | trauma, attachment, therapy, freud, depression... |
| `comunicacao` | 3 | negotiation, persuasion, cialdini, dark psychology... |
| `financas` | 0 | investing, buffett, compound, index fund... |
| `default` | 2 | sem categoria detectável |

### classify_by_content() — Algoritmo

```
1. Extrai os primeiros 30.000 caracteres do ficheiro
2. Para cada categoria (excepto default e metodo_ten):
   → Conta keywords únicas encontradas (case-insensitive)
   → Calcula % = encontrados / total de keywords
3. Escolhe categoria com maior % (empate: contagem absoluta)
4. Se melhor % >= 10% → usa essa categoria
   Se melhor % < 10% → "default"
5. Log: "Categoria detectada: 'inteligencia_artificial' (12/67 = 18%)"
```

**Gatilho:** `--category auto` (default no CLI).

---

## Comandos — Referência Completa

```bash
# Processar ficheiro (auto-detecta categoria)
cd ~/KnowledgeBase && ./venv/bin/python pipeline/livro_pipeline.py \
  --file "<path>" --category auto

# Reprocessar (remove versões antigas primeiro)
cd ~/KnowledgeBase && ./venv/bin/python pipeline/livro_pipeline.py \
  --file "<path>" --category auto --force

# Processar pasta com vários livros
cd ~/KnowledgeBase && ./venv/bin/python pipeline/livro_pipeline.py \
  --folder ~/Downloads/livros --category auto

# Ver estatísticas do banco
cd ~/KnowledgeBase && ./venv/bin/python pipeline/livro_pipeline.py --stats

# Consultar o RAG
cd ~/KnowledgeBase && ./venv/bin/python pipeline/livro_pipeline.py \
  --query "Como formar bons hábitos?" --top-k 5

# Deduplicar banco (remove chunks duplicados)
cd ~/KnowledgeBase && ./venv/bin/python pipeline/livro_pipeline.py --dedup

# Verificar ambiente
cd ~/KnowledgeBase && ./venv/bin/python pipeline/livro_pipeline.py --setup-check
```

---

## Bugs Críticos — Histórico Completo

### Bug 8: Pipeline reporta sucesso mas chunks não aparecem no banco (FALSO POSITIVE)
**Detectado:** 30/04/2026
**Sintoma:** Pipeline loga "✅ SUCESSO" e "X registros inseridos no banco" mas os chunks NÃO existem na tabela LanceDB. Bianinho só descobre ao verificar manualmente.
**Causa:** Desconhecida — pode ser race condition ou falha silenciosa na escrita.
**Fix:** **SEMPRE usar `--force`** ao processar. O `--force` remove versões antigas antes de inserir, garantindo reescrita completa.
**Verificação:** Após processar, confirmar no banco:
```python
import sys; sys.path.insert(0, '/home/alvarobiano/KnowledgeBase')
import lancedb
db = lancedb.connect('/home/alvarobiano/KnowledgeBase/knowledge_db')
df = db.open_table('chunks').to_pandas()
found = df[df['source'].str.contains('nome_livro', na=False)]
print(f"{len(found)} chunks encontrados")
```
Se 0 chunks → o livro não foi inserido. Reprocessar com `--force`.

### Bug 9: Arquivos duplicados com nomes diferentes (mesmo conteúdo)
**Detectado:** 30/04/2026
**Sintoma:** Dois livros com nomes diferentes têm EXACTAMENTE o mesmo conteúdo (mesmo MD5, mesmo char count).
**Exemplos confirmados:**
- `Emagrecer é Psicológico - Monica Sguerri.pdf` (600346 bytes, 99500 chars) = `Como Emagrecer Rápido Acelerando.pdf` (mesmo MD5)
- `As Plantas Curam - A. Balbach.pdf` (18297686 bytes, 498042 chars) = `Cura - Jo Marchant.pdf` (mesmo MD5)
**Prevenção:** Verificar MD5 antes de processar. Se MD5 já existe no banco, skip.
**Fix:** Antes de processar, verificar se arquivo já foi processado via hash do ficheiro. Para livros novos, processar. Para duplicados, apenas Skips.

### Bug 10: ZIP não é reconhecido como EPUB disfarçado pelo pipeline
**Detectado:** 30/04/2026
**Sintoma:** `livro_pipeline.py --file "livro.zip"` retorna `❌ Formato não suportado: .zip`
**Causa:** O pipeline só aceita PDF, EPUB, TXT, ZIP — mas o handling de ZIP tenta extrair como se fosse raw ZIP e não encontra a estrutura EPUB interna.
**Fix:** Não passar ZIP diretamente. Extrair primeiro e processar como TXT:
```bash
mkdir -p /tmp/book_extract
unzip -o "livro.zip" -d /tmp/book_extract/
# Identificar estrutura (OEBPS/xhtml/ ou text/)
cd ~/KnowledgeBase && ./venv/bin/python - <<'EOF'
import re, os
texts = []
base = '/tmp/book_extract/OEBPS/xhtml'  # ou /text/
for fname in sorted(os.listdir(base)):
    if fname.endswith('.xhtml') or fname.endswith('.html'):
        with open(f'{base}/{fname}') as f: content = f.read()
        text = re.sub(r'<[^>]+>', ' ', content)
        text = re.sub(r'\s+', ' ', text).strip()
        if len(text) > 50: texts.append(text)
combined = '\n\n'.join(texts)
with open('/tmp/book_name.txt','w') as f: f.write(combined)
EOF
cd ~/KnowledgeBase && ./venv/bin/python pipeline/livro_pipeline.py --file "/tmp/book_name.txt" --category auto
```

### Bug 1: NOISE_PATTERN a apagar livro inteiro
**Detectado:** 28/04/2026  
**Sintoma:** "How to Make Money with AI" extraiu 191.600 chars mas só 3 chunks.  
**Causa:** Padrão `^(capítulo|chapter|seção)\s+\d+\s*$` casava com TODAS as linhas "Chapter X:" incluindo as do corpo do livro.  
**Fix:** Padrão corrigido em `vector_brain.py` ~linha 162 — agora só casa com linhas puras de chapter number.  
**Verificação:**
```python
from vector_brain import TextSanitizer
s = TextSanitizer()
assert s._is_noise_line("Chapter 1") == True   # noise
assert s._is_noise_line("Chapter 1: Title") == False  # real content
```

### Bug 2: Estratégia 3 copyright apagava texto após copyright
**Detectado:** 28/04/2026  
**Sintoma:** Texto depois do copyright desaparecia.  
**Causa:** `normalized[:start_idx] + normalized[start_idx + len(copyright_text):]` não incluía o texto `after_start[len:]`.  
**Fix:** `vector_brain.py` ~linha 333 — ver comentário "bug fix".  
**Verificação:**
```python
s = TextSanitizer()
clean, cp = s._extract_copyright_block("Livro real. Copyright © 2024 Reservados. Mais livro.")
assert "Livro real" in clean
assert "Mais livro" in clean
```

### Bug 3: extract_txt não definido no classify_by_content
**Detectado:** 28/04/2026  
**Sintoma:** "Falha na detecção automática: name 'extract_txt' is not defined" — TXT sempre ia para `default`.  
**Causa:** `extract_txt` não estava importado no scope de `classify_by_content`.  
**Fix:** `from vector_brain import extract_epub, extract_pdf, extract_txt` no topo de `livro_pipeline.py`.  
**Verificação:** `python3 -c "from vector_brain import extract_txt; print('OK')"`

### Bug 4: Livros duplicados (EPUB + TXT)
**Sintoma:** Mesmo livro aparece duas vezes com categorias diferentes.  
**Prevenção:** Não processar EPUB e TXT do mesmo livro. Se acontecer, usar `recategorize.py` para remover o errado.

### Bug 5: Telegram rejeita EPUB
**Sintoma:** Hermes "Unsupported document type" para `.epub`.  
**Fix:** Renomear `.epub` → `.zip` no computador antes de enviar. Bianinho processa o ZIP.

### Bug 6: FileNotFoundError com caminho do Telegram (caracteres especiais)
**Detectado:** 28/04/2026  
**Sintoma:** `FileNotFoundError: No such file or directory` ao passar `--file` com o caminho exacto que o Telegram envia (ex: `Modern_Web_Design_in_30_Days_Beginner's_Guide...`).  
**Causa:** Aspas e plicas no nome do ficheiro causam falha no `pathlib.Path.stat()`.  
**Fix:** Copiar primeiro para `/tmp/` sem aspas — funciona porque o ficheiro existe fisicamente:
```bash
cp /home/alvarobiano/.hermes/cache/documents/doc_e103db5aeb8b_* /tmp/web_design.pdf
cd ~/KnowledgeBase && ./venv/bin/python pipeline/livro_pipeline.py --file "/tmp/web_design.pdf" --category auto
```
**Regra:** Nunca passar directamente o caminho do Telegram para `--file` — sempre copiar primeiro para `/tmp/`.

### Bug 7: Ficheiros pequenos rejeitados como "corrupted" (FALSE POSITIVE)
**Detectado:** 30/04/2026  \
**Sintoma:** Pipeline rejeita ficheiros txt/texto com ERRO: `❌ Arquivo muito pequeno (X bytes) — possivelmente corrupted`, mesmo quando o conteúdo é válido e tem chunks.  \
**Causa:** O pipeline tem um threshold de tamanho de ficheiro (~0.01 MB / ~10KB). Ficheiros com <10KB são rejeitados antes da verificação de chunks. **O conteúdo NÃO está corrompido — o pipeline é que tem um filtro de tamanho overly-agressivo.**  \
**Exemplo:** `minimax_agent.txt` com 4KB foi rejeitado; a mesma informação expandida para 12KB em `minimax_agent_knowledge.txt` foi aceite e processou 7 chunks válidos.  \
**Workaround:** Se um txt processado manualmente for rejeitado, expandir o conteúdo — adicionar mais texto, repetir secções com mais detalhe, ou incluir o triplo de conteúdo. O pipeline aceita ficheiros >10KB sem problema.  \
**Verificação:** `ls -la /tmp/ficheiro.txt` — se < 0.01 MB E foi rejeitado, é este bug.  \
**Fix ideal (futuro):** Remover o threshold de tamanho do pipeline OU aumentá-lo para ~1KB. Por agora, a solução é always criar txt de pelo menos 12KB quando se processa conteúdo manualmente.

### Bug 8: PDFs de imagens extraem poucos caracteres (chunks muito baixos)
**Detectado:** 30/04/2026  \
**Sintoma:** Livros com conteúdo válido extraem <10 chunks (ex: "127 Palavras" → 4 chunks, "Dieta Tipo Sanguíneo" → 3 chunks, ~3.700 caracteres). O PDF parece vazio mas tem conteúdo real.  \
**Causa:** O PDF é formatado como imagens (sem texto OCR). PyMuPDF extrai apenas o que existe como texto — nada. O que aparece é resultado parcial de metadata/altura de página.  \
**Indicadores:**
  - `caracteres extraídos < 10.000` E `chunks < 10` → provavelmente PDF de imagens
  - Tamanho do ficheiro >1 MB mas texto < 10KB → confirma
**Recuperação:** Usar OCR (marker-pdf, pymupdf + tesseract) para extrair texto de imagens antes de processar. Ver skill `ocr-and-documents` para o fluxo completo.  \
**Regra prática:** Se um PDF processado resulta em < 20 chunks E tem > 1 MB, investigar com `python3 -c "import fitz; doc=fitz.open('/tmp/file.pdf'); print(sum(len(p.get_text()) for p in doc))"` — se o total é < 10.000 chars, é PDF de imagem.

---

## Post-Processing — Recategorização de Health/Wellness

**Problema recorrente:** Livros sobre saúde, nutrição, emagrecimento, plantas medicinais e bem-estar sempre categorizam como `default` (scores 3-8% < 10% threshold). Bianinho corrige manualmente para `desenvolvimento_pessoal` após cada processamento.

**Keywords que faltam no classify_by_content** (para eventual update do classificador):

| Categoria | Keywords em falta |
|-----------|------------------|
| `desenvolvimento_pessoal` | saúde, dieta, emagrecer, nutricional, alimentar, Weight, perda de peso, autoimmune, inflamação, fitoterapia, naturopatia, sangue, tipo sanguíneo, medicinal, curam, natural, bem-estar, estilo de vida |

**Script de recategorização pós-processo (sempre aplicar após processar livros de saúde):**
```python
import sys
sys.path.insert(0, '/home/alvarobiano/KnowledgeBase')
import lancedb
import pyarrow as pa

db = lancedb.connect('/home/alvarobiano/KnowledgeBase/knowledge_db')
tbl = db.open_table('chunks')
df = tbl.to_pandas()

# Livros de saúde/wellness que sempre vão para default
wellness_books = [
    'saude_natural.pdf',
    'doencas_autoimunes.pdf',
    'dieta_tipo_sanguineo.pdf',
    'imagine_emagreca.pdf',
    'plantas_curam.pdf',
    'livro_negro_acucar.pdf',
    'fracasso_sucesso.pdf',   # borderline 10%
]

for source in wellness_books:
    mask = df['source'] == source
    if mask.sum() > 0 and df.loc[mask, 'category'].iloc[0] == 'default':
        n = mask.sum()
        print(f"'{source}': '{df.loc[mask,'category'].iloc[0]}' → 'desenvolvimento_pessoal' ({n} chunks)")
        df.loc[mask, 'category'] = 'desenvolvimento_pessoal'
        tbl.delete(f"source = '{source}'")
        tbl.add(pa.Table.from_pandas(df[mask]))
        print('✅')
```

**Regra de decisão para pós-correção:**
```
SE categoria == 'default' E (título contém saúde/nutrição/emagrecimento/bem-estar/plantas/dieta)
ENTÃO → desenvolvimento_pessoal
SENÃO SE score_category < 10% E score_desenvolvimento_pessoal >= 8%
ENTÃO → desenvolvimento_pessoal
```

**Limiar 10% (edge case):** O pipeline usa `if best_pct >= 10%` para atribuir categoria, e `< 10%` para `default`. Livros com exatamente 10% (ex: "fracasso_sucesso" com 10% em desenvolvimento_pessoal) vão para `default` — corrigir manualmente. O threshold exato (>=10%) está em `vector_brain.py` na função `classify_by_content`.

### Bug 8: Ficheiros já processados com chunk count suspiciously baixo (1 chunk)
**Detectado:** 30/04/2026
**Sintoma:** Livro processado mostra apenas 1 chunk no banco, quando deveria ter centenas.
**Causa:** O pipeline detecta source_id existente e pula o processamento (`⏭️ PULADO — já processado`).
**Fix:** Usar sempre `--force` para re-processar:
```bash
cd ~/KnowledgeBase && ./venv/bin/python pipeline/livro_pipeline.py \
  --file "<path>" --category auto --force
```

### Bug 9: to_arrow() não existe em DataFrame pandas
**Detectado:** 30/04/2026
**Sintoma:** `AttributeError: 'DataFrame' object has no attribute 'to_arrow'` ao fazer recategorização.
**Causa:** `pandas.DataFrame.to_arrow()` não existe. O método correto é `pyarrow.Table.from_pandas()`.
**Fix:** Substituir `df.to_arrow()` por `pa.Table.from_pandas(df)` nos scripts de manutenção.

### Bug 10: ZIP estruturalmente EPUB (não é renomeado pelo utilizador)
**Detectado:** 30/04/2026
**Sintoma:** Pipeline rejeita `.zip` com ERRO: `❌ Formato não suportado: .zip` — mas o ZIP é um EPUB válido (ex: `Captivate.zip` de Vanessa Van Edwards).
**Causa:** O pipeline só suporta EPUB se extensão for `.epub`. ZIPs que são EPUB internamente não são reconhecidos.
**Fix:** Extrair manualmente e converter para TXT:
```bash
# 1. Extrair ZIP
mkdir -p /tmp/book_extract
unzip -o "<path.zip>" -d /tmp/book_extract/ 2>&1 | tail -3

# 2. Verificar estrutura EPUB
ls /tmp/book_extract/OEBPS/
# Se existir: mimetype, content.opf, OEBPS/ → é EPUB

# 3. Detectar tipo de conteúdo
ls /tmp/book_extract/OEBPS/xhtml/ 2>/dev/null && echo "→ Capítulos XHTML separados"
ls /tmp/book_extract/OEBPS/*.xhtml 2>/dev/null | head && echo "→ XHTML plano"

# 4. Para capítulos em XHTML separados (padrão Captivate):
python3 - <<'PYEOF'
import re, os
texts = []
base = '/tmp/book_extract/OEBPS/xhtml'
for fname in sorted(os.listdir(base)):
    if fname.endswith('.xhtml') or fname.endswith('.html'):
        with open(f'{base}/{fname}', 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        text = re.sub(r'<[^>]+>', ' ', content)
        text = re.sub(r'\s+', ' ', text).strip()
        if len(text) > 50:
            texts.append(text)
combined = '\n\n'.join(texts)
with open('/tmp/book_name.txt', 'w', encoding='utf-8') as f:
    f.write(combined)
print(f'{len(combined)} chars de {len(texts)} partes')
PYEOF

# 5. Processar como TXT
cd ~/KnowledgeBase && ./venv/bin/python pipeline/livro_pipeline.py \
  --file "/tmp/book_name.txt" --category auto --force
```
**Prevenir:** Verificar `unzip -l <ficheiro.zip> | head` antes de processar — se contiver `OEBPS/`, é EPUB.

### Bug 12: Telegram "document too large" — limite 20 MB
**Detectado:** 30/04/2026
**Sintoma:** Hermes/Telegram rejeita ficheiros grandes com "The document is too large or its size could not be verified. Maximum: 20 MB." Ficheiros de 18 MB também são rejeitados se o Telegram não conseguir verificar o tamanho.
**Workaround:** Extrair conteúdo do ficheiro e enviar versão reduzida:
- Para ZIP/EPUB: extrair e processar como TXT
- Para PDF >20MB: comprimir com Ghostscript (`gs -sDEVICE=pdfwrite -dNOPAINT`)
- Em último caso: pedir ao utilizador para enviar via Google Drive
**Prevenir:** Antes de enviar, verificar tamanho: `ls -la ficheiro.pdf` — se > 18 MB, comprimir primeiro.

### Bug 13: find -name com caracteres especiais falha
**Detectado:** 30/04/2026
**Sintoma:** `find /caminho -name "*milionário*"` retorna "Arquivo ou diretório inexistente" mesmo quando o ficheiro existe.
**Causa:** O nome do ficheiro no disco usa codificação de caracteres diferente do terminal (ex: `ã` vs `ã` em UTF-8 normalizado diferente).
**Workaround:** Não usar curingas com caracteres especiais. Usar em vez:
```bash
# Listar todos os doc_* e filtrar manualmente
ls ~/.hermes/cache/documents/ | grep -i milion
# Ou usar find sem curingas
find ~/.hermes/cache/documents -maxdepth 1 -name "*milion*"  # funciona se não houver acentos
# Ou copiar todos e verificar por padrão único
find ~/.hermes/cache/documents -maxdepth 1 -name "*milion*" -exec cp {} /tmp/目标.pdf \;
# Se falhar com curingas, usar -path + -name sem caracteres especiais
```
**Regra:** Se `find -name` com texto do utilizador falha, copiar o ficheiro pela hash doc_ e renomear em `/tmp/`.

### Bug 14: Threshold borderline — 10% vai para default
**Detectado:** 30/04/2026
**Sintoma:** Livros com score exactamente 10% (ex: "fracasso_sucesso" com 10% em desenvolvimento_pessoal, "intestino" com 10%) são atribuídos a `default` em vez da categoria.
**Causa:** Possível floating point precision issue — 10.0 pode ser armazenado como 9.9999...making `>= 10%` evaluates to False.
**Fix manual:** Após processar, verificar se categoria ficou `default` E o scorelog mostra 10%. Se sim, corrigir com script de recategorização.
**Regra:** Sempre verificar o log — se "melhor: X 10%" E categoria é `default`, corrigir manualmente.

### Bug 16: `python3` no Hermes resolve para Python 3.14 sem pdfminer
**Detectado:** 30/04/2026
**Sintoma:** `ModuleNotFoundError: No module named 'pdfminer'` ao usar `python3 scripts/_archive/process_book.py`. Ficheiros que deviam extrair texto devolvem "No text extracted!".
**Causa:** `python3` no Hermes aponta para `/home/alvarobiano/.local/bin/python3` (Python 3.14.4). O pacote `pdfminer.six` está instalado em `/home/alvarobiano/.local/lib/python3.12/site-packages/` — invisível para Python 3.14.
**Fix:** Usar sempre `python3.12` explicitamente:
```bash
# Errado — python3 = 3.14 sem pdfminer
python3 scripts/_archive/process_book.py "livro.pdf" categoria

# Correto — python3.12 = 3.12 com pdfminer
python3.12 scripts/_archive/process_book.py "livro.pdf" categoria
```
**Regra:** Qualquer script que use pdfminer, pdfplumber, ou PyMuPDF deve ser executado com `python3.12`, não `python3`.

### Bug 20: `filepath.stat()` falha após copy via raw bytes para /tmp/
**Detectado:** 01/05/2026
**Sintoma:** `FileNotFoundError` em `livro_pipeline.py` na linha `filepath.stat().st_size` mesmo depois de copiar o ficheiro para `/tmp/` via raw bytes.
**Causa:** O pipeline usa `filepath` (o caminho original do Telegram) para o stat, não o caminho `/tmp/` para onde o ficheiro foi copiado. O `filepath.stat()` é chamado antes de o código usar o `/tmp/` path internamente.
**Fix:** Copiar o ficheiro para `/tmp/` e usar o caminho `/tmp/` directamente no `--file`. O pipeline precisa do stat do ficheiro original apenas para logging do tamanho — se o stat falha, o pipeline crasha. Solução: copiar E passar o caminho `/tmp/` ao pipeline:
```bash
# 1. Copiar via raw bytes (único método que funciona com Unicode filenames)
python3 -c "
import glob
src = glob.glob('/home/alvarobiano/.hermes/cache/documents/doc_<hash>*')[0]
with open(src, 'rb') as f:
    data = f.read()
with open('/tmp/book_simple.pdf', 'wb') as f:
    f.write(data)
"

# 2. Passar o caminho /tmp/ ao pipeline
cd ~/KnowledgeBase && ./venv/bin/python pipeline/livro_pipeline.py \
  --file "/tmp/book_simple.pdf" --category auto --force
```
**Regra:** Nunca passar o caminho original do Telegram directamente em `--file`. Sempre copiar primeiro para `/tmp/` e passar esse caminho.

---

### Bug 17: Ficheiro existe no `ls` mas Python não consegue abrir — Unicode normalization
**Detectado:** 30/04/2026
**Sintoma:** `ls ~/.hermes/cache/documents/` mostra `doc_xxx_O Cardápio Contra o cáncer.pdf`, mas `cp` e `python3 -c "open(...)"` devolvem "Arquivo ou diretório inexistente". `python3` (3.14) não consegue resolver o caminho.
**Causa:** O nome do ficheiro no disco usa Unicode normalization diferente (NFD vs NFC). O `ls` mostra uma forma, mas o kernel e Python veem outra. Especialmente sensível com `ã`, `ç`, espaços e acentos.
**Sintomas:**
- `ls` encontra → `cp`/`open()` falha
- `FileNotFoundError` com caminho que o `ls` mostra como existente
- Funciona num terminal, falha noutro

**Workaround completo — glob + leitura raw bytes (único padrão que funciona 100%):**

```python
import glob, shutil
# 1. Encontrar via glob — usa o nome que o ls mostra
matches = glob.glob('/home/alvarobiano/.hermes/cache/documents/doc_ad320*')
print('Matches:', matches)  # ['/home/alvarobiano/.hermes/cache/documents/doc_ad320...pdf']

# 2. Copiar via leitura de bytes crus (NÃO usar shutil.copy2() — falha)
src = matches[0]
dst = '/tmp/book_simple_name.pdf'
with open(src, 'rb') as f:
    data = f.read()
with open(dst, 'wb') as f:
    f.write(data)
print(f'Copiado: {len(data)} bytes')
```

**O que NÃO funciona:**
- `shutil.copy2(src, dst)` → `FileNotFoundError`
- `subprocess.run(['cp', src, dst])` → `não foi possível obter estado`
- `pathlib.Path(src).stat()` → `No such file or directory`
- Caminho literal com acentos copiado da mensagem do Telegram

**O que FUNCIONA:**
- `glob.glob()` para descobrir o caminho
- `open(src, 'rb').read()` para ler bytes crus
- `open(dst, 'wb').write()` para escrever

**Regra:** Nunca usar o caminho literal com acentos/espaços. USAR SEMPRE `glob.glob()` + leitura raw bytes. Este workaround foi validado 5+ vezes em succession — é o padrão definitivo para ficheiros do Telegram cache.

### Bug 18: `db.list_tables()` devolve pydantic model — não lista
**Detectado:** 30/04/2026
**Sintoma:** `TypeError: argument 'name': 'tuple' object cannot be converted to 'PyString'` ao iterar resultado de `list_tables()`.
**Causa:** `db.list_tables()` devolve um objecto pydantic (ou namedtuple) com atributo `.tables` que é a lista real, não a lista directamente.
**Workaround:**
```python
# Errado
for t in db.list_tables():  # itera sobre campos do pydantic, não strings
    tbl = db.open_table(t)  # falha

# Correto
result = db.list_tables()
tables = result.tables if hasattr(result, 'tables') else list(result)
for t in tables:
    tbl = db.open_table(t)  # funciona
```
**Regra:** Ao iterar `list_tables()`, extrair o atributo `.tables` do resultado primeiro.

### Bug 19: `process_book.py` (archive) usa schema errado para LanceDB
**Detectado:** 30/04/2026
**Sintoma:** `ValueError: Invalid input, field 'id' does not exist in table schema` ao tentar inserir chunks do `process_book.py` na tabela LanceDB.
**Causa:** O script `scripts/_archive/process_book.py` usa um schema de chunk diferente (campo `id` em vez de `vector`) e não gera embeddings. As tabelas LanceDB (`chunks`, `metodoten`) têm schema fixo com `vector` obrigatório.
**Fix:** NUNCA usar `scripts/_archive/process_book.py` para inserção em LanceDB. Esse script apenas extrai texto e guarda em JSON. Usar SEMPRE `~/KnowledgeBase/vector_brain.py` para inserção em LanceDB:
```bash
cd ~/KnowledgeBase && ~/venv/bin/python vector_brain.py \
  --action process --file "/tmp/book.pdf" --category desenvolvimento_pessoal --table metodoten
```
**Regra:** O único script de processamento correcto para o RAG é `~/KnowledgeBase/vector_brain.py` com `--action process`.

---

### Bug 15: Livros duplicados — detectar via MD5 antes de processar
**Detectado:** 30/04/2026
**Sintoma:** O mesmo livro é enviado duas vezes (ex: `milionário_consciente.pdf` appeared twice). Processar a segunda vez desperdiça quota de API.
**Fix:** Verificar MD5 antes de processar:

```bash
# Listar ficheiros na pasta docs
cd ~/.hermes/cache/documents
md5sum doc_*.pdf | sort | uniq -d -w32
# Se mostrar hash repetido → ficheiro duplicado

# Ou comparar dois ficheiros específicos
md5sum arquivo1.pdf arquivo2.pdf
# Se igual → são o mesmo ficheiro
```

**Regra:** Se MD5 igual E chunk count já é alto (200+ chunks), não reprocessar. Apenas confirmar que já está no banco.

---

## Quality Assurance — Checklist

Depois de processar um livro, confirmar:

```
□ Chunk count razoável: ~200-500 chunks por livro (300-500 pág)
□ Remoção pelo sanitizer < 50% do total
  → Se >90%: bug NOISE_PATTERNS activo
□ Categoria com % >= 10% (se "default" E score próximo de 10%: 8-10%, corrigir para categoria mais provável — ver nota abaixo)
□ ⚠️ **Alerta de PDF-imagem:** Se chunk count < 10 E ficheiro > 100KB → provavelmente PDF de imagens (texto extraído = 0). Não é bug do pipeline — o PDF genuinamente não tem texto.
□ Nenhum erro "ModuleNotFoundError" ou "ImportError"
□ **VERIFICAÇÃO OBRIGATÓRIA: confirmar que os chunks estão no banco** (ver abaixo)

**Nota sobre categoria "default" borderline:** Livros com score entre 8-10% (ex: "Fracasso É Apenas..." com 10%, "As Plantas Curam" com 8%) frequentemente pertencem a `desenvolvimento_pessoal`. Corrigir com script de recategorização se o tema se ajustar. Threshold exato é 10%, mas conteúdo real pode ser relevante.

**Alerta Telegram size limit:** Se Telegram报告 "document too large", não perguntar — extrair conteúdo e processar como TXT/ZIP. O limite é ~20MB.
```

### ⚠️ BUG CRÍTICO: Pipeline pode reportar SUCCESS sem inserir

**Sintoma:** Pipeline loga "✅ SUCESSO" mas o livro NÃO aparece no banco (0 chunks).
**Detectado:** 30/04/2026 — `fracasso_sucesso.pdf` reportou sucesso mas não estava no DB.
**Causa:** Falha silenciosa na inserção (possível race condition ou timeout).

**Verificação obrigatória após cada processamento:**
```python
import sys
sys.path.insert(0, '/home/alvarobiano/KnowledgeBase')
import lancedb

db = lancedb.connect('/home/alvarobiano/KnowledgeBase/knowledge_db')
tbl = db.open_table('chunks')
df = tbl.to_pandas()

# Substituir pelo nome do livro processado
source_name = 'fracasso_sucesso.pdf'  # ou o nome que apareceu no log
chunks_found = df[df['source'] == source_name]
print(f"Chunks no banco: {len(chunks_found)}")
if len(chunks_found) == 0:
    print("❌ ALERTA: Livro não está no banco! Reprocessar com --force")
else:
    print(f"✅ Confirmado: {len(chunks_found)} chunks em '{chunks_found['category'].iloc[0]}'")
```

**Se 0 chunks → reprocessar com `--force`:**
```bash
cd ~/KnowledgeBase && ./venv/bin/python pipeline/livro_pipeline.py \
  --file "/tmp/NOME.pdf" --category auto --force
```

**Debug rápido se chunk count é suspiciously baixo:**
```python
import sys
sys.path.insert(0, '/home/alvarobiano/KnowledgeBase')
from vector_brain import TextSanitizer, extract_txt
s = TextSanitizer()
text = extract_txt('/tmp/book_name.txt')
cleaned = s.clean(text)
print(f"Antes: {len(text)}")
print(f"Depois: {len(cleaned)}")
print(f"Removido: {len(text)-len(cleaned)} ({(1-len(cleaned)/max(len(text),1)):.1%})")
# Se >90% removido → bug activo
```

---

## Scripts de Manutenção

### Verificar estado do banco
```python
import sys
sys.path.insert(0, '/home/alvarobiano/KnowledgeBase')
import lancedb
db = lancedb.connect('/home/alvarobiano/KnowledgeBase/knowledge_db')
tbl = db.open_table('chunks')
df = tbl.to_pandas()
print(f"Total: {len(df)} chunks, {df['source'].nunique()} livros")
print(df.groupby('category').agg(
    chunks=('text','count'), livros=('source','nunique')
).sort_values('chunks', ascending=False).to_string())
```

### Recategorizar livro (sem re-vectorizar) — PADRÃO INLINE

**Método recomendado:** Executar inline via Python do KnowledgeBase venv.

```python
import sys
sys.path.insert(0, '/home/alvarobiano/KnowledgeBase')
import lancedb
import pyarrow as pa

db = lancedb.connect('/home/alvarobiano/KnowledgeBase/knowledge_db')
tbl = db.open_table('chunks')
df = tbl.to_pandas()

source = 'nome_do_livro.ext'
new_cat = 'categoria_correta'
mask = df['source'] == source
n = mask.sum()
print(f"'{df.loc[mask,'category'].iloc[0]}' → '{new_cat}' ({n} chunks)")

df.loc[mask, 'category'] = new_cat
tbl.delete(f"source = '{source}'")
tbl.add(pa.Table.from_pandas(df[mask]))   # ← NÃO usar df.to_arrow()
print('✅ Feito')
```

**ATENÇÃO:** `pandas.DataFrame.to_arrow()` **não existe**. Sempre usar `pa.Table.from_pandas(df)`.

### Limpeza completa do banco
```python
import sys
sys.path.insert(0, '/home/alvarobiano/KnowledgeBase')
from pathlib import Path
import lancedb, pandas as pd, pyarrow as pa

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

db = lancedb.connect('/home/alvarobiano/KnowledgeBase/knowledge_db')
tbl = db.open_table('chunks')
df = tbl.to_pandas()

# ... modificações no df ...

db.drop_table('chunks')
db.create_table('chunks', schema=SCHEMA, mode='create')
tbl_new = db.open_table('chunks')
tbl_new.add(df)
print(f'✅ {len(df)} chunks')
```

### Debug do TextSanitizer
```python
import sys
sys.path.insert(0, '/home/alvarobiano/KnowledgeBase')
from vector_brain import TextSanitizer
s = TextSanitizer()

tests = [
    ("Chapter 1", True),
    ("Chapter 1: Introduction", False),
    ("[123]", True),
    ("123. 456", True),
    ("© 2024 Todos os direitos reservados", True),
    ("Conteúdo real do livro.", False),
    ("____________", True),
]
for text, expected_noise in tests:
    result = s._is_noise_line(text)
    status = "✅" if result == expected_noise else "❌"
    print(f"{status} '{text[:40]}' → {'RUÍDO' if result else 'OK'}")
```

---

## Regra de Ouro

**Processar imediatamente sem perguntar.** O Álvaro envia o livro, Bianinho processa e categoriza. Se a categoria ficar errada, corrigir com o script de recategorização — sem precisar re-vectorizar.

**Pipeline correcto (sempre):**
```bash
cd ~/KnowledgeBase && ~/venv/bin/python vector_brain.py \
  --action process --file "/tmp/book.pdf" --category desenvolvimento_pessoal --table chunks
```
- ** NÃO** usar `scripts/_archive/process_book.py` para LanceDB (schema incompatível)
- **SEMPRE** usar `~/KnowledgeBase/venv/bin/python` (Python 3.14 do venv com lancedb)
- O argumento `--table` permite escolher entre `chunks` (default) e `metodoten`

**PASSO 0 — Pré-verificação (sempre fazer antes de processar):**
```
1. md5sum do ficheiro → se hash igual a source já no banco → skip e notificar
2. unzip -l *.zip | head → se contém OEBPS/mimetype → EPUB disfarçado → extrair primeiro
3. Se ficheiro > 18 MB → texto extraído vai ser pouco → processar mas avisar
```

**VERIFICAÇÃO OBRIGATÓRIA após cada processamento:**
Após inserir, Bianinho DEVE confirmar que os chunks existem no banco. Se 0 chunks → reprocessar com `--force`.

**DUPLICADOS:** Livros com nomes diferentes mas conteúdo idêntico são comuns (mesmo MD5). Antes de processar, comparar MD5 com sources já no banco. Se duplicado, apenas Skips e notificar.

**TELEGRAM FILE SIZE:** Se o Telegram rejeitar com "document too large", o ficheiro está perto de 20 MB. Extrair conteúdo (EPUB de ZIP, ou usar Ghostscript para PDF) e processar. Não perguntar — fazer.

**EPUB-ZIP:** Ficheiros .zip que são EPUB internamente (ex: Captivate) precisam de extracção manual. Ver `references/epub-zip-workaround.md`.

**LIMITE DE THRESHOLD:** Se log mostra "melhor: X 10%" mas categoria ficou `default`, corrigir manualmente. Threshold de 10% pode ter edge case para valores exactamente 10.0.

---

### Ficheiros da Skill

- `scripts/rag_cleanup.py` — Limpeza completa do banco
- `scripts/recategorize.py` — Recategorizar livro sem re-vectorizar
- `references/epub-structures.md` — Inventário das estruturas EPUB internas (ZIP) detectadas — Padrão 1 (`OEBPS/xhtml/`), Padrão 2 (`OEBPS/` plano), Padrão 3 (`OEBPS/Text/`). Inclui código de detecção automática.
- `references/duplicate-detection.md` — Detectar ficheiros duplicados via MD5 antes de processar.
- `references/pipeline-verification.md` — Verificação pós-processamento: bug de sucesso falso e como detectá-lo.
- `references/epub-zip-workaround.md` — EPUB enviado como ZIP (ex: Captivate): detecção, extracção e fluxo completo.
