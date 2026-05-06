---
name: macbook-performance-tuning
description: Diagnóstico e otimização de performance do MacBook — memória RAM, LaunchAgents, processos, bateria e swap. Workflow completo de 5 ações testado no MacBook Pro M1 Pro 16GB.
trigger: Quando o utilizador pede "optimizar Mac", "performance do Mac", "libertar RAM", "Mac lento", "diagnóstico do Mac", "limpar caches", "espaço em disco", "mac cheio", "otimizar macbook"
category: apple
tags: [macos, performance, ram, launchagents, memory, swap, battery, m1]
owner: bianinho
---

# MacBook Performance Tuning

## Diagnóstico Completo do MacBook Pro

### Step 1: Inventário de Hardware e Sistema

```bash
# Modelo, chip, RAM, macOS
system_profiler SPHardwareDataType | grep -E "Model Name|Model Identifier|Chip|Memory"
sw_vers

# Espaço em disco
df -h /

# CPU e núcleos
sysctl -n machdep.cpu.brand_string
sysctl -n hw.ncpu
sysctl -n hw.memsize | awk '{print $1/1024/1024/1024 " GB"}'
```

### Step 2: Estado da Memória (CRÍTICO)

```bash
# Memory pressure e swap
vm_stat | grep -E "Pages free|swap"
memory_pressure
sysctl -n vm.swapusage

# Pages free é o indicador principal:
# < 10.000 páginas = PRESSÃO ALTA
# > 20.000 páginas = BOM
```

### Step 3: LaunchAgents ativos

```bash
ls -la ~/Library/LaunchAgents/

# Processos Setapp/Steam/Canva ativos
pgrep -af "setapp|steam|canva|google updater"
```

### Step 4: Processos que mais consomem RAM

```bash
# Top 10 por memória
top -l 1 -n 10 -o mem -s 0 | grep -E "^\s*[0-9]"

# Top 10 por CPU
top -l 1 -n 10 -o cpu -s 0 | grep -E "^\s*[0-9]"
```

### Step 5: Estado da Bateria

```bash
pmset -g batt
ioreg -r -k "CycleCount" -k "MaxCapacity" | grep -E "CycleCount|MaxCapacity"
```

---

## Framework de Ações de Otimização (5 Ações)

### AÇÃO 1: Consolidar Processos Duplicados/Órfãos (Impacto: ALTO)

**Problema**: Processos órfãos (Hermes, Python, etc.) ficam em sleep consumindo RAM.

```bash
# Listar todos os processos Python/agent
ps aux | grep -E "Python.*hermes|Python.*rag_server|Python.*bianinho_bridge" | grep -v grep

# Identificar órfãos (mesmo processo, um ativo e outro em sleep antigo)
# Encerrar apenas o órfão (manter o que tem CPU ativo)
kill <PID_ORFÃO>
```

**Como identificar órfão**: dois processos iguais, um com CPU% alto (ativo), outro com CPU% 0.0 e uptime muito antigo. O uptime aparece na coluna TIME do `ps aux`.

**Exemplo real** (MacBook Pro M1 Pro Álvaro):
- PID 57692 `hermes acp` — CPU 25.9%, uptime 8:21AM → ATIVO ✅
- PID 37895 `hermes acp` — CPU 0.0%, uptime 10:54PM (anterior) → ÓRFÃO ❌
→ `kill 37895` libertou ~58MB RAM

### AÇÃO 2: Desativar LaunchAgents Desnecessários (Impacto: ALTO)

```bash
# Agentes a DESATIVAR (desnecessários em background):
launchctl unload ~/Library/LaunchAgents/com.setapp.DesktopClient.SetappAgent.plist
launchctl unload ~/Library/LaunchAgents/com.setapp.DesktopClient.SetappLauncher.plist
launchctl unload ~/Library/LaunchAgents/com.setapp.DesktopClient.SetappAssistant.plist
launchctl unload ~/Library/LaunchAgents/com.setapp.DesktopClient.SetappUpdater.plist
launchctl unload ~/Library/LaunchAgents/com.canva.availability-check-agent.plist
launchctl unload ~/Library/LaunchAgents/com.google.GoogleUpdater.wake.plist
launchctl unload ~/Library/LaunchAgents/com.valvesoftware.steamclean.plist

# Matar processos residuais
kill $(pgrep -f "SetappAgent") 2>/dev/null
kill $(pgrep -f "Steamclean") 2>/dev/null
kill $(pgrep -f "canva") 2>/dev/null
```

**Agentes a MANTER**:
- `AlDente Pro` — crítico para saúde da bateria (nunca matar)
- `CleanMyMac-setapp` — ferramenta de manutenção

