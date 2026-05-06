---
name: aionui
description: "AionUI — plataforma multi-agent cowork (frontend Electron). Arquitectura real, modos de acesso (Xvfb, web viewer, noVNC), e integração com Bianinho/Hermes. NUNCA inventar arquitectura sem verificar primeiro."
triggers:
  - aionui
  - AionUI access
  - aionrs bridge
  - aionrs_bridge
  - AionUI Mac
  - AionUI remote access
  - AionUI interactivity
  - AionUI browser access
  - como funciona o AionUI
  - arquitectura AionUI
---

# AionUI — Complete Guide

## REGRA DE OURO: VERIFICAR ANTES DE DESCREVER

**NUNCA descrever arquitectura sem primeiro verificar o que está a correr.** O Álvaro清清楚楚 que eu estava a inventar coisas sobre o AionUI sem verificar. Antes de dizer como funciona, confirmar com:

```bash
# 1. O que está a correr
ps aux | grep -E "aionui|AionUi|Xvfb" | grep -v grep

# 2. Portas activas
ss -tlnp | grep -E "8765|18743|9223"

# 3. Ficheiros no directorio
ls ~/repos/aionui/
ls ~/repos/aionui-custom/scripts/
```

## O Que É

AionUI é um desktop de **multi-agent cowork** — Gemini CLI, Claude Code, Codex, e mais agentes que trabalham juntos 24/7. Não é um chatbot normal. O Álvaro tem um fork (`AlvaroBiano/AionUi`) com integração Bianinho/Hermes.

- Repo upstream: https://github.com/iOfficeAI/AionUi (Apache-2.0)
- Fork Álvaro: https://github.com/AlvaroBiano/AionUi
- Repo local fork: `~/repos/aionui-custom`
- Repo local original: `~/repos/aionui` (binário Electron + web viewer)

## Modos de Operação

### Modo 1: Servidor Linux + Xvfb (headless)

O AionUI corre no servidor Linux via Xvfb + Electron. Acesso por web viewer (porta 8765) via SSH tunneling Tailscale.

**BINÁRIO:** `~/repos/aionui/AionUi` (200MB, Electron)
**Scripts de controlo:**
- `~/repos/aionui/aionui-start.sh` — inicia Xvfb + AionUi
- `~/repos/aionui/aionui-stop.sh` — para tudo
- `~/repos/aionui/aionui-web-viewer.py` — Flask viewer (porta 8765), screenshot streaming via CDP
- `~/repos/aionui/start-web-access.sh` — script de acesso

**Acesso via SSH Tailscale (do Mac para o servidor):**
```bash
ssh -L 8765:localhost:8765 alvarobiano@alvarobiano-linuxmint.taile2fd75.ts.net
# Depois abre no browser: http://localhost:8765
```

### Modo 2: DMG no Mac (Electron nativo)

O AionUI corre como app Electron nativa no Mac. Liga-se ao BianinhoBridge HTTP no servidor via Tailscale (`100.79.189.95:18743`).

**DMG custom:** `~/repos/aionui-custom/out/` após build
**Bridge server:** `~/repos/aionui-custom/scripts/bianinho_bridge_server.py` (HTTP, porta 18743, systemd service)

### Modo 3: noVNC (interactivo)

x11vnc + websockify para interatividade total via browser.

## Ficheiros e Scripts Chave

| Ficheiro | Descrição |
|----------|-----------|
| `~/repos/aionui/AionUi` | Binário Electron (200MB) — só existe aqui, NÃO é o fork |
| `~/repos/aionui/aionui-web-viewer.py` | Flask viewer (porta 8765) |
| `~/repos/aionui/aionui-start.sh` | Script iniciar Xvfb + AionUI |
| `~/repos/aionui/aionui-stop.sh` | Script parar |
| `~/repos/aionui-custom/` | Fork do Álvaro — código fonte, scripts, bridge |
| `~/repos/aionui-custom/scripts/bianinho_bridge_server.py` | HTTP bridge (porta 18743) |
| `~/.config/systemd/user/bianinho-bridge-server.service` | systemd service para bridge |

## Estado Actual (verificado com `ps aux`)

```
alvarob+  424406  python3 /home/alvarobiano/repos/aionui-custom/scripts/bianinho_bridge_server.py  (porta 18743)
```

O AionUI (Xvfb + Electron) **NÃO está a correr** no servidor. Só o BianinhoBridge HTTP está activo.

## Acesso Remoto — Verificar Primeiro

**NÃO ASSUMIR sem verificar.** O AionUI pode estar a correr de formas diferentes conforme o contexto. Antes de dar instruções de acesso, confirmar sempre com:

```bash
ps aux | grep -E "aionui|AionUi|Xvfb|web-viewer" | grep -v grep
ss -tlnp | grep -E "8765|18743|9223"
curl -s http://localhost:8765 >/dev/null 2>&1 && echo "Web viewer ON" || echo "Web viewer OFF"
curl -s http://localhost:18743/ping >/dev/null 2>&1 && echo "Bridge ON" || echo "Bridge OFF"
```

### Opção 1: Web Viewer (porta 8765)

Se o web viewer estiver activo:
```bash
# SSH tunnel do Mac para o servidor
ssh -L 8765:localhost:8765 alvarobiano@alvarobiano-linuxmint.taile2fd75.ts.net
# Abre no browser: http://localhost:8765
```

Limitação: screenshot streaming — vês mas não interages.

### Opção 2: Iniciar o AionUI no Servidor + Web Viewer

Se quiseres ter o AionUI a correr no servidor:
```bash
~/repos/aionui/aionui-start.sh
# Depois: curl http://localhost:8765 para confirmar
```

### Opção 3: DMG no Mac

O DMG do fork `AlvaroBiano/AionUi` corre nativamente no Mac e liga-se ao BianinhoBridge HTTP (`100.79.189.95:18743`) via Tailscale.

## Estado Actual (sempre verificar — não confiar em valores antigos)

| Componente | Estado | Como verificar |
|-----------|--------|----------------|
| BianinhoBridge HTTP | `ps aux \| grep bianinho_bridge_server` | `curl http://100.79.189.95:18743/ping` |
| AionUI Xvfb | `ps aux \| grep Xvfb` | `ss -tlnp \| grep 8765` |
| Tailscale | `tailscale status` | `curl http://100.79.189.95:18743/ping` |

**Verificado em 02/05/2026:** Só o BianinhoBridge HTTP está activo. O AionUI via Xvfb NÃO está a correr.

## Ficheiros e Scripts Chave

| Ficheiro | Descrição |
|----------|-----------|
| `~/repos/aionui/AionUi` | Binário Electron |
| `~/repos/aionui/aionui-web-viewer.py` | Flask viewer com captura CDP (porta 8765) |
| `~/repos/aionui-hermes-ten/scripts/aionrs-bridge/aionrs_bridge.py` | Bridge para Hermes |
| `~/repos/aionui-custom/scripts/bianinho_bridge.py` | BianinhoBridge Python (TCP porta 18743) |
| `/tmp/aionui.log` | Log do AionUi |

## Estados Conhecidos (01/05/2026)

| Processo | PID | Porta/Display | Estado |
|----------|-----|---------------|--------|
| Xvfb | - | :99 | activo |
| BianinhoBridge | 39346 | 18743 | activo |
| cloudflared (noVNC) | - | - | activo |

## Resolução de Problemas

### AionUI não inicia
```bash
ps aux | grep Xvfb | grep -v grep
cat /tmp/aionui.log
```

### CDP screenshot não funciona
```bash
curl -s http://localhost:9223/json | python3 -c "import json,sys; pages=json.load(sys.stdin); print(f'{len(pages)} pages')"
```

### noVNC conecta mas mostra ecrã negro
```bash
ps aux | grep x11vnc | grep -v grep
x11vnc -display :99 -rfbport 5900 -shared -forever -nopw &
websockify --daemon --web /tmp/novnc --file-only 6080 localhost:5900 &
```

---

## Fork Workflow (AlvaroBiano/AionUi)

O Álvaro tem um fork próprio em `github.com/AlvaroBiano/AionUi`. O repo local vive em `~/repos/aionui-custom`.

### Dual remote
```
origin  → https://github.com/iOfficeAI/AionUi.git  (upstream, só leitura)
alvaro  → https://github.com/AlvaroBiano/AionUi.git (fork, push aqui)
```

### Build
```bash
# Bun necessário (não vem pré-instalado)
curl -fsSL https://bun.sh/install | bash
export PATH="$HOME/.bun/bin:$PATH"

# Instalar deps
cd ~/repos/aionui-custom
npm install --prefer-offline

# Build TypeScript → out/  (USA SEMPRE ESTE)
bunx electron-vite build
# Saída: out/main/, out/preload/, out/renderer/

# Push para fork
git add -A && git commit -m "descricao" && git push alvaro main
```

**Importante:**
- `npm run build` (electron-builder) FALHA com Node 24 + dmg-builder — não usar
- `bunx electron-vite build` é o comando correcto
- Build deve correr em **background** (`background=true`) — o comando demora ~40s e o foreground timeout é 60s

### Adicionar uma nova página

1. Criar directorio: `src/renderer/pages/<nome>/`
2. Criar `NomePage.tsx` + `index.tsx` + `index.module.css`
3. Importar no `Router.tsx`:
```tsx
const NomePage = React.lazy(() => import('@renderer/pages/<nome>'));
<Route path='/nome' element={withRouteFallback(NomePage)} />
```

