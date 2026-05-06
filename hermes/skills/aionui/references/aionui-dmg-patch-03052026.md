# AionUI DMG — Patching Session 03/05/2026

## The Problem

Goal: Make Hermes Agent appear in Teams → New Team → Team Leader dropdown (fixed position, never disappears).

After a rebuild attempt, the app stopped opening.

## What Was Tried

1. **Rebuild attempt (`bunx electron-vite build` + `electron-builder`)** → FAILS
   - `better-sqlite3` native module rebuild fails: `Node API incompatibility` (Node v136 vs Electron v136)
   - Even if it passed, creates `app.asar.unpacked/` which breaks macOS code signing

2. **app.asar extraction + modification + repack** → WORKS
   - Extract: `npx asar extract app.asar /tmp/app`
   - Modify files directly
   - Repack: `npx asar pack /tmp/app app.asar`
   - Re-sign: `codesign -f -s - /Applications/AionUi.app`

3. **RESTORATION** — original app.asar backup exists at:
   ```
   /Applications/AionUi.app/Contents/Resources/app.asar.backup_before_hermes_fix (464MB)
   ```
   Copied it back → app opens fine.

## Key Discovery

**Hermes is ALREADY in `KNOWN_TEAM_CAPABLE_BACKENDS` in the ORIGINAL app.asar:**
```javascript
const KNOWN_TEAM_CAPABLE_BACKENDS = new Set([
  "gemini", "claude", "codex", "aionrs", "hermes"
]);
```

**Hermes IS detected in logs:**
```
[AgentRegistry] Completed in 120ms, found 3 agents: Aion CLI, Gemini CLI, Hermes Agent
```

The original app.asar from the DMG already has the fix. The issue is NOT missing code — it's a runtime cache or UI state issue.

## Fix Applied

1. **Hermes symlink in PATH** (so Electron detects it):
   ```bash
   mkdir -p ~/.local/bin
   ln -sf ~/.hermes/venv/bin/hermes ~/.local/bin/hermes
   ```

2. **AcpDetector regex** (already patched in source, confirmed in original app.asar):
   ```typescript
   // Allows / in paths (for absolute paths)
   cmd => /^[a-zA-Z0-9_./-]+$/
   ```

3. **Cache clear** (so Teams UI refreshes agent list):
   ```bash
   pkill -9 -f "AionUi"
   rm -rf ~/Library/Application\ Support/AionUi/cache/swr*
   open -a AionUi
   ```

## Lessons

| Action | Result |
|--------|--------|
| Rebuild DMG to add feature | BREAKS native modules + code signing |
| Patch app.asar directly | WORKS, but must re-sign |
| Restore from backup | ALWAYS works |
| Check original app.asar first | Often already has the fix |

## Code Signing Fix

After ANY modification to `.app` contents:
```bash
codesign -f -s - /Applications/AionUi.app
codesign -vv /Applications/AionUi.app  # verify: "valid on disk"
```

If broken (shows "a sealed resource is missing"):
```bash
rm -rf "/Applications/AionUi.app/Contents/Resources/app.asar.unpacked"
codesign -f -s - /Applications/AionUi.app
```

## Backup Strategy

Before patching, ALWAYS:
```bash
cp "/Applications/AionUi.app/Contents/Resources/app.asar" \
   "/Applications/AionUi.app/Contents/Resources/app.asar.backup_before_patch"
```

Backup is 464MB — worth it.
