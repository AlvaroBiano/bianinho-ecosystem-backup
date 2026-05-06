#!/bin/bash
# ============================================================
# Server Health Check & Maintenance — Álvaro Biano Server
# Verificação completa de saúde com controle térmico e limpeza
# ============================================================

LOG_DIR="/home/alvarobiano/.hermes/logs"
REPORT_FILE="$LOG_DIR/server_health_$(date +%Y%m%d_%H%M%S).log"

# Cores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configurações
TEMP_WARNING=70
TEMP_CRITICAL=85
CLEAN_TEMP_AGE=7  # dias

mkdir -p "$LOG_DIR"

log() {
    echo -e "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$REPORT_FILE"
}

log_section() {
    echo "" | tee -a "$REPORT_FILE"
    echo "═══════════════════════════════════════════════════════" | tee -a "$REPORT_FILE"
    log "$1"
    echo "═══════════════════════════════════════════════════════" | tee -a "$REPORT_FILE"
}

alert() {
    echo -e "${RED}[ALERTA]${NC} $1" | tee -a "$REPORT_FILE"
}

ok() {
    echo -e "${GREEN}[OK]${NC} $1" | tee -a "$REPORT_FILE"
}

info() {
    echo -e "${BLUE}[INFO]${NC} $1" | tee -a "$REPORT_FILE"
}

# ============================================================
# INÍCIO
# ============================================================
echo "" | tee "$REPORT_FILE"
log "═══════════════════════════════════════════════════════════"
log "    VERIFICAÇÃO DE SAÚDE DO SERVIDOR — $(date '+%d/%m/%Y às %H:%M:%S')"
log "═══════════════════════════════════════════════════════════"

# ============================================================
# 1. TEMPERATURA
# ============================================================
log_section "1. TEMPERATURAS"

get_temp() {
    local zone=$1
    local temp=$(cat /sys/class/thermal/thermal_zone$zone/temp 2>/dev/null)
    if [ -n "$temp" ]; then
        echo $((temp / 1000))
    else
        echo "N/A"
    fi
}

get_temp_celsius() {
    local temp=$(cat "$1" 2>/dev/null)
    if [ -n "$temp" ] && [ "$temp" -gt 0 ]; then
        echo "$((temp / 1000))°C"
    else
        echo "N/A"
    fi
}

# CPU Temperature
CPU_TEMP=$(get_temp_celsius "/sys/class/thermal/thermal_zone0/temp")
CPU_TEMP_VAL=$(cat /sys/class/thermal/thermal_zone0/temp 2>/dev/null | awk '{print int($1/1000)}')

log "CPU Package: $CPU_TEMP"
if [ "$CPU_TEMP_VAL" != "N/A" ]; then
    if [ "$CPU_TEMP_VAL" -ge "$TEMP_CRITICAL" ]; then
        alert "CPU em temperatura CRÍTICA: ${CPU_TEMP_VAL}°C (crítico: ${TEMP_CRITICAL}°C)"
    elif [ "$CPU_TEMP_VAL" -ge "$TEMP_WARNING" ]; then
        alert "CPU quente: ${CPU_TEMP_VAL}°C (atenção: ${TEMP_WARNING}°C)"
    else
        ok "CPU em temperatura normal: ${CPU_TEMP_VAL}°C"
    fi
fi

# GPU Temperature
if [ -f /sys/class/drm/card0/device/hwmon/hwmon0/temp1_input ]; then
    GPU_TEMP=$(get_temp_celsius "/sys/class/drm/card0/device/hwmon/hwmon0/temp1_input")
    log "GPU: $GPU_TEMP"
fi

# Fan speeds
FANS=$(sensors 2>/dev/null | grep -E "RPM|fan" | head -5)
if [ -n "$FANS" ]; then
    log "Fans:\n$FANS"
fi

# Thermal zones
ZONE_COUNT=$(ls /sys/class/thermal/thermal_zone* 2>/dev/null | wc -l)
log "Zonas térmicas ativas: $ZONE_COUNT"

# ============================================================
# 2. SERVIÇOS CRÍTICOS
# ============================================================
log_section "2. SERVIÇOS CRÍTICOS"

SERVICES=("thermald" "tailscaled" "ssh" "systemd-timesyncd" "rsyslog" "cron")

for svc in "${SERVICES[@]}"; do
    if systemctl is-active --quiet "$svc" 2>/dev/null; then
        ok "$svc: ativo"
    elif systemctl list-unit-files | grep -q "^$svc"; then
        alert "$svc: inativo"
    else
        info "$svc: não instalado"
    fi
done

# ============================================================
# 3. CPU
# ============================================================
log_section "3. CPU"

