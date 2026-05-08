RAG: ~/Library/Application Support/hermes/KnowledgeBase/ — 1.9GB, 80k+ chunks. Embedding: OpenAI text-embedding-3-small via OpenRouter. LLM: MiniMax M2.7. PRD: ~/PRD_RAG_Arquitetura.md. Servidor offline (07/05). Copia local MacBook completa. Template PDF AZUL-VERDE: ~/.hermes/templates/scientific_report_template.html + skill ~/.hermes/skills/scientific-report-template/SKILL.md. Placeholders: {TITULO}, {DATA}, {SECTIONS_HTML}. Chrome: --print-to-pdf=$HOME/Documents/NOME.pdf. Pendente: adicionar facts template ao RAG quando servidor voltar.
§
AionUI v1.9.25. baseUrl corrigido para api.minimax.io. Config: ~/Library/Application Support/AionUi/config/aionui-config.txt. BD: aionui.db.
§
Cron sistema (crontab): team_leader */5min | cycle */15min | self_improving */6h | image */10min. Hermes jobs: 2ef7a80293de | 86098826da70 | 72ec656e69bd.
§
BACKUP EXTERNO (pendente — Álvaro vai plugar HD): Backup total: KnowledgeBase (~1.9GB) + sessions + videos + BD AionUI + .env real + ~/.hermes/ completo. Ver skill bianinho-sessao-05052026. Sem cron. Álvaro avisa quando HD pronto.
§
Cripto: crypto_signal_alert.py (5min, job 2ef7a80293de) + binance_sniper_alert.py (1h, job 86098826da70). Token Telegram: @AleteiaClaw_bot (8109921192:AAHc_kzlkMNPSXahkSmOq8jSnUoV_xv1MtY), chat 435025823. Álvaro NÃO quer alertas no chat com Bianinho — só no chat com @AleteiaClaw_bot. NajjaBot (851678... do .env) não funciona em chamadas API directas.
§
Sessão 07/05/2026 12:25-13:00: Relatório fibromialgia PDF ~/Documents/FIBROMIALGIA_Relatorio_Cientifico_2026-05-07.pdf. Template PDF científico AZUL-VERDE: ~/.hermes/templates/scientific_report_template.html + skill scientific-report-template. Álvaro: continuidade Telegram↔AionUI — memory partilhada, contexto sessão precisa consolidar com End-of-Session Trust Protocol.
§
Context-Aware Delegation v2.0 implementado (07/05/2026): Context Switch Optimizer (Jaccard), Contextual Recall (10 domínios), Morning Briefing cron (8h seg-sex, job 467545072028), Context Monitor cron (15min, job 958d737a7ecd). Scripts: context_morning_briefing.py, context_monitor.py. AionUI tasks: cron_d92c5871, cron_2e14f348.