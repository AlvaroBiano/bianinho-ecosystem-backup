# EPUB como ZIP — Workflow Completo

## Problema

Telegram/Hermes rejeita uploads de `.epub` → utilizador renomeia o ficheiro para `.zip` antes de enviar. O pipeline rejeita `.zip`.

## Regra Crítica (01/05/2026)

**NUNCA renomear o ficheiro para `.epub`.** EPUB que chega como `.zip` → extrair conteúdo → converter para `.txt` → pipeline.

**`ebook-convert` (Calibre) NÃO existe no servidor e não pode ser instalado.** Usar sempre o método Python abaixo.

## Detecção

```bash
unzip -l ficheiro.zip | head -5
```
Se contém `OEBPS/`, `mimetype`, `META-INF/` → é EPUB.

## Workflow Completo

### Passo 1 — Copiar para /tmp via bytes

```python
import glob
src = glob.glob('/home/alvarobiano/.hermes/cache/documents/doc_<hash>*')[0]
with open(src, 'rb') as f:
    data = f.read()
with open('/tmp/book_name.epub', 'wb') as f:
    f.write(data)
print(f'{len(data)} bytes')
```

### Passo 2 — Extrair EPUB para TXT (usar OPF spine — ordem correcta)

⚠️ **ERRO CRÍTICO:** Nunca usar `sorted(os.listdir())`. Isso põe "Chapter 10" antes de "Chapter 2" alfabeticamente. **Usar sempre o OPF spine.**

```python
import zipfile, xml.etree.ElementTree as ET, re, os

epub_path = '/tmp/book_name.epub'   # INPUT
txt_path = '/tmp/book_name.txt'      # OUTPUT

ns = {'opf': 'http://www.idpf.org/2007/opf',
      'dc':  'http://purl.org/dc/elements/1.1/'}

with zipfile.ZipFile(epub_path, 'r') as z:
    # 1. Achar o OPF
    opf_files = [f for f in z.namelist() if f.endswith('.opf')]
    opf_path  = opf_files[0]
    opf_dir   = os.path.dirname(opf_path)
    opf_root  = ET.fromstring(z.read(opf_path))

    # 2. Título
    title = opf_root.find('.//dc:title', ns)
    title_text = title.text if title is not None else 'Unknown'

    # 3. Mapa id → (href, media_type)
    manifest = opf_root.find('opf:manifest', ns)
    item_by_id = {item.get('id'): (item.get('href'), item.get('media-type'))
                  for item in manifest.findall('opf:item', ns) if item.get('href')}

    # 4. SPINE — ordem de leitura (não alfabética)
    spine = opf_root.find('opf:spine', ns)
    reading_order = [item_by_id[ir.get('idref')]
                     for ir in spine.findall('opf:itemref', ns)
                     if ir.get('idref') in item_by_id]

    # 5. Extrair texto na ordem do spine
    all_text = []
    for href, media_type in reading_order:
        if 'html' in (media_type or '') or 'xhtml' in (media_type or ''):
            fp = os.path.join(opf_dir, href).lstrip('/')
            try:
                root = ET.fromstring(z.read(fp))
            except ET.ParseError:  # mal-formed XML → envolver
                try:
                    root = ET.fromstring(z.read(fp) + b'</html>')
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

    result = f'TÍTULO: {title_text}\n\n' + '\n\n'.join(all_text)
    with open(txt_path, 'w', encoding='utf-8') as f:
        f.write(result)
    print(f'Título: {title_text}')
    print(f'Arquivos: {len(reading_order)}, Texto: {len(result)} chars')
```

### Passo 3 — Processar como TXT

```bash
cd ~/KnowledgeBase && ./venv/bin/python pipeline/livro_pipeline.py \
  --file "/tmp/book_name.txt" --category <categoria> --force
```

## Estruturas EPUB Confirmadas

| Estrutura | Conteúdo | Como processar |
|-----------|----------|---------------|
| `OEBPS/xhtml/*.xhtml` | Capítulos separados | Método OPF spine acima |
| `OEBPS/*.xhtml` | Capítulos no mesmo dir | Método OPF spine acima |
| `OEBPS/content.opf` | Estrutura Calibre | Método OPF spine acima |

## Casos Reais

| Livro | Ficheiro | Chars | Chunks | Categoria | Data |
|-------|----------|-------|--------|-----------|------|
| Como Ouvir as Crianças | EPUB→ZIP | 184.859 | 119 | familia | 01/05/2026 |
| Read People Like a Book (King) | EPUB→ZIP | 257.252 | 97 | comunicacao | 01/05/2026 |
| Master Your Thinking | EPUB→ZIP | 253.040 | 117 | desenvolvimento_pessoal | 01/05/2026 |
| Changing Belief Systems NLP | EPUB→ZIP | 307.124 | 148 | psicologia | 01/05/2026 |

## Checklist

```
□ unzip -l mostra OEBPS/ + mimetype → é EPUB → NÃO renomear
□ Copiar para /tmp via bytes (evita Unicode normalization)
□ Usar OPF spine para ordem — NÃO sorted(os.listdir())
□ Extrair para TXT
□ --force ao pipeline
□ Verificar chunks no banco após processamento
□ Título extraído correctamente (dc:title do OPF)
```