### Adicionar handlers IPC (bridge)

1. Criar `src/process/bridge/<nome>Bridge.ts`:
```typescript
import { ipcMain } from 'electron';
// handlers com ipcMain.handle('nome.metodo', async () => { ... })
```
2. Importar em `src/index.ts` dentro de `handleAppReady()`:
```typescript
import './process/bridge/<nome>Bridge';
```

3. Adicionar providers em `src/common/adapter/ipcBridge.ts`:
```typescript
nome: {
  metodo: () => invoke('nome.metodo'),
},
```

### Estrutura de directórios relevante

```
src/
  common/chat/bianinho/       ← módulos BianinhoBridge (TypeScript)
  renderer/pages/bianinho/      ← página UI do Bianinho
  renderer/pages/skill-studio/  ← Skill Studio (Fase 3)
  renderer/pages/memory/        ← Memory Visualizer (Fase 3)
  process/bridge/              ← handlers IPC
scripts/
  install.sh                   ← instalador Mac/Linux
  uninstall.sh                 ← desinstalador
  bianinho_bridge.py          ← bridge Python (TCP porta 18743)
  bianinho-venv/              ← venv Python (Python 3.14)
  bianinho-bridge/            ← docs (README.md, SPEC.md)
  benchmark_bridge.py          ← benchmark latência bridge
  benchmark_memory.py           ← benchmark memória bridge
```

---

## Preferências de Comunicação do Álvaro

- **Respostas curtas e directas** — sem explicações longas, sem "deixa-me ver", sem rodeios
- Quando pedir algo (link, ficheiro, acção): **executar imediatamente**, não perguntar sedeve fazer
- "manda o arquivo" = **anexar via MEDIA:path no Telegram** — não é só mencionar o link
- Em incidentes críticos (WiFi, servidores): tentar resolver sozinho antes de perguntar
- Se não sabe algo: dizer "não sei" — não inventar
- Ligar para serviço: primeiro verificar se está a funcionar, depois informar o resultado

---

## Estado Actual (02/05/2026)

| Componente | Estado |
|-----------|--------|
| BianinhoBridge HTTP Server | ✅ Funcional em `100.79.189.95:18743` |
| systemd service | ✅ activo |
| Tailscale | ✅ ambos dispositivos ligados |
| AionUI Xvfb + Web Viewer (8765) | ✅ Funcional no servidor |
| cloudflared named tunnel | ✅ `d532ba47-1f57-4c2d-8622-011a259b5a90` |
| **AionUI URL pública** | ✅ **https://aionui.masterclasslife.com.br** |

### Acesso ao AionUI do MacBook (PRIMÁRIO — 02/05/2026)

O Álvaro pode aceder ao AionUI que corre no **servidor Linux Mint** a partir do **MacBook Pro** através de:

👉 **https://aionui.masterclasslife.com.br**

**Arquitectura:**
```
Servidor (Linux Mint)
  ├── Xvfb :99
  ├── AionUi (Electron, porta CDP 9223)
  ├── aionui-web-viewer.py (Flask, porta 8765, screenshots via CDP)
  └── cloudflared tunnel → aionui.masterclasslife.com.br
          │
          └── Internet (HTTPS)
                  │
MacBook Pro ──────┘
  └── Browser → https://aionui.masterclasslife.com.br
```

**Estado verificado (02/05/2026):**
- `curl https://aionui.masterclasslife.com.br` → HTTP 200 ✅
- AionUI binary: `~/repos/aionui/AionUi` (v1.9.23, ELF 64-bit x86_64)
- Web viewer em `localhost:8765` → 200 OK, screenshot 79KB
- DNS CNAME: `aionui.masterclasslife.com.br` → `d532ba47-...cfargotunnel.com` (proxied=true)
- Túnel cloudflared: processo activo com PID

**Verificação rápida:**
```bash
# Servidor: túnel a correr?
ps aux | grep cloudflared | grep tunnel | grep -v grep

# Servidor: AionUI a responder?
curl -s --connect-timeout 5 http://localhost:8765/ -o /dev/null -w "%{http_code}"

# MacBook: acesso externo?
curl -s --connect-timeout 8 https://aionui.masterclasslife.com.br -o /dev/null -w "%{http_code}"
```

**Se ERRO 1033 ("Cloudflare Tunnel error — Cloudflare is currently unable to resolve it"):**
→ O túnel cloudflared NÃO está a correr. Verificar com `ps aux | grep cloudflared`. Se não estiver, iniciar com:
```bash
cloudflared tunnel run >> /tmp/cloudflared.log 2>&1 &
sleep 8
curl -s --connect-timeout 8 https://aionui.masterclasslife.com.br -o /dev/null -w "%{http_code}"
```

### Acesso ao AionUI do MacBook (PRIMÁRIO — 02/05/2026)

O Álvaro quer aceder ao AionUI que corre no **servidor Linux Mint** a partir do **MacBook Pro**. Este é o caso de uso principal, não o DMG.

**Arquitectura:**
```
Servidor (Linux Mint)
  ├── Xvfb :99
  ├── AionUi (Electron, porta CDP 9223)
  ├── aionui-web-viewer.py (Flask, porta 8765, screenshots via CDP)
  └── cloudflared (túnel nomeado → aionui.trycloudflare.dev)
          │
          └── Internet (HTTPS)
                  │
MacBook Pro ──────┘
  └── Browser → https://aionui.trycloudflare.dev/
```

**Estado verificado (02/05/2026):**
- AionUI binary: `~/repos/aionui/AionUi` (v1.9.23, ELF 64-bit x86_64)
- AionUI a correr com Xvfb :99 + `--remote-debugging-port=9223`
- Web viewer a servir em `localhost:8765` (Flask/Werkzeug)
- Screenshot funciona: 79KB por frame, 2fps, `curl localhost:8765/screenshot.png` = 200 OK
- cloudflared tunnel connected mas `aionui.trycloudflare.dev` DNS não existe

**Para continuar (needs Cloudflare API token):**
Criar o DNS record via `cloudflared tunnel route dns d532ba47-1f57-4c2d-8622-011a259b5a90 aionui.trycloudflare.dev`. Requer API token da Cloudflare com permissão DNS.

**SEM Cloudflare API token — alternativas:**
1. Túnel rápido (instável, URL muda a cada reinício): `cloudflared tunnel --url http://localhost:8765` → URL disponível em `https://*.trycloudflare.com`
2. SSH tunnel (funciona mas requer SSH abierto): `ssh -L 8765:localhost:8765 alvarobiano@alvarobiano-linuxmint.taile2fd75.ts.net`

### Problema: cloudflared quick tunnel dá sempre 404

**Sintoma:** `curl https://*.trycloudflare.com/screenshot.png` = HTTP 404, mas `curl http://localhost:8765/screenshot.png` = 200 OK.

**Causa:** O quick tunnel (`--url`) cria um túnel "account-less" que faz routing básico. paths como `/screenshot.png` são rejeitados — o túnel só funciona para o root `/` ou não faz o forwarding completo dos headers HTTP.

**Solução:** Não usar `--url` para produção. Usar túnel nomeado com DNS record criado via API, ou SSH tunnel.

### Problema: websocket-client não disponível no Python do aionui-web-viewer

**Sintoma:** `aionui-web-viewer.py` falha com `ModuleNotFoundError: No module named 'websocket'`.

**Causa:** O script usa `#!/usr/bin/env python3` que aponta para `/home/alvarobiano/.local/bin/python3` (uv-managed Python 3.14). O módulo `websocket-client` está instalado em `/usr/lib/python3/dist-packages/` (sistema) e no venv do Hermes (Python 3.11), mas não no Python 3.14.

**Solução:**
```bash
/usr/bin/python3 -m pip install websocket-client --break-system-packages
# Confirma: /usr/bin/python3 -c "import websocket; print('OK')"
# O web viewer precisa de correr com /usr/bin/python3:
/usr/bin/python3 ~/repos/aionui/aionui-web-viewer.py
```

### Regra de Ouro: Clarificar Objectivo Antes de Agir

Quando o Álvaro diz "vamos recomeçar do zero", significa que eu passei demasiado tempo numa abordagem errada sem confirmar o que ele realmente queria. **Antes de gastar mais de 5 minutos numa tarefa, confirmar:**
- "Qual é o resultado final que procuras?"
- "Estás a falar do AionUI no servidor ou do DMG no Mac?"

## AVISO CRÍTICO: Web Viewer (porta 8765) é Screenshot-Only

**O web viewer em `localhost:8765` é um fluxo de screenshots via Flask/CDP — NÃO é o AionUI interactivo.** É um espelho VNC, não uma sessão real.

- `curl localhost:8765/screenshot.png` → 200 OK, imagem PNG (screenshot)
- `curl localhost:8765/` → 200 OK, HTML com iframe do screenshot
- **Não é possível interagir** com o AionUI através do web viewer
- Não deve ser exposto como "AionUI acessível" — é enganoso

**Se o Álvaro pedir para expor o AionUI na internet, JAMAIS expor a porta 8765 como se fosse acesso interactivo.** Explicar que é apenas um espelho read-only.

Para acesso **real e interactivo**, as opções são:
1. **SSH X11 forwarding** (XQuartz no Mac) — sessão X11 real
2. **DMG local** — AionUI compilado para macOS, corre nativamente
3. **noVNC** — VNC interactivo via browser (x11vnc + websockify)
4. **OpenClaw Remote Agent** — WebSocket, mas requer OpenClaw Gateway no servidor (não existe ainda)

