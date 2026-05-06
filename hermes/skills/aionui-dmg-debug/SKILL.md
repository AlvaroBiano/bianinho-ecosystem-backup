---
name: aionui-dmg-debug
description: Debug protocol for AionUI macOS DMG white screen crashes — pattern, fixes, bundle analysis, and workflow.
---

# AionUI macOS DMG — Debug & Fix Protocol

## Contexto
Fork: `github.com/AlvaroBiano/AionUi`, branch `main`, remote `alvaro`.
Repo local: `~/repos/aionui-custom`.

## Workflow de Build DMG

```bash
# 1. Commit + push
cd ~/repos/aionui-custom
git add . && git commit -m "fix: descricao" && git push alvaro main

# 2. Disparar build
gh workflow run build-dmg.yml --field arch=arm64 --repo AlvaroBiano/AionUi

# 3. Obter artifact ID
gh api repos/AlvaroBiano/AionUi/actions/runs?branch=main&per_page=3 --jq '.workflow_runs[0] | "\(.id) \(.head_sha[:8]) \(.status)"'

# 4. Obter SAS URL do artifact (método correcto quando gh falha)
python3 - << 'PYEOF'
import urllib.request, json, re
token = re.search(r'password\s+(\S+)', open('/home/alvarobiano/.netrc').read()).group(1)
headers = {'Authorization': f'token {token}', 'Accept': 'application/vnd.github.v3+json'}
req = urllib.request.Request('https://api.github.com/repos/AlvaroBiano/AionUi/actions/artifacts/ARTIFACT_ID', headers=headers)
with urllib.request.urlopen(req, timeout=15) as r:
    art = json.loads(r.read())
print(art['archive_download_url'])
PYEOF

# 5. Download directo com curl (o gh cli tem bugs com nvm Node 24)
curl -L -o /tmp/output.dmg.zip "SAS_URL_DO_PASSO_4"

# 6. Criar/upload release
gh release create v1.9.x-fixN --repo AlvaroBiano/AionUi --title "v1.9.x-fixN" --notes "fix: desc"
gh release upload v1.9.x-fixN /tmp/output.dmg.zip --repo AlvaroBiano/AionUi
```

**Nota sobre gh CLI**: O `gh run download` e `gh api` podem falhar com HTTP 404 ou "not a git repository" quando usados com Node 24 (nvm). Usa sempre Python urllib para chamadas à API e curl com a SAS URL directa para downloads.

## Padrão do Bug White Screen (e.map is not a function)

### Sintomas
- App abre com ecrã branco
- Erro: `TypeError: e.map is not a function` (ou `e?.map is not a function`)
- Hash do bundle muda consoante o build (ex: `index-B7FSMILK.js`, `index-CBvrP838.js`)
- Stack trace: React reconciler → componente com `.map()` → OptionalChainingInline ou similar

### Root Cause Pattern — CRÍTICO
1. Um hook/componente recebe dados de SWR ou IPC
2. O `ipcBridge.team.list` no DMG (sem BianinhoBridge) retorna um **objeto de erro** `{__bridgeError: true, message: "...", ...}` — **NÃO** `undefined`
3. O código faz `.map()` — crash porque `e` é truthy (o objeto de erro) mas não é array

**Isto é o que fez falhar todas as tentativas iniciais com `?? []`** — o valor não era `null`/`undefined`, era um objeto truthy.

### Como confirmar: objeto de erro vs undefined
```typescript
// No fetcher SWR — isto é o fix definitivo:
.finally((data) => {
  if (Array.isArray(data)) return data;
  console.warn('[useTeamList] IPC returned non-array type:', typeof data, data);
  return [];
})
```

### Padrão de crash no corpo vs useEffect
- Crash no **corpo da função do hook** (render síncrono) → `.map()` recebe `undefined` antes do fetch resolver
- Crash por **objeto de erro** → `.map()` recebe `{__bridgeError: true, ...}` — é truthy, `?? []` não ajuda
- `useEffect` protege contra o primeiro; `Array.isArray()` protege contra ambos

### Fixes Aplicados (commit 95e4a7404)

