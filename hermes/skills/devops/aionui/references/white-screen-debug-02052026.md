# White Screen Debug — Sessão 02/05/2026 (AionUI DMG Mac)

## Root Cause Encontrada

**Causa 4 — `useEffect` dependency array com `.map()` em `useSiderTeamBadges`**

- **Ficheiro:** `src/renderer/pages/team/hooks/useSiderTeamBadges.ts`, linha 105
- **Crash:** `e.map is not a function` — não é num render JSX, é na **avaliação do dependency array** do `useEffect`
- **Stack:** `at Mc (vendor-react)` como pai — React reconciler, não componente

```typescript
// LINHA 105 — ANTES (crasha)
}, [teams.map((t) => `${t.id}:${t.agents.map((a) => a.conversationId || '').join(',')}`).join('|')]);

// LINHA 105 — DEPOIS (defensivo)
}, [teams?.map((t) => `${t.id}:${t.agents?.map((a) => a.conversationId || '').join(',')}`).join('|') ?? '']);
```

**Porquê ocurre:** `useTeamList()` usa SWR — durante re-renderizações rápidas entre mount e primeira resolução, `teams` pode ser `undefined` por um frame. O `useEffect` evaluado nesse momento crasha no `.map()` do dependency array antes de React poder capturar.

**Fix commitado:** `1d5aef0bb` — "fix: useSiderTeamBadges - proteger teams?.map contra undefined"

## Método de Debug (Linux, sem macOS)

1. **Download artifact** via `gh api repos/.../actions/artifacts/$ID/zip > file.zip`
2. **7z x** no `.dmg` (nativo Linux, sem hdiutil)
3. **asar extract** no `app.asar` (npm install -g asar)
4. **Pesquisar** no bundle minificado pela string do erro: `r.agents.map` no bundle é prova concreta
5. **Mapear** para o源代码 (TeamSiderSection → useSiderTeamBadges)

## Fluxo Completo Descoberto

```
Bundle: index-B7FSMILK.js, linha ~7560, col 1358
  → r.agents.map() crasha
  → O1t(i) onde i = resultado de O1t(teams)
  → teams vem de R1t() = useTeamList().teams
  → teams é undefined durante SWR loading
  → useSiderTeamBadges.useEffect dependency [teams.map(...)]
  → .map() avaliado com teams = undefined
  → TypeError: e.map is not a function
```

## 4 Causas White Screen no DMG (02/05/2026)

| # | Causa | Ficheiro | Fix |
|---|-------|----------|-----|
| 1 | `isDesktopRuntime = false` no packaged app | `AuthContext.tsx` | Forçar `= true` |
| 2 | IPC handlers em falta (null return) | `bianinhoBridge.ts` | Adicionar fallback `{}` |
| 3 | `.map()` sem guarda em render | `BianinhoPage.tsx`, `GuidPage.tsx` | `?.` + validação IPC |
| 4 | `useEffect` dependency com `.map()` em undefined | `useSiderTeamBadges.ts:105` | `teams?.map() ?? ''` |

## Erro Original do Álvaro (02/05/2026)

```
Uncaught TypeError: e.map is not a function
    at O1t (index-B7FSMILK.js:7560:1358)
    at fAt (index-B7FSMILK.js:7588:218)
    at Mc (vendor-react-Bsw3macJ.js:40:47990)  ← React reconciler
```

**Componente:** `fAt` = `TeamSiderSection` (definido em `src/renderer/components/layout/Sider/TeamSiderSection.tsx:7588` no bundle)

## Build Node 20 Deprecation

GitHub Actions warning: `Node.js 20 actions are deprecated`. Fix no workflow:

```yaml
jobs:
  build-macos:
    runs-on: macos-14
    env:
      FORCE_JAVASCRIPT_ACTIONS_TO_NODE24: true  # ← adicionar
    steps:
      ...
```

Commit fix: `3fcab7b29` — "fix: FORCE_JAVASCRIPT_ACTIONS_TO_NODE24 para corrigir warning deprecation Node 20"

## Atalhos Úteis

- **DMG download direto:** `https://github.com/AlvaroBiano/AionUi/releases/download/v1.9.24-fix2/AionUi-v1.9.24-fix2.dmg.zip`
- **Artifact ID mais recente:** `gh api repos/AlvaroBiano/AionUi/actions/runs --jq '.workflow_runs[0].id'`
- **Build workflow:** `build-dmg.yml` (ID: `269706228`), só `workflow_dispatch`