---

### Arquitectura de Ligação AionUI ↔ Bianinho/Hermes (Cenários Reais)

| Cenário | Como funciona | Estado |
|---------|--------------|--------|
| **DMG Mac → BianinhoBridge HTTP (servidor)** | AionUI Electron no Mac liga-se a `100.79.189.95:18743` via Tailscale | ✅ Produção |
| **DMG Mac → Hermes via ACP stdio** | Hermes CLI local no Mac (não existe ainda) | ❌ Não existe |
| **AionUI no servidor (Xvfb) → BianinhoBridge** | Electron no servidor + bridge HTTP local | ⚠️ Apenas leitura (web viewer) |
| **AionUI Mac → Hermes remoto via OpenClaw** | Remote Agent WebSocket → OpenClaw Gateway no servidor | ❌ Requer setup OpenClaw |
| **SSH X11 forwarding** | Mac XQuartz → servidor Xvfb | ⚠️ Funciona mas lento e sem som |

**O cenário que o Álvaro mais provavelmente quer:** DMG local no Mac conectado ao BianinhoBridge HTTP no servidor via Tailscale. Este é o fluxo documentado em "BianinhoBridge (HTTP via Tailscale)" e está em produção.

**O que NÃO é:** expor a porta 8765 do web viewer como "AionUI na internet" — isso é apenas um screenshot read-only.

Esta regra aplica-se a TODAS as tarefas, especialmente quando há várias abordagens possíveis.

O BianinhoBridge tem **dois modos**, conforme o caso de uso:

### Modo 1: TCP Local (default no packager DMG)

O bridge corre como subprocesso Python local no Mac, binds a `127.0.0.1:18743`.
Usado quando Hermes + Bianinho estão instalados localmente no Mac.

**Scripts:** `scripts/bianinho_bridge.py` (TCP, 4-byte length prefix + JSON)
**Estado:** Em desuso para o Mac (precisa Hermes local)

### Modo 2: HTTP via Tailscale (cloud — 02/05/2026)

O bridge corre no servidor Linux, binds a `100.79.189.95:18743` (IP Tailscale).
O AionUI no MacLiga-se ao servidor via rede Tailscale ponto-a-ponto.
**Não precisa de SSH, nem de portas abertas no firewall, nem de cloudflared.**

**Scripts:** `scripts/bianinho_bridge_server.py` (HTTP server, porta 18743)
**Estado:** ✅ Produção — activo em `100.79.189.95:18743`

**Endpoints HTTP (todos respondem GET ou POST):**

| Método | Path | Descrição |
|--------|------|-----------|
| GET | `/ping` | Health check |
| GET | `/status` | Uptime, msgs, errors |
| GET | `/platform_info` | OS, machine, python version |
| GET | `/check_hermes` | Verifica 5 checks do Hermes |
| GET | `/hermes_path` | Path do Hermes |
| GET | `/list_skills` | Lista 71 skills |
| GET | `/rag_stats` | Estatísticas RAG |
| POST | `/rag_search` | Pesquisa: `{query, category, topK}` |
| POST | `/rag_backup` | Backup: `{label?}` |
| GET | `/inbox_list` | Lista inbox |
| POST | `/inbox_add` | Adiciona: `{content, priority, tags, source}` |
| POST | `/inbox_done` | Toggle done: `{id}` |
| POST | `/inbox_delete` | Remove: `{id}` |
| GET | `/cycle_status` | Estado do ciclo autónomo |
| POST | `/cycle_trigger` | Força ciclo |
| GET | `/memory?key=X` | Lê chave |
| POST | `/memory_set` | Escreve: `{key, value}` |
| GET | `/config?key=X` | Lê config |
| POST | `/config_set` | Escreve: `{key, value}` |
| GET | `/sync_status` | Estado sync |

**Verificação rápida (servidor):**
```bash
curl http://100.79.189.95:18743/ping
curl http://100.79.189.95:18743/rag_stats
curl http://100.79.189.95:18743/list_skills
```

**Verificação rápida (Mac — via Tailscale):**
```bash
curl http://100.79.189.95:18743/ping
```

**Se não responder — debugging:**
```bash
# No servidor — ver se está a correr
ss -tlnp | grep 18743
systemctl --user status bianinho-bridge-server

# Logs
journalctl --user-unit bianinho-bridge-server -n 20

# Reiniciar
systemctl --user restart bianinho-bridge-server
```

#### systemd Service (bianinho-bridge-server)

**Ficheiro:** `~/.config/systemd/user/bianinho-bridge-server.service`

```ini
[Unit]
Description=BianinhoBridge HTTP Server
After=network.target tailscaled.service

[Service]
ExecStart=/usr/bin/python3 /home/alvarobiano/repos/aionui-custom/scripts/bianinho_bridge_server.py
WorkingDirectory=/home/alvarobiano/repos/aionui-custom
Restart=on-failure
RestartSec=10

[Install]
WantedBy=default.target
```

```bash
systemctl --user daemon-reload
systemctl --user enable bianinho-bridge-server
systemctl --user start bianinho-bridge-server
```

**Nota:** O bind a `100.79.189.95` (Tailscale IP) só funciona se o Tailscale estiver activo. Se o Tailscale cair, o servidor recusa o bind e o serviço entra em crash-loop — o `RestartSec=10` dá tempo ao Tailscale para recuperar.

#### Código do Bridge (bianinhoBridge.ts — Electron main process)

O `src/process/bridge/bianinhoBridge.ts` usa Electron `net.request` (não `fetch`) para comunicar com o servidor HTTP via Tailscale:

```typescript
import { ipcMain, net } from 'electron';
const BRIDGE_HOST = '100.79.189.95';
const BRIDGE_PORT = 18743;

async function httpSend(method: 'GET' | 'POST', path: string, body?: Record<string, unknown>): Promise<unknown> {
  const url = `http://${BRIDGE_HOST}:${BRIDGE_PORT}${path}`;
  return new Promise((resolve) => {
    const req = net.request({ method, url });
    req.setHeader('Content-Type', 'application/json');
    // ... response handling ...
    req.end();
  });
}
```

Os handlers IPC (ex: `bianinho.ragSearch`) fazem `httpSend('POST', '/rag_search', args)`.

## BianinhoBridge (Python Sidecar)

O BianinhoBridge é o layer Python que integra o Bianinho autónomo no AionUI. Corre como processo sidecar em `scripts/bianinho_bridge.py` (Python 3.14, venv `bianinho-venv`).

**Estado:** Em produção (porta 18743, pids activos 39346/39528/81794)

### Arquitectura
```
AionUI (Electron)
    │  TCP 127.0.0.1:18743 (4-byte length prefix + JSON)
    ▼
BianinhoBridge (Python)
    ├── RAG: ~/KnowledgeBase/knowledge_db/
    ├── Hermes: ~/.hermes/
    ├── Skills: ~/.hermes/skills/ (72 skills)
    ├── Backup: ~/.hermes/backups/
    └── Inbox/Memory: ~/.hermes/inbox.json, memory.json
```

---

## Protocolo TCP Bridge

### Formato
```
[4 bytes: big-endian length][JSON payload]
```

### Teste rápido com nc
```bash
printf '\x00\x00\x00\x1d{"cmd":"ping","args":{"echo":"test"}}' | nc -N 127.0.0.1 18743
# Recebe: \x00\x00\x00\x1d{"ok":true,"pong":"test","platform":"linux"}
```

### Erro comum: `shutdown(SHUT_WR)` quebra
```python
# ERRADO
sock.send(payload)
sock.shutdown(socket.SHUT_WR)  # ❌ — broken pipe
resp = sock.recv(...)

# CORRECTO — sem shutdown, length prefix determina quando parar
sock.sendall(len(payload).to_bytes(4, 'big') + payload)
```

---

## Comandos Disponíveis (22)

### Sistema
| Comando | Args | Descrição |
|---|---|---|
| `ping` | `echo` | Teste de conectividade |
| `status` | — | Uptime, msgs, errors, rate_limit_hits |
| `platform_info` | — | system, release, machine, python version |
| `check_hermes` | — | Verifica paths do Hermes (5/6 checks) |

### RAG
| Comando | Args | Descrição |
|---|---|---|
| `rag_search` | `query`, `category?`, `topK?` | Pesquisa com isolation |
| `rag_stats` | — | Estatísticas: total chunks, categorias |
| `rag_backup` | `label?` | Backup pre-write |
| `rag_restore` | `backup_name` | Restore |
| `rag_list_backups` | — | Lista backups |

### Inbox / Skills / Ciclo / Memória / Snapshots
| Comando | Args | Descrição |
|---|---|---|
| `inbox_list/add/done/delete` | — | CRUD tarefas |
| `list_skills`, `skill_execute`, `skill_validate` | — | Skills |
| `cycle_status`, `cycle_trigger` | — | Ciclo autónomo |
| `memory_get`, `memory_set` | — | Memória factual |
| `snapshot_export`, `snapshot_import` | — | Backup encriptado |

---

## Segurança

| Mecanismo | Implementação |
|-----------|--------------|
| HMAC Auth | Token `timestamp.signature`, TTL 24h |
| Rate Limiting | 100 req/min por cliente TCP |
| Skills Sandbox | CPU 60s, RAM 500MB, timeout 30s |
| RAG Access Levels | `full`, `read_sac`, `read_personal` |
| Payload Validation | schemas para todos os comandos |

---

## Build Testado

| Comando | Resultado | Nota |
|---------|-----------|------|
| `bunx electron-vite build` | ✅ OK (~36s) | Compila 3 alvos |
| `npm run package` | ✅ OK | electron-vite build via package.json |
| `node scripts/build-with-builder.js --linux --x64 --publish=never` | ✅ OK | Produz .deb (252MB) com todos extraResources |
| `node scripts/build-with-builder.js --mac` | ❌ SÓ macOS | `dmg-license` não instala em Linux |
| Build em foreground | ⚠️ TIMEOUT | Corre em background (60s limit) |

---

## White Screen — Debugging Sem DevTools (RESOLVIDO — 02/05/2026)

O white screen com `e.map is not a function` foi diagnosed e resolvido **sem acesso a DevTools** — o Álvaro não conseguiu abrir DevTools no Mac. As **4 causas raiz** foram identificadas e corrigidas.

### Fluxo de debug cego (sempre aplicar na ordem)

#### 1. Adicionar ErrorBoundary Global (PRIMEIRO)

Sem ErrorBoundary, crashes de renderização mostram só `e.map is not a function` sem contexto — impossível saber que componente crashou. Com ErrorBoundary, o browser mostra o stack trace completo.

**Criar `src/renderer/components/ErrorBoundary.tsx`:**
```tsx
import React from 'react';