CPU_MODEL=$(grep "Model name" /proc/cpuinfo | head -1 | sed 's/.*: //')
CPU_COUNT=$(nproc)
CPU_MHZ=$(cat /proc/cpuinfo | grep "cpu MHz" | head -1 | awk '{printf "%.0f", $3}')
GOVERNOR=$(cat /sys/devices/system/cpu/cpu0/cpufreq/scaling_governor 2>/dev/null || echo "N/A")

log "Modelo: $CPU_MODEL"
log "Cores: $CPU_COUNT"
log "Frequência atual: ${CPU_MHZ} MHz"
log "Governor: $GOVERNOR"

# ============================================================
# 4. RAM E SWAP
# ============================================================
log_section "4. RAM E SWAP"

RAM_TOTAL=$(free -h | grep Mem | awk '{print $2}')
RAM_USED=$(free -h | grep Mem | awk '{print $3}')
RAM_AVAIL=$(free -h | grep Mem | awk '{print $7}')
SWAP_TOTAL=$(free -h | grep Swap | awk '{print $2}')
SWAP_USED=$(free -h | grep Swap | awk '{print $3}')

log "RAM Total: $RAM_TOTAL | Usado: $RAM_USED | Disponível: $RAM_AVAIL"
log "Swap Total: $SWAP_TOTAL | Usado: $SWAP_USED"

# ============================================================
# 5. DISCO
# ============================================================
log_section "5. DISCO"

DF_OUTPUT=$(df -h / | tail -1)
DISK_USED=$(echo "$DF_OUTPUT" | awk '{print $3}')
DISK_TOTAL=$(echo "$DF_OUTPUT" | awk '{print $2}')
DISK_PERC=$(echo "$DF_OUTPUT" | awk '{print $5}')

log "Disco: $DISK_USED usado de $DISK_TOTAL ($DISK_PERC)"

if [ "${DISK_PERC%?}" -ge 90 ]; then
    alert "Disco acima de 90%!"
elif [ "${DISK_PERC%?}" -ge 80 ]; then
    info "Disco acima de 80% — considere limpar"
else
    ok "Disco com espaço adequado"
fi

# ============================================================
# 6. PROCESSOS TOP
# ============================================================
log_section "6. TOP 5 PROCESSOS (CPU)"

ps aux --sort=-%cpu | head -6 | while read line; do
    log "$line"
done

log ""
log "TOP 5 PROCESSOS (MEM)"
ps aux --sort=-%mem | head -6 | while read line; do
    log "$line"
done

# ============================================================
# 7. CONECTIVIDADE
# ============================================================
log_section "7. CONECTIVIDADE"

PING_GW=$(ping -c 1 -W 2 192.168.1.1 2>/dev/null && echo "OK" || echo "FALHOU")
PING_DNS=$(ping -c 1 -W 2 8.8.8.8 2>/dev/null && echo "OK" || echo "FALHOU")

log "Gateway: $PING_GW"
log "DNS (8.8.8.8): $PING_DNS"

# ============================================================
# 8. LOGS DO SISTEMA (ÚLTIMOS ERROS)
# ============================================================
log_section "8. ÚLTIMOS ERROS DO SISTEMA"

ERRORS=$(journalctl -p3 -n 10 --no-pager 2>/dev/null | tail -10)
if [ -n "$ERRORS" ]; then
    log "$ERRORS"
else
    ok "Nenhum erro crítico recente"
fi

# ============================================================
# 9. LIMPEZA DO SISTEMA
# ============================================================
log_section "9. LIMPEZA DO SISTEMA"

CLEANED=0

# Cache APT
APT_CACHE_SIZE=$(du -sh /var/cache/apt/archives 2>/dev/null | awk '{print $1}')
if [ -n "$APT_CACHE_SIZE" ] && [ "$APT_CACHE_SIZE" != "0" ]; then
    log "Cache APT: $APT_CACHE_SIZE"
    info "Limpando cache APT..."
    sudo apt-get clean 2>/dev/null && ok "Cache APT limpo" || alert "Falha ao limpar APT"
    ((CLEANED++))
fi

# Temp files antigos
TEMP_COUNT=$(find /tmp -type f -atime +$CLEAN_TEMP_AGE 2>/dev/null | wc -l)
if [ "$TEMP_COUNT" -gt 0 ]; then
    log "Arquivos tempórios antigos (>${CLEAN_TEMP_AGE} dias): $TEMP_COUNT"
    find /tmp -type f -atime +$CLEAN_TEMP_AGE -delete 2>/dev/null && ok "Temp files antigos removidos" || true
    ((CLEANED++))
