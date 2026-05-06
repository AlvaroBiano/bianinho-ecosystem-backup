---
name: cerebro-vetorial-lancedb
description: Projeto de base de conhecimento vetorial — LanceDB + OpenAI via OpenRouter + Z-Library. Inclui setup, armadilhas (gotchas), e workflow completo.
triggers:
  - vector brain
  - lancedb setup
  - embeddings
  - knowledge base
  - vector database
---

# Cérebro Vetorial — LanceDB + OpenRouter

## Contexto

Projeto de base de conhecimento vetorial para Álvaro Biano. Livros baixados da Z-Library (10/dia), vetorizados com OpenAI embeddings via OpenRouter, armazenados no LanceDB.

**Conta Z-Library:** bianinhoclaw@gmail.com | @BianinhoZLib2026!xK9
**Banco vetorial:** ~/KnowledgeBase/knowledge_db/
**Pipeline:** ~/KnowledgeBase/pipeline/livro_pipeline.py
**venv:** ~/KnowledgeBase/venv/bin/python (Python 3.14)
**Categorias:** ~/KnowledgeBase/{psicologia,marketing,desenvolvimento_pessoal,inteligencia_artificial,financas,comunicacao,metodo_ten,default}/livros/

**Taxonomia profissional (8 categorias):**
| Categoria | Descrição |
|-----------|-----------|
| `inteligencia_artificial` | IA, LLMs, agentes, prompt engineering |
| `psicologia` | Terapia, trauma, emoções, saúde mental |
| `desenvolvimento_pessoal` | Hábitos, produtividade, mindset |
| `financas` | Investimentos, riqueza, mercado |
| `marketing` | Marketing, vendas, marca |
| `comunicacao` | Negociação, influência, persuasão |
| `metodo_ten` | Conteúdo próprio do método |
| `default` | Livros sem categoria definida |

## Setup Completo

### 1. Instalar dependências (Python 3.12 — NÃO 3.14)

```bash
pip install --break-system-packages lancedb openai tiktoken pdfplumber ebooklib
# OU via pip3
pip3 install lancedb openai tiktoken pdfplumber ebooklib
```

**ATENÇÃO:** O servidor tem Python 3.14 como default, mas os pacotes foram instalados no Python 3.12 (em `/usr/lib/python3.12/`). Usar sempre `/usr/bin/python3` que aponta pro 3.12.

### 2. Estrutura de pastas

```bash
mkdir -p ~/KnowledgeBase/{psicologia,marketing,desenvolvimento_pessoal,matematica,default}/livros
mkdir -p ~/KnowledgeBase/knowledge_db
```

### 3. API Key OpenRouter

Ler de `~/.hermes/auth.json`:
```python
import json
with open(os.path.expanduser("~/.hermes/auth.json")) as f:
    auth = json.load(f)
api_key = auth["credential_pool"]["openrouter"][0]["access_token"]
```

## Armadilhas Encontradas (Gotchas)

### Python Environment — USO OBRIGATÓRIO DO VENV
### Python Environment — venv em ~/KnowledgeBase/venv

O servidor tem Python 3.14 como default (`python3 --version` → 3.14.4).
O venv em `~/KnowledgeBase/venv/` (Python 3.14) é o ambiente correto com lancedb, ebooklib, tiktoken, pyarrow.

**Verificar:**
```bash
ls ~/KnowledgeBase/venv/bin/python  # deve existir
~/KnowledgeBase/venv/bin/python --version  # 3.14.x
```

**Para rodar o pipeline:**
```bash
cd ~/KnowledgeBase && ./venv/bin/python pipeline/livro_pipeline.py --help
```

### LanceDB API (v0.30+)
- `db.table_names()` → Deprecated, usar `db.list_tables()`
- `db.list_tables()` retorna objeto `ListTablesResponse`, não list — verificar `.tables` attribute:
```python
tables_response = db.list_tables()
tables = tables_response.tables if hasattr(tables_response, 'tables') else list(tables_response)
```

### ⚠️ query_type="hybrid" REQUIRES embedding function on table
**PROBLEMA:** `tbl.search(query, query_type="hybrid")` lança `"No embedding function for vector"` se a tabela não tiver embedding function registrada — e as tabelas existentes (`chunks`, `metodoten`) não têm.

**Causa:** `query_type="hybrid"` tenta gerar embedding internamente, mas LanceDB v0.30+ exige que a embedding function esteja registada na tabela via `table.create_fts_index()` ou similar — o que não existe nas tabelas já criadas.

