---
name: hermes-incident-recovery
description: Recuperação de incidentes críticos — WiFi BCM4360, Hermes ModuleNotFoundError, Gateway FileExistsError
category: devops
---

# Hermes Incident Recovery

## WiFi BCM4360 — broadcom-sta-dkms Removido / Driver Não Carrega

### Sintoma
Interface WiFi desaparece, `ip link` não mostra wlan*/wlp*. `lspci` mostra BCM4360 mas sem interface.

### Diagnóstico
```bash
lspci | grep Broadcom
ls /sys/class/net/ | grep -E "wl|wlan|wifi"
nmcli device
lsmod | grep wl
# Verificar se broadcom-sta-dkms foi removido
dpkg -l broadcom-sta-dkms | grep "^ii" || echo "NAO INSTALADO"
# Verificar log de remocao
cat /var/log/dpkg.log.1 | grep broadcom-sta | tail -5
```

### Causa Raiz Mais Comum
Remoção automática de `broadcom-sta-dkms` durante transição de kernel HWE (e.g. ubuntu-drivers devices, apt autoremove). O driver `wl` é proprietário e não está no kernel — sem o dkms, não há driver.

### Diagnóstico — Driver b43 vs brcmfmac vs wl (BCM4360 AC)
```
# b43 — erro "Unsupported PHY (Analog 12, Type 11 (AC), Revision 1)"
# b43 é antigo demais para BCM4360 AC — nao serve

# brcmfmac — carrega mas nao cria interface
# Este driver tem firmware SDIO, nao PCI — nao serve para esta placa

# wl (broadcom-sta) — driver proprietario correcto
# Compila só em kernels mais antigos (6.14.x funciona, 6.17.x falha)
```

### Resolução — Padrão de 3 Camadas

#### Camada 1: Compilar driver no kernel que funciona (6.14/6.17)

Se DKMS falha no kernel actual (6.17.x tem headers quebrados):
```bash
# Identificar kernel que funciona
ls /boot/vmlinuz-* | grep -E "6\.14|6\.17"

# Compilar manualmente (exemplo: kernel 6.14.0-37-generic)
mkdir -p /tmp/broadcom-build
cp -r /usr/src/broadcom-sta-6.30.223.271 /tmp/broadcom-build/

cd /tmp/broadcom-build
make -C /lib/modules/6.14.0-37-generic/build M=$(pwd) KERNELRELEASE=6.14.0-37-generic modules

# Instalar
sudo mkdir -p /lib/modules/6.14.0-37-generic/updates/dkms
sudo cp wl.ko /lib/modules/6.14.0-37-generic/updates/dkms/wl.ko
sudo depmod -a 6.14.0-37-generic
```

#### Camada 2: GRUB — arrancar kernel com driver funcional

```bash
# Ver entradas disponíveis
grep "menuentry" /boot/grub/grub.cfg | head -10

# Definir default para kernel 6.14 (ex: Advanced menu -> entry 2)
# Formato: "menu>submenu_entry" ou "saved_entry"
grep "^GRUB_DEFAULT" /etc/default/grub

# Exemplo: GRUB_DEFAULT="1>2" = submenu 1 (Advanced) -> entry 2 (6.14)
sudo grub-editenv /boot/grub/grubenv set saved_entry="1>2"
cat /boot/grub/grubenv | grep saved_entry
```

#### Camada 3: Proteger contra remoção futura

```bash
# Impedir remocao automatica
sudo apt-mark hold broadcom-sta-dkms bcmwl-kernel-source

# Tambem proteger kernel packages para evitar transicoes HWE automaticas
sudo apt-mark hold linux-headers-6.17.0-20-generic linux-image-6.17.0-20-generic

# Verificar holds
apt-mark showhold
```

### Se GRUB Default Ja Aponta Para 6.14

O driver já está em `/lib/modules/6.14.0-37-generic/updates/dkms/wl.ko`. Só precisa de reboot:
```bash
sudo reboot
# Na proxima sessao:
lsmod | grep wl
ip link show type wifi
nmcli device
```

