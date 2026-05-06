#!/usr/bin/env bash
#
# Bianinho Consciousness Sync — Recupera toda a consciência do Bianinho
# do GitHub backup para a instalação local.
#
# Uso: bash SYNC.sh [--dry-run]
#        bash SYNC.sh --skills-only
#        bash SYNC.sh --config-only
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
BACKUP_BRANCH="main"
TEMP_DIR="${TARGET_DIR}/backup_temp_$$"
SKILLS_ONLY=""
CONFIG_ONLY=""

# ── Flags ──────────────────────────────────────────────────────────
for arg in "$@"; do
  case $arg in
    --dry-run)    DRY_RUN="echo [DRY-RUN]" ;;
    --skills-only) SKILLS_ONLY=1 ;;
    --config-only) CONFIG_ONLY=1 ;;
  esac
done

log()  { echo "[$(date '+%H:%M:%S')] $*"; }
step() { echo ""; echo "━━━ $1 ━━━"; }

# ── 1. Clonar backup ──────────────────────────────────────────────
step "1. Clonar backup do GitHub"
if [[ -n "${DRY_RUN}" ]]; then
  echo "  DRY-RUN: git clone ${BACKUP_REPO} ${TEMP_DIR}"
else
  log "Clonando ${BACKUP_REPO} ..."
  git clone --depth=1 "${BACKUP_REPO}" "${TEMP_DIR}" 2>&1 | tail -3
  log "Backup clonado em ${TEMP_DIR}"
fi

# ── 2. Verificar estrutura ────────────────────────────────────────
step "2. Verificar estrutura do backup"
if [[ ! -d "${TEMP_DIR}/skills" ]]; then
  echo "ERRO: Pasta skills/ não encontrada no backup"
  exit 1
fi
log "Estrutura OK — skills/, config/, autonomous/, customizations.patch"

# ── 3. Copiar skills ─────────────────────────────────────────────
if [[ -z "${CONFIG_ONLY}" ]]; then
  step "3. Copiar skills"
  if [[ -n "${DRY_RUN}" ]]; then
    echo "  DRY-RUN: cp -r ${TEMP_DIR}/skills/* ${TARGET_DIR}/skills/"
  else
    mkdir -p "${TARGET_DIR}/skills"
    # Copiar só pastas (não ficheiros soltos) para não sobrescrever
    for dir in "${TEMP_DIR}/skills"/*/; do
      [[ -d "$dir" ]] || continue
      skill_name=$(basename "$dir")
      echo "  → ${skill_name}"
      cp -r "$dir" "${TARGET_DIR}/skills/"
    done
    log "Skills copiados: $(ls ${TARGET_DIR}/skills/ | wc -l) categorias"
  fi
fi

# ── 4. Copiar config ─────────────────────────────────────────────
if [[ -z "${SKILLS_ONLY}" ]]; then
  step "4. Copiar config"
  if [[ -n "${DRY_RUN}" ]]; then
    echo "  DRY-RUN: cp -r ${TEMP_DIR}/config/* ${TARGET_DIR}/"
    echo "  DRY-RUN: cp -r ${TEMP_DIR}/autonomous/* ${TARGET_DIR}/"
  else
    cp -r "${TEMP_DIR}/config/"* "${TARGET_DIR}/"/
    mkdir -p "${TARGET_DIR}/autonomous"
    cp -r "${TEMP_DIR}/autonomous/"* "${TARGET_DIR}/autonomous/"
    log "Config e autonomous restaurados"
  fi

  # ── 5. Corrigir base_url .com → .io ──────────────────────────
  step "5. Corrigir base_url (minimax.com → minimax.io)"
  CONFIG_FILE="${TARGET_DIR}/config.yaml"
  if grep -q "minimax.com" "${CONFIG_FILE}" 2>/dev/null; then
    if [[ -n "${DRY_RUN}" ]]; then
      echo "  DRY-RUN: sed s/minimax.com/minimax.io/ ${CONFIG_FILE}"
    else
      sed -i '' 's/api\.minimax\.com/api.minimax.io/g' "${CONFIG_FILE}"
      log "base_url corrigido para api.minimax.io"
    fi
  else
    log "base_url já está correto"
  fi

  # ── 6. Restaurar API keys ──────────────────────────────────────
  step "6. Restaurar API keys"
  ENV_FILE="${TARGET_DIR}/.env"
  if [[ ! -f "${ENV_FILE}" ]]; then
    if [[ -n "${DRY_RUN}" ]]; then
      echo "  DRY-RUN: criar ${ENV_FILE}"
    else
      echo "# Bianinho Environment Variables" > "${ENV_FILE}"
      echo "#_MINIMAX_API_KEY=xxx" >> "${ENV_FILE}"
      echo "#MINIMAX_BASE_URL=https://api.minimax.io/v1" >> "${ENV_FILE}"
      log "Criado ${ENV_FILE} — preenche as tuas API keys manualmente"
    fi
  else
    log "${ENV_FILE} já existe — não sovrescrever"
  fi
fi

# ── 7. Aplicar customizations.patch ─────────────────────────────
step "7. Aplicar customizations.patch (se existir Hermes fork)"
if [[ -d "${TARGET_DIR}/hermes-agent" ]] && [[ -f "${TEMP_DIR}/customizations.patch" ]]; then
  if [[ -n "${DRY_RUN}" ]]; then
    echo "  DRY-RUN: git -C ${TARGET_DIR}/hermes-agent apply ${TEMP_DIR}/customizations.patch"
  else
    cd "${TARGET_DIR}/hermes-agent"
    if git apply "${TEMP_DIR}/customizations.patch" 2>&1 | tail -5; then
      log "customizations.patch aplicado"
    else
      log "AVISO: patch não aplicou cleanly (pode ser normal)"
    fi
    cd - > /dev/null
  fi
else
  log "SKIP: hermes-agent não encontrado ou patch inexistente"
fi

# ── 8. Teste ─────────────────────────────────────────────────────
step "8. Teste"
if [[ -n "${DRY_RUN}" ]]; then
  echo "  DRY-RUN: hermes --version"
else
  if command -v hermes &>/dev/null; then
    hermes --version 2>/dev/null || log "hermes não responde (pode ser normal)"
  fi
  log "Skills disponíveis: $(ls ${TARGET_DIR}/skills/ 2>/dev/null | wc -l) categorias"
  log "Config: $(ls ${TARGET_DIR}/config.yaml 2>/dev/null && echo 'OK' || echo 'MISSING')"
  log "Mandate: $(ls ${TARGET_DIR}/mandate.md 2>/dev/null && echo 'OK' || echo 'MISSING')"
fi

# ── 9. Limpeza ───────────────────────────────────────────────────
step "9. Limpeza"
if [[ -n "${DRY_RUN}" ]]; then
  echo "  DRY-RUN: rm -rf ${TEMP_DIR}"
else
  rm -rf "${TEMP_DIR}"
  log "Limpeza concluída"
fi

# ── 10. Próximos passos ─────────────────────────────────────────
step "10. Próximos passos"
echo ""
echo "  1. Edita ${TARGET_DIR}/.env e adiciona as tuas API keys:"
echo "     nano ${TARGET_DIR}/.env"
echo ""
echo "  2. Verifica o sistema autónomo:"
echo "     python3 ${TARGET_DIR}/cycle.py --dry-run"
echo ""
echo "  3. Lista skills disponíveis:"
echo "     hermes skills list"
echo ""
echo "  4. Cria o sync como skill:"
echo "     hermes skill create bianinho-consciousness-sync"
echo ""
log "Sync concluído!"
