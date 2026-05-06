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

## Releases
- v1.9.24-fix3: primeiro ErrorBoundary
- v1.9.24-fix4: Array.isArray defensivo em useTeamList + useSiderTeamBadges — parcialmente resolvido
- v1.9.24-fix5: BianinhoBridge HTTP via Tailscale (02/05/2026) — AionUI conecta ao servidor em `100.79.189.95:18743`

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