**Solução correta — gerar embedding manualmente:**
```python
from vector_brain import embedder  # já configurado com OpenRouter
db = lancedb.connect("~/KnowledgeBase/knowledge_db")
tbl = db.open_table("chunks")

# Gerar embedding separadamente (~0.1s)
vectors = embedder.generate_text_embeddings(["minha query"])
query_embedding = vectors[0]["embedding"]

# Buscar com vector_column_name explícito (~0.3s)
results = tbl.search(query_embedding, vector_column_name="vector").limit(top_k).to_list()
```

**NUNCA usar** `tbl.search("texto", query_type="hybrid")` — vai falhar.

### Schema PyArrow
- LanceDB moderno requer schema PyArrow, não dict Python:
```python
import pyarrow as pa
SCHEMA = pa.schema([
    pa.field("vector", pa.list_(pa.float32(), 1536)),
    pa.field("text", pa.string()),
    pa.field("source", pa.string()),
    pa.field("category", pa.string()),
    pa.field("chunk_index", pa.int32()),
    pa.field("total_chunks", pa.int32()),
    pa.field("filepath", pa.string()),
    pa.field("language", pa.string()),
])
```

### Embeddings via OpenRouter
- OpenRouter tem endpoint `/api/v1/embeddings` compatível com OpenAI
- Modelo: `text-embedding-3-small` (1536 dimensões)
- Endpoint: `https://openrouter.ai/api/v1/embeddings`
- Fazer wrapper próprio em vez de confiar em SDK com versão errada

## Pipeline de Processamento de Livros

**Script principal:** `~/KnowledgeBase/pipeline/livro_pipeline.py`

```bash
# Estatísticas do banco
cd ~/KnowledgeBase && ./venv/bin/python pipeline/livro_pipeline.py --stats

# Processar arquivo único (auto-detecta categoria)
cd ~/KnowledgeBase && ./venv/bin/python pipeline/livro_pipeline.py --file /path/to/livro.pdf --category auto

# Processar com categoria fixa
cd ~/KnowledgeBase && ./venv/bin/python pipeline/livro_pipeline.py --file /path/to/livro.pdf --category inteligencia_artificial

# Processar EPUB (ZIP disfarçado — primeiro extrair)
# Ver secção "Bug 3: EPUB disfarçado de ZIP" acima

# Verificar setup
cd ~/KnowledgeBase && ./venv/bin/python pipeline/livro_pipeline.py --setup-check

# Deduplicar banco completo
cd ~/KnowledgeBase && ./venv/bin/python pipeline/livro_pipeline.py --dedup
```

### Sistema de detecção de categoria (classify_by_content)
- Usa 30.000 primeiros caracteres do livro
- Pontuação: % de keywords da categoria encontradas (evita viés para categorias com mais keywords)
- Limiar mínimo: 10% das keywords devem estar presentes
- Keywords em português + inglês para cada categoria (8 categorias)
- Categorias disponíveis: `inteligencia_artificial`, `psicologia`, `financas`, `marketing`, `desenvolvimento_pessoal`, `comunicacao`, `metodo_ten`, `default`

## Bugs Corrigidos em vector_brain.py

### Bug 1: Estratégia 3 copyright block a remover livro inteiro
**Ficheiro:** `~/KnowledgeBase/vector_brain.py` linha ~327-332

**Problema:** `clean_text = normalized[start_idx + len(copyright_text):]` — remove ANTES do copyright (mantém copyright, remove resto do livro).

**Fix:** `clean_text = normalized[:start_idx] + normalized[start_idx + len(copyright_text):]`

### Bug 2: NOISE_PATTERNS "Chapter X:" a matar capítulo inteiro
**Ficheiro:** `~/KnowledgeBase/vector_brain.py` linha ~161

**Problema:** `r'^\s*(capítulo|chapter|seção|section)\s+\d+'` casa com TODA a linha "Chapter 1: Welcome to AI" — remove todo o conteúdo do livro.

**Fix:** `r'^\s*(capítulo|chapter|seção|section)\s+\d+\s*\.?\s*\d*\s*$'` — só casa com linhas de TOC sem conteúdo real (sem `:` seguido de texto).

**Sintoma:** Livro com 195KB extraído → só 3 chunks. `clean()` remove >97% do texto.

**Debug:** Ver skill `knowledge-base-content-validation` para fluxo completo.

### Bug 3: EPUB disfarçado de ZIP — como processar
**Problema:** O Telegram às vezes envia EPUB como `.zip`. O `livro_pipeline.py` só aceita `.epub`, `.pdf`, `.txt`.