interface ErrorBoundaryState {
  hasError: boolean;
  error: Error | null;
  errorInfo: React.ErrorInfo | null;
}

export class ErrorBoundary extends React.Component<React.PropsWithChildren<object>, ErrorBoundaryState> {
  constructor(props: React.PropsWithChildren<object>) {
    super(props);
    this.state = { hasError: false, error: null, errorInfo: null };
  }

  // React 19 — APENAS getDerivedStateFromError. componentDidCatch NÃO funciona.
  static getDerivedStateFromError(error: Error): Partial<ErrorBoundaryState> {
    return { hasError: true, error };
  }

  // NÃO USAR componentDidCatch em React 19 — está break. getDerivedStateFromError é suficiente.
  // componentDidCatch foi deprecated em React 16 e não é lifecycle seguro em React 18+.
  // O state update de errorInfo é opcional para debug — stack já está em error.stack.

  render(): React.ReactNode {
    if (this.state.hasError) {
      return (
        <div style={{ padding: '40px', maxWidth: '600px', margin: '40px auto', fontFamily: 'monospace', fontSize: '13px' }}>
          <h2 style={{ color: '#c00' }}>Erro de renderização</h2>
          <p><strong>Mensagem:</strong> {this.state.error?.message}</p>
          <details style={{ marginTop: '16px', whiteSpace: 'pre-wrap' }}>
            <summary style={{ cursor: 'pointer', fontWeight: 'bold' }}>Stack trace</summary>
            <pre style={{ fontSize: '11px', background: '#fff', padding: '8px' }}>
              {this.state.error?.stack}
            </pre>
          </details>
          {this.state.errorInfo?.componentStack && (
            <details style={{ marginTop: '12px', whiteSpace: 'pre-wrap' }}>
              <summary style={{ cursor: 'pointer', fontWeight: 'bold' }}>Component stack</summary>
              <pre style={{ fontSize: '11px', background: '#fff', padding: '8px' }}>
                {this.state.errorInfo.componentStack}
              </pre>
            </details>
          )}
        </div>
      );
    }
    return this.props.children;
  }
}
```

**Nota crítica:** `componentDidCatch` como lifecycle method **não funciona em React 18+**. Em React 19 está completamente broken. O único método que funciona é `getDerivedStateFromError`. Se o ErrorBoundary mostrar ecrã branco em vez do UI de erro, é porque `componentDidCatch` está a话了 o render — remover imediatamente.

**Em `src/renderer/main.tsx`:**
```tsx
import { ErrorBoundary } from './components/ErrorBoundary';
root.render(
  React.createElement(
    ErrorBoundary, null,
    React.createElement(AppProviders, null, React.createElement(App))
  )
);
```

#### 2. Debug cego — 3 causas mais comuns

Após o ErrorBoundary, se o utilizador reportar erro visível com stack trace, o diagnóstico é directo. Se ainda branco total, aplicar cegamente (resolvem ~90% dos casos):

**Causa 1 — `isDesktopRuntime = false` (mais crítica)**
- Ficheiro: `src/renderer/hooks/context/AuthContext.tsx`
- `Boolean(window.electronAPI)` retorna `false` no DMG → app bloqueia em `checking`
- Fix: `const isDesktopRuntime = true;`

**Causa 2 — IPC handlers em falta**
- Ficheiro: `src/process/bridge/bianinhoBridge.ts`
- Handlers ausentes: `ragStats`, `inboxList`, `cycleStatus`, `memoryGet/Set`, `ragSearch`, `ragBackup`, `inboxAdd/Done/Delete`
- Todos devem ter fallback: `return { count: 0, items: [] }` etc.

**Causa 3 — `.map()` em null no renderer**
- Ficheiros: `BianinhoPage.tsx`, `GuidPage.tsx`
- `result` do IPC pode ser `null` → `setSkillsInfo(null)` → crash no `.map()`
- Validar: `if (result && typeof result === 'object' && Array.isArray((result as any).skills))`
- Renderização: `ragStats?.categories?.length > 0` (usar `?.`)

#### 3. Push + Rebuild DMG

```python
# gh CLI tem bug com Node 24 — usar API REST via Python urllib
import urllib.request, json, re
token = re.search(r'password\s+(\S+)', open('~/.netrc').read()).group(1)
headers = {'Authorization': f'token {token}', 'Accept': 'application/vnd.github.v3+json', 'Content-Type': 'application/vnd.github.v3+json'}

# Obter workflow ID
req = urllib.request.Request('https://api.github.com/repos/AlvaroBiano/AionUi/actions/workflows', headers=headers)
with urllib.request.urlopen(req) as r:
    wf_id = next(w['id'] for w in json.loads(r.read())['workflows'] if 'dmg' in w['name'].lower())

# Dispatch (build-dmg.yml TEM APENAS workflow_dispatch — não corre no push)
dispatch_req = urllib.request.Request(
    f'https://api.github.com/repos/AlvaroBiano/AionUi/actions/workflows/{wf_id}/dispatches',
    method='POST', data=json.dumps({'ref': 'main'}).encode(), headers=headers
)
urllib.request.urlopen(dispatch_req)  # 204 = OK

# Aguardar ~8-12 min, depois:
# Artifact URL: https://github.com/{org}/{repo}/releases/download/{tag}/{filename}
```

**Nota:** O `build-dmg.yml` só tem trigger `workflow_dispatch` — não corre automaticamente no push. Após cada commit, é preciso dispatchar manualmente.
#### PASSO 4 — Download do artifact

```bash
ARTIFACT_ID=6762494110  # obter do API (gh api repos/.../actions/runs/.../artifacts --jq '.artifacts[0].id')
gh api repos/AlvaroBiano/AionUi/actions/artifacts/$ARTIFACT_ID/zip > /tmp/AionUi.dmg.zip
unzip -o /tmp/AionUi.dmg.zip && ls *.dmg
```

#### 5. Criar Release com Asset

```bash
# Criar tag + release
gh release create v1.9.24-fix2 \
  --repo AlvaroBiano/AionUi \
  --title "AionUI v1.9.24 (fix white screen)" \
  --notes "Fix white screen on Mac DMG"

# Upload DMG
gh release upload v1.9.24-fix2 /tmp/AionUi-1.9.24-mac-arm64.dmg --repo AlvaroBiano/AionUi

# URL do asset: https://github.com/AlvaroBiano/AionUi/releases/download/v1.9.24-fix2/AionUi-1.9.24-mac-arm64.dmg
```

#### Atalhos úteis para debug

- `Cmd + Alt + I` (Mac) → abre DevTools directamente, mesmo sem menu
- Linha de comando: `/Applications/AionUI.app/Contents/MacOS/AionUI --no-sandbox 2>&1 | head -50`
- Log do macOS: `~/Library/Logs/AionUi/`

O white screen com `e.map is not a function` foi diagnosed e resolvido **sem acesso a DevTools** — o Álvaro não conseguiu abrir DevTools no Mac. O fluxo de debug começa SEMPRE com o ErrorBoundary.

#### PASSO 1 — Adicionar ErrorBoundary Global (primeiro fix a aplicar)

Quando o utilizador reporta white screen, o primeiro passo é adicionar um ErrorBoundary ao `main.tsx`. Sem ele, crashes de renderização mostram SOMENTE `e.map is not a function` sem contexto. Com ele, o browser mostra o stack trace exacto do componente que crashou.

**Ficheiro: `src/renderer/components/ErrorBoundary.tsx`** (criar):
```tsx
import React from 'react';

interface ErrorBoundaryState {
  hasError: boolean;
  error: Error | null;
  errorInfo: React.ErrorInfo | null;
}

export class ErrorBoundary extends React.Component<React.PropsWithChildren<object>, ErrorBoundaryState> {
  constructor(props: React.PropsWithChildren<object>) {
    super(props);
    this.state = { hasError: false, error: null, errorInfo: null };
  }

  static getDerivedStateFromError(error: Error): Partial<ErrorBoundaryState> {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo): void {
    this.setState({ errorInfo });
    (window as unknown as Record<string, unknown>).__RENDER_ERROR__ = { error, errorInfo };
    console.error('[ErrorBoundary] Render error:', error.message);
    console.error('[ErrorBoundary] Stack:', error.stack);
    console.error('[ErrorBoundary] Component stack:', errorInfo.componentStack);
  }

