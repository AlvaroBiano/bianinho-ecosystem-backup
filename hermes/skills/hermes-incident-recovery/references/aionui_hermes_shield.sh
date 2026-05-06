#!/bin/bash
#===============================================================================
# AIONUI HERMES BACKEND SHIELD
# Blindagem para garantir que o Hermes aparece sempre no Teams do AionUI
#===============================================================================
set -e

AIONUI_APP="/Applications/AionUI.app"
APP_ASAR="${AIONUI_APP}/Contents/Resources/app.asar"
APP_ASAR_UNPACKED="${AIONUI_APP}/Contents/Resources/app.asar.unpacked"
INDEX_JS="${APP_ASAR_UNPACKED}/out/main/index.js"
BACKUP_DIR="${HOME}/.hermes/backups/aionui_hermes_shield"
LOCK_FILE="${HOME}/.hermes/locks/aionui_hermes_shield.lock"

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; BLUE='\033[0;34m'; NC='\033[0m'
log_info() { echo -e "${BLUE}[INFO]${NC} $*"; }
log_success() { echo -e "${GREEN}[OK]${NC} $*"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $*"; }
log_error() { echo -e "${RED}[ERROR]${NC} $*"; }

acquire_lock() {
    mkdir -p "$(dirname "$LOCK_FILE")" 2>/dev/null || true
    if [ -f "$LOCK_FILE" ]; then
        local pid=$(cat "$LOCK_FILE" 2>/dev/null)
        if [ -n "$pid" ] && kill -0 "$pid" 2>/dev/null; then
            log_error "Já existe uma instância a correr (PID: $pid)"; exit 1
        fi
    fi
    echo $$ > "$LOCK_FILE"
}

create_backup() {
    mkdir -p "$BACKUP_DIR"
    cp "$APP_ASAR" "${BACKUP_DIR}/app.asar.backup.$(date +%Y%m%d_%H%M%S)"
    log_success "Backup criado"
}

unpack_app_asar() {
    [ -d "$APP_ASAR_UNPACKED" ] && return 0
    log_info "A extrair app.asar..."
    cd "${AIONUI_APP}/Contents/Resources"
    npx asar extract app.asar app.asar.unpacked
    log_success "app.asar.extraído"
}

apply_hermes_backend_fix() {
    log_info "A aplicar modificação..."

    [ ! -f "$INDEX_JS" ] && { log_error "index.js não encontrado. Execute --unpack primeiro."; return 1; }

    create_backup

    if grep -q 'KNOWN_TEAM_CAPABLE_BACKENDS.*"hermes"' "$INDEX_JS"; then
        log_success "Hermes já está presente"; return 0
    fi

    sed -i '' 's/\["gemini", "claude", "codex", "aionrs"\]/["gemini", "claude", "codex", "aionrs", "hermes"]/g' "$INDEX_JS"

    if grep -q 'KNOWN_TEAM_CAPABLE_BACKENDS.*"hermes"' "$INDEX_JS"; then
        log_success "Modificação aplicada!"
        cd "${AIONUI_APP}/Contents/Resources"
        cp app.asar app.asar.original 2>/dev/null || true
        npx asar pack app.asar.unpacked app.asar
        log_success "app.asar actualizado!"
        log_warn "NOTA: Reinicie o AionUI para aplicar"
    else
        log_error "Falha ao aplicar modificação"; return 1
    fi
}

verify_hermes() {
    [ ! -f "$INDEX_JS" ] && { log_error "index.js não encontrado"; return 1; }
    grep -q 'KNOWN_TEAM_CAPABLE_BACKENDS.*hermes' "$INDEX_JS" && log_success "Hermes JÁ está em KNOWN_TEAM_CAPABLE_BACKENDS" || log_warn "Hermes NÃO está"
}

show_help() {
    echo "AionUI Hermes Backend Shield v1.0"
    echo "USO: $0 --unpack|--apply|--verify|--watch|--help"
}

case "${1:-}" in
    --unpack) unpack_app_asar ;;
    --apply) unpack_app_asar; apply_hermes_backend_fix ;;
    --verify) verify_hermes ;;
    --watch)
        verify_hermes || { log_info "A aplicar protecção..."; unpack_app_asar; apply_hermes_backend_fix; }
        acquire_lock
        while true; do
            if ! verify_hermes > /dev/null 2>&1; then
                log_warn "Hermes desapareceu! A re-aplicar..."
                unpack_app_asar; apply_hermes_backend_fix
            fi
            sleep 60
        done ;;
    --help|-h) show_help ;;
    *) show_help ;;
esac
