# DMG Build — electron-builder macOS

## Critical constraint: dmg-license requires macOS

`dmg-license` (dependency of `dmg-builder`) **cannot be installed on Linux**:

```
npm error EBADPLATFORM: unsupported platform for iconv-corefoundation@1.1.7
  wanted: {"os":"darwin"} (current: {"os":"linux"})
```

**Consequence:** `node scripts/build-with-builder.js --mac` fails on Linux with `Cannot find module 'dmg-license'`.

**Solution:** DMG builds must run on GitHub Actions `macos-14` runner. Linux can build `.deb` fine.

## Fix: publish: null

Even with `--publish=never`, electron-builder may still fail with:

```
GitHub Personal Access Token is not set, neither programmatically, nor using env "GH_TOKEN"
```

**Fix in `electron-builder.yml`:**

```yaml
publish: null  # Disabled — use --publish=never to skip publishing entirely
```

Without `publish: null`, the `publish:` block with `provider: github` triggers a token check even in `never` mode.

## Build commands

| Command | Platform | Output |
|---------|----------|--------|
| `npm run package` | Any | `out/` (electron-vite only) |
| `node scripts/build-with-builder.js --mac --arm64 --publish=never` | macOS only | `.dmg` |
| `node scripts/build-with-builder.js --linux --x64 --publish=never` | Linux | `.deb` |

## extraResources in packaged .app

In the built `.app` bundle:

```
Contents/Resources/
├── bianinho/           ← BianinhoBridge + scripts
├── hermes-source/      ← Hermes Agent source (42MB)
├── bundled-bun/
├── hub/
└── app.asar
```

The main process must extract these to `~/Library/ApplicationSupport/AionUI/` on first launch:

```typescript
// process.resourcesPath = Contents/Resources/ inside the .app
const resourceBianinho = path.join(process.resourcesPath!, 'bianinho');
const resourceHermes = path.join(process.resourcesPath!, 'hermes-source');
const bianinhoDest = path.join(app.getPath('home'), 'Library/ApplicationSupport/AionUI');
```

Use a marker file (`.extracted`) to avoid re-copying on every launch.

## Workflow dispatch via API (when gh CLI is broken)

When `gh workflow run` fails due to gh bug with Node 24 (`Cannot read properties of undefined (reading 'options')`), trigger via GitHub REST API with token from `~/.netrc`:

```python
import urllib.request, json, netrc

n = netrc.netrc()
token = n.authenticators('github.com')[1]

# Get workflow ID
req = urllib.request.Request(
    'https://api.github.com/repos/OWNER/REPO/actions/workflows',
    headers={'Authorization': f'token {token}', 'Accept': 'application/vnd.github.v3+json'}
)
with urllib.request.urlopen(req) as resp:
    data = json.loads(resp.read())
    wf_id = next(w['id'] for w in data['workflows'] if 'dmg' in w['name'].lower())

# Dispatch
dispatch_req = urllib.request.Request(
    f'https://api.github.com/repos/OWNER/REPO/actions/workflows/{wf_id}/dispatches',
    method='POST',
    data=json.dumps({'ref': 'main', 'inputs': {'arch': 'arm64'}}).encode(),
    headers={'Authorization': f'token {token}', 'Accept': 'application/vnd.github.v3+json',
             'Content-Type': 'application/vnd.github.v3+json'}
)
urllib.request.urlopen(dispatch_req)
```

**Note:** Token from `~/.netrc` may need `chmod 600 ~/.netrc` first. Token may still be invalid if GitHub token doesn't have `workflows` scope.

## DMG size estimation

| Component | Size |
|-----------|------|
| AionUI Electron app | ~150MB |
| BianinhoBridge + scripts | ~88KB |
| Hermes source | ~42MB |
| bundled-bun | varies |
| **Total DMG** | **~200-250MB** |
| Python venv (lancedb) | ~382MB (first-run, pip install) |
| Knowledge Base | ~500MB (first-run, from server) |

The venv + KB are **not bundled** — created/downloaded on first-run setup, keeping the DMG small.

## Bundle transfer strategy (Opção Completa)

Since venv and KB can't be bundled (Linux pip packages ≠ macOS, KB = 1.1GB):

1. **DMG (~200MB):** Installs AionUI + BianinhoBridge + Hermes source
2. **First-run:** `setup-complete.sh` creates venv + downloads KB from server (~900MB total)
3. **Alternative:** Server runs `export-lean-bundle.sh` → creates `.tar.gz` → user downloads via USB or LAN

Bundle complete size (validated 01/05/2026): **724MB** compressed (MD5: `2c3dcf029de8800ab0db251fa870421d`).

## White Screen — Debugging Sem DevTools (RESOLVIDO — 02/05/2026)

O white screen com `e.map is not a function` foi diagnosed e resolvido **sem acesso a DevTools** — o Álvaro não conseguiu abrir DevTools no Mac. As **4 causas raiz** foram identificadas e corrigidas.

### Fluxo de debug cego (sempre aplicar na ordem)

1. **Fix `isDesktopRuntime`** — causa mais provável de ecrã branco total
   -Ficheiro: `src/renderer/hooks/context/AuthContext.tsx`
   ```typescript
   // ANTES:
   const isDesktopRuntime = typeof window !== 'undefined' && Boolean(window.electronAPI);
   // DEPOIS:
   const isDesktopRuntime = true;
   ```
   Sem isto, o app tenta ir à rede buscar utilizador → `status === 'checking'` para sempre → Router bloqueado → ecrã branco.