**useTeamList.ts** — fetcher defensivo (fix primário):
```typescript
useSWR<TTeam[]>(
  `teams/${userId}`,
  () => ipcBridge.team.list.invoke({ userId }).then((data) => {
    if (Array.isArray(data)) return data;
    console.warn('[useTeamList] IPC returned non-array:', data);
    return [];
  }),
  { revalidateOnFocus: false }
);
```
O `.then()` no fetcher SWR é o local correto para a guarda — todos os consumers beneficiam.

**useSiderTeamBadges.ts** — dupla defesa (fix secundário):
```typescript
const safeTeams: TTeam[] = Array.isArray(teams) ? teams : [];
// USA safeTeams em todo o corpo do hook, não só na guarda
// Dentro dos loops: team.agents ?? []
```
`safeTeams` é declarado no início e usado em TODO o hook. `team.agents ?? []` dentro dos loops.

### Regra Defensiva para SWR
- **NUNCA** confiar que SWR retorna array no primeiro render
- O `= []` default do destructuring **não protege** durante a re-renderização rápida
- Sempre usar `const safe = Array.isArray(data) ? data : []` OU `const safe = data ?? []` E verificar dentro de useEffect
- O crash ocorre quando `.map()` é chamado NO CORPO da função (não dentro de useEffect) antes dos dados chegarem

### Análise de Bundle Minificado (para identificar componente exacto)

```python
# Ler bundle do DMG extraído
with open('out/renderer/assets/index-HASH.js') as f:
    content = f.read()
lines = content.split('\n')

# Buscar a linha do crash (ex: linha 7560)
for i in range(7540, 7580):
    if 'e.map' in lines[i] or 'O1t' in lines[i]:
        print(f"Line {i+1}: {lines[i][:400]}")
```

### Como Extrair ASAR (Electron app)

```bash
# Opção 1: com asar CLI
npm install -g asar
asar extract app.asar dest/

# Opção 2: com node (para arquivos grandes)
node -e "
const asar = require('asar');
asar.extractFile('app.asar', 'out/file.js', (err) => { if(err) console.error(err); });
asar.extractAll('app.asar', 'dest/', (err) => { /* done */ });
"
```

### Download de Artifact via Azure Blob SAS URL (quando gh falha)
O `gh run download` pode falhar com "not a git repository" ou HTTP 404 em contextos não-git. Usa a SAS URL direta:

```bash
# Obter SAS URL:
curl -sI "https://api.github.com/repos/AlvaroBiano/AionUi/actions/artifacts/ARTIFACT_ID/zip" \
  -H "Authorization: token $(python3 -c "import re; print(re.search(r'password\s+(\S+)', open('/home/alvarobiano/.netrc').read()).group(1))")"

# O header Location: contém a SAS URL do Azure Blob
# Download direto com curl:
curl -L -o /tmp/output.zip "SAS_URL_DO_LOCATION_HEADER"
```

### Como Identificar o Componente que Crasha

1. Criar ErrorBoundary global (React 19 = `getDerivedStateFromError`, NÃO `componentDidCatch`)
2. Build → DMG → user testa → component stack mostra o caminho do componente
3. Sem source maps, usar análise de bundle + comparar com source code

### Padrão ErrorBoundary (React 19)
### Padrão ErrorBoundary (React 19)
```tsx
// src/renderer/components/ErrorBoundary.tsx
import React from 'react';
class ErrorBoundary extends React.Component<
  { children: React.ReactNode },
  { hasError: boolean; error: Error | null; componentStack: string }
> {
  // React 19: APENAS getDerivedStateFromError — componentDidCatch foi removido
  static getDerivedStateFromError(error: Error) {
    return { hasError: true, error };
  }
  // NOT componentDidCatch — não existe em React 19
  render() {
    if (this.state.hasError) {
      return (
        <div style={{ padding: 20, color: 'red', background: '#fff' }}>
          <h2>Erro de renderização</h2>
          <pre>{this.state.error?.message}</pre>
        </div>
      );
    }
    return this.props.children;
  }
}
```
**Nota**: Em React 19, `componentDidCatch` foi removido. Apenas `getDerivedStateFromError` funciona para ErrorBoundary. O `componentDidCatch` no código original desta skill foi REMOVIDO — não usar.

## Root Cause Definitivo (descoberto em 02/05/2026)

O bug não era `teams === undefined`. Era `teams` sendo um **objeto de erro** retornado pelo IPC bridge quando o BianinhoBridge server está ausente:

```
{ __bridgeError: true, message: "Connection failed: refused", ... }
```