**Solução:** Extrair manualmente os XHTMLs e combinar em TXT:
```bash
mkdir -p /tmp/book_extract
unzip -o arquivo.zip -d /tmp/book_extract/
# Combinar c*.xhtml em txt
~/KnowledgeBase/venv/bin/python -c "
import re, os
texts = []
for fname in sorted(os.listdir('/tmp/book_extract/')):
    if fname.startswith('c') and fname.endswith('.xhtml'):
        with open(f'/tmp/book_extract/{fname}', 'r', encoding='utf-8', errors='ignore') as f:
            text = re.sub(r'<[^>]+>', ' ', f.read())
            text = re.sub(r'\s+', ' ', text).strip()
            if len(text) > 50:
                texts.append(text)
combined = '\n\n'.join(texts)
with open('/tmp/book.txt', 'w', encoding='utf-8') as f:
    f.write(combined)
"
# Processar
~/KnowledgeBase/venv/bin/python ~/KnowledgeBase/pipeline/livro_pipeline.py --file /tmp/book.txt --category default
```

## Workflow de Limpeza e Categorização do RAG

Quando o Álvaro pedir para "melhorar a categorização" ou "auditar o RAG":

### Diagnóstico completo (ler banco)
```python
~/KnowledgeBase/venv/bin/python -c "
import lancedb, pandas as pd
db = lancedb.connect('knowledge_db')
tbl = db.open_table('chunks')
df = tbl.to_pandas()
print(df.groupby('source').agg(chunks=('text','count'), cat=('category','first'))
      .sort_values('chunks', ascending=False).to_string())
"
```

### Padrão DROP + RECREATE para reescrever tabela LanceDB
**Use quando:** precisar alterar categorias de muitos livros de uma só vez, ou remover duplicados.

```python
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

db = lancedb.connect('knowledge_db')
tbl = db.open_table('chunks')
df = tbl.to_pandas()

# 1. Modificar df (recategorizar, remover duplicados, etc.)
# 2. Apagar e recriar
db.drop_table('chunks')
db.create_table('chunks', schema=SCHEMA, mode='create')
tbl_new = db.open_table('chunks')
tbl_new.add(df)  # df com mudanças aplicadas
```

### Como identificar problemas de categorização
1. **Duplicados TXT vs EPUB**: mesmo livro em txt E epub — remover o txt
2. **Arquivos de sessão**: nomes que começam com `consolidation-` — são sessões do Hermes, não livros
3. **Livros em `default`**: se parecem com IA/psicologia/marketing, recategorizar
4. **Chunks < 50 por livro grande** (>100KB texto): provavelmente sanitizer a destruir conteúdo

### Script de categorização completo
Ler `/tmp/rag_categorization_fix.py` — script já criado com o workflow de limpeza e recategorização.

## EPUB → TXT (via ebooklib)

O Hermes não aceita EPUB como upload. Truque: `.epub` é um `.zip` — renomear e extrair:

```python
import os, re, glob
from ebooklib import epub

def epub_to_txt(epub_path, out_txt_path):
    """Converte EPUB para TXT limpando CSS/HTML residual."""
    book = epub.read_epub(epub_path)
    text_parts = []
    for item in book.get_items():
        if item.get_type() == 9:  # HTML
            content = item.get_content().decode("utf-8", errors="ignore")
            clean = re.sub(r"<style[^>]*>.*?</style>", " ", content, flags=re.DOTALL)
            clean = re.sub(r"<[^>]+>", " ", clean)
            clean = re.sub(r"\s+", " ", clean).strip()
            if len(clean) > 50:
                text_parts.append(clean)
    full_text = "\n\n".join(text_parts)
    with open(out_txt_path, "w", encoding="utf-8") as f:
        f.write(full_text)
    return len(full_text)
```

**Passos:**
1. Renomear `.epub` → `.zip` no Mac
2. Enviar pelo Telegram
3. Bianinho extrai e processa com ebooklib

## Pipeline de Sanitização (TextSanitizer)

Implementado no script — etapas automática:

1. **Remoção de controle** — caracteres `\x00-\x1f`, `\x7f-\x9f`
2. **Limpeza de ruído** — números de página (`[123]`, `— 45 —`), headers, footers, URLs soltas
3. **Normalização** — whitespace, aspas, travessões, reticências
4. **Validação de chunk** — mínimo 50 chars, 10 palavras, <30% números
5. **Deduplicação** — hash MD5 do chunk (intra-livro + inter-livro)

