---
name: image-generation-pipeline
description: Cron-based image generation pipeline with MiniMax API — rotating themes, consistent style, format post-processing
---
# Image Generation Pipeline

Sistema de geração automática de imagens via cron com a API MiniMax `image-01`, mantendo estilo visual consistente e alternando formatos/formato.

## Arquivos

- `~/.hermes/scripts/image_generator.py` — Script principal
- `~/.hermes/scripts/themes.json` — Lista de temas rotating
- `~/.hermes/scripts/.image_generator_state.json` — Estado (índice do tema atual, último formato usado)
- `~/Images/generated/youtube/YYYY-MM-DD/` — Thumbnails YouTube (1920×1080)
- `~/Images/generated/instagram/YYYY-MM-DD/` — Posts Instagram (1080×1080)

## Como funciona

1. Carrega próximo tema da lista (round-robin)
2. Alterna formato: YouTube → Instagram → YouTube → ...
3. Monta prompt com **Style Lock** (descritores visuais fixos) + tema variável
4. Chama API MiniMax `image-01` (sempre retorna 1024×1024)
5. **Post-processing**: crop/resize Pillow para formato correto
6. Salva com timestamp

## Style Lock

O SEGREDO da consistência visual — mesmo prompt base para todas as imagens:

```python
STYLE_LOCK = (
    "Photorealistic photography, maximum detail, 8K resolution, cinematic lighting, "
    "shallow depth of field, professional color grading, Canon EOS R5, 85mm lens, f/1.8 aperture, "
    "natural textures, volumetric lighting, desaturated shadows, warm highlights, "
    "anamorphic lens flare, studio lighting setup, clean background with subtle gradient, "
    "high dynamic range, sharp focus, professional retouching"
)
```

## Executar manualmente

```bash
python3 ~/.hermes/scripts/image_generator.py
```

## Cron

```cron
*/10 * * * * python3 ~/.hermes/scripts/image_generator.py >> ~/.hermes/logs/image_generator.log 2>&1
```

## Editar temas

Editar `~/.hermes/scripts/themes.json`:

```json
[
  {"name": "Nome do Tema", "description": "Descrição visual para o prompt"}
]
```

## Troubleshooting

### Imagem com texto indesejado
Adicionar NO TEXT explícito no prompt:
```
"NO TEXT, NO WORDS, NO LETTERS, NO NUMBERS. Pure visual composition only."
```

### Formato errado
A API sempre retorna 1024×1024. O script faz crop/resize via Pillow:
- YouTube: crop centro de 1024×1024 para 16:9 (1024×576) → resize para 1920×1080
- Instagram: resize 1024×1024 para 1080×1080

### SSL errors no macOS
Python 3.14 no macOS tem issues com `urllib.request`. O script usa `curl` como subprocess.

## API Key

Lê automaticamente de `~/.hermes/.env` (variável `MINIMAX_API_KEY`).

## Limites

- 50 imagens/dia (quota MiniMax image-01)
- Com cron de 10min = máximo 144 execuções/dia (vai estourar quota rapidamente)
- Considerar aumentar intervalo do cron para 30-60min se usar muito
