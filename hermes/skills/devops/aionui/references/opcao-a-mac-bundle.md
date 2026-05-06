# Opção A — Mac Bundle Workflow

## Overview

Transferir o Bianinho completo (Hermes + KB + Skills) do servidor Linux para o Mac, para uso 100% local sem dependência do servidor.

## Quick Start

### Server side (once)
```bash
cd ~/repos/aionui-custom
bash scripts/export-mac-bundle.sh both
```

### Mac side (once)
```bash
# Install
curl -fsSL https://raw.githubusercontent.com/AlvaroBiano/AionUi/main/scripts/install.sh | bash

# Download bundle (server must be running export-mac-bundle.sh)
curl -o ~/Downloads/bianinho-mac-full.tar.gz http://SERVER_IP:8878/download

# Extract
tar -xzf ~/Downloads/bianinho-mac-full.tar.gz \
  -C ~/Library/ApplicationSupport/AionUI/

# Setup
bash ~/AionUI-Bianinho/scripts/setup-mac.sh
```

## Scripts Detail

### export-mac-bundle.sh (servidor)

Cria archive com Hermes + venv + KB + skills, serve via HTTP na porta 8878.

**Uso:**
```bash
bash export-mac-bundle.sh bundle    # só criar archive
bash export-mac-bundle.sh serve     # só servir
bash export-mac-bundle.sh both      # criar + servir (default)
```

**O que inclui:**
- `hermes/` — código fonte do Hermes Agent
- `venv/` — Python venv com packages (requests, paho-mqtt, psutil, lancedb, fastapi, uvicorn)
- `knowledge_db/` — LanceDB KB (~65k chunks)
- `skills/` — 72 skills do Bianinho
- `config/` — bridge keys e configs (sem API keys)

**Output:** `/tmp/bianinho-mac-full.tar.gz`

**Serve na porta:** 8878

**Testar conexão:**
```bash
curl -I http://SERVER_IP:8878/
# 200 OK = servidor activo
```

### serve-kb.sh (servidor, alternativa mais rápida)

Se só precisas da KB (Hermes já existe localmente), usa este:

```bash
bash scripts/serve-kb.sh both
# Cria /tmp/bianinho-kb-mac.tar.gz (~600MB)
# Serve na porta 8877
```

**Download no Mac:**
```bash
curl -o ~/Downloads/bianinho-kb.tar.gz http://SERVER_IP:8877/download
tar -xzf ~/Downloads/bianinho-kb.tar.gz \
  -C ~/Library/ApplicationSupport/AionUI/knowledge_db/
```

### setup-mac.sh (Mac, interactivo)

Setup que pergunta:
1. Descarregar KB do servidor ou importar de ficheiro?
2. IP do servidor para download
3. MiniMax API key
4. Servidor Hermes opcional (para modo híbrido)

**Executar após extrair o bundle:**
```bash
bash ~/AionUI-Bianinho/scripts/setup-mac.sh
```

## KB Sizes (measured 01/05/2026)

```
KB source:  ~/KnowledgeBase/knowledge_db/
KB compressed (tar.gz): 599MB
Compression ratio: ~55%

Hermes venv:  ~/.hermes/hermes-agent/venv/
Hermes source:  ~/.hermes/hermes-agent/src/

Full bundle (uncompressed): ~3.1GB
Full bundle (tar.gz): ~400-600MB
```

## Transfer Methods

### 1. HTTP (mais rápido em rede local)
```bash
# Servidor
bash scripts/export-mac-bundle.sh serve

# Mac
curl -o ~/Downloads/bianinho-mac-full.tar.gz http://IP:8878/download
```

### 2. SCP (se HTTP não funcionar)
```bash
# Do servidor
scp /tmp/bianinho-mac-full.tar.gz macbook@IP:/tmp/

# No Mac
tar -xzf /tmp/bianinho-mac-full.tar.gz \
  -C ~/Library/ApplicationSupport/AionUI/
```

### 3. USB
```bash
# Copiar /tmp/bianinho-mac-full.tar.gz para USB no servidor
# No Mac: copiar para ~/Downloads/
tar -xzf ~/Downloads/bianinho-mac-full.tar.gz \
  -C ~/Library/ApplicationSupport/AionUI/
```

## Troubleshooting

### "Connection refused" ao descarregar
Servidor não está a correr. No servidor:
```bash
bash scripts/export-mac-bundle.sh serve
```

### "404 Not Found"
O path correcto é `/download` (não `/`):
```
http://IP:8878/download
```

### Bundle muito grande para transferir
Usa `serve-kb.sh` em vez de `export-mac-bundle.sh` — só ~600MB em vez de ~500MB.

### MD5 mismatch após download
Verifica integridade:
```bash
md5sum ~/Downloads/bianinho-mac-full.tar.gz
# Compara com o MD5 mostrado pelo servidor
```

## State (01/05/2026)

- Fork: `github.com/AlvaroBiano/AionUi`, commit `dee83f6`
- Scripts criados: `export-mac-bundle.sh`, `serve-kb.sh`, `setup-mac.sh`, `install.sh`
- KB archive testado: `/tmp/knowledge_base.tar.gz` = 599MB
- Bundling completo: **não testado ainda** — primeiro teste completo requer MacBook