### Aftermath — Limpar Estados Pendentes do dpkg

Depois do reboot, podem existir pacotes "half-configured" que bloqueiam `apt upgrade`:
```bash
# Ver estado
sudo dpkg --audit

# Forçar remocao limpa
sudo dpkg --remove --force-remove-reinstreq broadcom-sta-dkms linux-headers-6.17.0-22-generic bcmwl-kernel-source

# Reinstalar sem build (já temos o .ko compilado)
sudo apt-get install -y broadcom-sta-dkms
```

### WiFi Guardian — Monitor Automatico

Criar script de monitorização em `/usr/local/bin/wifi-guardian.sh`:
```bash
#!/bin/bash
LOGFILE="/var/log/wifi-guardian.log"
INTERFACE=$(ip link show | grep -E "^[[:digit:]]+: wl" | awk -F: '{print $2}' | tr -d ' ')

if [ -z "$INTERFACE" ]; then
    echo "[$(date)] AVISO: Interface WiFi nao encontrada. Verificando driver..." >> "$LOGFILE"
    if lsmod | grep -q "^wl "; then
        echo "[$(date)] Driver wl carregado mas sem interface. Tentando up..." >> "$LOGFILE"
        ip link set "$INTERFACE" up 2>/dev/null || true
    else
        echo "[$(date)] ERRO: Driver wl nao carregado. Carregando..." >> "$LOGFILE"
        modprobe wl 2>&1 >> "$LOGFILE"
    fi
else
    if ! ip link show "$INTERFACE" | grep -q "UP"; then
        echo "[$(date)] Interface WiFi down. Subindo..." >> "$LOGFILE"
        ip link set "$INTERFACE" up 2>&1 >> "$LOGFILE"
    fi
fi
```

 systemd service em `/etc/systemd/system/wifi-guardian.service`:
```ini
[Unit]
Description=WiFi Guardian - Keep WiFi interface up
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
ExecStart=/usr/local/bin/wifi-guardian.sh
StandardOutput=null
StandardError=null
Restart=always
RestartSec=30

[Install]
WantedBy=multi-user.target
```

Activar:
```bash
sudo systemctl daemon-reload
sudo systemctl enable wifi-guardian.service
sudo systemctl start wifi-guardian.service
```

### GRUB saved_entry pode ser ignorado em reinícios normais

**Problema:** `GRUB_DEFAULT=saved` + `grub-editenv set saved_entry="1>4"` pode não funcionar em todos os boots — o GRUB por vezes ignora o saved_entry e usa o padrão do ficheiro.

**Solução definitiva:** Usar `GRUB_DEFAULT="1>4"` (hardcoded) em `/etc/default/grub` em vez de `saved`. O hook `zz-fix-grub-default` em `/etc/kernel/postinst.d/` garante que isto é corrigido automaticamente após cada update de kernel.

### nmcli — nomes de campos correctos para con show

**Problema:** `nmcli -f autoconnect con show` retorna "campo inválido". O nmcli usa namespaces como `connection.autoconnect`, não apenas `autoconnect`.

**Correto:**
```bash
nmcli -f connection con show <uuid> | grep -i auto
# ou
nmcli -f GENERAL con show <uuid>
```

### Padrão de criação de serviços systemd (workaround terminal)

**Problema:** Comandos `sudo tee /etc/systemd/system/foo.service << 'EOF'` falham com "Foreground command uses '&' backgrounding" no terminal do Hermes (o terminal detecta o heredoc como backgrounding acidental).

**Solução:** Usar `write_file` para criar em `/tmp/` e depois `terminal("sudo cp ...; sudo chmod ...")`:
```
write_file(content, path="/tmp/foo.service")
terminal("sudo cp /tmp/foo.service /etc/systemd/system/foo.service && sudo chmod +x /etc/systemd/system/foo.service")
```

### Detalhe Técnico — Kernel 6.17.x HWE Headers Quebrados