### AÇÃO 3: Limpar Finder e Apps com Memória Acumulada (Impacto: MÉDIO)

```bash
# Finder — reinicia automaticamente
killall Finder

# Telegram — encerra e alerta utilizador para reabrir
killall Telegram

# Brave Browser — fechar abas desnecessárias manualmente
```

**Nota**: Quando apps ficam com uptime muito alto (20h+), acumulam memória cached. Encerrar limpa.

### AÇÃO 4: Otimizar Browser Brave (Impacto: MÉDIO)

```bash
# Múltiplos processos Brave consomem RAM excessiva
# Reduzir abas abertas
# Desativar extensões desnecessárias
# Preferir uma janela com poucas abas
```

### AÇÃO 5: Verificar AlDente Pro (Impacto: BATERIA)

```bash
# Garantir que AlDente está ativo e limitado
ps aux | grep -i "aldente" | grep -v grep
```

Manter carregamento entre 50-80% para preservar longevidade da bateria.

### AÇÃO 6: Limpeza de Caches e /tmp (Impacto: DISCO, ~10-12 GB recuperáveis)

**ATENÇÃO:-report before execute** — usar sempre o padrão: investigar primeiro, apresentar relatório, depois pedir confirmação antes de limpar.

#### Diagnóstico de caches e disco:

```bash
# Espaço em /tmp (lixo de instalações antigas)
du -sh /tmp/* 2>/dev/null | sort -rh

# Caches do sistema (Application Support)
du -sh ~/Library/Application\ Support/* 2>/dev/null | sort -rh | head -15

# Caches do usuário
du -sh ~/Library/Caches/* 2>/dev/null | sort -rh | head -10

# Logs grandes
du -sh ~/Library/Logs/* 2>/dev/null | sort -rh | head -10
```

#### Limpeza SEGURA (nunca afeta dados reais):

```bash
# /tmp — seguro pois são cópias de instalação, não dados
rm -rf /tmp/aionui-mac
rm -rf /tmp/AionUi
rm -rf /tmp/app_original_hermes
rm -rf /tmp/app_original_check

# Caches de apps (regeneram automaticamente)
rm -rf ~/Library/Caches/com.brave.Browser/*
rm -rf ~/Library/Caches/BraveSoftware/*
rm -rf ~/Library/Caches/SiriTTS/*
rm -rf ~/Library/Caches/electron-builder/*
rm -rf ~/Library/Caches/electron/*
rm -rf ~/Library/Caches/Google/*
rm -rf ~/Library/Caches/Steam/*
rm -rf ~/Library/Caches/Homebrew/*

# Logs
rm -rf ~/Library/Application\ Support/Google/DriveFS/Logs/*
```

#### NÃO LIMPAR (dados reais):

| Pasta | Tamanho típico | Motivo |
|---|---|---|
| `anythingllm-desktop/storage` | 12 GB | Vector database RAG — dados TEN |
| `Google/Chrome/Default/` | 8 GB | Dados reais do browser |
| `hermes/venv/` | 644 MB | Ambiente Python |
| `Whisky/Bottles/` | 5 GB | Jogos Windows (requer confirmação) |

#### Limites de limpeza por app:

| App | Limpar? | Comandos seguros |
|---|---|---|
| Brave Browser | ✅ Cache sim, dados não | `~/Library/Caches/BraveSoftware/*`, `com.brave.Browser/*` |
| SiriTTS | ✅ Sim | `~/Library/Caches/SiriTTS/*` |
| Electron apps | ✅ Cache sim | `~/Library/Caches/electron*/*` |
| Google Drive | ⚠️ Só logs | `DriveFS/Logs/*` — nunca tocar em `content/` |
| Whisky | ❌ Confirmar | Bottle de 5GB pode ser jogo ativo |
| Steam | ⚠️ Só cache | `~/Library/Caches/Steam/*` |
| AnythingLLM | ❌ Nunca | `storage/` = dados RAG |

#### Descoberta real (MacBook Pro M1 Pro Álvaro):

```
Lixo em /tmp:               ~8.5 GB  (aionui-mac 6.4GB, AionUi 979MB, app_original* 1.1GB)
Caches Brave/electron:       ~1.6 GB
Logs DriveFS/MiniMax:        ~184 MB
─────────────────────────────────────────
TOTAL recuperável seguro:    ~10.3 GB
```

---

## Referência: Comandos de Diagnóstico Rápido

```bash
# Resumo completo numa linha
echo "=== MEMÓRIA ===" && vm_stat | grep -E "Pages free|swap"

# Verificar se há swap activo (sinal de pressão)
sysctl -n vm.swapusage

# Pages free: below 10000 = problem, above 20000 = good

# Calcular ganho de RAM (pages × page_size / 1024 / 1024 = MB)
# page_size do M1 Pro = 16384 bytes
vm_stat | grep "Pages free" | awk '{print "Pages livres:", $3, "~"(($3 * 16384) / 1024 / 1024)"MB"}'
```