  render(): React.ReactNode {
    if (this.state.hasError) {
      return (
        <div style={{ padding: '40px', maxWidth: '600px', margin: '40px auto', fontFamily: 'monospace', fontSize: '13px' }}>
          <h2 style={{ color: '#c00' }}>Erro de renderização</h2>
          <p><strong>Mensagem:</strong> {this.state.error?.message}</p>
          <details style={{ marginTop: '16px', whiteSpace: 'pre-wrap' }}>
            <summary style={{ cursor: 'pointer', fontWeight: 'bold' }}>Stack trace</summary>
            <pre style={{ fontSize: '11px', background: '#fff', padding: '8px' }}>
              {this.state.error?.stack}
            </pre>
          </details>
          <details style={{ marginTop: '12px', whiteSpace: 'pre-wrap' }}>
            <summary style={{ cursor: 'pointer', fontWeight: 'bold' }}>Component stack</summary>
            <pre style={{ fontSize: '11px', background: '#fff', padding: '8px' }}>
              {this.state.errorInfo?.componentStack}
            </pre>
          </details>
        </div>
      );
    }
    return this.props.children;
  }
}
```

**Em `src/renderer/main.tsx`:**
```tsx
import { ErrorBoundary } from './components/ErrorBoundary';
// ...
root.render(
  React.createElement(
    ErrorBoundary,
    null,
    React.createElement(AppProviders, null, React.createElement(App))
  )
);
```

**Nota:** O ErrorBoundary DEVE usar `getDerivedStateFromError` — `componentDidCatch` não funciona em React 18+.

#### PASSO 2 — Debug cego (3 causas mais comuns)

Após adicionar ErrorBoundary, se o utilizador报告ar um erro visível, seguir o fluxo. Se ainda branco total, aplicar os 3 fixes cegos (causam ~90% dos casos):

**Causa 1 — `isDesktopRuntime` é `false` no packaged app (MAIS CRÍTICA)**

O `AuthContext.tsx` lia `Boolean(window.electronAPI)` para detectar se está no desktop. No packaged DMG, o preload pode não expor o `electronAPI` correctamente → `isDesktopRuntime = false` → app tenta ir à rede buscar utilizador → `status === 'checking'` para sempre → Router bloqueado → ecrã branco.

**Fix em `src/renderer/hooks/context/AuthContext.tsx`:**
```typescript
// Substituir:
const isDesktopRuntime = typeof window !== 'undefined' && Boolean(window.electronAPI);
// Por:
const isDesktopRuntime = true;  // Desktop nunca precisa de servidor externo
```

**Causa 2 — IPC handlers em falta (BianinhoBridge)**

Os handlers `ragStats`, `inboxList`, `cycleStatus`, `memoryGet`, `memorySet`, `ragSearch`, `ragBackup`, `inboxAdd`, `inboxDone`, `inboxDelete` **não existiam** em `src/process/bridge/bianinhoBridge.ts`. Quando o renderer chamava estes, o IPC retornava `undefined`.

**Padrão de fix — todos os handlers devem ter fallback defensivo:**
```typescript
// Handler em bianinhoBridge.ts — SEMPRE com fallback
ipcMain.handle('bianinho.ragStats', async () => {
  const result = await tcpSend('rag_stats');
  if (result && typeof result === 'object' && 'stats' in result) {
    return result;
  }
  return { stats: { total_chunks: 0, categories: [] } };  // fallback seguro
});

ipcMain.handle('bianinho.inboxList', async () => {
  const result = await tcpSend('inbox_list');
  if (result && typeof result === 'object' && 'items' in result) {
    return result;
  }
  return { count: 0, items: [] };  // fallback seguro
});

ipcMain.handle('bianinho.listSkills', async () => {
  const result = await tcpSend('list_skills');
  if (result && typeof result === 'object' && Array.isArray((result as { skills?: unknown }).skills)) {
    return result;
  }
  return { count: 0, skills: [] };
});
```

**Causa 3 — `.map()` chamado em null no renderer**

Em `BianinhoPage.tsx`, o resultado do IPC era guardado directamente na state sem validação. Também na renderização, `.map()` era chamado sem guarda `?.`.

```typescript
// fetchSkills — validar antes de guardar na state
const result = await ipcBridge.bianinho.listSkills.invoke();
if (result && typeof result === 'object' && Array.isArray((result as { skills?: unknown }).skills)) {
  setSkillsInfo(result as SkillsInfo);
} else {
  setSkillsInfo({ count: 0, skills: [] });
}

// Na renderização — usar ?. em vez de acesso directo
{ragStats?.categories?.length > 0 && ragStats.categories.map(cat => ...)}
{skillsInfo?.skills?.length ? skillsInfo.skills.map(...) : null}

// Em GuidPage.tsx — guard adicional
if (!agentSelection.availableAgents?.length) return [];
```

#### PASSO 3 — Push + Rebuild DMG

```python
# 1. Commit
git add -A && git commit -m "fix: white screen" && git push alvaro main

# 2. Dispatch build via API REST (gh CLI tem bug com Node 24)
import urllib.request, json, re
token = re.search(r'password\s+(\S+)', open('~/.netrc').read()).group(1)
headers = {'Authorization': f'token {token}', 'Accept': 'application/vnd.github.v3+json', 'Content-Type': 'application/json'}

# Obter workflow ID
req = urllib.request.Request('https://api.github.com/repos/AlvaroBiano/AionUi/actions/workflows', headers=headers)
with urllib.request.urlopen(req) as r:
    wf_id = next(w['id'] for w in json.loads(r.read())['workflows'] if 'dmg' in w['name'].lower())

# Dispatch (204 = OK)
dispatch_req = urllib.request.Request(
    f'https://api.github.com/repos/AlvaroBiano/AionUi/actions/workflows/{wf_id}/dispatches',
    method='POST', data=json.dumps({'ref': 'main'}).encode(), headers=headers
)
urllib.request.urlopen(dispatch_req)

# 3. Aguardar ~8-12 min, depois obter artifact
# Artifact URL: https://github.com/{org}/{repo}/releases/download/{tag}/{filename}
```

**Nota importante:** O workflow `build-dmg.yml` tem **APENAS** `workflow_dispatch` — não corre automaticamente no push. É preciso dispatchar manualmente após cada commit.

**Download do artifact (gh CLI OK para download):**
```bash
# Obter artifact ID primeiro
gh api repos/AlvaroBiano/AionUi/actions/runs/25252230954/artifacts --jq '.artifacts[0] | "\(.id) \(.name)"'
# Output: 6763103414 AionUI-Bianinho-arm64.dmg

# Download — gh api stdout redirect é suficiente
ARTIFACT_ID=6763103414
gh api repos/AlvaroBiano/AionUi/actions/artifacts/$ARTIFACT_ID/zip > /tmp/AionUi.dmg.zip

# GitHub sempre zipa artifacts — o .zip contém o .dmg
unzip -o /tmp/AionUi.dmg.zip && ls *.dmg
```

**Upload para release:**
```bash
gh release create v1.9.24-fix2 --repo AlvaroBiano/AionUi --notes "Build c6c3dca6b"
gh release upload v1.9.24-fix2 /tmp/AionUi.dmg.zip --repo AlvaroBiano/AionUi
# URL: https://github.com/AlvaroBiano/AionUi/releases/download/v1.9.24-fix2/AionUi-1.9.24-mac-arm64.dmg
```

#### PASSO 5 — Informar o utilizador

```markdown
Link: https://github.com/AlvaroBiano/AionUi/releases/download/v1.9.24-fix2/AionUi-1.9.24-mac-arm64.dmg

Instruções:
1. Apaga o AionUI antigo em Applications
2. Descarrega o .dmg pelo link
3. Duplo-click para montar > Arrasta para Applications
4. Terminal: sudo xattr -rd com.apple.quarantine /Applications/AionUI.app
5. Abre AionUI
```

**Tag de release:** criar com `gh release create v1.9.24-fix2 --repo AlvaroBiano/AionUi --title "..." --notes "..."` e depois fazer upload do DMG.

#### atalhos Úteis para Debug

- `Cmd + Alt + I` no Mac → abre DevTools directamente (mesmo sem menu)
- Linha de comando: `/Applications/AionUI.app/Contents/MacOS/AionUI --no-sandbox 2>&1 | head -50`
- Log do macOS: `~/Library/Logs/AionUi/`

**(RESOLVIDO — 02/05/2026)**

### 13. White Screen — Root Cause: `useSiderTeamBadges` + SWR `teams=undefined` + `useTeamList` fetcher

**Data: 02/05/2026 — 5 DMG builds needed to resolve.**

**Sintoma:** `TypeError: e.map is not a function` na linha 7560 do bundle. Hash muda entre builds (`B7FSMILK` → `CBvrP838`).

**Metodologia de debug (crítica para futuras ocorrências):**

O problema não estava nos sítios óbvios (`AuthContext`, `BianinhoPage`, `GuidPage`). O crash era num hook aparentemente unrelated — `useSiderTeamBadges(teams)`. SWR pode retornar `undefined` durante o primeiro render antes do fetch resolver, mesmo com `= []` default no destructuring.

**Lição aprendida (02/05/2026):** O `?? []` fallback NO DESTRUCTURING não protege contra `undefined` durante a execução do `useState(initCounts)`. A defence `const safe = teams ?? []` tem de ser a **primeira linha** do hook, antes de qualquer uso de `teams`.

**Os 2 fixes em `useTeamList.ts` e `useSiderTeamBadges.ts` (commit `95e4a7404`):**

```typescript
// useTeamList.ts — fetcher defensivo NO SWR
const { data: teams = [], mutate } = useSWR<TTeam[]>(
  `teams/${userId}`,
  () => ipcBridge.team.list.invoke({ userId }).then((data) => {
    // Defensive: IPC pode retornar {} ou null em vez de array
    if (Array.isArray(data)) return data;
    console.warn('[useTeamList] IPC returned non-array:', data);
    return [];
  }),
  { revalidateOnFocus: false }
);

