#!/bin/bash
# Sync KnowledgeBase: servidor Linux → MacBook local
# Agendado: a cada 4 horas via cron

LOG=~/.hermes/logs/kb_sync.log
DEST="/Users/alvarobiano/Library/Application Support/hermes/KnowledgeBase"
SRC="alvarobiano@100.79.189.95:/home/alvarobiano/KnowledgeBase"

mkdir -p ~/.hermes/logs

echo "[$(date)] Início sync KnowledgeBase" >> "$LOG"

rsync -avz --exclude='__pycache__' --exclude='logs' --exclude='.session_bridge' --exclude='sessions' --exclude='reflections' --exclude='.hub' \
  "$SRC/" "$DEST/" >> "$LOG" 2>&1

if [ $? -eq 0 ]; then
  SIZE=$(du -sh "$DEST" | cut -f1)
  echo "[$(date)] ✓ Sync completo — $SIZE" >> "$LOG"
else
  echo "[$(date)] ✗ Erro no sync (código: $?)" >> "$LOG"
fi