**Importante**: macOS ARM usa page size de 16384 bytes (16KB), não 4KB como x86. Isto afecta cálculos de RAM.

---

## Indicadores de Sucesso

| Métrica | Antes | Depois |
|---|---|---|
| Pages free | < 10.000 | > 20.000 |
| Swap usado | > 1 GB | < 500 MB |
| RAM consumo total | > 12 GB | < 9 GB |
| Processos órfãos | > 0 | 0 |
| Espaço em disco livre | basal | +10-12 GB após limpeza |
| /tmp | com resíduos | < 10 MB |

---

## armadilhas (Pitfalls)

1. **NUNCA matar AlDente Pro** — é crítico para a bateria. Se a bateria degrana rapidamente sem ele.
2. **NUNCA matar CleanMyMac** — é a ferramenta de manutenção do sistema. Confirmado com utilizador: "CleanMyMac é fundamental deixar aberto".
3. **Matar apenas o órfão** — quando há dois processos iguais, verificar qual está ativo antes de matar.
4. **Python 3.14** — path beta em `/Library/Frameworks/Python.framework/Versions/3.14/` pode ter memory leaks. Monitorizar instâncias Python.
5. **Telegram** — após matar, informar o utilizador para reabrir manualmente.
6. **Swap activo** — se swap > 1GB, prioridade é matar processos, não há outra solução.
7. **Regra do utilizador: REPORT BEFORE EXECUTE** — "me traga um relatório sempre antes de executar qualquer tarefa". Nunca fazer limpeza sem apresentar dados primeiro e pedir confirmação.

---

## AÇÃO 4 — Brave Browser: NOTA IMPORTANTE

**O Brave NÃO pode ser otimizado remotamente** — não há forma de fechar abas ou desativar extensões via terminal sem encerrar todo o browser (perdes todas as tabs).

**Estado real do Brave** (MacBook Pro M1 Pro Álvaro):
- 27 processos activos
- ~5.3 GB RAM consumida
- 13 extensões instaladas

**Recomendações**: informar o utilizador para fechar abas manualmente. Se ele confirmar que quer encerrar tudo: `killall "Brave Browser"`.

## AÇÃO 6 — Descobertas Adicionais (Session 04/05/2026)

**Bottles Whisky (5GB)** — encontrado `~/Library/Containers/com.isaacmarovitz.Whisky/Bottles/AB208556-E3C7-4D7A-9E80-8D5D4B1727E1` com 5GB. **NUNCA limpar sem confirmação** — pode ser jogo activo.

**Python 3.14** — detectado em `/Library/Frameworks/Python.framework/Versions/3.14/` (beta/candidate). Instâncias Python com path 3.14 devem ser monitorizadas — podem ter memory leaks.

## Cron Job — Criar Tarefas Agendadas de Limpeza

Para criar um cron job que executa limpeza automática do Desktop:

```bash
# 1. Criar script em ~/.hermes/scripts/ (OBRIGATORIO path absoluto do hermes)
cat << 'SCRIPT' > ~/.hermes/scripts/organizar_desktop.sh
#!/bin/bash
DESKTOP="$HOME/Desktop"
MESA="$HOME/Documents/Mesa"
mkdir -p "$MESA/Capturas" "$MESA/Documentos" "$MESA/Screen Recordings"
# ... lógica de categorização
SCRIPT
chmod +x ~/.hermes/scripts/organizar_desktop.sh

# 2. Criar via hermes cron (script path SEM ~/ ou /home/, apenas nome do ficheiro)
hermes cron create \
  --name "Organizar Desktop automaticamente" \
  --deliver local \
  --workdir ~/Documents/Mesa \
  --script organizar_desktop.sh \
  -- "0 * * * *" \
  "Execute o script organizar_desktop.sh para organizar o Desktop."
```

**Regras do hermes cron create**:
- `script` deve ser apenas o nome do ficheiro (não path completo) — o script vai para `~/.hermes/scripts/`
- `schedule` é expressão cron (`0 * * * *` = hourly)
- `prompt` ou `--skill` é obrigatório (não é opcional)
- `workdir` é caminho absoluto

## Relatório Gerado

Quando pedir diagnóstico completo, formatar assim:
- Tabela hardware + estado
- Tabela processos que mais consomem RAM
- Tabela LaunchAgents (a manter vs a desativar)
- Tabela de ações com prioridade e impacto
- Expectativa de ganho percentual
- Nota sobre estado da bateria (saúde, ciclos)
- Nota sobre Python 3.14 (se detectado)
