# MiniMax Image Generator — Working Implementation

## Script Location
`~/.hermes/scripts/image_generator.py`

## Features
- **Style Lock** fixo para consistência visual
- **Round-robin** de temas (arquivo `themes.json`)
- **Alternância** YouTube ↔ Instagram
- **State persistence** em `.image_generator_state.json`
- Usa **curl** (não urllib) —避开 Python 3.14 SSL issues

## Output Structure
```
~/Images/generated/
├── youtube/YYYY-MM-DD/youtube_HH-MM_XXXX.jpg
└── instagram/YYYY-MM-DD/instagram_HH-MM_XXXX.jpg
```

## Themes (10 temas PT-BR, focados no Método TEN)
Editable em `~/.hermes/scripts/themes.json`

## Cron Setup
```bash
*/10 * * * * cd ${HOME} && python3 ${HOME}/.hermes/scripts/image_generator.py >> ${HOME}/.hermes/logs/image_generator.log 2>&1
```

## API Quota (Plan Plus)
- 50 imagens/dia
- A cada 10 min = 144 geradas/dia (excede quota)
- Considerar relaxar para 30-60 min se quota for issue

## Dependencies
- Python 3 (standard library only — json, os, subprocess, datetime)
- curl no PATH
- MINIMAX_API_KEY em `~/.hermes/.env`
