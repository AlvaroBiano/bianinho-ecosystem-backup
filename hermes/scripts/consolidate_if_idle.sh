#!/bin/bash
# End-of-Session Auto-Consolidate
# Executa o protocolo de fim de sessão automaticamente após 30min de inatividade
# Uso: chmod +x consolidate_if_idle.sh && ./consolidate_if_idle.sh
# Ou via cron: */10 * * * * /Users/alvarobiano/.hermes/scripts/consolidate_if_idle.sh >> /Users/alvarobiano/.hermes/logs/consolidate.log 2>&1

LOG="/Users/alvarobiano/.hermes/logs/consolidate.log"
STATE_FILE="/Users/alvarobiano/.hermes/.last_consolidate"
SESSION_DB="/Users/alvarobiano/Library/Application Support/AionUi/aionui/aionui.db"
IDLE_MINUTES=30

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" >> "$LOG"
}

# Verifica se existe sessão ativa recente na DB do AionUI
get_last_session_activity() {
    if [ -f "$SESSION_DB" ]; then
        # Pega timestamp do último mensaje da sessão mais recente
        LAST_MSG=$(sqlite3 "$SESSION_DB" "SELECT MAX(created_at) FROM messages WHERE type IN ('text', 'user', 'assistant') LIMIT 1;" 2>/dev/null)
        echo "$LAST_MSG"
    fi
}

# Verifica se já consolidamos recentemente (evitar duplicates)
has_recently_consolidated() {
    if [ -f "$STATE_FILE" ]; then
        LAST=$(cat "$STATE_FILE")
        NOW=$(date +%s)
        DIFF=$((NOW - LAST))
        # Se última consolidação foi há menos de 20 min, skip
        if [ $DIFF -lt 1200 ]; then
            echo "yes"
        else
            echo "no"
        fi
    else
        echo "no"
    fi
}

# Marca que consolidamos
mark_consolidated() {
    date +%s > "$STATE_FILE"
}

# Verifica inatividade
is_idle() {
    LAST_ACTIVITY=$(get_last_session_activity)
    if [ -z "$LAST_ACTIVITY" ] || [ "$LAST_ACTIVITY" = "" ]; then
        # Não consegue determinar - verifica por timestamp de ficheiro
        LAST_SESSION_FILE=$(ls -t ~/.hermes/sessions/*.json 2>/dev/null | head -1)
        if [ -f "$LAST_SESSION_FILE" ]; then
            FILE_AGE=$(($(date +%s) - $(stat -f %m "$LAST_SESSION_FILE" 2>/dev/null || stat -c %Y "$LAST_SESSION_FILE" 2>/dev/null)))
            if [ $FILE_AGE -gt $((IDLE_MINUTES * 60)) ]; then
                echo "yes"
            else
                echo "no"
            fi
        else
            echo "no"
        fi
    else
        # Compara timestamps (formato ISO: 2026-05-07T12:30:00)
        ACTIVITY_EPOCH=$(date -j -f "%Y-%m-%dT%H:%M:%S" "$LAST_ACTIVITY" +%s 2>/dev/null)
        if [ -z "$ACTIVITY_EPOCH" ]; then
            echo "no"
        else
            NOW=$(date +%s)
            DIFF=$((NOW - ACTIVITY_EPOCH))
            if [ $DIFF -gt $((IDLE_MINUTES * 60)) ]; then
                echo "yes"
            else
                echo "no"
            fi
        fi
    fi
}

# Atualiza memory HOT com facts da sessão
update_memory() {
    SESSION_SUMMARY=$(ls -t ~/.hermes/sessions/*.json 2>/dev/null | head -1)
    if [ -n "$SESSION_SUMMARY" ] && [ -f "$SESSION_SUMMARY" ]; then
        # Lê fact mais recente da sessão (se existir)
        NEW_FACT=$(python3 -c "
import json, sys
try:
    with open('$SESSION_SUMMARY') as f:
        data = json.load(f)
    # Pega últimos 500 chars do contexto
    if 'messages' in data:
        last_msgs = data['messages'][-3:]
        summary = ' '.join([m.get('content', '')[:100] for m in last_msgs if isinstance(m, dict)])
        print(summary[:200])
except:
    print('')
" 2>/dev/null)
        
        if [ -n "$NEW_FACT" ] && [ ${#NEW_FACT} -gt 20 ]; then
            log "Fact de sessão: $NEW_FACT"
        fi
    fi
}

# Push para git (se existir repo)
push_to_git() {
    CEREBRO_DIR="/Users/alvarobiano/bianinho-cerebro"
    if [ -d "$CEREBRO_DIR/.git" ]; then
        cd "$CEREBRO_DIR" || return
        if git diff --quiet 2>/dev/null; then
            log "Git: sem changes para commit"
        else
            git add -A
            git commit -m "feat: auto-consolidate $(date '+%Y-%m-%d %H:%M')"
            if git push origin main 2>>"$LOG"; then
                log "Git: push OK"
            else
                log "Git: push FALHOU"
            fi
        fi
    else
        log "Git: repo bianinho-cerebro não existe neste máquina"
    fi
}

# ========== MAIN ==========
log "=== Verificando inatividade (limiar: ${IDLE_MINUTES}min) ==="

if [ "$(is_idle)" = "yes" ]; then
    log "Sessão inativa há >${IDLE_MINUTES}min — iniciando consolidate"
    
    if [ "$(has_recently_consolidated)" = "yes" ]; then
        log "Já consolidado recentemente — skip"
        exit 0
    fi
    
    update_memory
    push_to_git
    mark_consolidated
    log "✅ Consolidate completo"
else
    log "Sessão ativa ou recente — skip"
fi