2. **Adicionar IPC handlers em falta** com fallback seguro
   - Ficheiro: `src/process/bridge/bianinhoBridge.ts`
   - Handlers que faltavam: `ragStats`, `inboxList`, `cycleStatus`, `memoryGet`, `memorySet`, `ragSearch`, `ragBackup`, `inboxAdd`, `inboxDone`, `inboxDelete`
   - **Padrão:** qualquer handler deve retornar estrutura segura quando o bridge falha
   ```typescript
   ipcMain.handle('bianinho.inboxList', async () => {
     const result = await tcpSend('inbox_list');
     if (result && typeof result === 'object' && 'items' in result) return result;
     return { count: 0, items: [] };  // fallback — nunca null
   });
   ```

3. **Guardar `.map()` no renderer**
   - Ficheiros: `src/renderer/pages/bianinho/BianinhoPage.tsx`, `GuidPage.tsx`
   - Validar resultado do IPC antes de guardar na state
   ```typescript
   const result = await ipcBridge.bianinho.listSkills.invoke();
   if (result && typeof result === 'object' && Array.isArray((result as any).skills)) {
     setSkillsInfo(result as SkillsInfo);
   } else {
     setSkillsInfo({ count: 0, skills: [] });  // fallback seguro
   }
   ```
   - Na renderização: `ragStats?.categories?.length > 0` em vez de `ragStats.categories.length > 0`

4. **Push + rebuild DMG**
   ```python
   # Workflow dispatch via API REST
   urllib.request.Request(
     'https://api.github.com/repos/AlvaroBiano/AionUi/actions/workflows/269706228/dispatches',
     method='POST',
     data=json.dumps({'ref': 'main', 'inputs': {'arch': 'arm64'}}).encode(),
     headers={'Authorization': f'token {token}', 'Content-Type': 'application/vnd.github.v3+json'}
   )
   ```
   Build demora ~10-15 min. Artifact: `AionUI-Bianinho-arm64.dmg` (~257MB).

### Como confirmar que funcionou

No Mac, após instalar o novo DMG:
1. Abrir AionUI — deve mostrar a interface (GuidPage ou login)
2. Se ainda branco: o problema é `isDesktopRuntime` ou o preload não está a expor `electronAPI` correctamente
3. Para verificar: abrir o app por linha de comando:
   ```bash
   /Applications/AionUI.app/Contents/MacOS/AionUI --no-sandbox 2>&1 | head -30
   ```

### Download do artifact DMG

```bash
# gh CLI funciona para download (não tem o bug do Node 24)
gh api repos/AlvaroBiano/AionUi/actions/runs/25252230954/artifacts --jq '.artifacts[0].id'
# Output: 6763103414

ARTIFACT_ID=6763103414
gh api repos/AlvaroBiano/AionUi/actions/artifacts/$ARTIFACT_ID/zip > /tmp/AionUi.dmg.zip

# Extrair — GitHub sempre zipa artifacts
unzip -o /tmp/AionUi.dmg.zip && ls *.dmg

# Upload para release
gh release create v1.9.24-fix2 --repo AlvaroBiano/AionUi --notes "..."
gh release upload v1.9.24-fix2 /tmp/AionUi.dmg.zip --repo AlvaroBiano/AionUi
# URL: https://github.com/AlvaroBiano/AionUi/releases/download/v1.9.24-fix2/AionUi-1.9.24-mac-arm64.dmg
```

### Padrão de IPC handler defensivo (regra)

Todos os handlers IPC em `bianinhoBridge.ts` devem seguir esta regra:

```typescript
// REGRA: SEMPRE retornar fallback correcto quando o bridge falha
ipcMain.handle('bianinho.<method>', async () => {
  const result = await tcpSend('<cmd>');
  // Validar estrutura antes de retornar
  if (result && typeof result === 'object' && 'expected_field' in result) {
    return result;
  }
  // Fallback que o renderer sabe tratar
  return { expected_field: <tipo_default> };
});
```

Se o renderer também precisa de proteger:
```typescript
const result = await ipcBridge.bianinho.<method>.invoke();
if (result && typeof result === 'object' && 'expected_field' in result) {
  setState(result);
} else {
  setState(<default_value>);
}
```

## extractBianinhoResources() — extracção de recursos do DMG

```typescript
// src/index.ts — DENTRO de handleAppReady(), ANTES de registerBianinhoBridge()
async function extractBianinhoResources(): Promise<void> {
  if (process.platform !== 'darwin') return;
  if (!app.isPackaged) return;

  const appSupport = path.join(app.getPath('home'), 'Library/ApplicationSupport/AionUI');
  const bianinhoDest = path.join(appSupport, 'bianinho');
  const hermesDest = path.join(appSupport, 'hermes');
  const resourceBianinho = path.join(process.resourcesPath!, 'bianinho');
  const resourceHermes = path.join(process.resourcesPath!, 'hermes-source');
  const markerFile = path.join(bianinhoDest, '.extracted');

  if (fs.existsSync(markerFile)) return;

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
  const launcher = path.join(bianinhoDest, 'hermes-launcher.sh');
  if (fs.existsSync(launcher)) fs.chmodSync(launcher, 0o755);
}
```
