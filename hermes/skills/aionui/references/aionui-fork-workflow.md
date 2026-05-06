# AionUI Fork Workflow — Session Notes (01/05/2026)

## Fork Setup

**Repo:** `https://github.com/AlvaroBiano/AionUi`
**Local:** `~/repos/aionui-custom`
**Upstream:** `https://github.com/iOfficeAI/AionUi`

```bash
git clone https://github.com/iOfficeAI/AionUi.git ~/repos/aionui-custom
cd ~/repos/aionui-custom
git remote add alvaro https://github.com/AlvaroBiano/AionUi.git
git push alvaro main:alvaro/main
```

## Build Dependencies

1. **Bun** — não vem pré-instalado:
   ```bash
   curl -fsSL https://bun.sh/install | bash
   export PATH="$HOME/.bun/bin:$PATH"
   ```
   Confirmar: `bun --version`

2. **npm install** — sempre antes do primeiro build:
   ```bash
   npm install --prefer-offline
   ```

3. **Build TypeScript:**
   ```bash
   bunx electron-vite build
   ```
   Output: `~/repos/aionui-custom/out/` → `main/`, `preload/`, `renderer/`

4. **Build completo (.app/.exe):**
   ```bash
   npm run build
   ```
   ⚠️ FALHA com Node 24 + dmg-builder. `bunx electron-vite build` é suficiente.

## Adding a New Page

**Exemplo:** `src/renderer/pages/bianinho/`

### Ficheiros mínimos:
```
src/renderer/pages/bianinho/
  BianinhoPage.tsx      ← componente React principal
  index.ts              ← export { default } from './BianinhoPage'
  index.module.css      ← estilos
```

### Router (`src/renderer/components/layout/Router.tsx`):

```tsx
// 1. Importar (com as outras imports)
const BianinhoPage = React.lazy(() => import('@renderer/pages/bianinho'));

// 2. Adicionar rota DENTRO do <Route element={<ProtectedLayout ...>}>
<Route path='/bianinho' element={withRouteFallback(BianinhoPage)} />
```

## Adding IPC Bridge Handlers

**Padrão do AionUI:** handlers auto-registam-se no import.

### 1. Criar `src/process/bridge/<nome>Bridge.ts`:
```typescript
import { ipcMain } from 'electron';

export function registerFooBridge(): void {
  ipcMain.handle('foo.bar', async (_event, args) => {
    return { ok: true, data: 'result' };
  });
}

registerFooBridge();  // auto-registo
```

### 2. Importar em `src/index.ts` — DENTRO de `handleAppReady()`:
```typescript
const handleAppReady = async () => {
  // ... código existente ...
  registerFooBridge();  // ← aqui, não top-level
};
```

### 3. Adicionar providers ao ipcBridge (`src/common/adapter/ipcBridge.ts`):
```typescript
foo: {
  bar: () => invoke('foo.bar'),
},
```

### 4. Do renderer, chamar via:
```typescript
import { ipcBridge } from '@/common';
const result = await ipcBridge.foo.bar();
```

## Python Bridge (bianinho_bridge.py)

Corre como processo separado (Python subprocess via TCP):

- **Porta:** 18743
- **Protocolo:** JSON sobre TCP, newline-delimited
- **venv:** `~/repos/aionui-custom/bianinho-venv/` (deps: requests, paho-mqtt, psutil)

Para iniciar:
```bash
cd ~/repos/aionui-custom
./bianinho-venv/bin/python3 scripts/bianinho_bridge.py 18743 &
echo $! > ~/repos/aionui-custom/bianinho_bridge.pid
```

Para matar:
```bash
kill $(cat ~/repos/aionui-custom/bianinho_bridge.pid)
```

**Teste (Python socket — `nc` NÃO funciona para este protocolo):**
```python
python3 -c "
import socket, json
sock = socket.socket()
sock.connect(('127.0.0.1', 18743))
sock.send(json.dumps({'cmd':'ping','args':{'echo':'pong'}}).encode()+b'\n')
sock.shutdown(socket.SHUT_WR)
data = b''
while True:
    chunk = sock.recv(4096)
    if not chunk: break
    data += chunk
print(data.decode())
"
```

**Resposta esperada:** `{"ok": true, "pong": "pong", "platform": "linux"}`

## Install Script para Mac (`scripts/install.sh`)

O script de instalação:
1. Verificar dependências (git, node, npm, python3)
2. Clonar o repo
3. Criar venv Python com deps (requests, paho-mqtt, psutil)
4. `npm install`
5. `bunx electron-vite build`
6. Criar launcher em `~/bin/aionui-bianinho`

**Uso no Mac:**
```bash
curl -fsSL https://raw.githubusercontent.com/AlvaroBiano/AionUi/alvaro/main/scripts/install.sh | bash
```

**Login por omissão:** `admin` / `bianinho2026`

## Build Testado

| Comando | Resultado | Nota |
|---------|-----------|------|
| `bunx electron-vite build` | ✅ OK (~41s, 3 alvos) | out/main/, out/preload/, out/renderer/ |
| `npm run build` | ❌ FALHA | dmg-builder + Node 24 |
| `npm install` | ✅ OK | Precisa de internet |

## armadilhas

### Ícones @icon-park/react
Verificar nomes em `node_modules/@icon-park/react/icons.json`. Mapeamento confirmado:
- `Clock` → `Timer`
- `Pluse` → `Plus`
- `Sparkle` → `Magic`
- `CheckCircle` → `Check`
- `Brain` → `MindMapping`
- `Database` → `HardDisk`

### TCP Bridge — `nc` não funciona
O protocolo requer `shutdown(SHUT_WR)` após enviar. `nc -w3` não recebe resposta.

### IPC Bridge providers
Além do handler IPC, é preciso adicionar ao `ipcBridge` providers em `src/common/adapter/ipcBridge.ts`.

### registerBianinhoBridge()
Chamar DENTRO de `handleAppReady()` em `src/index.ts`, não ao nível do módulo.

## Ficheiros Criados (01/05/2026)

```
scripts/bianinho_bridge.py        — Python TCP bridge (porta 18743)
scripts/install.sh               — instalador Mac/Linux
src/common/chat/bianinho/types.ts
src/common/chat/bianinho/pythonBridge.ts
src/common/chat/bianinho/authManager.ts      — login PBKDF2 + AES-256-GCM
src/common/chat/bianinho/syncDaemon.ts       — sync bidireccional
src/common/chat/bianinho/index.ts
src/process/bridge/bianinhoBridge.ts         — IPC handlers main
src/renderer/pages/bianinho/BianinhoPage.tsx — dashboard UI
src/renderer/pages/bianinho/index.module.css
src/renderer/pages/bianinho/index.ts
src/common/adapter/ipcBridge.ts             — modified: added bianinho providers
src/renderer/components/layout/Router.tsx    — modified: added /bianinho route
src/index.ts                                 — modified: registerBianinhoBridge()
```
