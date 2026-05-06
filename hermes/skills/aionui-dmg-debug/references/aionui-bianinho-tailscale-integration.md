# AionUI + BianinhoBridge HTTP Server — Integração via Tailscale
**Criado:** 02/05/2026

## Arquitectura

```
┌─────────────────────┐       Tailscale        ┌──────────────────────────┐
│  AionUI (Mac DMG)  │ ──────────────────────▶│  BianinhoBridge HTTP      │
│  100.x.y.z:18743   │   100.79.189.95:18743  │ bianinho_bridge_server.py │
│                     │◀────────────────────── │  no servidor Linux        │
└─────────────────────┘       JSON/HTTP        │  Ligado ao Hermes:        │
                                             │  • RAG (porta 3101)      │
                                             │  • Skills (~/.hermes)    │
                                             │  • Inbox (inbox.json)    │
                                             │  • Memory                │
                                             └──────────────────────────┘
```

## Pré-requisitos

- Tailscale instalado e ligado no Mac E no servidor
- IP Tailscale do servidor: `100.79.189.95`
- Porta 18743 aberta no firewall do servidor (Tailscale é peer-to-peer, firewall local não bloqueia)

## Servidor: bianinho_bridge_server.py

**Localização:** `~/repos/aionui-custom/scripts/bianinho_bridge_server.py`

Este é um servidor HTTP Python (não precisa de venv, usa libs std) que:
- Escuta em `100.79.189.95:18743` (Tailscale IP)
- Liga localmente ao RAG server em `127.0.0.1:3101`
- Expõe endpoints REST para: RAG, inbox, skills, memory, config

**Endpoints disponíveis:**
```
GET  /ping, /status, /platform_info, /check_hermes
GET  /list_skills, /rag_stats, /inbox_list, /cycle_status
GET  /memory?key=..., /config?key=...
POST /rag_search, /inbox_add, /inbox_done, /inbox_delete
POST /memory_set, /config_set, /cycle_trigger, /token
```

## Electron: bianinhoBridge.ts (renderer → server)

**Localização:** `~/repos/aionui-custom/src/process/bridge/bianinhoBridge.ts`

Substitui o TCP bridge original por HTTP via Electron `net.request`:

```typescript
async function httpSend(method: 'GET' | 'POST', path: string, body?: Record<string, unknown>): Promise<unknown> {
  const url = `http://${BRIDGE_HOST}:${BRIDGE_PORT}${path}`;
  return new Promise((resolve) => {
    const req = net.request({ method, url });
    req.setHeader('Content-Type', 'application/json');
    if (bodyStr) { req.setHeader('Content-Length', String(Buffer.byteLength(bodyStr))); }
    let responseData = '';
    req.on('response', (response) => {
      response.on('data', (chunk) => { responseData += chunk.toString(); });
      response.on('end', () => {
        try { resolve(responseData ? JSON.parse(responseData) : { ok: false }); }
        catch { resolve({ ok: false, error: 'Invalid JSON' }); }
      });
    });
    req.on('error', (err) => resolve({ ok: false, error: err.message }));
    if (bodyStr) { req.write(bodyStr); }
    req.end();
    setTimeout(() => resolve({ ok: false, error: 'timeout' }), TIMEOUT_MS);
  });
}
```

**Nota:** `BRIDGE_HOST = '100.79.189.95'` (hardcoded para já — futuro: configdinâmica)

## Serviço systemd

**Ficheiro:** `~/.config/systemd/user/bianinho-bridge-server.service`

```ini
[Unit]
Description=BianinhoBridge HTTP Server — ligacao AionUI ao Hermes via Tailscale
After=network.target tailscaled.service

[Service]
Type=simple
ExecStart=/usr/bin/python3 /home/alvarobiano/repos/aionui-custom/scripts/bianinho_bridge_server.py
WorkingDirectory=/home/alvarobiano/repos/aionui-custom
Restart=on-failure
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=default.target
```

**Comandos:**
```bash
systemctl --user daemon-reload
systemctl --user enable bianinho-bridge-server
systemctl --user start bianinho-bridge-server
systemctl --user status bianinho-bridge-server
journalctl --user-unit bianinho-bridge-server -f
```

## IP Tailscale — Comandos úteis

```bash
# Ver IP atual e peers
tailscale status

# IP do servidor: 100.79.189.95
# Mac do Álvaro: 100.113.160.102 (pode mudar quando reconnecta)

# Testar conectividade
curl http://100.79.189.95:18743/ping
```

## RAG Server (porta 3101)

O servidor HTTPliga também ao RAG server que já existe:

```
curl http://127.0.0.1:3101/health
# {"status":"ok","metodoten_chunks":16,"initialized":true}
```

Formato RAG search:
```
POST /rag_search
Body: {"query": "...", "category": "chunks", "topK": 5}
Response: {"results": [...]}
```

## Limitações Conhecidas

1. **IP Tailscale hardcoded** no `bianinhoBridge.ts` — se o IP do servidor mudar, precisa recompilar
2. **Sem autenticação** — qualquer peer Tailscale pode aceder (Tailscale auth é a segurança)
3. **Não é bidirecional** — só o Mac inicia conexões ao servidor (Tailscale não precisa de port forwarding)
4. **Skills execution não implementada** — só leitura (list, search)

## Se o Mac não conecta

1. Verificar Tailscale ligado no Mac: `tailscale status`
2. Pingar o servidor: `ping 100.79.189.95`
3. Testar porta: `curl http://100.79.189.95:18743/ping`
4. Ver logs no servidor: `journalctl --user-unit bianinho-bridge-server -n 20`
5. Reiniciar serviço: `systemctl --user restart bianinho-bridge-server`
