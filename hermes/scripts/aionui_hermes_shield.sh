#!/bin/bash
#===============================================================================
# AIONUI HERMES BACKEND SHIELD
# Blindagem para garantir que o Hermes aparece sempre no Teams do AionUI
#===============================================================================
# Este script verifica e re-aplica a modificação do KNOWN_TEAM_CAPABLE_BACKENDS
# para garantir que o Hermes aparece como opção de Team Leader.
#
# USO:
#   ./aionui_hermes_shield.sh --apply    (aplica a modificação)
#   ./aionui_hermes_shield.sh --verify  (verifica se está aplicada)
#   ./aionui_hermes_shield.sh --watch    (monitorização contínua)
#===============================================================================

set -e

AIONUI_APP="/Applications/AionUI.app"
APP_ASAR="${AIONUI_APP}/Contents/Resources/app.asar"
APP_ASAR_UNPACKED="${AIONUI_APP}/Contents/Resources/app.asar.unpacked"
INDEX_JS="${APP_ASAR_UNPACKED}/out/main/index.js"
BACKUP_DIR="${HOME}/.hermes/backups/aionui_hermes_shield"
LOCK_FILE="${HOME}/.hermes/locks/aionui_hermes_shield.lock"

# ANSI colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log_info() { echo -e "${BLUE}[INFO]${NC} $*"; }
log_success() { echo -e "${GREEN}[OK]${NC} $*"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $*"; }
log_error() { echo -e "${RED}[ERROR]${NC} $*"; }

#===============================================================================
# FUNÇÕES AUXILIARES
#===============================================================================

acquire_lock() {
    mkdir -p "$(dirname "$LOCK_FILE")" 2>/dev/null || true
    if [ -f "$LOCK_FILE" ]; then
        local pid=$(cat "$LOCK_FILE" 2>/dev/null)
        if [ -n "$pid" ] && kill -0 "$pid" 2>/dev/null; then
            log_error "Já existe uma instância a correr (PID: $pid)"
            exit 1
        fi
        log_warn "Lock file antigo encontrado, a limpar..."
    fi
    echo $$ > "$LOCK_FILE"
}

release_lock() {
    rm -f "$LOCK_FILE" 2>/dev/null || true
}

create_backup() {
    mkdir -p "$BACKUP_DIR"
    local backup_file="${BACKUP_DIR}/app.asar.backup.$(date +%Y%m%d_%H%M%S)"
    cp "$APP_ASAR" "$backup_file"
    log_success "Backup criado: $backup_file"
}

#===============================================================================
# VERIFICAÇÃO
#===============================================================================

verify_hermes_in_known_backends() {
    if [ ! -f "$INDEX_JS" ]; then
        log_error "Ficheiro index.js não encontrado: $INDEX_JS"
        log_error "Execute --unpack primeiro para extrair o app.asar"
        return 1
    fi

    # Verificar se hermes está no KNOWN_TEAM_CAPABLE_BACKENDS
    if grep -q 'KNOWN_TEAM_CAPABLE_BACKENDS.*hermes' "$INDEX_JS"; then
        log_success "Hermes JÁ está em KNOWN_TEAM_CAPABLE_BACKENDS"
        return 0
    else
        log_warn "Hermes NÃO está em KNOWN_TEAM_CAPABLE_BACKENDS"
        return 1
    fi
}

#===============================================================================
# UNPACK DO APP.ASAR
#===============================================================================

unpack_app_asar() {
    if [ -d "$APP_ASAR_UNPACKED" ]; then
        log_info "app.asar.unpacked já existe"
        return 0
    fi

    log_info "A extrair app.asar..."
    cd "${AIONUI_APP}/Contents/Resources"
    npx asar extract app.asar app.asar.unpacked
    log_success "app.asar.extraído para app.asar.unpacked"
}

#===============================================================================
# APLICAÇÃO DA MODIFICAÇÃO
#===============================================================================

apply_hermes_backend_fix() {
    log_info "A aplicar modificação do KNOWN_TEAM_CAPABLE_BACKENDS..."

    if [ ! -f "$INDEX_JS" ]; then
        log_error "index.js não encontrado. Execute --unpack primeiro."
        return 1
    fi

    # Criar backup antes de modificar
    create_backup

    # Verificar se "hermes" já está na lista
    if grep -q 'KNOWN_TEAM_CAPABLE_BACKENDS.*"hermes"' "$INDEX_JS"; then
        log_success "Hermes já está presente, nada a fazer"
        return 0
    fi

    # Modificar a linha KNOWN_TEAM_CAPABLE_BACKENDS para incluir "hermes"
    # Padrão atual: new Set(["gemini", "claude", "codex", "aionrs"])
    # Novo padrão: new Set(["gemini", "claude", "codex", "aionrs", "hermes"])

    sed -i '' 's/\["gemini", "claude", "codex", "aionrs"\]/["gemini", "claude", "codex", "aionrs", "hermes"]/g' "$INDEX_JS"

    # Verificar se a modificação foi aplicada
    if grep -q 'KNOWN_TEAM_CAPABLE_BACKENDS.*"hermes"' "$INDEX_JS"; then
        log_success "Modificação aplicada com sucesso!"

        # Re-embrulhar o app.asar
        repack_app_asar
        return 0
    else
        log_error "Falha ao aplicar modificação"
        return 1
    fi
}

#===============================================================================
# RE-EMPACOTAMENTO DO APP.ASAR
#===============================================================================

repack_app_asar() {
    log_info "A re-embrulhar app.asar..."

    cd "${AIONUI_APP}/Contents/Resources"

    # Fazer backup do app.asar original
    cp app.asar app.asar.original 2>/dev/null || true

    # Criar novo app.asar com as modificações
    npx asar pack app.asar.unpacked app.asar.new

    # Substituir o app.asar original
    mv app.asar.new app.asar

    log_success "app.asar actualizado!"

    log_warn "NOTA: Para aplicar as alterações, reinicie o AionUI"
}

#===============================================================================
# MONITORIZAÇÃO CONTÍNUA
#===============================================================================

watch_mode() {
    log_info "A iniciar modo de monitorização (CTRL+C para parar)..."
    acquire_lock

    while true; do
        if ! verify_hermes_in_known_backends > /dev/null 2>&1; then
            log_warn "Hermes desapareceu do Teams! A re-aplicar..."
            unpack_app_asar
            apply_hermes_backend_fix
            log_success "Protecção activada"
        fi
        sleep 60  # Verificar a cada minuto
    done
}

#===============================================================================
# HELP
#===============================================================================

show_help() {
    echo "AionUI Hermes Backend Shield v1.0"
    echo ""
    echo "Blindagem para garantir que o Hermes aparece no Teams do AionUI"
    echo ""
    echo "USO:"
    echo "  $0 --unpack           Extrair app.asar para modificação"
    echo "  $0 --apply            Aplicar/modificar KNOWN_TEAM_CAPABLE_BACKENDS"
    echo "  $0 --verify           Verificar se Hermes está protegido"
    echo "  $0 --watch            Modo de monitorização contínua"
    echo "  $0 --restore          Restaurar app.asar do backup"
    echo "  $0 --help             Mostrar esta ajuda"
    echo ""
}

#===============================================================================
# MAIN
#===============================================================================

main() {
    case "${1:-}" in
        --unpack)
            unpack_app_asar
            ;;
        --apply)
            unpack_app_asar
            apply_hermes_backend_fix
            ;;
        --verify)
            if ! verify_hermes_in_known_backends; then
                log_error "Hermes NÃO está protegido!"
                exit 1
            fi
            ;;
        --watch)
            verify_hermes_in_known_backends || {
                log_info "A aplicar protecção inicial..."
                unpack_app_asar
                apply_hermes_backend_fix
            }
            watch_mode
            ;;
        --restore)
            if [ -d "$BACKUP_DIR" ]; then
                latest=$(ls -t "$BACKUP_DIR" | head -1)
                if [ -n "$latest" ]; then
                    cp "${BACKUP_DIR}/${latest}" "$APP_ASAR"
                    log_success "Restaurado: ${BACKUP_DIR}/${latest}"
                fi
            else
                log_error "Não há backups para restaurar"
                exit 1
            fi
            ;;
        --help|-h|*)
            show_help
            ;;
    esac
}

main "$@"