// useSiderTeamBadges.ts — DOUBLE defence
export function useSiderTeamBadges(teams: TTeam[] | undefined): Map<string, number> {
  // 1. Array.isArray é mais seguro que ?? — pega {} e 'string' também
  const safeTeams: TTeam[] = Array.isArray(teams) ? teams : [];

  const initCounts = (): Map<string, number> => {
    for (const team of safeTeams) { ... }  // safeTeams, não teams
  };

  useEffect(() => {
    for (const team of safeTeams) {
      for (const agent of team.agents ?? []) { ... }  // ?? [] dentro do loop
    }
  }, [
    // safeTeams em vez de teams — não optional chaining ?.
    safeTeams.map((t) => `${t.id}:${(t.agents ?? []).map((a) => a.conversationId || '').join(',')}`).join('|')
  ]);
}
```

**Nota:** `Optional chaining no dependency array` (`teams?.map(...)`) NÃO previne crash no corpo da função — o crash era em `initCounts()` que é chamado DURANTE o render, antes do useEffect correr.

**Extração do ASAR para análise (sempre fazer em builds未知):**

```bash
# 1. Extrair DMG
cd /tmp && 7z x AionUi-1.9.24-mac-arm64.dmg -o/tmp/dmg-contents -y

# 2. Instalar asar (7z não consegue ler ASAR directamente)
cd /tmp && npm install asar --no-save

# 3. Extrair ASAR
node -e "require('asar').extractAll('/path/to/app.asar', '/tmp/asar-extracted')"

# 4. Encontrar bundle com erro (o hash do ficheiro aparece no stack trace do utilizador)
find /tmp/asar-extracted -name "index-*.js" | head -5

# 5. Analisar com Python — procurar .map calls na zona do crash
python3 - << 'PYEOF'
with open('/tmp/asar-extracted/out/renderer/assets/index-B7FSMILK.js') as f:
    content = f.read()
lines = content.split('\n')
# Mostrar contexto da linha do crash (número vem do stack trace)
for i in range(7559, 7570):
    print(f"{i+1}: {lines[i][:200]}")
# Procurar r.agents.map no bundle — identifica o hook exacto
import re
for i, line in enumerate(lines):
    if 'r.agents.map' in line and 'conversationId' in line:
        print(f"FOUND at line {i+1}: {line[:300]}")
PYEOF
```

**O bug real (useSiderTeamBadges):**

```typescript
// ❌ ANTES — assume teams sempre array (SWR pode retornar undefined)
export function useSiderTeamBadges(teams: TTeam[]): Map<string, number> {
  const initCounts = () => {
    for (const team of teams)    // CRASH: teams = undefined
      map.set(team.id, readStorage(team.id));
    return map;
  };
  useEffect(() => {
    for (const team of teams)    // CRASH: teams = undefined
      for (const agent of team.agents)  // CRASH: agents = undefined
        ...;
  }, [teams.map(...)])           // CRASH: teams = undefined
}

// ✅ DEPOIS — defesa completa em 3 sítios
export function useSiderTeamBadges(teams: TTeam[] | undefined): Map<string, number> {
  const safeTeams: TTeam[] = teams ?? [];  // ← GARANTIA desde o início do hook
  const initCounts = () => {
    for (const team of safeTeams) { ... }
  };
  useEffect(() => {
    for (const team of safeTeams) {
      for (const agent of team.agents ?? []) { ... }
    }
  }, [safeTeams.map((t) => `${t.id}:${(t.agents ?? []).map(...).join(',')}`).join('|')]);
}
```

**Padrão geral:** qualquer hook que recebe dados de SWR/fetch como prop/argumento DEVE defender contra `undefined` no primeiro render. O default `= []` no destructuring NÃO protege durante a execução de `initCounts()` ou `useEffect` quando `teams` é passado como parâmetro. A defesa `const safe = teams ?? []` deve ser a primeira linha do hook.

**(RESOLVIDO — 02/05/2026)**

Quando o utilizador não consegue abrir DevTools no Mac (não sabe como, ou está frustrado), aplicar o fluxo de debug cego: as 3 causas mais comuns são `isDesktopRuntime = false`, handlers IPC em falta, e `.map()` sem guarda. Push + rebuild DMG resolve ~90% dos casos. Ver secção completa em `references/dmg-build.md` → "White Screen — Debugging Sem DevTools". (RESOLVIDO — 02/05/2026)

O app compila e abre, mas fica com ecrã branco. Erro no Console DevTools:

```
Uncaught TypeError: e.map is not a function
    at N1t (index-BRdc99Ma.js:7560)
```

**Três causas raiz descobertas e corrigidas:**

#### Causa 1 — `isDesktopRuntime` é `false` no packaged app (MAIS CRÍTICA)

O `AuthContext.tsx` lia `Boolean(window.electronAPI)` para detectar se está no desktop. No packaged DMG, o preload pode não expor o `electronAPI` correctamente, então `isDesktopRuntime = false` → o app tenta ir à rede buscar utilizador → fica em loading eterno → ecrã branco.

**Fix em `src/renderer/hooks/context/AuthContext.tsx`:**
```typescript
// Substituir:
const isDesktopRuntime = typeof window !== 'undefined' && Boolean(window.electronAPI);
// Por:
const isDesktopRuntime = true;  // Desktop nunca precisa de servidor externo
```

**Isto é a causa mais provável quando o ecrã é branco desde o primeiro frame** — o Router fica bloqueado no `status === 'checking'` para sempre.

#### Causa 2 — IPC handlers em falta (BianinhoBridge)

Os handlers `ragStats`, `inboxList`, `cycleStatus`, `memoryGet`, `memorySet`, `ragSearch`, `ragBackup`, `inboxAdd`, `inboxDone`, `inboxDelete` **não existiam** em `src/process/bridge/bianinhoBridge.ts`. Quando o renderer chamava estes, o IPC retornava `undefined` ou erro.

**Padrão de fix — todos os handlers devem ter fallback defensivo:**
```typescript
// Handler em bianinhoBridge.ts — SEMPRE com fallback
ipcMain.handle('bianinho.ragStats', async () => {
  const result = await tcpSend('rag_stats');
  if (result && typeof result === 'object' && 'stats' in result) {
    return result;
  }
  return { stats: { total_chunks: 0, categories: [] } };  // fallback seguro
});

ipcMain.handle('bianinho.inboxList', async () => {
  const result = await tcpSend('inbox_list');
  if (result && typeof result === 'object' && 'items' in result) {
    return result;
  }
  return { count: 0, items: [] };  // fallback seguro
});

ipcMain.handle('bianinho.listSkills', async () => {
  const result = await tcpSend('list_skills');
  if (result && typeof result === 'object' && Array.isArray((result as { skills?: unknown }).skills)) {
    return result;
  }
  return { count: 0, skills: [] };
});
```

#### Causa 3 — `.map()` chamado em null no renderer

Em `BianinhoPage.tsx`, o resultado do IPC era guardado directamente na state sem validação:

```typescript
// ANTES (crasha se bridge retornar null)
const result = await ipcBridge.bianinho.listSkills.invoke();
setSkillsInfo(result);  // null → crash no .map()

// DEPOIS (defensivo)
const result = await ipcBridge.bianinho.listSkills.invoke();
if (result && typeof result === 'object' && Array.isArray((result as { skills?: unknown }).skills)) {
  setSkillsInfo(result as SkillsInfo);
} else {
  setSkillsInfo({ count: 0, skills: [] });
}
```

Na renderização, usar `?.` para proteger todos os `.map()`:
```typescript
//危险
{ragStats.categories.map(cat => ...)}

//安全
{ragStats?.categories?.length > 0 && ragStats.categories.map(cat => ...)}

