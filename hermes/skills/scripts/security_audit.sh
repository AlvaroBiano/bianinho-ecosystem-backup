#!/bin/bash
# ============================================================
# Security Audit Script — Álvaro Biano Server
# Auditoria automática de segurança com correções automáticas
# ============================================================

LOG_DIR="/home/alvarobiano/.hermes/logs"
REPORT_FILE="$LOG_DIR/security_audit_$(date +%Y%m%d_%H%M%S).log"
ALERT_FILE="$LOG_DIR/security_alerts_$(date +%Y%m%d).log"

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Criar diretório de logs se não existir
mkdir -p "$LOG_DIR"

# Função de log
log() {
    echo -e "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$REPORT_FILE"
}

log_section() {
    echo "" | tee -a "$REPORT_FILE"
    echo "═══════════════════════════════════════════════════════" | tee -a "$REPORT_FILE"
    log "$1"
    echo "═══════════════════════════════════════════════════════" | tee -a "$REPORT_FILE"
}

# Função para corrigir permissões
fix_permissions() {
    local file="$1"
    local expected_perm="600"
    local current_perm=$(stat -c "%a" "$file" 2>/dev/null)
    
    if [ -f "$file" ]; then
        if [ "$current_perm" != "$expected_perm" ]; then
            chmod 600 "$file"
            log "${RED}[CORRIGIDO]${NC} Permissão de $file: $current_perm → $expected_perm"
            echo "[CORRIGIDO] Permissão: $file ($current_perm → $expected_perm)" >> "$ALERT_FILE"
            return 1
        else
            log "${GREEN}[OK]${NC} $file — permissão correta ($current_perm)"
            return 0
        fi
    fi
    return 0
}

# ============================================================
# INÍCIO DA AUDITORIA
# ============================================================
echo "" | tee "$REPORT_FILE"
log "═══════════════════════════════════════════════════════════"
log "    AUDITORIA DE SEGURANÇA — $(date '+%d/%m/%Y às %H:%M:%S')"
log "═══════════════════════════════════════════════════════════"

ALERTS=0

# ============================================================
# 1. VERIFICAÇÃO DE PERMISSÕES DE ARQUIVOS SENSÍVEIS
# ============================================================
log_section "1. PERMISSÕES DE ARQUIVOS SENSÍVEIS"

SENSITIVE_FILES=(
    "/home/alvarobiano/.google_oauth_tokens.json"
    "/home/alvarobiano/.paperclip/auth.json"
    "/home/alvarobiano/.hermes/.env"
    "/home/alvarobiano/.hermes/.env.backup"
    "/home/alvarobiano/.hermes/config.yaml"
    "/home/alvarobiano/.hermes/gateway.log"
    "/home/alvarobiano/.hermes/interrupt_debug.log"
    "/home/alvarobiano/.hermes/auth.json"
)

for file in "${SENSITIVE_FILES[@]}"; do
    if [ -f "$file" ]; then
        fix_permissions "$file"
        if [ $? -eq 1 ]; then
            ((ALERTS++))
        fi
    fi
done

# ============================================================
# 2. VERIFICAÇÃO DE PORTAS E SERVIÇOS
# ============================================================
log_section "2. PORTAS TCP ABERTAS"

OPEN_PORTS=$(ss -tlnp 2>/dev/null | grep -v "127.0.0.1\|::1" | grep LISTEN || echo "Nenhuma porta externa exposta")
log "$OPEN_PORTS"

# Verifica SSH exposto
if ss -tlnp 2>/dev/null | grep -q ":22 "; then
    log "${YELLOW}[ALERTA]${NC} SSH (porta 22) está aberto"
    echo "[ALERTA] SSH porta 22 aberta" >> "$ALERT_FILE"
    ((ALERTS++))
fi

# ============================================================
# 3. VERIFICAÇÃO DE PROCESSOS SUSPEITOS
# ============================================================
log_section "3. PROCESSOS COM ALTO USO DE CPU/MEM"

HIGH_CPU=$(ps aux --sort=-%cpu | head -10)
log "$HIGH_CPU"

# Verifica processos desconhecidos ou suspeitos (exclui processos normais do sistema)
SUSPICIOUS=$(ps aux | grep -iE "nc |netcat|nc -e|mkfifo|/dev/tcp|wget.*http.*sh|curl.*http.*sh" | grep -v -E "grep|kworker|systemd|at-spi|cinnamon-launcher|postgres|lightdm" | grep -v grep)
if [ -n "$SUSPICIOUS" ]; then
    log "${RED}[ALERTA]${NC} Processos suspeitos detectados:"
    log "$SUSPICIOUS"
    echo "[ALERTA] Processos suspeitos: $SUSPICIOUS" >> "$ALERT_FILE"
    ((ALERTS++))
fi

# ============================================================
# 4. BACKUPS (TIMESHIFT)
# ============================================================
log_section "4. STATUS DOS BACKUPS (TIMESHIFT)"

