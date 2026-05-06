---
name: rtf-to-txt
description: Converter ficheiros RTF para TXT via LibreOffice headless
triggers:
  - ficheiro .rtf
  - documento rtf
---

# RTF to TXT Converter

## Quando usar
Quando o utilizador envia um ficheiro `.rtf` e precisa convertê-lo para `.txt`.

## Método — Python decode (preferido, funciona 100%)

RTFs de Mac/Word guardado como .rtf usam encoding latin-1 com hex codes como \'e9 → é.

```python
python3 - << 'PYEOF'
import re
path = "/caminho/ficheiro.rtf"
with open(path, 'rb') as f:
    content = raw = f.read().decode('latin-1')

def decode_rtf(text):
    def hex_replace(m):
        try:
            return chr(int(m.group(1), 16))
        except:
            return m.group(0)
    text = re.sub(r"\\'([0-9a-fA-F]{2})", hex_replace, text)
    text = re.sub(r'\\[a-z]+-?\d*', '', text)
    text = re.sub(r'\\', '', text)
    text = re.sub(r'[{}\r]', '', text)
    text = re.sub(r'\n+', '\n', text)
    text = re.sub(r' +', ' ', text)
    return text.strip()

plain = decode_rtf(content)
with open('/tmp/rtf_conversions/output.txt', 'w') as f:
    f.write(plain)
print(plain)
PYEOF
```

## Alternativa — lowriter (inconsistente)

```bash
lowriter --headless --convert-to txt --outdir /tmp /caminho/ficheiro.rtf
```

⚠️ lowriter falha em RTFs com hex encoding — usar sempre Python primeiro.

## Passos

1. Receber ficheiro `.rtf` do utilizador
2. Identificar caminho/nome
3. Executar conversão com `lowriter`
4. Verificar resultado com `read_file`
5. Informar utilizador que está pronto