### Schema completo (com sanitização)
```python
SCHEMA = pa.schema([
    pa.field("vector", pa.list_(pa.float32(), 1536)),
    pa.field("text", pa.string()),
    pa.field("source", pa.string()),
    pa.field("category", pa.string()),
    pa.field("chunk_index", pa.int32()),
    pa.field("total_chunks", pa.int32()),
    pa.field("filepath", pa.string()),
    pa.field("language", pa.string()),
    pa.field("chunk_hash", pa.string()),    # NEW: hash dedup
    pa.field("processed_at", pa.string()),  # NEW: timestamp
])
```

### Drop table (se precisar recriar schema)
```bash
rm -rf ~/KnowledgeBase/knowledge_db/chunks.lance
```

## Integração como Tool do Hermes Agent

O vector brain foi integrado como tool nativo do Hermes Agent (Opção 1+2 da discussão).

### Arquivos

**Ferramenta:** `~/.hermes/hermes-agent/tools/knowledge_vector_tool.py`
- `knowledge_query` — busca semântica
- `knowledge_stats` — estatísticas
- `knowledge_process` — processa categoria

**Integração em 2 arquivos do Hermes Agent:**
1. `~/.hermes/hermes-agent/model_tools.py` — adicionar à lista `_modules`:
   ```python
   "tools.knowledge_vector_tool",
   ```
2. `~/.hermes/hermes-agent/toolsets.py` — adicionar ao `_HERMES_CORE_TOOLS`:
   ```python
   "knowledge_query", "knowledge_stats", "knowledge_process",
   ```

### Integração como Tool do Hermes Agent

O vector brain foi integrado como tool nativo do Hermes Agent.

**Tool:** `knowledge_query`, `knowledge_stats`, `knowledge_process` — chamam `vector_brain.py` via subprocess usando `~/KnowledgeBase/venv/bin/python`.

**Importante:** As tools do Hermes usam o venv local (`~/KnowledgeBase/venv`) automaticamente via subprocess. Não é necessário restartar Hermes Agent para mudanças no script — só se mudar a tool registration.

**Verificar se venv existe:**
```bash
ls ~/KnowledgeBase/venv/bin/python
```
Se não existir, criar conforme instrução acima na seção Python Environment.

### Schema atualizado (com sanitização)

**Escolha: LanceDB** pelos motivos:
- Persistência em disco (ChromaDB padrão é RAM)
- Escala a petabytes (ChromaDB limitado a ~10M vetores)
- Formato Apache Arrow mais eficiente
- Mais ativo em desenvolvimento

## RAG Server (BM25) — porta 3101

O servidor BM25 (`rag_service.py`) oferece pesquisa por similaridade via API RESTful na porta 3101.

### Iniciar manualmente (foreground)

```bash
cd ~/KnowledgeBase
venv/bin/python ~/.hermes/scripts/rag_service.py 2>&1 &
```

**ATENÇÃO:** Não redirecionar stdout/stderr para `/dev/null` — sem ver os logs é impossível debugar crashes por porta já em uso.

### Persistência com systemd (recomendado)

Criar serviço user-level:

```bash
mkdir -p ~/.config/systemd/user
# Criar ~/.config/systemd/user/rag-server.service
systemctl --user daemon-reload
systemctl --user enable rag-server
systemctl --user start rag-server
```

Conteúdo do serviço (`~/.config/systemd/user/rag-server.service`):
```ini
[Unit]
Description=RAG BM25 Server
After=network.target

[Service]
Type=simple
WorkingDirectory=/home/alvarobiano/KnowledgeBase
ExecStart=/home/alvarobiano/KnowledgeBase/venv/bin/python /home/alvarobiano/.hermes/scripts/rag_service.py
Restart=always
RestartSec=5

[Install]
WantedBy=default.target
```

**Verificar estado:**
```bash
systemctl --user status rag-server
curl http://127.0.0.1:3101/health
```

### Armadilha: conflito de processos

Se o systemd mostrar `active (auto-restart) (Result: exit-code)` e a porta já estiver em uso, há outro processo `rag_service.py` a correr. Mate-o primeiro antes de iniciar o serviço.

## Fluxo de Trabalho

1. Baixar livro da Z-Library → salvar em `~/KnowledgeBase/{categoria}/livros/`
2. `/usr/bin/python3 ~/KnowledgeBase/vector_brain.py --action process --category NOME`
3. Buscar: `/usr/bin/python3 ~/KnowledgeBase/vector_brain.py --action query --query "pergunta"`

## ◆ Fix Missing Vectors in Existing Chunks

**Skill original:** `lancedb-fix-missing-vectors`