Este objeto é **truthy** — `?? []` não dispara. `OptionalChaining` `?.` também não ajuda. `.map()` é chamado e crasha porque `Object` não tem método `.map()`.

### Como o IPC Bridge retorna erro no DMG
No DMG standalone (sem BianinhoBridge server), `ipcRenderer.invoke()` retorna `undefined` no renderer process, MAS:
- `safeProvider` no `teamBridge.ts` pode envolver isso num objeto de erro
- Ou o valor chega como string/erro via TCP no `bianinhoBridge.ts`

**Conclusão**: a guarda `Array.isArray()` no fetcher SWR (não `??`) é a solução correcta porque lida com qualquer valor não-array — `undefined`, `null`, `{}`, `""`, etc.

## Armadilhas Encontradas

1. **`?? []` não basta — o valor pode ser um objeto de erro** — se `data` é `null`/`undefined`, `?? []` funciona. Mas se for `{__bridgeError: true, message: "..."}`, é truthy e `?? []` não dispara. `Array.isArray()` é mais seguro.

2. **`__bridgeError` é retornado pelo `safeProvider` em `teamBridge.ts`** — quando `listTeams()` falha, o `safeProvider` retorna `{__bridgeError: true, message: "..."}` em vez de lançar excepção. Este objeto é truthy, não `undefined`, por isso `?? []` não ajuda. O fetcher SWR em `useTeamList.ts` deve verificar com `Array.isArray()` E tambem verificar se não é o sentinel `__bridgeError`.

3. **O crash do `useTeamList` pode não ser o problema primário** — se o Team layout (sidebar/badges) crasha, bloqueia toda a navegação, não só o Bianinho. Álvaro reportou "não aparece nada" — isso sugere que a app abre mas o layout principal está crashado.

4. **SWR first render = undefined** — o `= []` default só funciona se o código usar o valor só depois de fetch resolver. Se o hook for chamado antes, recebe `undefined`.

5. **7z não extrai DMG correctamente** — DMG é um formato de disco, não um archive. Para extrair: `7z x file.dmg` cria a estrutura mas pode falhar em links simbólicos. Alternativa: usar `hdiutil` (macOS) ou ferramenta `dmg2img`.

## Ficheiros-Chave do Bug
- `src/renderer/pages/team/hooks/useTeamList.ts`
- `src/renderer/pages/team/hooks/useSiderTeamBadges.ts`
- `src/renderer/components/ErrorBoundary.tsx` (criado nesta sessão)
- `.github/workflows/build-dmg.yml`

### ⚠️ Padrão Crítico: Renderer Bundle vs Main Process Sets (03/05/2026)

**Sintoma:** Hermes Agent aparece em "New Chat" mas **NÃO** aparece em "Teams → New Team → Team Leader".

**Root Cause:** O AionUI Electron tem **DUAS** listas separadas de backends team-capable:

| Localização | Ficheiro | Conteúdo |
|---|---|---|
| Main process | `out/main/index.js` | `"hermes"` ✅ presente |
| Renderer (React UI) | `out/renderer/assets/index-*.js` | `Set(["gemini","claude","codex","aionrs"])` ❌ falta "hermes" |

O Teams Leader dropdown usa o Set do **renderer bundle** (filter `lAt`/`filterTeamSupportedAgents`). O New Chat usa a detecção do main process. Se só o main process for actualizado, o Teams Leader continua sem ver o Hermes.

**Fix: Patching o renderer bundle dentro do app.asar**

⚠️ **Não fazer rebuild do app** (`bun run build`) — quebra módulos nativos e assinatura. Em vez disso, patch directo no asar:

```bash
# 1. Extrair app.asar
asar extract /Applications/AionUi.app/Contents/Resources/app.asar /tmp/aionui-extracted/

# 2. Encontrar o renderer bundle (o nome muda entre versões)
grep -rn "aAt=new Set" /tmp/aionui-extracted/out/renderer/assets/
# Output: index-HASH.js: aAt=new Set(["gemini","claude","codex","aionrs"])

# 3. Patch: adicionar "hermes" ao Set
sed -i '' 's/aAt=new Set(\["gemini","claude","codex","aionrs"\])/aAt=new Set(["gemini","claude","codex","aionrs","hermes"])/' \
  /tmp/aionui-extracted/out/renderer/assets/index-HASH.js

# 4. Backup do asar actual
cp /Applications/AionUi.app/Contents/Resources/app.asar \
   /Applications/AionUi.app/Contents/Resources/app.asar.backup_hermes_v1

# 5. Repack
asar pack /tmp/aionui-extracted/ /tmp/aionui-patched.asar

# 6. Instalar
cp /tmp/aionui-patched.asar /Applications/AionUi.app/Contents/Resources/app.asar

# 7. Re-assinar (CRÍTICO para macOS)
codesign -f -s - /Applications/AionUi.app

# 8. Verificar assinatura
codesign -vv /Applications/AionUi.app  # deve dizer "valid on disk"
```

**Nota:** O filename do renderer bundle (ex: `index-CVd-wlNn.js`) muda entre versões do app. O `grep` do passo 2 encontra sempre o correcto.

**Se o app não abrir após patch:** Restaurar de backup:
```bash
cp /Applications/AionUi.app/Contents/Resources/app.asar.backup_hermes_v1 \
   /Applications/AionUi.app/Contents/Resources/app.asar
codesign -f -s - /Applications/AionUi.app
```

**Cache do ServiceWorker:** O renderer pode usar ServiceWorker que faz cache do JS. Se após o patch o app continuar a não mostrar Hermes, limpar cache:
- Force-quit AionUI
- `rm -rf ~/Library/Application\ Support/AionUi/Cache/`
- Reiniciar

**Lição geral:** Ao investigar bugs de UI no Electron, verificar SEMPRE se o código tem lógica separada no renderer e no main process. O renderer usa bundles minificados que podem ter configurações diferentes das do main process.

---

### BianinhoBridge — Debugging de Conexão (03/05/2026)

### ⚠️ Padrão de Erro Crítico: Hermes Agent ACP Falha com "Agent exited before initialize completed"

**Sintoma no AionUI (logs em `~/Library/Logs/AionUi/YYYY-MM-DD.log`):**
```
Failed to parse JSON message: ACP dependencies not installed.
Install them with:  pip install -e '.[acp]'
SyntaxError: Unexpected token 'I', "Install th"... is not valid JSON

[ACP hermes] Process exited with code 1 [reason: process_exit]
AgentStartupError: Agent exited before initialize completed (code: 1)
```

**Causa:** O `acp_adapter` é um módulo local do repositório hermes-agent. Quando o Electron faz spawn do `hermes acp`, o Python subprocess não tem o directório do hermes-agent repo em `sys.path`, logo `import acp_adapter` falha.

**Fix — executar uma vez:**
```bash
cd ~/.hermes/hermes-agent && pip install -e '.[acp]'
```

**Verificação:**
```bash
~/.hermes/venv/bin/hermes acp
# Deve mostrar: "Starting hermes-agent ACP adapter" e ficar a ouvir (CTRL+C para sair)
```

**Nota:** O `hermes` normal (`hermes chat`, `hermes gateway run`) funciona sem o editable install — só o subprocess `hermes acp` precisa.

---

## ⚠️ REGRA CRÍTICA: Nunca Rebuild do Electron App (Mas Patching Directo do asar É Possível)

### O Que NÃO Fazer
**Nunca fazer `bun run build` nem modificar ficheiros dentro de `/Applications/AionUI.app/`** modificando o source e recompilando. O rebuild cria `app.asar.unpacked/` com módulos nativos compilados para uma versão diferente do Node.js e **invalidou a assinatura de código do macOS** — app morre silenciosamente.

O AionUI tem `~/.local/bin/` no PATH. Para adicionar `hermes` ao PATH do Electron, **não é preciso modificar o app**:

1. **Criar symlink no PATH do sistema** (não dentro do app):
   ```bash
   mkdir -p ~/.local/bin
   ln -sf ~/.hermes/venv/bin/hermes ~/.local/bin/hermes
   ```

2. **Garantir que o PATH é carregado pelo shell do Electron** — adicionar ao `~/.zshrc`:
   ```bash
   echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.zshrc
   ```

3. **Instalar acp_adapter no hermes-agent** (fora do app):
   ```bash
   cd ~/.hermes/hermes-agent && pip install -e '.[acp]'
   ```

4. **Verificar que o Electron consegue ver o hermes** — o `AcpDetector` do AionUI vai procurar no PATH que inclui `~/.local/bin` e `~/.hermes/venv/bin`.