fi

# Thumbnail cache
THUMB_SIZE=$(du -sh ~/.cache/thumbnails 2>/dev/null | awk '{print $1}')
if [ -n "$THUMB_SIZE" ] && [ "$THUMB_SIZE" != "0" ]; then
    log "Thumbnail cache: $THUMB_SIZE"
    rm -rf ~/.cache/thumbnails/* 2>/dev/null && ok "Thumbnails limpos" || true
    ((CLEANED++))
fi

# npm cache
NPM_CACHE=$(du -sh ~/.npm/_cacache 2>/dev/null | awk '{print $1}')
if [ -n "$NPM_CACHE" ] && [ "$NPM_CACHE" != "0" ]; then
    log "NPM cache: $NPM_CACHE"
    npm cache clean --force 2>/dev/null && ok "NPM cache limpo" || true
    ((CLEANED++))
fi

# node compile cache
NODE_CACHE=$(du -sh /tmp/node-compile-cache 2>/dev/null | awk '{print $1}')
if [ -n "$NODE_CACHE" ] && [ "$NODE_CACHE" != "0" ]; then
    log "Node compile cache: $NODE_CACHE"
    rm -rf /tmp/node-compile-cache 2>/dev/null && ok "Node compile cache limpo" || true
    ((CLEANED++))
fi

# Hermes cache (report only)
HERMES_CACHE_SIZE=$(du -sh ~/.hermes/cache 2>/dev/null | awk '{print $1}')
if [ -n "$HERMES_CACHE_SIZE" ] && [ "$HERMES_CACHE_SIZE" != "0" ]; then
    log "Hermes cache: $HERMES_CACHE_SIZE"
fi

# Hermes request_dump files (debug dumps — safe to prune after 7 days)
# These accumulate rapidly (300-520KB each) from session debugging.
# Preserves sessions.json and session_*.json / session_cron_*.json (real session data)
REQUEST_DUMP_COUNT=$(find ~/.hermes/sessions/request_dump\* -type f -mtime +$CLEAN_TEMP_AGE 2>/dev/null | wc -l)
if [ "$REQUEST_DUMP_COUNT" -gt 0 ]; then
    REQUEST_DUMP_SIZE=$(find ~/.hermes/sessions/request_dump\* -type f -mtime +$CLEAN_TEMP_AGE -ls 2>/dev/null | awk '{sum+=$5} END {printf "%.1fM", sum/1024/1024}')
    log "request_dump* (>${CLEAN_TEMP_AGE} dias): $REQUEST_DUMP_COUNT files (${REQUEST_DUMP_SIZE})"
    find ~/.hermes/sessions/request_dump\* -type f -mtime +$CLEAN_TEMP_AGE -delete 2>/dev/null && ok "request_dump* limpos" || true
    ((CLEANED++))
fi

# Sync filesystem
sync

# Drop caches (somente root)
if [ "$(id -u)" -eq 0 ]; then
    echo 3 > /proc/sys/vm/drop_caches 2>/dev/null && ok "Caches do sistema liberados" || true
fi

if [ "$CLEANED" -gt 0 ]; then
    info "Itens limpos: $CLEANED"
else
    ok "Sistema já está limpo"
fi

# ============================================================
# 10. RECOMENDAÇÕES
# ============================================================
log_section "10. RECOMENDAÇÕES"

if [ "$CPU_TEMP_VAL" != "N/A" ] && [ "$CPU_TEMP_VAL" -ge "$TEMP_WARNING" ]; then
    alert "RECOMENDAÇÃO: CPU em ${CPU_TEMP_VAL}°C — considere:"
    echo "  - Fechar processos pesados desnecessários" | tee -a "$REPORT_FILE"
    echo "  - Verificar ventilação do notebook" | tee -a "$REPORT_FILE"
    echo "  - Considerar usar modo de baixo consumo" | tee -a "$REPORT_FILE"
fi

if [ "${DISK_PERC%?}" -ge 80 ]; then
    alert "RECOMENDAÇÃO: Disco em ${DISK_PERC} — considere:"
    echo "  - Limpar logs antigos: sudo journalctl --vacuum-time=7d" | tee -a "$REPORT_FILE"
    echo "  - Remover snapshots antigos do Timeshift" | tee -a "$REPORT_FILE"
    echo "  - Limpar cache pip/npm: npm cache clean --force" | tee -a "$REPORT_FILE"
fi

# ============================================================
# FIM
# ============================================================
log_section "FIM DA VERIFICAÇÃO"
log "Relatório: $REPORT_FILE"
log "═══════════════════════════════════════════════════════════"
