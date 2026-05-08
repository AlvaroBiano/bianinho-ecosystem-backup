---
name: bianinho-sessao-07052026
description: Estado da sessão Bianinho — 07 de maio de 2026, 03:30AM. Importante para contexto antes de restart.
---

# Estado da Sessão — 07/05/2026 03:30AM

## Crons Alterados
- `team_leader_session_bridge.py`: `*/2` → `*/5` min (system crontab)

## Servidor Linux
- DESLIGADO desde 07/05/2026. Cópia local completa no MacBook.
- Pendente: ligar servidor → sincronizar KnowledgeBase
- SSH: alvarobiano@100.79.189.95 (TailScale)

## MacBook Performance
- Load: 9.61 | Swap: 4.6/6GB (75%) | RAM: 16GB
- Uptime: 5 dias
- Recomendação: reboot + reduzir login items (SetappAgent, Canva agent, Google keystone, Steam)
- Login items ativos: 13 (muito)

## RAG
- Cópia local: ~/Library/Application Support/hermes/KnowledgeBase/ (1.9GB)
- embedding: OpenAI text-embedding-3-small via OpenRouter, 1536 dim
- LLM: MiniMax M2.7
- PRD: ~/PRD_RAG_Arquitetura.md
- futures_trading_kyle_august.txt EM books/ — NUNCA vectorizado
- Servidor offline → vectorização pendente

## Cripto
- Scripts ativos: crypto_signal_alert.py (5min) + binance_sniper_alert.py (1h)
- Hermes jobs: 2ef7a80293de | 86098826da70 | 72ec656e69bd
- Filtros: score>=95, RSI 50-75, DD 0-6%, Vol 3x+
- news: ~/Library/Application Support/hermes/scripts/cripto_news.py
- status: ~/Library/Application Support/hermes/scripts/cripto_status.py
- multi_ticker: ~/Library/Application Support/hermes/scripts/cripto_multi_ticker.py

## AionUI
- v1.9.25, baseUrl corrigido para api.minimax.io
- Config: ~/Library/Application Support/AionUi/config/aionui-config.txt

## Transcrição CURSO APC
- M6 completo (104 ficheiros)
- M7+M8 pendentes
- Local: ~/Movies/CURSO APC/

## Backup HD Externo
- Pendente — Álvaro vai plugar HD e avisa
- items: KnowledgeBase + sessions + videos + BD AionUI + .env + ~/.hermes/

## Pendências Prioritárias
1. Reboot MacBook (performance)
2. Ligar servidor Linux e sincronizar RAG
3. Vectorizar futures_trading_kyle_august.txt
4. Reduzir login items
5. Backup HD externo
