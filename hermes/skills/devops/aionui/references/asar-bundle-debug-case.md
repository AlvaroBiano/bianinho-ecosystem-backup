# ASAR Bundle Debug — White Screen Case Study (02/05/2026)

## Resumo
5 DMG builds, 2h+ debugging. Bug: `e.map is not a function` na linha 7560.

## Dados do Bug
- **Hash bundle:** `index-B7FSMILK.js` → `index-CBvrP838.js` (muda por build)
- **Linha crash:** 7560, coluna ~1358
- **Stack:** React reconciler → `O1t` (minified) → `fAt` (TeamSiderSection)
## Root cause: `useSiderTeamBadges(teams)` recebe `teams = undefined` do SWR no primeiro render

**CRÍTICO — O valor não era `undefined` era um objeto de erro:** O IPC `ipcBridge.team.list` no DMG (sem BianinhoBridge server) retorna `{__bridgeError: true, message: "...", ...}` — um objeto **truthy** que faz `.map()` crashar. O `?? []` não ajuda porque o valor não é `null`/`undefined` — é um objeto. `Array.isArray()` é a defesa correcta.

## Metodologia
1. **ErrorBoundary** global (React 19 — `getDerivedStateFromError`, NÃO `componentDidCatch`)
2. **Bundle extraction** do `.asar` para análise local
3. **Stack trace** do utilizador com hash do bundle → identificar ficheiro exacto
4. **Python** para ler bundle minificado e encontrar linha exacta do crash

## Como Extrair ASAR (Linux)

```bash
# 1. Extrair DMG (7z não lê ASAR, só cria estrutura)
cd /tmp && 7z x AionUi-1.9.24-mac-arm64.dmg -o/tmp/dmg-contents -y

# 2. Instalar asar (npm)
cd /tmp && npm install asar --no-save

# 3. Extrair ASAR via node (asar CLI tem issues com Node 24)
node -e "
const asar = require('./node_modules/asar/lib/asar.js');
asar.extractAll('/tmp/dmg-contents/AionUi 1.9.24-arm64/AionUi.app/Contents/Resources/app.asar', '/tmp/asar-extracted', (err) => {
  if (err) console.error(err.message);
  else console.log('Done');
});
"

# 4. Encontrar bundle com hash do erro
find /tmp/asar-extracted -name "index-*.js" | head -5
```

## Como Analisar o Bundle

```python
with open('/tmp/asar-extracted/out/renderer/assets/index-B7FSMILK.js') as f:
    content = f.read()
lines = content.split('\n')

# Linha 7560 (0-indexed: 7559)
print(lines[7559][:400])

# Procurar .map calls problemáticos na zona do crash
for i in range(7540, 7590):
    line = lines[i]
    if '.map' in line and ('team' in line.lower() or 'agents' in line.lower() or 'r.' in line):
        print(f"Line {i+1}: {line[:300]}")
```

## Lições Chave

1. **SWR first render = undefined** — `= []` default no destructuring NÃO protege durante `useState(initCounts())`
2. **`?? []` não basta** — se `data` é `{}` ou `"string"`, não funciona. `Array.isArray()` é mais seguro
3. **Optional chaining no dependency array** não previne crash no corpo da função
4. **Múltiplos bundles** — Electron code splitting cria múltiplos chunks. Hash do stack trace indica qual chunk
5. **7z não extrai DMG** — DMG é formato de disco, não archive. Usa `hdiutil` (macOS) ou analiza o `.app` dentro do DMG

## Fixes Aplicados (commit `95e4a7404`)

- `useTeamList.ts`: fetcher com `Array.isArray()` check
- `useSiderTeamBadges.ts`: `Array.isArray(teams) ? teams : []` + `team.agents ?? []`