### When to Use
Chunks exist in a LanceDB table but vector search doesn't find them. Symptoms:
- Query returns no results or irrelevant results even though matching text exists
- Chunks show up in `tbl.to_pandas()` but search misses them

### Diagnosis
```python
tbl = db.open_table('TABLE_NAME')
print(tbl.schema)
df = tbl.to_pandas()
print(df['vector'].isna().sum(), 'chunks without vectors')
```

### Fix: Delete + Re-add with Vectors
```python
import lancedb, pandas as pd, json, os, urllib.request

auth = json.load(open(os.path.expanduser('~/.hermes/auth.json')))
key = next((c['access_token'] for c in auth.get('credential_pool',{}).get('openrouter',[]) if c.get('access_token')), None)

db = lancedb.connect('~/KnowledgeBase/knowledge_db/')
tbl = db.open_table('TABLE_NAME')
df = tbl.to_pandas()
target = df[df['source'] == 'TARGET_SOURCE']
texts = target['text'].tolist()

payload = {'model': 'text-embedding-3-small', 'input': texts}
req = urllib.request.Request('https://openrouter.ai/api/v1/embeddings',
    data=json.dumps(payload).encode(),
    headers={'Authorization': f'Bearer {key}', 'Content-Type': 'application/json'},
    method='POST')
with urllib.request.urlopen(req, timeout=60) as resp:
    embeddings = [e['embedding'] for e in json.loads(resp.read())['data']]

tbl.delete(f"source = 'TARGET_SOURCE'")
batch_data = []
for i, (_, row) in enumerate(target.iterrows()):
    d = row.to_dict()
    d['vector'] = embeddings[i]
    for k in list(d.keys()):
        if k.startswith('_row'):
            del d[k]
    batch_data.append(d)
tbl.add(batch_data)
print(f'Fixed {len(batch_data)} chunks')
```

### Notes
- LanceDB Python API: `tbl.update({'vector': emb}).where(...)` — newer versions require `updates=` not positional
- Delete + re-add is more reliable than update for missing vectors

---

## ◆ Create New LanceDB Collection with PyArrow Schema

**Skill original:** `lancedb-new-collection`

### Quando Usar
O `vector_brain.py` só sabe inserir na tabela `metodoten` existente. Para criar uma **nova coleção** (ex: "api", "paperclip"), é preciso criar a tabela com schema pyarrow.

### Método Correto
```python
import pyarrow as pa, lancedb, sys, json, os, urllib.request

KB_PATH = '/home/alvarobiano/KnowledgeBase'
auth = json.load(open(os.path.expanduser('~/.hermes/auth.json')))
key = next((c['access_token'] for c in auth.get('credential_pool',{}).get('openrouter',[]) if c.get('access_token')), None)

sys.path.insert(0, KB_PATH)
from vector_brain import chunk_text

text = open('/path/to/arquivo.md', 'r', encoding='utf-8').read()
chunks = chunk_text(text, chunk_size=512, overlap=64)

def embed_batch(texts):
    req = urllib.request.Request('https://openrouter.ai/api/v1/embeddings',
        data=json.dumps({'model': 'text-embedding-3-small', 'input': texts}).encode(),
        headers={'Authorization': f'Bearer {key}', 'Content-Type': 'application/json'}, method='POST')
    with urllib.request.urlopen(req, timeout=60) as r:
        return [d['embedding'] for d in json.loads(r.read())['data']]

embs = embed_batch(chunks)

db = lancedb.connect(f'{KB_PATH}/knowledge_db')
schema = pa.schema([
    pa.field('text', pa.string()), pa.field('source', pa.string()),
    pa.field('chunk_index', pa.int32()), pa.field('vector', pa.list_(pa.float32(), 1536))])
tbl = db.create_table('nome_da_colecao', schema=schema)
tbl.add([{'text': c, 'source': 'arquivo.md', 'chunk_index': i, 'vector': e}
         for i, (c, e) in enumerate(zip(chunks, embs))])
print(f'Inseridos {len(chunks)} chunks')
```

### Armadilha
`db.create_table()` **não aceita** dicionário Python como schema. Precisa usar `pa.schema([...])` com `pa.field()`.

### Verificar Tabelas Existentes
```python
db = lancedb.connect('knowledge_db')
print(db.list_tables())
```

---

## Otimização de Cota

- Z-Library: 10 livros/dia por conta
- Embeddings: ~$0.00002 por 1K tokens (text-embedding-3-small é barato)
- Cron job sugerido: download diário às 6h → vetorização automática