//Também seguro
{skillsInfo?.skills?.length ? skillsInfo.skills.slice(0, 30).map(...) : null}
```

Em `GuidPage.tsx`:
```typescript
// Guard extra para availableAgents ser array
if (!agentSelection.availableAgents?.length) return [];
```

**Padrão geral:** qualquer dado que venha do IPC bridge deve ser tratado como potencialmente `null`/`undefined`/`wrong-shape` — nunca confiar que vem no formato esperado.

#### Debug sem DevTools

Quando o utilizador não consegue abrir DevTools, aplicar todos os fixes acima cegamente (são as 3 causas mais comuns). Depois fazer push e rebuild — o DMG novo resolve o problema na esmagadora maioria dos casos.

Se ainda não resolver, perguntar ao utilizador:
- O ecrã mostra algum conteúdo (mesmo que parcialmente)?
- Há algum log no Terminal se o app for aberto por linha de comando?
  ```bash
  /Applications/AionUI.app/Contents/MacOS/AionUI --no-sandbox 2>&1 | head -50
  ```

#### Fluxo de debug cego (quando DevTools não está disponível)

1. `isDesktopRuntime` → forçar a `true` (causa mais provável de branco total)
2. IPC handlers em falta → adicionar todos com fallback seguro
3. `.map()` sem guarda → adicionar `?.` em todos os `.map()` de dados IPC
4. Push → rebuild DMG via GitHub Actions workflow dispatch
5. Download e teste

Este fluxo resolve ~90% dos casos de white screen em DMG.

### 14. extractBianinhoResources() — extracção de recursos no primeiro lançamento

Quando o app é instalado via DMG, os `extraResources` ficam dentro do `.app`:

```
/Applications/AionUI.app/Contents/Resources/
├── bianinho/           ← BianinhoBridge + scripts
├── hermes-source/      ← Hermes Agent (42MB)
└── app.asar
```

O main process precisa de os copiar para `~/Library/ApplicationSupport/AionUI/` no primeiro lançamento:

```typescript
// src/index.ts — dentro de handleAppReady(), ANTES de registerBianinhoBridge()
async function extractBianinhoResources(): Promise<void> {
  if (process.platform !== 'darwin') return;
  if (!app.isPackaged) return;

  const appSupport = path.join(app.getPath('home'), 'Library/ApplicationSupport/AionUI');
  const bianinhoDest = path.join(appSupport, 'bianinho');
  const hermesDest = path.join(appSupport, 'hermes');
  const resourceBianinho = path.join(process.resourcesPath!, 'bianinho');
  const resourceHermes = path.join(process.resourcesPath!, 'hermes-source');
  const markerFile = path.join(bianinhoDest, '.extracted');

  if (fs.existsSync(markerFile)) return;  // já extraiu

  const copyDir = (src: string, dest: string) => {
    if (!fs.existsSync(src)) return;
    fs.mkdirSync(dest, { recursive: true });
    for (const entry of fs.readdirSync(src)) {
      const srcPath = path.join(src, entry);
      const destPath = path.join(dest, entry);
      const stat = fs.statSync(srcPath);
      if (stat.isDirectory()) copyDir(srcPath, destPath);
      else fs.copyFileSync(srcPath, destPath);
    }
  };

  copyDir(resourceBianinho, bianinhoDest);
  copyDir(resourceHermes, hermesDest);
  fs.writeFileSync(markerFile, new Date().toISOString());
  if (fs.existsSync(path.join(bianinhoDest, 'hermes-launcher.sh')))
    fs.chmodSync(path.join(bianinhoDest, 'hermes-launcher.sh'), 0o755);
}
```

### 15. gh CLI Broken com Node 24

`gh` CLI tem bug com Node 24 — qualquer comando dá:

```
TypeError: Cannot read properties of undefined (reading 'options')
    at getAvailableArgsOnCmd
```

**Alternativas quando gh está partido:**
```bash
# gh auth login --with-token (requer token válido)
# gh workflow run (falha)
# gh run list (falha)

# Opção 1: API REST via curl
curl -s -H "Authorization: token $TOKEN" \
  "https://api.github.com/repos/AlvaroBiano/AionUi/actions/workflows"

# Opção 2: gh via nvm (trocar versão do Node)
nvm use 22 && gh workflow run build-dmg.yml --field arch=arm64

# Opção 3: Trigger manual na web
# https://github.com/AlvaroBiano/AionUi/actions/workflows/build-dmg.yml → Run workflow
```

Token GitHub para API: está em `~/.netrc` (machine `github.com`, password = token <GITHUB_PAT>). Pode estar inválido — "Bad credentials" se expirou.

---

## armadilhas Descobertas (01/05/2026)

### 1. Ícones @icon-park/react — VERIFIED LIST v1.9.8

O build FALHA com "X does not exist" para ícones inexistentes. **SEMPRE verificar antes de usar.**

**Verificar:**
```bash
ls ~/repos/aionui-custom/node_modules/@icon-park/react/es/icons/ | grep -i "^NomeProcurado"
```

**ÍCONES VERIFICADOS (usar estes):**

| Categoria | Ícones |
|-----------|--------|
| Acção | `Plus`, `PlayOne`, `SaveOne`, `Delete`, `Download`, `Refresh`, `Edit`, `Block` |
| UI | `Check`, `Error`, `Signal`, `Timer`, `Trend`, `Power`, `Sync`, `Mute`, `Sound`, `HardDisk` |
| Docs | `FileText`, `FileAddition`, `FolderOpen`, `Tag`, `TagOne` |
| Agent | `Robot`, `Brain`, `MindMapping`, `Code`, `Terminal` |
| Misc | `Book`, `Info`, `PreviewOpen`, `TestTube`, `ManualGear`, `Flashlamp`, `Lightning`, `AlarmClock` |

**ÍCONES INEXISTENTES (não usar):**

| NÃO usar | Substituto |
|----------|-----------|
| `Trash` | `Block` |
| `Settings` / `Gear` | `ManualGear` |
| `Database` | `HardDisk` |
| `CheckCircle` | `Check` |
| `XCircle` | `Error` |
| `Clock` | `AlarmClock` ou `Timer` |
| `Flash` | `Flashlamp` |
| `Energy` | `Lightning` |
| `Notification` | `Signal` |
| `Eye` | `PreviewOpen` |
| `Edit2` | `Edit` |
| `FilePlus` | `FileAddition` |
| `Play` | `PlayOne` |
| `Save` | `SaveOne` |

**Rebuild IMEDIATAMENTE** após adicionar ícone — erros de ícone param o build inteiro (10585 módulos).

### 2. Arco Design — TabPane não é export directo

```tsx
// ERRADO
import { Tabs, TabPane } from '@arco-design/web-react';
<TabPane key='1' title='Tab 1'><Content /></TabPane>

// CORRECTO
import { Tabs } from '@arco-design/web-react';
<Tabs.TabPane key='1' title='Tab 1'><Content /></Tabs.TabPane>
```

### 3. TCP Bridge —nc é mais fiável que socket Python

Socket Python directo com length-prefix tem problemas de buffering no `recv()`. O `nc` funciona sempre:

```python
# Abordagem que funciona — subprocess + nc
import subprocess, json

def send_cmd(cmd, host='127.0.0.1', port=18743):
    payload = json.dumps(cmd)
    length_bytes = len(payload).to_bytes(4, 'big')
    p = subprocess.run(
        f'echo -n "{length_bytes.decode("latin-1")}{payload}" | nc -N {host} {port}',
        shell=True, capture_output=True, timeout=5
    )
    return p.stdout.decode()
```

### 4. IPC Bridge providers — não basta handlers IPC

Além dos handlers `ipcMain.handle()` em `bianinhoBridge.ts`, adicionar providers em `src/common/adapter/ipcBridge.ts`:

```typescript
bianinho: {
  ping: () => invoke('bianinho.ping'),
  status: () => invoke('bianinho.status'),
  checkHermes: () => invoke('bianinho.checkHermes'),
  listSkills: () => invoke('bianinho.listSkills'),
  // etc.
},
```

### 5. `registerBianinhoBridge()` dentro de `handleAppReady()`

Importar ao nível do módulo funciona para handlers auto-registados, mas `registerBianinhoBridge()` precisa de ser chamado dentro de `handleAppReady()` no `src/index.ts`.

### 6. Python — funções definidas ANTES de classes que as usam

```python
# ERRADO
class SkillsSandbox:
    def __init__(self):
        self.hermes_path = detect_hermes_path()  # NameError!

skills_sandbox = SkillsSandbox()
def detect_hermes_path():
    ...

# CORRECTO
def detect_hermes_path():
    ...

class SkillsSandbox:
    def __init__(self):
        self.hermes_path = detect_hermes_path()

skills_sandbox = SkillsSandbox()
```

### 7. Subagentes — Gap UI vs Python Bridge

A implementacao TypeScript (BianinhoPage tab "Subagentes") cria interfaces e mock data em memória, mas os comandos Python correspondentes (`subagent_list`, `subagent_create`, etc.) **não foram adicionados** ao `scripts/bianinho_bridge.py`.

**Para completar a feature:** adicionar handlers em `scripts/bianinho_bridge.py` que persistem em `~/.hermes/config/subagents.json`.

### 8. Build — corre SEMPRE em background

`bunx electron-vite build` demora ~40s e o foreground timeout é 60s — às vezes passa, às vezes não. Para evitar surpresas:

```bash
# Usar background=true — sempre
terminal(command="bunx electron-vite build", background=true, notify_on_complete=true)
process(action="wait", session_id="...procid...", timeout=90)
```

Iterações typicas até build OK: 3-5 (cada vez um ícone diferente corrigido).

### 9. Delegação — max 3 concurrent + verificação de outputs

`delegate_task` com `max_concurrent_children=3`. Se enviar 5 tasks, 2 ficam pendentes. Dividir em batches de 3.

**IMPORANTE — Verificar outputs após subagente terminar:**

Subagentes podem completar mas criar ficheiros com erros (ícones inexistentes, imports wrong) ou criar ficheiros fora do path esperado. SEMPRE fazer após cada batch:

```bash
# 1. Verificar ficheiros criados
git status --short

# 2. Se Build falhar com erro de ícone, identificar e corrigir
grep -rn "Trash\|Settings\|Gear\|Database\|CheckCircle" src/
# Corrigir com sed, ex: sed -i 's/Trash/Block/g' src/file.tsx