TIMESHIFT_STATUS=$(sudo timeshift --list 2>/dev/null | head -15)
if [ -n "$TIMESHIFT_STATUS" ]; then
    log "$TIMESHIFT_STATUS"
    SNAPSHOT_COUNT=$(echo "$TIMESHIFT_STATUS" | grep -c "20[0-9][0-9]-[0-9]")
    if [ "$SNAPSHOT_COUNT" -lt 2 ]; then
        log "${YELLOW}[ALERTA]${NC} Poucos snapshots disponíveis: $SNAPSHOT_COUNT"
        echo "[ALERTA] Poucos snapshots Timeshift: $SNAPSHOT_COUNT" >> "$ALERT_FILE"
        ((ALERTS++))
    else
        log "${GREEN}[OK]${NC} $SNAPSHOT_COUNT snapshots disponíveis"
    fi
else
    log "${RED}[ERRO]${NC} Timeshift não acessível"
    echo "[ERRO] Timeshift não disponível" >> "$ALERT_FILE"
    ((ALERTS++))
fi

# ============================================================
# 5. LOGS SSH (TENTATIVAS DE ACESSO)
# ============================================================
log_section "5. TENTATIVAS DE ACESSO SSH"

SSH_FAILS=$(grep -i "BREAK-IN\|Failed password\|Failed publickey" /var/log/auth.log 2>/dev/null | tail -10)
if [ -n "$SSH_FAILS" ]; then
    log "${YELLOW}[ALERTA]${NC} Tentativas de login SSH falhadas detectadas:"
    log "$SSH_FAILS"
    echo "[ALERTA] Tentativas SSH falhadas detectadas" >> "$ALERT_FILE"
    ((ALERTS++))
else
    log "${GREEN}[OK]${NC} Nenhuma tentativa de acesso SSH falhada recente"
fi

SSH_ACCEPTS=$(grep -i "Accepted" /var/log/auth.log 2>/dev/null | tail -5)
if [ -n "$SSH_ACCEPTS" ]; then
    log "Últimos logins SSH aceitos:"
    log "$SSH_ACCEPTS"
fi

# ============================================================
# 6. ATUALIZAÇÕES DE SEGURANÇA
# ============================================================
log_section "6. ATUALIZAÇÕES DE SEGURANÇA"

SEC_UPDATES=$(apt list --upgradable 2>/dev/null | grep -i security || echo "Nenhuma atualização de segurança pendente")
log "$SEC_UPDATES"

if echo "$SEC_UPDATES" | grep -q "upgradable"; then
    log "${YELLOW}[ALERTA]${NC} Atualizações de segurança pendentes"
    echo "[ALERTA] Atualizações de segurança pendentes" >> "$ALERT_FILE"
    ((ALERTS++))
fi

# ============================================================
# 7. TAILSCALE VPN
# ============================================================
log_section "7. STATUS TAILSCALE VPN"

TAILSCALE_STATUS=$(tailscale status 2>/dev/null | head -10)
if [ -n "$TAILSCALE_STATUS" ]; then
    log "$TAILSCALE_STATUS"
    log "${GREEN}[OK]${NC} Tailscale ativo"
else
    log "${RED}[ERRO]${NC} Tailscale não está rodando"
    echo "[ERRO] Tailscale não ativo" >> "$ALERT_FILE"
    ((ALERTS++))
fi

# ============================================================
# 8. USO DE DISCO E RAM
# ============================================================
log_section "8. USO DE RECURSOS"

DISK=$(df -h / | tail -1 | awk '{print "Disco: "$3" usado de "$2" ("$5")"}')
RAM_TOTAL=$(free -h | grep Mem | awk '{print $2}')
RAM_USED=$(free -h | grep Mem | awk '{print $3}')
log "Disco: $(df -h / | tail -1 | awk '{print $3}') usado de $(df -h / | tail -1 | awk '{print $2}') ($(df -h / | tail -1 | awk '{print $5}'))"
log "RAM: $RAM_USED usado de $RAM_TOTAL"

# ============================================================
# RESUMO FINAL
# ============================================================
log_section "RESUMO DA AUDITORIA"

log "Total de alertas/correções: $ALERTS"
log "Relatório completo: $REPORT_FILE"

if [ $ALERTS -gt 0 ]; then
    log "${YELLOW}[ATENÇÃO]${NC} $ALERTS problema(s) encontrado(s) — ver detalhes acima"
    log "Alertas do dia salvos em: $ALERT_FILE"
else
    log "${GREEN}[SUCESSO]${NC} Nenhum problema crítico encontrado"
fi

log "═══════════════════════════════════════════════════════════"
log "    FIM DA AUDITORIA — $(date '+%d/%m/%Y às %H:%M:%S')"
log "═══════════════════════════════════════════════════════════"

# Enviar notificação se houver alertas
if [ $ALERTS -gt 0 ]; then
    echo ""
    echo "⚠️  $ALERTS alerta(s) detectado(s). Verifique: $ALERT_FILE"
fi
