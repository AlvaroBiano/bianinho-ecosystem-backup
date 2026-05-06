# AionUI + Hermes ACP — Sessão 03/05/2026

## Problema: Hermes Agent não aparece no picker

## Root Cause
`AcpDetector.ts` regex `/^[a-zA-Z0-9_.-]+$/` rejeita paths com `/`.  
O Hermes está em `/Users/alvarobiano/.hermes/venv/bin/hermes` — path com `/` é filtrado antes de `command -v`.

## Ficheiros modificados

### `/tmp/aionui-mac/src/process/agent/acp/AcpDetector.ts` (linha ~56)
```typescript
// ANTES
cmd => /^[a-zA-Z0-9_.-]+$/

// DEPOIS
cmd => /^[a-zA-Z0-9_./-]+$/
```

## Comandos executados

```bash
# 1. Patch AcpDetector.ts
sed -i 's|cmd => /^\[a-zA-Z0-9_\.-\]+$/|cmd => /^[a-zA-Z0-9_./-]+$/|' src/process/agent/acp/AcpDetector.ts

# 2. Rebuild better-sqlite3 para Electron 37.10.3
npm rebuild better-sqlite3 --runtime=electron --target=37.10.3

# 3. Install acp_adapter no Hermes venv
cd ~/.hermes/hermes-agent && ~/.hermes/venv/bin/pip install -e '.[acp]'

# 4. Symlink hermes para PATH
ln -sf ~/.hermes/venv/bin/hermes ~/.local/bin/hermes

# 5. Build AionUI
cd /tmp/aionui-mac && bunx electron-vite build

# 6. Instalar DMG e remover quarantine
sudo xattr -rd com.apple.quarantine /Applications/AionUI.app

# 7. Launch
open -n /Applications/AionUI.app --args --no-sandbox
```

## Verificação

```bash
# Logs do AionUI
tail -20 ~/Library/Logs/AionUi/2026-05-03.log | grep -i "hermes\|detector\|found\|agent"

# Deve mostrar:
# [INFO] acp_adapter.session: Created ACP session ...
# [INFO] acp_adapter.server: Session ... mode switched to default
```

## Estado final
- AionUI 1.9.24 instalado em `/Applications/AionUI.app`
- Hermes Agent aparece no picker ✅
- ACP direct connection (BianinhoBridge abandonado)
- Hermes conectado e a processar sessões

## Ficheiros relevantes
- Repo: `~/repos/aionui-custom` / `/tmp/aionui-mac`
- Hermes: `/Users/alvarobiano/.hermes/venv/bin/hermes`
- Symlink: `~/.local/bin/hermes`