O symlink `arch/x86/include/asm/rwonce.h` aponta para directório inexistente:
```bash
# Sintoma: compilacao falha com "asm/rwonce.h: No such file or directory"
ls /usr/src/linux-headers-6.17.0-20-generic/arch/x86/include/asm/rwonce.h  # missing

# Fix temporario (nao resolve o problema de compilacao completa)
sudo cp /usr/src/linux-headers-6.17.0-20-generic/arch/x86/include/generated/asm/rwonce.h \
   /usr/src/linux-headers-6.17.0-20-generic/arch/x86/include/asm/rwonce.h
```

Mesmo com este fix, a compilacao do broadcom-sta falha porque o driver usa `-I$(src)/src/include` mas o makefile do kernel nao propaga o `EXTRA_CFLAGS` correctamente para submódulos. **Recomendação: usar kernel 6.14.**

### BLINDAGEM COMPLETA — Proteger WiFi Contra Regressões (01/05/2026)

Além da recuperação, aplicar TODAS as camadas abaixo para impedir que o problema se repita:

#### Camada 1: Módulo wl carregado no boot
```bash
echo "wl" | sudo tee /etc/modules-load.d/wl.conf
```
Garante que o driver carrega automaticamente a cada boot, mesmo antes do NetworkManager.

#### Camada 2: Proteger kernel 6.14 contra remoção
```bash
echo 'Package: linux-image-6.14.0-37-generic
Pin: version 6.14.0-37
Pin-Priority: 1000

Package: linux-headers-6.14.0-37-generic
Pin: version 6.14.0-37
Pin-Priority: 1000' | sudo tee /etc/apt/preferences.d/kernel-614
```
O apt nunca vai remover ou substituir o kernel 6.14.0-37.

#### Camada 3: GRUB auto-corrigido após updates de kernel
```bash
sudo tee /etc/kernel/postinst.d/zz-fix-grub-default << 'EOF'
#!/bin/bash
set -e
KERNEL_VERSION="6.14.0-37-generic"
GRUB_DEFAULT_FILE="/etc/default/grub"
CURRENT_DEFAULT=$(grep "^GRUB_DEFAULT=" "$GRUB_DEFAULT_FILE" | cut -d'"' -f2)
if [ "$CURRENT_DEFAULT" != "1>4" ]; then
    echo "[WiFi-blinding] Corrigindo GRUB_DEFAULT de '$CURRENT_DEFAULT' para '1>4'"
    sed -i 's/GRUB_DEFAULT=".*"/GRUB_DEFAULT="1>4"/' "$GRUB_DEFAULT_FILE"
    update-grub
fi
if [ ! -f "/boot/vmlinuz-${KERNEL_VERSION}" ]; then
    echo "[WiFi-blinding] ERRO: Kernel ${KERNEL_VERSION} não encontrado!"
    exit 1
fi
echo "[WiFi-blinding] GRUB default verificado: OK"
EOF
sudo chmod +x /etc/kernel/postinst.d/zz-fix-grub-default
```

Este hook de post-instalação de kernel verifica e corrige automaticamente o GRUB_DEFAULT após qualquer atualização de kernel.

#### Camada 4: Serviço de recovery no boot
```bash
# Criar /usr/local/bin/wifi-recover.sh e /etc/systemd/system/wifi-recover.service
# Ver script completo em: references/wifi-bcm4360-2026-05-01.md
```
Executado automaticamente após cada boot:
- Verifica se módulo wl está carregado (recarrega se necessário)
- Verifica se interface wlp3s0 existe
- Garante que NetworkManager está ativo
- Reconecta WiFi automaticamente se perder conexão

#### Camada 5 (existente): apt-mark hold
```bash
sudo apt-mark hold broadcom-sta-dkms bcmwl-kernel-source
```
Complementar às camadas acima — não substituir.

### Stack Completa de Proteção WiFi

