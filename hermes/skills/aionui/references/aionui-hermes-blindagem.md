# Hermes Blindagem Permanente — AionUI Patch Auto-Restore

**Data:** 03/05/2026
**Problema:** Hermes aparece em New Chat mas NÃO no Teams Leader dropdown
**Solução:** Patch dual-location + LaunchAgent auto-restore

---

## Root Cause — Dual Location Issue

O Hermes precisava de estar em **duas localizações** para aparecer no Teams Leader:

| Localização | Ficheiro | Set | Estado |
|---|---|---|---|
| Main process | `out/main/index.js` | `KNOWN_TEAM_CAPABLE_BACKENDS` | ✅ Já tinha 'hermes' |
| **Renderer** | `out/renderer/assets/index-*.js` | `aAt = new Set([...])` | ❌ NÃO tinha 'hermes' |

**Porque é que o Teams Leader usa o renderer Set:**

```
TeamCreateModal → useConversationAgents() → filterTeamSupportedAgents()
  → isTeamCapableBackend(backend, cachedInitResults)
    → aAt.has(backend)  ← renderer bundle Set, NÃO o main process Set
```

New Chat usa o main process `KNOWN_TEAM_CAPABLE_BACKENDS` → Hermes aparecia lá.
Teams Leader usa o renderer's `aAt` Set → Hermes NÃO aparecia.

**Nota:** O `aAt = new Set(...)` no renderer é **hardcoded no bundle compilado**, sem correspondência directa no source TypeScript. O source `teamTypes.ts` define `KNOWN_TEAM_CAPABLE_BACKENDS` (main process), mas o renderer tem a sua própria cópia inline no bundle.

---

## Ficheiros Criados

### 1. Backup permanente do bundle
```
~/Library/Application Support/hermes/aionui-hermes-patch/
└── renderer/assets/index-CVd-wlNn.js  ← bundle PATCHED (1.7MB)
```

### 2. Source TypeScript patchado
```
~/Library/Application Support/hermes/aionui-hermes-patch/main/teamTypes.ts
```
Linha 16:
```typescript
// ANTES:
const KNOWN_TEAM_CAPABLE_BACKENDS = new Set(['gemini', 'claude', 'codex', 'aionrs']);

// DEPOIS:
const KNOWN_TEAM_CAPABLE_BACKENDS = new Set(['gemini', 'claude', 'codex', 'aionrs', 'hermes']);
```
Este source patchado serve para quando o AionUI for recompilado — o Hermes já vem incluído.

### 3. Backup do app.asar
```
~/Library/Application Support/hermes/aionui-hermes-patch/app_backup.asar  (442MB)
```

### 4. Script de restore
`~/Library/Application Support/hermes/aionui-hermes-patch/restore_hermes_patch.sh`

### 5. LaunchAgent
`~/Library/LaunchAgents/com.bianinho.aionui-hermes-patch.plist`

---

## Script de Restore Completo

```bash
#!/bin/bash
# restore_hermes_patch.sh — re-aplica patch Hermes após actualização do AionUI
set -e

APP_PATH="/Applications/AionUi.app"
RESOURCES_PATH="$APP_PATH/Contents/Resources"
ASAR_PATH="$RESOURCES_PATH/app.asar"
PATCH_DIR="$HOME/Library/Application Support/hermes/aionui-hermes-patch"
LOG="$PATCH_DIR/restore.log"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG"
}

log "=== Starting Hermes patch restore ==="

[ -d "$APP_PATH" ] || { log "ERROR: AionUI app not found"; exit 1; }
[ -f "$ASAR_PATH" ] || { log "ERROR: app.asar not found"; exit 1; }

PATCHED_BUNDLE="$PATCH_DIR/renderer/assets/index-CVd-wlNn.js"
[ -f "$PATCHED_BUNDLE" ] || { log "ERROR: Patched bundle not found"; exit 1; }

TMP_DIR=$(mktemp -d)
cd "$TMP_DIR"

log "Extracting app.asar..."
npx asar extract "$ASAR_PATH" app_extracted

# Encontrar o renderer bundle (o hash muda entre versões)
BUNDLE_PATH=$(ls app_extracted/out/renderer/assets/index-*.js 2>/dev/null | head -1)

if grep -q 'aAt=new Set(\["gemini","claude","codex","aionrs"\])' "$BUNDLE_PATH" 2>/dev/null; then
    log "Applying renderer bundle patch..."
    sed -i '' 's/aAt=new Set(\["gemini","claude","codex","aionrs"\])/aAt=new Set(["gemini","claude","codex","aionrs","hermes"])/g' "$BUNDLE_PATH"
    log "Bundle patched successfully"
elif grep -q 'aAt=new Set(\["gemini","claude","codex","aionrs","hermes"\])' "$BUNDLE_PATH" 2>/dev/null; then
    log "Bundle already patched — no action needed"
    rm -rf "$TMP_DIR"
    exit 0
else
    log "WARNING: Could not determine patch status, proceeding..."
fi

log "Repacking app.asar..."
rm -f "$ASAR_PATH"
npx asar pack app_extracted "$ASAR_PATH"

log "Re-signing AionUI app..."
codesign -f -s - "$APP_PATH"

rm -rf "$TMP_DIR"
log "=== Hermes patch restore complete ==="
```

---

## LaunchAgent plist

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.bianinho.aionui-hermes-patch</string>
    <key>ProgramArguments</key>
    <array>
        <string>/bin/bash</string>
        <string>/Users/alvarobiano/Library/Application Support/hermes/aionui-hermes-patch/restore_hermes_patch.sh</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>StartInterval</key>
    <integer>300</integer>
    <key>StandardOutPath</key>
    <string>/Users/alvarobiano/Library/Application Support/hermes/aionui-hermes-patch/launchd.log</string>
    <key>StandardErrorPath</key>
    <string>/Users/alvarobiano/Library/Application Support/hermes/aionui-hermes-patch/launchd.err</string>
    <key>ProcessType</key>
    <string>Background</string>
</dict>
</plist>
```

---

## Fluxo After AionUI Update

1. Utilizador instala novo DMG → `app.asar` substituído (perde patch)
2. LaunchAgent detecta dentro de ≤5 minutos
3. `restore_hermes_patch.sh` corre
4. Extrai novo `app.asar` → faz sed → repack → re-assina
5. Hermes volta a aparecer no Teams Leader

---

## Notas Importantes

1. **O renderer Set é sempre necessário** — mesmo que o source TypeScript já tenha 'hermes', o bundle compilado tem de ser patchado manualmente porque o `aAt` Set está inline no JS compilado, não como referência ao TypeScript.

2. **codesign é obrigatório** — qualquer modificação ao `.app` contents quebra a code signature do macOS. Sem `codesign -f -s -`, o app não abre.

3. **Não usar KeepAlive** — o script já tem protecção contra correr desnecessariamente (verifica se o patch já existe). Mas o LaunchAgent NÃO deve ter `KeepAlive: true` para evitar loops com serviços que já têm restart logic interno.

4. **Verificar antes de forçar** — o LaunchAgent corre a cada 5 min. Para forçar agora: `launchctl start com.bianinho.aionui-hermes-patch`