# 3. Rebuild
```

Iterações típicas até build OK após trabalho de subagente: **3-5** (cada vez um ícone diferente corrigido).

### 10. Ícones — VERIFICAR ANTES de usar no prompt do subagente

Ao delegar para subagente, incluir na lista de contexto os ícones VERIFICADOS e os que NÃO existem. Erro comum: subagente usa `Edit2`, `Trash`, `Eye` sem saber que não existem.

**ÍCONES VERIFICADOS (usar):**
```
Plus, PlayOne, SaveOne, Delete, Download, Refresh, Edit, Block, Check, Error,
Signal, Timer, Trend, Power, Sync, Mute, Sound, HardDisk, FileText,
FileAddition, FolderOpen, Tag, TagOne, Robot, Brain, MindMapping, Code,
Terminal, Book, Info, PreviewOpen, TestTube, ManualGear, Flashlamp,
Lightning, AlarmClock
```

**NÃO USAR (vão quebrar o build):**
```
Trash→Block, Settings/Gear→ManualGear, Database→HardDisk, CheckCircle→Check,
XCircle→Error, Clock→AlarmClock/Timer, Flash→Flashlamp, Energy→Lightning,
Notification→Signal, Eye→PreviewOpen, Edit2→Edit, FilePlus→FileAddition,
Play→PlayOne, Save→SaveOne
```

Se o subagente usar ícone wrong, corrigir com sed após, mas idealmente evitar o ciclo.

### 11. GitHub Actions — Build DMG manual via workflow_dispatch

O repo tem `.github/workflows/build-dmg.yml` que pode ser accionado manualmente para gerar `.dmg` para Mac:

1. Ir a https://github.com/AlvaroBiano/AionUi/actions → "Build DMG (macOS)"
2. Clicar "Run workflow" → escolher `arm64` (Apple Silicon) ou `x64` (Intel)
3. Aguardar ~10-15 min → artifact `.dmg` disponível para download (7 dias)

Architecture choices no workflow: `arm64`, `x64`, ou `universal` (ambos).

### 12. gh release upload — nunca fazer ANTES do download do artifact terminar

O `gh api .../zip > file.zip` demora ~40s para um artifact de 257MB. Se faz `gh release upload` antes do download terminar, o zip fica incompleto (4KB em vez de 257MB) e o utilizador recebe um ficheirocorrupto.

**Sequência CORRECTA:**
```bash
# 1. Dispatch build
gh workflow run build-dmg.yml --field arch=arm64 --repo AlvaroBiano/AionUi

# 2. Obter run ID + artifact ID (polling até status=completed)
gh api repos/AlvaroBiano/AionUi/actions/runs --jq '.workflow_runs[0].id'    # run ID
gh api repos/AlvaroBiano/AionUi/actions/runs/$RUN_ID/artifacts --jq '.artifacts[0].id'  # artifact ID

# 3. Download em background
curl -L -H "Authorization: token $TOKEN" \
  -o /tmp/AionUi-new.dmg.zip \
  "https://api.github.com/repos/.../actions/artifacts/$ARTIFACT_ID/zip" &
DOWNLOAD_PID=$!

# 4. wait do PID — NÃO fazer release upload até download terminar
wait $DOWNLOAD_PID
ls -lh /tmp/AionUi-new.dmg.zip  # confirmar ~257MB

# 5. Só agora criar release e upload
gh release create v1.9.24-fix4 --repo AlvaroBiano/AionUi --notes "..."
gh release upload v1.9.24-fix4 /tmp/AionUi-new.dmg.zip --repo AlvaroBiano/AionUi
```

**O erro clássico:** criar o release, fazer upload, e só depois perceber que o zip está mal. Remedy: verificar `du -h` do ficheiro antes de fazer upload — tem de ter o tamanho correcto (≈257MB para DMG).

### 13. Bundle — lancedb é o package mais pesado do venv

Na Opção Completa (bundle para Mac), o `lancedb` sozinho pesa ~362 MB dentro do venv. Isto é 95% do peso do venv:

| venv | Tamanho |
|------|---------|
| Sem lancedb | 19 MB |
| Com lancedb | **382 MB** |

Se o bundle precisar de ser mais pequeno, remover `lancedb` do `pip install` em `export-lean-bundle.sh`. Sem lancedb, o bundle fica ~350 MB mas o RAG local não funciona — pesquisas vão ao servidor.

---

## Opção A — TUDO Local no Mac (Opção Completa)

O fork `AlvaroBiano/AionUi` suporta instalação 100% local no Mac — sem dependência do servidor Linux.

### Arquitectura

```
DMG (~200MB) ──first-run──> Lean Bundle (~900MB) ──> TUDO LOCAL
                                         │
                    ┌────────────────────┴────────────────────┐
                    │                                          │
              Hermes Agent                              Knowledge Base
              + BianinhoBridge                            (~1.1GB)
              + Skills                                    + 65k chunks
              + Lean venv
              (~382MB)
```

### Tamanhos Reais (medidos em 01/05/2026)

| Componente | Tamanho real | Comprimido |
|---|---|---|
| Hermes source | 1.1 MB | 1 MB |
| Lean venv (c/ lancedb) | 382 MB | ~100 MB |
| Lean venv (s/ lancedb) | 19 MB | 5 MB |
| Knowledge Base | 1.1 GB | ~300 MB |
| Skills | 16 MB | 5 MB |
| **Bundle COMPLETO (c/ lancedb)** | **~1.5 GB** | **724 MB** |
| **Bundle LEAN (s/ lancedb)** | **~1.1 GB** | **~350 MB** |

**Nota:** O package mais pesado do venv é `lancedb` (362 MB). Sem lancedb, o venv é só 19 MB — mas sem lancedb não há RAG local.

### Modos de Bundle

**Lean (~350MB):** UI + Hermes + Bridge + Skills. RAG vai ao servidor (precisa de rede). Mais rápido de transferir.

**Completo (~900MB):** UI + Hermes + KB + Skills + lancedb. 100% offline. Sem dependência do servidor.

### Fluxo Completo — Opção Completa

**1. No servidor — criar e servir bundle:**
```bash
cd ~/repos/aionui-custom
bash scripts/export-lean-bundle.sh both
# Cria /tmp/bianinho-lean-mac.tar.gz (~724MB)
# Serve HTTP na porta 8878
```

**2. No MacBook — instalar AionUI:**
```bash
curl -fsSL https://raw.githubusercontent.com/AlvaroBiano/AionUi/main/scripts/install.sh | bash
```

**3. No MacBook — descarregar bundle (~724MB):**
```bash
# IP do servidor aparece no output do passo 1
curl -o ~/Downloads/bianinho-lean.tar.gz http://IP_SERVIDOR:8878/download
```

**4. No MacBook — extrair e setup completo:**
```bash
mkdir -p ~/Library/ApplicationSupport/AionUI
tar -xzf ~/Downloads/bianinho-lean.tar.gz \
  -C ~/Library/ApplicationSupport/

# Setup interactivo: API key, configurações
bash ~/AionUI-Bianinho/scripts/setup-complete.sh
```

### Scripts de Transferência

| Script | Corre em | Função |
|--------|----------|--------|
| `export-lean-bundle.sh` | Servidor | Cria bundle + serve HTTP (porta 8878) |
| `serve-kb.sh` | Servidor | Serve só a KB (~600MB) via HTTP |
| `export-mac-bundle.sh` | Servidor | Bundle antigo (full venv 1.8GB) |
| `setup-complete.sh` | Mac | Setup completo (API key + start services) |
| `setup-mac.sh` | Mac | Setup interactivo (KB, API key, servidor) |
| `install.sh` | Mac | Instalador (clone + deps + build) |

### Nota Importante

O bundle (~724MB) **não** cabe num release GitHub como asset. O fluxo é sempre:
1. DMG pequeno instala o app (~200MB)
2. First-run descarga bundle (~724MB) do servidor

Se o Mac e servidor estiverem na **mesma rede local**, a transferência demora ~3-5 min (100Mbps). Por USB é mais rápido.

**DMG build:** O workflow `build-dmg.yml` acciona-se manualmente em:
`https://github.com/AlvaroBiano/AionUi/actions/workflows/build-dmg.yml` → Run workflow → escolher `arm64`.
O gh CLI tem bug com Node 24 (`gh workflow run` fails) — usar a UI web ou API REST se necessário.

---

## Referências

- `references/bianinho-bridge.md` — protocolo completo, 22 comandos, segurança, benchmarks
- `references/icon-park-verified.md` — lista completa de ícones verificados vs ausentes (v1.9.8)
- `references/aionui-interface-02052026.md` — **Interface real do AionUI (pesquisado 02/05/2026):** o que é, características, comparison DMG vs servidor, nota sobre debugging sem DevTools
- `references/aionui-fork-workflow.md` — fork setup, build, add page/IPC bridge
- `references/aionui-fork-workflow.md` — fork setup, build, add page/IPC bridge
- `references/aionui-remote-connection.md` — **como ligar AionUI Mac ao Bianinho no servidor (Tailscale vs cloudflared vs bundle)** *(added 02/05/2026)*
- `references/dmg-build.md` — **DMG build: dmg-license macOS-only, publish:null fix, extraResources extraction, gh CLI workarounds** *(added 02/05/2026)*
- `references/asar-bundle-debug-case.md` — **Case study completo: 4 builds para resolver white screen | extracção ASAR + Python + SWR defensive pattern | root cause: useSiderTeamBadges teams=undefined** *(added 02/05/2026)*
- `references/white-screen-debug-02052026.md`
- `scripts/bianinho-bridge/SPEC.md` — OpenAPI 3.0.3 (no repo)