| Camada | Ficheiro | Proteção |
|--------|----------|----------|
| 1 | `/etc/modules-load.d/wl.conf` | Módulo carrega no boot |
| 2 | `/etc/apt/preferences.d/kernel-614` | Kernel 6.14 não é removido |
| 3 | `GRUB_DEFAULT="1>4"` em `/etc/default/grub` | Boot sempre no kernel correto |
| 4 | `/etc/kernel/postinst.d/zz-fix-grub-default` | Auto-corrige GRUB após updates |
| 5 | `apt-mark hold` | Complementar |

### Prevenir

- **SEMPRE** aplicar TODAS as 5 camadas após qualquer intervenção no WiFi
- A camada 3 (GRUB) é a mais frágil — a camada 4 (postinst hook) é a rede de segurança
- Antes de reiniciar após update de kernel, verificar: `grep "^GRUB_DEFAULT=" /etc/default/grub`

---

## Hermes — ModuleNotFoundError after git pull

### Sintoma
`Error: No module named 'agent.smart_model_routing'`

### Causa
Local changes em cli.py ou toolsets.py bloqueiam merge.

### Resolução
```bash
cd ~/.hermes/hermes-agent
git checkout -- cli.py toolsets.py
git pull origin main
./venv/bin/pip3 install -e .
```

### Verificar
```bash
which pip3   # .../hermes-agent/venv/bin/pip3
python3 --version  # 3.11
```

---

## Referências
- Doc completo: `~/.hermes/docs/incidente-2026-04-23.md`
- Ver incidents ativos: `cat ~/.hermes/docs/incidente-2026-04-23.md`

---

## Gateway — FileExistsError PID

### Resolução
```bash
kill $(cat ~/.hermes/gateway.pid) 2>/dev/null
sudo systemctl reset-failed hermes-gateway
sudo systemctl daemon-reload
systemctl --user start hermes-gateway
```

---

## Credential Pool — All Entries Exhausted (HTTP 401/429)

### Sintoma
`⚠️ Non-retryable error (HTTP 401) — trying fallback...` no Telegram e todos os
logs mostram `credential pool: no available entries (all exhausted or empty)`.

### Diagnóstico
```bash
cat ~/.hermes/auth.json | python3 -c "import json,sys; p=json.load(sys.stdin); print(json.dumps(p['credential_pool'], indent=2))"
# Todos os entries teráo "last_status": "exhausted" + "last_error_code": 401/429
# Sem "last_error_reset_at" definido (null) = nunca recuperam sozinhos
```

### Causa Raiz
Quando o credential pool recebe erros 401 ou 429, marca a entrada como
"exhausted" e define `last_error_reset_at`. Se o reset_at for null,
a entrada fica permanentemente esgotada até intervencao manual.

### Resolução — Reset Completo do Pool
```bash
# 1. Backup
cp ~/.hermes/auth.json ~/.hermes/auth.json.bak.$(date +%Y%m%d_%H%M%S)

# 2. Reset — mudar todos "last_status" de "exhausted" para null
python3 -c "
import json
with open('/home/alvarobiano/.hermes/auth.json') as f:
    p = json.load(f)
for prov in p['credential_pool'].values():
    for e in prov:
        e['last_status'] = None
        e['last_status_at'] = None
        e['last_error_code'] = None
        e['last_error_reason'] = None
        e['last_error_message'] = None
        e['last_error_reset_at'] = None
with open('/home/alvarobiano/.hermes/auth.json', 'w') as f:
    json.dump(p, f, indent=2)
print('Pool resetado')
"

# 3. Reiniciar gateway para recolher credenciais
systemctl --user restart hermes-gateway
```

### Nota Importante
Se o `.env` também tiver as chaves mascaradas como `***`, o pool nao vai
funcionar mesmo apos reset. Verificar:
```bash
grep "MINIMAX_API_KEY\|OPENROUTER_API_KEY" ~/.hermes/.env
# Se mostrar "***", a chave real esta ausente e precisa ser restaurada
```

Se as chaves estao em backup:
```bash
# Backup pode ter parte da chave
grep MINIMAX ~/.hermes/.env.backup
```

---

