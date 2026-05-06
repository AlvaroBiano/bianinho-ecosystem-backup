RAG: ~/Library/Application Support/hermes/KnowledgeBase/ — 1.9GB, 80k+ chunks. Queries: ~/.hermes/venv/bin/python. REGRA: Consultar RAG ANTES de criar conteúdo sobre Método TEN.
§
Servidor Linux: alvarobiano@100.79.189.95 (TailScale: alvarobiano-linuxmint.taile2fd75.ts.net). Path servidor: /home/alvarobiano/. MacBook: ~/Library/Application Support/hermes/. Cron sync KB a cada 4h. SSH sem password. Hermes Agent via ACP no AionUI.
§
AionUI Teams MCP: EACCES em ~/.aionui-config/aionui-config.txt — chmod u+w applied (03/05). Verificar pós-updates.
AionUI Scheduled Tasks: painel usa ~/Library/Application Support/AionUi/aionui/aionui.db (tabela cron_jobs). Hermes Cron jobs.json NÃO aparece lá — são sistemas independentes. Para tasks visíveis no painel AionUI: inserir na SQLite com conversation_id válido (ex: 'b6a516ca'). Scripts em ~/.hermes/scripts/.
§
Info Método TEN (do RAG): Psicoterapia não é regulamentada no BR — qualquer pessoa ética pode atuar como terapeuta. Método TEN aberto a TODOS sem necessidade de formação prévia em saúde. 3 Pilares: Não Inferência + Emoção + Técnica. Estrutura: RNL→RE→RCC→RG. Foco: Adulto Saudável + cura de FEBs e MEIs. 40 módulos de formação.
§
Transcrição vídeos: ~/.hermes/venv/bin/python + PYTHONPATH="" + medium/int8/beam=1/vad=True. Videos em ~/Movies/CURSO APC/. Output .txt ao lado do .mp4. user quer respostas curtas — sem "a processar", sem explicação excessiva.
§
§
GERAÇÃO IMAGENS + TEXTO ESTILIZADO (05/05/2026):
- MiniMax API: image_generation endpoint, model=image-01. Output sempre 1024x1024 — usar PIL crop/resize
- Python 3.14 macOS: usar subprocess com curl para chamadas API (evitar urllib)
- Script stylish_text.py: ~/.hermes/scripts/stylish_text.py — 7 estilos (neon, 3d, vintage, outline_glow, gradient, solid_box, mirror)
- Fontes macOS: /System/Library/Fonts/Supplemental/Verdana Bold.ttf. Demo: ~/Desktop/img_test/
- Álvaro gostou: neon, 3d, gradient, outline_glow. Não gostou: mirror (reflexo ocupa espaço)