**NUNCA fazer `bun run build` nem modificar ficheiros dentro de `/Applications/AionUI.app/`**. Se uma modificação no source for necessária, a abordagem correcta é pedir um novo DMG build ao GitHub Actions com as alterações mergeadas.

### Padrão de Crash Silencioso do macOS

Quando um app modificado perde a assinatura:
- O `open -a AionUi` retorna `exit 0` mas nenhum processo arranca
- `log show --predicate 'process == "AionUi"' --last 2m` mostra o processo a iniciar e terminar imediatamente
- `~/Library/Logs/DiagnosticReports/` não tem reports (não é treated como crash pelo macOS)
- A solução é sempre: restaurar de backup + re-assinar

### Ficheiros de Backup Criados

```
/Applications/AionUi.app/Contents/Resources/app.asar.backup_before_hermes_fix  # 442MB original
```

**Se o backup não existir**,.download do último DMG funcional via GitHub Actions.

# AionUI — Localhost Integration Reference (03/05/2026, updated 03/05/2026 21h)

## Arquitectura 100% Local (MacBook)

```
AionUI.app (Electron, signed + sealed)
  └─ AcpDetector → finds "hermes" in PATH
        └─ spawns: hermes acp (subprocess, stdio)
              └─ acp_adapter.server → Hermes Agent (minimax API)
                    ├─ RAG LanceDB (localhost:3101)
                    └─ Skills, Inbox, Memory (~/.hermes/)
```

**Nota:** O BianinhoBridge HTTP (port 18743) já não é necessário. O AionUI comunica directamente com o Hermes Agent via ACP (subprocess stdio).

**Nota de mudança:** Previously used Tailscale IP `100.79.189.95`. Now uses `127.0.0.1` after bridge server was patched to bind localhost.

### Como Verificar se o Bridge Conecta

**O problema mais comum:** AionUI abre em `/#/guid` (página principal), **não** em `/#/bianinho`. O componente `BianinhoPage` só é renderizado quando se clica no separador Bianinho — só aí faz pedidos ao bridge.

1. **Verificar bridge a ouvir:**
   ```bash
   nc -z 127.0.0.1 18743 && echo "port open"
   ```

2. **Verificar bridge com execute_code (NÃO usar curl no terminal — hangs):**
   ```python
   import urllib.request, json
   r = urllib.request.urlopen("http://127.0.0.1:18743/status", timeout=5)
   data = json.loads(r.read())
   print(f"messagesProcessed: {data['messagesProcessed']}")
   ```

3. **Verificar logs:**
   ```bash
   tail -f ~/.hermes/logs/bianinho_bridge.log
   ```

4. **Pedidos directos ao bridge (testar endpoints):**
   ```python
   # Todos os endpoints GET:
   for ep in ["/ping", "/status", "/platform_info", "/check_hermes",
              "/list_skills", "/rag_stats", "/inbox_list", "/cycle_status"]:
       r = urllib.request.urlopen(f"http://127.0.0.1:18743{ep}", timeout=5)
       print(ep, json.loads(r.read()).get("ok", "N/A"))
   ```

### Padrão de Debug: Bridge com 0 Conexões

Se `messagesProcessed: 0` no status, significa AionUI nunca fez um pedido ao bridge.

**Causa provável:** AionUI abriu na página `/#/guid` (default), não no separador Bianinho.

**Solução:** Clicar manualmente no botão "Bianinho" na sidebar do AionUI. A página Bianinho (`/#/bianinho`) é carregada via `React.lazy()` — só quando é navegada é que os handlers IPC são registados e os pedidos ao bridge são feitos.

### Rota HashRouter

```
/#/guid          ← página principal (default ao abrir AionUI)
/#/bianinho      ← separador Bianinho (precisa de clique manual)
/#/conversation  ← conversas
/#/team/:id      ← equipa
```

### O que o BianinhoPage Faz (quando renderizado)

```typescript
// BianinhoPage.tsx — useEffect ao montar:
void fetchAll();  // ipcBridge.bianinho.status.invoke()
void handlePing(); // ipcBridge.bianinho.ping.invoke()

// Estatísticas bridge (bianinhoBridge.ts no main process):
// ipcMain.handle('bianinho.status') → httpSend('GET', '/status')
// ipcMain.handle('bianinho.ping')  → httpSend('GET', '/ping')
```