## Hermes Gateway — PID Race Condition

**Skill original:** `hermes-gateway-pid-race-diagnosis`

### Sintomas
- `errors.log`: `gateway.run: PID file race lost to another gateway instance` (4+ ocorrências rápidas)
- `journalctl`: `Start request repeated too quickly` → service entra em `failed` state
- `ps aux` mostra gateway a correr, mas systemd diz que o serviço está morto

### Causa Raiz
`~/.hermes/gateway.pid` contém um PID stale de um processo morto. A instância manual está a correr (PID A). O systemd tenta iniciar nova instância → vê o PID file existe → "race lost" exit imediato. Repeat 5x → systemd bloqueia o serviço como failed.

### Diagnóstico
```bash
# 1. Is a gateway actually running?
ps aux | grep "hermes_cli.main gateway" | grep -v grep

# 2. What does the PID file say?
cat ~/.hermes/gateway.pid

# 3. Is that PID alive?
ps -p $(cat ~/.hermes/gateway.pid) -o pid,cmd 2>/dev/null

# 4. Systemd status
systemctl --user status hermes-gateway.service
```

### Fix (4 passos, por ordem)
```bash
# Step 1: Remove stale PID file
rm -f ~/.hermes/gateway.pid

# Step 2: Update with actual running PID (if running manually)
echo ACTUAL_PID > ~/.hermes/gateway.pid

# Step 3: Reset systemd failed state
systemctl --user reset-failed hermes-gateway.service

# Step 4: Patch RestartSec from 30s to 120s to prevent burst
sed -i 's/RestartSec=30/RestartSec=120/' ~/.config/systemd/user/hermes-gateway.service
```

### Prevenção
- On manual gateway start: always update `~/.hermes/gateway.pid` with the new PID
- RestartSec=120s prevents burst restart when another instance is already running
- The running manual instance should NOT be stopped — systemd must not be allowed to start a second one

---

## Hermes 401 — MiniMax API Key Inválida

**Skill original:** `hermes-401-troubleshoot`

### Sintomas
```
credential pool: marking Hermes exhausted (status=401)
Non-retryable client error: Error code: 401 — login fail: Please carry the API secret key
```

### Causa Raiz
O `.env` pode ter a key real ou um placeholder `***` literal. O terminal mascara ambos, impossibilitando distinguir visualmente. **O credential pool em `~/.hermes/auth.json` é a fonte da verdade.**

### Diagnóstico
```bash
# Inspect credential pool
python3 -c "
import json
with open('/home/alvarobiano/.hermes/auth.json') as f:
    data = json.load(f)
for prov, entries in data.get('credential_pool', {}).items():
    for e in entries:
        print(f'{e.get(\"label\")} status={e.get(\"last_status\")} id={e[\"id\"][:8]}')
"

# Inspect .env em bytes (terminal mascara valores)
python3 -c "
with open('/home/alvarobiano/.hermes/.env', 'rb') as f:
    c = f.read()
i = c.find(b'MINIMAX_API_KEY')
e = c.find(b'\n', i)
kb = c[i+15:e]
print(f'Key len={len(kb)}, val={kb[:8]}')
if kb == b'***': print('PROBLEMA: placeholder literal')
"
```

### Fix — 3 Passos
1. **Corrigir .env** (binary write, evita masking do terminal):
```python
python3 << 'PYEOF'
import json
with open('/home/alvarobiano/.hermes/auth.json') as f:
    data = json.load(f)
key = next((e['access_token'] for e in data['credential_pool']['minimax']
            if e['label'] == 'MINIMAX_API_KEY' and e['last_status'] != 'exhausted'), None)
if not key: print('No valid key'); exit(1)
with open('/home/alvarobiano/.hermes/.env', 'rb') as f: c = f.read()
needle = b'MINIMAX_API_KEY='
i = c.find(needle); end = c.find(b'\n', i)
new = c[:i] + needle + key.encode() + c[end:]
with open('/home/alvarobiano/.hermes/.env', 'wb') as f: f.write(new)
print(f'.env fixed with key ({len(key)} chars)')
PYEOF
```

