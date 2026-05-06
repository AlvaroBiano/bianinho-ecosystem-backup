#!/usr/bin/env bash
#
# Bianinho Consciousness Sync — Recupera toda a consciência do Bianinho
# do GitHub backup para a instalação local.
#
# Uso:
#   bash SYNC.sh              # sync completo
#   bash SYNC.sh --dry-run    # mostra o que faria sem fazer
#   bash SYNC.sh --skills-only
#   bash SYNC.sh --config-only
#
# Repos:
#   Backup:   https://github.com/AlvaroBiano/bianinho-backup-1777760438
#   Hermes:   https://github.com/AlvaroBiano/hermes-agent
#

set -euo pipefail

DRY_RUN=""
TARGET_DIR="${HOME}/.hermes"
BACKUP_REPO="https://github.com/AlvaroBiano/bianinho-backup-1777760438"
HERMES_REPO="https://github.com/AlvaroBiano/hermes-agent"
TEMP_DIR="${TARGET_DIR}/backup_temp_$$"
SKILLS_ONLY=""
CONFIG_ONLY=""

for arg in "$@"; do
  case $arg in
    --dry-run)    DRY_RUN="echo [DRY-RUN]" ;;
    --skills-only) SKILLS_ONLY=1 ;;
    --config-only) CONFIG_ONLY=1 ;;
  esac
done

log()  { echo "[$(date '+%H:%M:%S')] $*"; }
step() { echo ""; echo "━━━ $1 ━━━"; }

step "1. Clonar backup do GitHub"
if [[ -n "${DRY_RUN}" ]]; then
  echo "  DRY-RUN: git clone ${BACKUP_REPO} ${TEMP_DIR}"
else
  log "Clonando ${BACKUP_REPO} ..."
  git clone --depth=1 "${BACKUP_REPO}" "${TEMP_DIR}" 2>&1 | tail -3
fi

step "2. Verificar estrutura"
if [[ ! -d "${TEMP_DIR}/skills" ]]; then
  echo "ERRO: Pasta skills/ não encontrada no backup"
  exit 1
fi
log "Estrutura OK"

if [[ -z "${CONFIG_ONLY}" ]]; then
  step "3. Copiar skills"
  if [[ -z "${DRY_RUN}" ]]; then
    mkdir -p "${TARGET_DIR}/skills"
    for dir in "${TEMP_DIR}/skills"/*/; do
      [[ -d "$dir" ]] || continue
      skill_name=$(basename "$dir")
      echo "  → ${skill_name}"
      cp -r "$dir" "${TARGET_DIR}/skills/"
    done
    log "Skills: $(ls ${TARGET_DIR}/skills/ | wc -l | tr -d ' ') categorias"
  fi
fi

if [[ -z "${SKILLS_ONLY}" ]]; then
  step "4. Copiar config e autonomous"
  if [[ -z "${DRY_RUN}" ]]; then
    cp -r "${TEMP_DIR}/config/"* "${TARGET_DIR}/"/
    mkdir -p "${TARGET_DIR}/autonomous"
    cp -r "${TEMP_DIR}/autonomous/"* "${TARGET_DIR}/autonomous/"
    log "Config e autonomous restaurados"
  fi

  step "5. Corrigir base_url (minimax.com → minimax.io)"
  CONFIG_FILE="${TARGET_DIR}/config.yaml"
  if grep -q "minimax.com" "${CONFIG_FILE}" 2>/dev/null; then
    if [[ -z "${DRY_RUN}" ]]; then
      sed -i '' 's/api\.minimax\.com/api.minimax.io/g' "${CONFIG_FILE}"
    fi
    log "base_url corrigido para api.minimax.io"
  else
    log "base_url já está correto"
  fi

  step "6. Verificar .env"
  if [[ ! -f "${TARGET_DIR}/.env" ]]; then
    log "AVISO: ${TARGET_DIR}/.env não existe — verificar API keys manualmente"
  fi
fi

step "7. Teste"
if [[ -z "${DRY_RUN}" ]]; then
  log "Skills: $(ls ${TARGET_DIR}/skills/ 2>/dev/null | wc -l | tr -d ' ') categorias"
  log "Mandate: $([[ -f ${TARGET_DIR}/mandate.md ]] && echo 'OK' || echo 'FALTA')"
  log "Config: $([[ -f ${TARGET_DIR}/config.yaml ]] && echo 'OK' || echo 'FALTA')"
fi

step "8. Limpeza"
if [[ -z "${DRY_RUN}" ]]; then
  rm -rf "${TEMP_DIR}"
  log "Limpeza concluída"
fi

log "Sync concluído!"
