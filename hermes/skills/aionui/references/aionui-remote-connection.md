# AionUI Mac → Bianinho Servidor: Arquitectura de Ligação

**Data:** 02/05/2026
**Problema:** Álvaro quer usar AionUI no Mac para aceder a TODO o Bianinho (RAG, skills, inbox, tudo). O Bianinho está no servidor Linux, não no Mac.

---

## Situação Actual do Servidor

O servidor **não tem portas de entrada acessíveis do exterior**:

| Porta | Interno | Externo (186.235.80.200) |
|-------|---------|--------------------------|
| 22 (SSH) | ✅ aberta | ❌ firewall bloqueia |
| 80/443 | ✅ aberta | ❌ firewall bloqueia |
| 8080/8081 | ✅ aberta | ❌ firewall bloqueia |
| 18743 | ✅ aberta | ❌ firewall bloqueia |

O servidor está atrás de NAT. A única saída para o exterior é o túnel cloudflared existente (`tunnel: d532ba47-1f57-4c2d-8622-011a259b5a90` → `http://localhost:5123`, ou seja, só expõe o SAC Bot).

---

## O Problema com o BianinhoBridge Actual

O BianinhoBridge actual (`scripts/bianinho_bridge.py`) foi desenhado para funcionar **100% local**:

```
AionUI (Mac) → BianinhoBridge (Mac) → ~/.hermes (Mac) + ~/KnowledgeBase (Mac)
```

Espera que `~/.hermes` e `~/KnowledgeBase` existam no mesmo computador que o AionUI. No Mac, esses paths não existem.

---

## Soluções Possíveis

### Opção A — Tailscale (RECOMENDADA)

Tailscale cria uma VPN ponto-a-ponto encriptada. Ambos (Mac e servidor) ficam na mesma rede virtual `100.x.y.z`, sem NAT, sem precisar de portas abertas.

**Passos:**
1. Álvaro instala Tailscale no Mac (app da Mac App Store ou download)
2. Álvaro instala Tailscale no servidor: `curl -fsSL https://tailscale.com/install.sh | sh`
3. Álvaro faz login no Tailscale no servidor com o auth key
4. Servidor fica com IP tipo `100.84.123.45`
5. Mac fica com IP tipo `100.79.189.95`
6. O MacLiga-se ao servidor pelo IP Tailscale: `http://100.84.123.45:18743` (BianinhoBridge)

**Vantagens:**
- Sem custos para até 100 dispositivos
- Não precisa de portas abertas
- Funciona mesmo que o servidor mude de rede
- Latência baixa (directa, não passa por relay)

**Passos no servidor:**
```bash
# Instalar Tailscale
curl -fsSL https://tailscale.com/install.sh | sh

# Starting Tailscale (precisas de um auth key de tailscale.com)
tailscale up --authkey=<AUTH_KEY>
# OU: tailscale login (abre link para autenticar)

# Obter IP Tailscale
tailscale ip -4
```

### Opção B — Cloudflared + API HTTP Hermes

Criar um endpoint HTTP no servidor que expõe os comandos do Bianinho via REST API, e ligar o AionUI a esse endpoint.

**Problema:** Expor o Hermes na internet requer autenticação forte, rate limiting, validação de payloads — trabalho significativo de segurança.

### Opção C — Bundle Completo no Mac

A "Opção A" do skill `aionui` — instalar o Hermes e Knowledge Base completos no Mac via bundle. O Mac teria tudo local.

**Problema:** Bundle são ~900MB. RAG local no Mac precisa de `lancedb`. É pesado e significa ter duas bases de conhecimento sincronizadas.

---

## Arquitectura Alvo com Tailscale

```
┌─────────────────────┐          Tailscale VPN           ┌─────────────────────┐
│      MacBook        │ ◄─────── 100.79.189.95 ──────── │    Servidor Linux   │
│                     │                                  │                     │
│   AionUI (DMG)     │                                  │  Hermes + Bianinho  │
│   BianinhoBridge    │ ──────── 100.84.123.45:18743 ──►│  ~/KnowledgeBase    │
│   (cliente TCP)    │                                  │  ~/hermes           │
│                     │                                  │  porta 18743 (TCP)  │
└─────────────────────┘                                  └─────────────────────┘
```

---

## Modificações Necessárias no BianinhoBridge

### 1. Ouvir em todas as interfaces (não só 127.0.0.1)

```python
# scripts/bianinho_bridge.py
HOST = '0.0.0.0'  # Em vez de '127.0.0.1'
```

### 2. Firewall local (Tailscale IP only)

```python
ALLOWED_TAILSCALE_IPS = ['100.79.189.95']  # IP do MacBook

def is_allowed(ip: str) -> bool:
    return ip in ALLOWED_TAILSCALE_IPS
```

### 3. No Mac — apontar para o IP do servidor

```typescript
// src/common/chat/bianinho/pythonBridge.ts
const BRIDGE_HOST = '100.84.123.45';  // IP Tailscale do servidor
const BRIDGE_PORT = 18743;
```

---

## Prioridade

1. **Tailscale** — solução mais limpa e rápida
2. Bundle completo no Mac — válido mas ~900MB e duas bases de conhecimento
3. REST API via cloudflared — trabalho de segurança significativo

**Próximo passo:** Álvaro instala Tailscale no Mac e dá auth key do servidor para configurar.