### AionUI Sem Servidor (DMG Standalone)

No DMG sem BianinhoBridge server, o `ipcBridge.bianinho.*` retorna `{__bridgeError: true, message: "Connection failed"}`. O componente mostra "Bridge offline". Isto é **normal** — o DMG standalone não inclui o BianinhoBridge server.

### Limitações de Debug do AionUI

- **Logs da aplicação:** `~/Library/Logs/AionUi/YYYY-MM-DD.log` — **este é o log principal** para qualquer erro do AionUI (Electron main/renderer, ACP subprocess, etc.)
- **Remote debugging** (Chrome DevTools Protocol): `open -n /Applications/AionUI.app --args --remote-debugging-port=9222` — a porta pode não abrir
- **AppleScript UI automation**: bloqueado por "acesso assistivo não permitido" (-1719)
- **screencapture**: pode falhar com "could not create image from display"
- **Electron IPC**: invisível no DevTools normal — os pedidos são feitos pelo main process, não pelo renderer

## Releases
- v1.9.24-fix3: primeiro ErrorBoundary
- v1.9.24-fix4: Array.isArray defensivo em useTeamList + useSiderTeamBadges — parcialmente resolvido
- v1.9.24-fix5: BianinhoBridge HTTP via Tailscale (02/05/2026)
- **v1.9.24-fix6 (03/05/2026):** BianinhoBridge 100% local — Bridge em localhost:18743, RAG em localhost:3101, Knowledge Base em ~/KnowledgeBase/ (sync do servidor a cada 4h)

## Estado Actual (02/05/2026 14h) — AINDA NÃO RESOLVIDO

**O white screen PERSISTE** apesar dos fixes 4 e 5. O crash do `useTeamList` aparece no console:
```
[useTeamList] IPC returned non-array: Object
```
Isto significa que o fetcher SWR em `useTeamList.ts` recebe um **objeto** em vez de array. O `Array.isArray()` guarda loga o warning mas retorna `[]` — no entanto, o crash continua a ocorrer.

**Hipótese actual:** O problema pode não ser só `useTeamList`. O `useTeamList` está a retornar `[]` (defensivamente), mas o crash pode vir de **outro hook** que também recebe o resultado do IPC. O `Object` que aparece no console pode ser o valor `{__bridgeError: true, message: "..."}` retornado pelo `teamBridge.ts` safeProvider.

**Sintomas:**
- App abre mas mostra ecrã branco ou sem conteúdo funcional
- Console DevTools mostra `[useTeamList] IPC returned non-array: Object`
- A página do Bianinho não carrega porque a navegação está bloqueada pelo crash do Team layout

**Próximo passo de debug:**
1. O objeto de erro `__bridgeError: true` vem do `safeProvider` em `teamBridge.ts` — quando `TeamSessionService.listTeams()` falha, retorna esse sentinel
2. Precisa de descobrir porque é que `listTeams()` está a falhar no DMG (sem BianinhoBridge server)
3. Verificar se o `useTeamList` fetcher RETORNA realmente `[]` ou se há outro código a usar o valor原始 antes do `.then()`

## Ficheiros-Chave do Bug
- `src/renderer/pages/team/hooks/useTeamList.ts`
- `src/renderer/pages/team/hooks/useSiderTeamBadges.ts`
- `src/renderer/components/ErrorBoundary.tsx` (criado nesta sessão)
- `.github/workflows/build-dmg.yml`
- `src/process/bridge/bianinhoBridge.ts` — **HTTP via Tailscale** (bianinho_bridge_server.py)
- `scripts/bianinho_bridge_server.py` — **servidor HTTP no servidor Linux**

## Integração AionUI + Bianinho via Tailscale
Ver `references/aionui-bianinho-tailscale-integration.md` para arquitectura, configuração systemd, endpoints e troubleshooting.
- Conectando AionUI ao Bianinho via Tailscale (bianinho_bridge_server.py HTTP, 02/05/2026)
- **references/aionui-bianinho-localhost.md (03/05/2026):** Arquitectura 100% local, erro Hermes Agent ACP "Agent exited before initialize completed", fix `pip install -e '.[acp]'`, navegação HashRouter, nota sobre bridge vs ACP