2. **Limpar entries exaustas:**
```python
python3 << 'PYEOF'
import json
with open('/home/alvarobiano/.hermes/auth.json') as f: data = json.load(f)
valid = [e for e in data['credential_pool']['minimax'] if e.get('last_status') != 'exhausted']
print(f'Pool: {len(data["credential_pool"]["minimax"])} -> {len(valid)}')
data['credential_pool']['minimax'] = valid
with open('/home/alvarobiano/.hermes/auth.json', 'w') as f: json.dump(data, f, indent=2)
PYEOF
```

3. **Reiniciar:**
```bash
systemctl --user restart hermes-gateway && sleep 5 && systemctl --user is-active hermes-gateway
```

### Prevenção
- Nunca `git reset --hard origin/main` com mudanças locais — sobrescreve .env
- Usar `hermes update` (stash automático) em vez de reset manual

---

## Hermes Telegram — Erros de Conexão do Bot

**Skill original:** `hermes-telegram-troubleshooting`

### Sintomas
- Bot não responde a mensagens no Telegram
- HTTP 400 erros no logs
- HTTP 401 no journal do gateway (token truncado)

### Diagnóstico
```bash
hermes gateway status
journalctl --user -u hermes-gateway -n 50 | grep -E "401|400|Shutdown|diagnostic"
ps aux | grep -E "hermes|sac_agent" | grep -v grep
curl -s "https://api.telegram.org/botTOKEN/getMe"
```

### HTTP 400 — Funções com Argumentos JSON Mal Formatados
**Causa:** O modelo MiniMax gera JSON malformatado para chamadas de função (delegate_task com goals complexos).
**Solução:**
```bash
systemctl --user kill -s SIGKILL hermes-gateway && sleep 3 && hermes gateway start
```
**Prevenção:** No Telegram, evitar `delegate_task` com goals complexos — usar trabalho directo com `terminal` ou goals simples.

### HTTP 401 — Token Telegram Truncado no .env
**Sintoma:** `HTTP 401: login fail` no journal do gateway. `grep TELEGRAM_BOT_TOKEN ~/.hermes/.env` mostra token com `...`.

**Verificar token real (não confiar no grep):**
```python
python3 -c "
with open('/home/alvarobiano/.hermes/.env', 'rb') as f:
    content = f.read()
idx = content.find(b'TELEGRAM_BOT_TOKEN=8')
end = content.find(b'\n', idx)
line = content[idx:end]
print('Bytes reais:', line)
print('Token OK:', line.startswith(b'TELEGRAM_BOT_TOKEN=8'))
"
```

**Solução — Corrigir token no .env:**
1. Obter token novo do @BotFather (`/mybots` → seleccionar bot → `/token`)
2. Substituir com Python binary mode:
```python
python3 << 'PYEOF'
with open('/home/alvarobiano/.hermes/.env', 'rb') as f:
    content = f.read()
new = b'TELEGRAM_BOT_TOKEN=NOVO_TOKEN_AQUI'
idx = content.find(b'TELEGRAM_BOT_TOKEN=8')
end = content.find(b'\n', idx)
new_content = content[:idx] + new + content[end:]
with open('/home/alvarobiano/.hermes/.env', 'wb') as f:
    f.write(new_content)
PYEOF
```

### Gateway Exits — "Shutdown diagnostic — other hermes processes running"
O gateway tem mecanismo de protecção excessivamente cauteloso. SAC Bot e gateway usam tokens diferentes e não conflitam.
**Solução:**
```bash
hermes gateway start
```

### Fix Permanente — Restart Automático
```bash
sed -i 's/Restart=on-failure/Restart=always/' ~/.config/systemd/user/hermes-gateway.service
systemctl --user daemon-reload
```

### Gateway Stuck in "deactivating"
```bash
systemctl --user kill -s SIGKILL hermes-gateway
sleep 2
systemctl --user start hermes-gateway
```
