# Estruturas EPUB Encontradas — Bianinho

Inventário das variações de estrutura interna de ficheiros EPUB (ZIP) processados pelo Bianinho. Actualizado: 30/04/2026.

---

## Padrão 1 — `OEBPS/xhtml/` (mais comum)

Estrutura com directoria `xhtml/` dentro de `OEBPS/`. Cada capítulo é um ficheiro separado.

```
EPUB/
├── META-INF/
├── mimetype
├── OEBPS/
│   ├── content.opf
│   ├── toc.ncx
│   ├── stylesheet.css
│   ├── fonts/
│   ├── images/
│   └── xhtml/
│       ├── 01_Cover.xhtml
│       ├── 02_Title_Page.xhtml
│       ├── 03_Copyright.xhtml
│       ├── 06_Introduction.xhtml
│       ├── 07_PART_I_THE_FIRST_FIVE.xhtml
│       ├── 08_Chapter_1_Control_How.xhtml
│       ├── 09_Chapter_2_Capture_How.xhtml
│       └── ...
```

**Como extrair:**
```python
base = '/tmp/book_extract/OEBPS/xhtml'
for fname in sorted(os.listdir(base)):
    if fname.endswith('.xhtml'):
        # ... processar
```

**Livros detectados:** Captivate (Vanessa Van Edwards)

---

## Padrão 2 — `OEBPS/` plano (sem xhtml/)

Directoria `OEBPS/` contém os XHTMLs directamente, sem subdirectoria. Ficheiros tipicamente nomeados `part0000.xhtml`, `part0001.xhtml`, etc.

```
EPUB/
├── META-INF/
├── mimetype
├── OEBPS/
│   ├── content.opf
│   ├── ncx.ncx
│   ├── base.css
│   ├── c001.xhtml
│   ├── c002.xhtml
│   └── ...
```

**Como extrair:**
```python
base = '/tmp/book_extract/OEBPS'
for fname in sorted(os.listdir(base)):
    if fname.endswith('.xhtml') or fname.endswith('.html'):
        # ... processar
```

**Livros detectados:** NLP Secrets

---

## Padrão 3 — `OEBPS/Text/` (subdirectoria Text)

Directoria `OEBPS/` tem uma subdirectoria `Text/` que contém os capítulos. Ficheiros nomeados `part0000.xhtml` a `part0037.xhtml`.

```
EPUB/
├── META-INF/
├── mimetype
├── OEBPS/
│   ├── Text/
│   │   ├── cover_page.xhtml
│   │   ├── part0000.xhtml
│   │   ├── part0001.xhtml
│   │   └── ...
│   ├── toc.ncx
│   └── content.opf
```

**Como extrair:**
```python
base = '/tmp/book_extract/OEBPS/Text'
for fname in sorted(os.listdir(base)):
    if fname.endswith('.xhtml') or fname.endswith('.html'):
        # ... processar
```

**Livros detectados:** Millionaire Mindset

---

## Código Genérico de Detecção Automática

```python
import re, os

def extract_epub_from_zip(zip_path, output_txt):
    import zipfile, shutil
    
    extract_dir = f'/tmp/{os.path.basename(zip_path)}_extract'
    if os.path.exists(extract_dir):
        shutil.rmtree(extract_dir)
    os.makedirs(extract_dir)
    
    with zipfile.ZipFile(zip_path, 'r') as z:
        z.extractall(extract_dir)
    
    # Detectar estrutura
    texts = []
    
    # Padrão 1: OEBPS/xhtml/
    xhtml_dir = os.path.join(extract_dir, 'OEBPS', 'xhtml')
    if os.path.exists(xhtml_dir):
        base = xhtml_dir
    else:
        # Padrão 2: OEBPS/ directo (procurar primeiro .xhtml)
        oebps_dir = os.path.join(extract_dir, 'OEBPS')
        if os.path.exists(oebps_dir):
            xhtmls = [f for f in os.listdir(oebps_dir) if f.endswith('.xhtml')]
            if xhtmls:
                base = oebps_dir
            else:
                # Padrão 3: OEBPS/Text/
                text_dir = os.path.join(oebps_dir, 'Text')
                if os.path.exists(text_dir):
                    base = text_dir
                else:
                    raise ValueError(f"Estrutura EPUB desconhecida em {zip_path}")
        else:
            raise ValueError(f"Directoria OEBPS não encontrada em {zip_path}")
    
    for fname in sorted(os.listdir(base)):
        if not (fname.endswith('.xhtml') or fname.endswith('.html')):
            continue
        with open(os.path.join(base, fname), 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        text = re.sub(r'<[^>]+>', ' ', content)
        text = re.sub(r'\s+', ' ', text).strip()
        if len(text) > 50:
            texts.append(f"=== {fname} ===\n{text}")
    
    combined = '\n\n'.join(texts)
    with open(output_txt, 'w', encoding='utf-8') as f:
        f.write(combined)
    
    return len(combined), len(texts)
```

---

## Nota de Fiabilidade

O pipeline `livro_pipeline.py` do `rag-book-processor` usa `ebooklib` para EPUB directos. Para ZIPs (EPUB renomeados pelo utilizador), a extracção manual via `unzip` + regex é o método correcto, porque ebooklib não funciona com ficheiros renomeados para .zip.

A detecção da estrutura correcta é feita por tentativa: procura-se `OEBPS/xhtml/` → senão, `OEBPS/*.xhtml` directo → senão, `OEBPS/Text/*.xhtml`.
