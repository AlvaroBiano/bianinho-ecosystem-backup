---
name: systematic-debugging
description: Use when encountering any bug, test failure, or unexpected behavior. 4-phase root cause investigation — NO fixes without understanding the problem first.
version: 1.1.0
author: Hermes Agent (adapted from obra/superpowers)
license: MIT
metadata:
  hermes:
    tags: [debugging, troubleshooting, problem-solving, root-cause, investigation]
    related_skills: [test-driven-development, writing-plans, subagent-driven-development]
---

# Systematic Debugging

## Overview

Random fixes waste time and create new bugs. Quick patches mask underlying issues.

**Core principle:** ALWAYS find root cause before attempting fixes. Symptom fixes are failure.

**Violating the letter of this process is violating the spirit of debugging.**

## The Iron Law

```
NO FIXES WITHOUT ROOT CAUSE INVESTIGATION FIRST
```

If you haven't completed Phase 1, you cannot propose fixes.

## When to Use

Use for ANY technical issue:
- Test failures
- Bugs in production
- Unexpected behavior
- Performance problems
- Build failures
- Integration issues

**Use this ESPECIALLY when:**
- Under time pressure (emergencies make guessing tempting)
- "Just one quick fix" seems obvious
- You've already tried multiple fixes
- Previous fix didn't work
- You don't fully understand the issue

**Don't skip when:**
- Issue seems simple (simple bugs have root causes too)
- You're in a hurry (rushing guarantees rework)
- Someone wants it fixed NOW (systematic is faster than thrashing)

## The Four Phases

You MUST complete each phase before proceeding to the next.

---

## Phase 1: Root Cause Investigation

**BEFORE attempting ANY fix:**

### 1. Read Error Messages Carefully

- Don't skip past errors or warnings
- They often contain the exact solution
- Read stack traces completely
- Note line numbers, file paths, error codes

**Action:** Use `read_file` on the relevant source files. Use `search_files` to find the error string in the codebase.

### 2. Reproduce Consistently

- Can you trigger it reliably?
- What are the exact steps?
- Does it happen every time?
- If not reproducible → gather more data, don't guess

**Action:** Use the `terminal` tool to run the failing test or trigger the bug:

```bash
# Run specific failing test
pytest tests/test_module.py::test_name -v

# Run with verbose output
pytest tests/test_module.py -v --tb=long
```

### 3. Check Recent Changes

- What changed that could cause this?
- Git diff, recent commits
- New dependencies, config changes

**Action:**

```bash
# Recent commits
git log --oneline -10

# Uncommitted changes
git diff

# Changes in specific file
git log -p --follow src/problematic_file.py | head -100
```

### 4. Gather Evidence in Multi-Component Systems

**WHEN system has multiple components (API → service → database, CI → build → deploy):**

**BEFORE proposing fixes, add diagnostic instrumentation:**

For EACH component boundary:
- Log what data enters the component
- Log what data exits the component
- Verify environment/config propagation
- Check state at each layer

Run once to gather evidence showing WHERE it breaks.
THEN analyze evidence to identify the failing component.
THEN investigate that specific component.

### 5. Trace Data Flow

**WHEN error is deep in the call stack:**

- Where does the bad value originate?
- What called this function with the bad value?
- Keep tracing upstream until you find the source
- Fix at the source, not at the symptom

**Action:** Use `search_files` to trace references:

```python
# Find where the function is called
search_files("function_name(", path="src/", file_glob="*.py")

# Find where the variable is set
search_files("variable_name\\s*=", path="src/", file_glob="*.py")
```

### Phase 1 Completion Checklist

- [ ] Error messages fully read and understood
- [ ] Issue reproduced consistently
- [ ] Recent changes identified and reviewed
- [ ] Evidence gathered (logs, state, data flow)
- [ ] Problem isolated to specific component/code
- [ ] Root cause hypothesis formed

**STOP:** Do not proceed to Phase 2 until you understand WHY it's happening.

---

## Phase 2: Pattern Analysis

**Find the pattern before fixing:**

### 1. Find Working Examples

- Locate similar working code in the same codebase
- What works that's similar to what's broken?

**Action:** Use `search_files` to find comparable patterns:

```python
search_files("similar_pattern", path="src/", file_glob="*.py")
```

### 2. Compare Against References

- If implementing a pattern, read the reference implementation COMPLETELY
- Don't skim — read every line
- Understand the pattern fully before applying

### 3. Identify Differences

- What's different between working and broken?
- List every difference, however small
- Don't assume "that can't matter"

### 4. Understand Dependencies

- What other components does this need?
- What settings, config, environment?
- What assumptions does it make?

---

## Phase 3: Hypothesis and Testing

**Scientific method:**

### 1. Form a Single Hypothesis

- State clearly: "I think X is the root cause because Y"
- Write it down
- Be specific, not vague

### 2. Test Minimally

- Make the SMALLEST possible change to test the hypothesis
- One variable at a time
- Don't fix multiple things at once

### 3. Verify Before Continuing

- Did it work? → Phase 4
- Didn't work? → Form NEW hypothesis
- DON'T add more fixes on top

### 4. When You Don't Know

- Say "I don't understand X"
- Don't pretend to know
- Ask the user for help
- Research more

---

## Phase 4: Implementation

**Fix the root cause, not the symptom:**

### 1. Create Failing Test Case

- Simplest possible reproduction
- Automated test if possible
- MUST have before fixing
- Use the `test-driven-development` skill

### 2. Implement Single Fix

- Address the root cause identified
- ONE change at a time
- No "while I'm here" improvements
- No bundled refactoring

### 3. Verify Fix

```bash
# Run the specific regression test
pytest tests/test_module.py::test_regression -v

# Run full suite — no regressions
pytest tests/ -q
```

### 4. If Fix Doesn't Work — The Rule of Three

- **STOP.**
- Count: How many fixes have you tried?
- If < 3: Return to Phase 1, re-analyze with new information
- **If ≥ 3: STOP and question the architecture (step 5 below)**
- DON'T attempt Fix #4 without architectural discussion

### 5. If 3+ Fixes Failed: Question Architecture

**Pattern indicating an architectural problem:**
- Each fix reveals new shared state/coupling in a different place
- Fixes require "massive refactoring" to implement
- Each fix creates new symptoms elsewhere

**STOP and question fundamentals:**
- Is this pattern fundamentally sound?
- Are we "sticking with it through sheer inertia"?
- Should we refactor the architecture vs. continue fixing symptoms?

**Discuss with the user before attempting more fixes.**

This is NOT a failed hypothesis — this is a wrong architecture.

---

## API Endpoint Debugging — The 404→401 Cascade

**WHEN: auth_error or 401 errors appear in large numbers (×50+) without obvious credentials issues.**

The root cause is often a **wrong API base_url**, not bad credentials:
- Wrong path returns 404 nginx → Hermes client logs as 401 Unauthorized
- One misconfigured URL generates hundreds of seemingly unrelated auth errors

### Diagnosis Steps

1. **Test the exact endpoint in config:**
```python
import urllib.request, json
from pathlib import Path

# Read API key
api_key = ''
for line in Path.home().joinpath('.hermes/.env').read_text().splitlines():
    if line.startswith('MINIMAX_API_KEY='):
        api_key = line.split('=', 1)[1].strip()
        break

# Test the base_url from config
url = 'https://api.minimax.io/anthropic/v1/chat/completions'  # from config
body = json.dumps({'model': 'MiniMax-M2.7', 'messages': [{'role': 'user', 'content': 'Hi'}], 'max_tokens': 5}).encode()
req = urllib.request.Request(url, data=body, headers={'Authorization': f'Bearer {api_key}', 'Content-Type': 'application/json'})
try:
    with urllib.request.urlopen(req, timeout=15) as r:
        print(f'HTTP {r.status}')
except urllib.error.HTTPError as e:
    print(f'HTTP {e.code} → {e.read()[:100]}')
```
2. **If 404: try the correct base path** — e.g., `/v1/chat/completions` instead of `/anthropic/v1/chat/completions`
3. **Verify**: If correct path returns 200, the config is wrong — fix base_url in both config.yaml and .env

### Fix Applied (2026-04-26)
- `~/.hermes/config.yaml`: `base_url: https://api.minimax.io/anthropic` → `https://api.minimax.io/v1`
- `~/.hermes/.env`: `MINIMAX_BASE_URL=.../anthropic` → `.../v1`
- Result: 80+ auth_errors eliminated, quality 2.3→4.2

### Files to Check for API Config
- `~/.hermes/config.yaml` — provider base_url
- `~/.hermes/.env` — API keys and endpoint overrides
- `~/.hermes/hermes-agent/hermes_cli/auth.py` — credential loading
- `~/.hermes/endpoint_health.json` — previous diagnosis state

---

## SiteTen Admin — Frontend Triage Checklist

**WHEN: User reports "nothing appears" on an admin tab (e.g., E-books blank page)**

The symptom has three distinct causes requiring different diagnostics. Diagnose in order:

### Step 1: Check if it's a backend or frontend problem
Open browser DevTools → **Network** tab → filter by XHR/Fetch → trigger the tab.
- **No request made** → JS error preventing execution. Check Console for red errors.
- **Request made but red** → API returning error (401 auth, 500 PHP error, etc.)
- **Request succeeds (200)** → API works, problem is in frontend rendering.

### Step 2: Verify server files are updated (not just local)
```bash
# Check server-side JS has your changes (cloudflared tunnel = server ≠ localhost)
curl -s "https://alvarobiano-linuxmint.taile2fd75.ts.net/admin/js/admin.js" | grep -c "function_name_you_added"

# Check server-side PHP has your changes
curl -s "https://alvarobiano-taile2fd75.ts.net/api/ebooks.php" -H "Accept: text/plain" | grep -c "new_field"
```
**Local files being updated ≠ server running updated code.** Always verify the tunnel URL.

### Step 3: Check for JS errors
Browser Console (F12 → Console) — look for:
- `ReferenceError` → function not defined (likely stale JS cache)
- `TypeError` → null property access (data mismatch)
- Network errors → CORS or mixed content

### Step 4: Force refresh
**Ctrl+Shift+R** (hard refresh) clears stale cached JS/PHP responses.

---

## Critical Pitfall: Tailwind `hidden` class + JavaScript `classList.remove`

**Symptom:** Element has `display: block` or `display: flex` in inline style, but is still invisible. `getBoundingClientRect()` returns 0×0.

**Root cause:** Tailwind's `.hidden` class uses `!important`:
```css
.hidden { display: none !important; }
```
When JavaScript adds `classList.add('hidden')` followed by `classList.remove('hidden')`, the `!important` in the CSS rule overrides the inline style removal.

**Affected code pattern (SiteTen admin):**
```javascript
// In switchTab() — adds hidden
document.getElementById('crud-main').classList.add('hidden');

// In renderTable() — DOES NOT remove it → table invisible!
renderTable() { ... }
```

**Fix:** `renderTable()` MUST explicitly remove the class:
```javascript
function renderTable() {
    // CRITICAL: Remove hidden first — Tailwind's !important blocks inline style removal
    document.getElementById('crud-main')?.classList.remove('hidden');
    // ... rest of render
}
```

**Diagnosis via Playwright:**
```javascript
const states = await page.evaluate(() => {
    const el = document.getElementById('crud-main');
    const style = window.getComputedStyle(el);
    const rect = el.getBoundingClientRect();
    return {
        display: style.display,
        hidden: el.classList.contains('hidden'),  // ← key check
        width: Math.round(rect.width),
        height: Math.round(rect.height)
    };
});
// If hidden=true + width=0 → found the bug
```

**Discovered:** 30/04/2026 — E-books tab showed blank despite 6 rows in `dynamic-table-body`. `renderTable()` was rendering correctly but `crud-main` remained invisible due to this `!important` conflict.

---

## Playwright + Authenticated Admin: Cookie-Passing Workaround

**Symptom:** Headless Playwright cannot authenticate via file input (`<input type="file">`). The browser security model blocks programmatic file selection in headless mode, causing the admin login to fail silently.

**Context:** SiteTen admin uses RSA key file upload for login — Playwright's `setInputFiles()` works for visible inputs but the auth flow in headless mode may have timing/credential issues.

**Workaround: Authenticate via curl first, then pass session cookie to Playwright**

```javascript
// Step 1: Get authenticated session cookie via curl
const { execSync } = require('child_process');

// Login via curl with real .pem file
const cookies = execSync(`
  curl -s -c /tmp/cookies.txt -X POST "https://alvarobiano-linuxmint.taile2fd75.ts.net/api/auth.php" \\
    -F "password=AeSm1979@#" \\
    -F "private_key=@/home/alvarobiano/repos/SiteTen/api/security/private_key.pem"
`).toString();

// Read the PHPSESSID from cookies file
const cookieContent = require('fs').readFileSync('/tmp/cookies.txt', 'utf8');
const phpsessid = cookieContent.match(/PHPSESSID\\s+(\\w+)/)?.[1];

// Step 2: Use the cookie in Playwright
const browser = await chromium.launch({ headless: true });
const context = await browser.newContext({
  cookieStore: [{ name: 'PHPSESSID', value: phpsessid, domain: 'alvarobiano-linuxmint.taile2fd75.ts.net', path: '/' }]
});
const page = await context.newPage();
// Now page is authenticated — no login form needed
```

**Why this matters:** Direct Playwright login via file input fails because:
1. Headless Chrome security model restricts file input automation
2. The `auth.php` POST requires the exact private key that matches the server's public key
3. curl with the real file path (`@/path/to/private_key.pem`) works reliably

**Alternative:** Use `page.setInputFiles()` for the `.pem` file but ensure the `button[type="submit"]` click happens AFTER the file is fully associated (add 300-500ms wait).

**Discovered:** 30/04/2026 — Playwright tests confirmed the E-books tab WAS working (6 rows rendered) even though the browser showed nothing, because the browser had cached an older JavaScript version. The curl→cookie technique bypassed the Playwright file-input limitation entirely.

---

## Quick Reference

If you catch yourself thinking:
- "Quick fix for now, investigate later"
- "Just try changing X and see if it works"
- "Add multiple changes, run tests"
- "Skip the test, I'll manually verify"
- "It's probably X, let me fix that"
- "I don't fully understand but this might work"
- "Pattern says X but I'll adapt it differently"
- "Here are the main problems: [lists fixes without investigation]"
- Proposing solutions before tracing data flow
- **"One more fix attempt" (when already tried 2+)**
- **Each fix reveals a new problem in a different place**

**ALL of these mean: STOP. Return to Phase 1.**

**If 3+ fixes failed:** Question the architecture (Phase 4 step 5).

## Common Rationalizations

| Excuse | Reality |
|--------|---------|
| "Issue is simple, don't need process" | Simple issues have root causes too. Process is fast for simple bugs. |
| "Emergency, no time for process" | Systematic debugging is FASTER than guess-and-check thrashing. |
| "Just try this first, then investigate" | First fix sets the pattern. Do it right from the start. |
| "I'll write test after confirming fix works" | Untested fixes don't stick. Test first proves it. |
| "Multiple fixes at once saves time" | Can't isolate what worked. Causes new bugs. |
| "Reference too long, I'll adapt the pattern" | Partial understanding guarantees bugs. Read it completely. |
| "I see the problem, let me fix it" | Seeing symptoms ≠ understanding root cause. |
| "One more fix attempt" (after 2+ failures) | 3+ failures = architectural problem. Question the pattern, don't fix again. |

## Quick Reference

| Phase | Key Activities | Success Criteria |
|-------|---------------|------------------|
| **1. Root Cause** | Read errors, reproduce, check changes, gather evidence, trace data flow | Understand WHAT and WHY |
| **2. Pattern** | Find working examples, compare, identify differences | Know what's different |
| **3. Hypothesis** | Form theory, test minimally, one variable at a time | Confirmed or new hypothesis |
| **4. Implementation** | Create regression test, fix root cause, verify | Bug resolved, all tests pass |

## Hermes Agent Integration

### Investigation Tools

Use these Hermes tools during Phase 1:

- **`search_files`** — Find error strings, trace function calls, locate patterns
- **`read_file`** — Read source code with line numbers for precise analysis
- **`terminal`** — Run tests, check git history, reproduce bugs
- **`web_search`/`web_extract`** — Research error messages, library docs

### With delegate_task

For complex multi-component debugging, dispatch investigation subagents:

```python
delegate_task(
    goal="Investigate why [specific test/behavior] fails",
    context="""
    Follow systematic-debugging skill:
    1. Read the error message carefully
    2. Reproduce the issue
    3. Trace the data flow to find root cause
    4. Report findings — do NOT fix yet

    Error: [paste full error]
    File: [path to failing code]
    Test command: [exact command]
    """,
    toolsets=['terminal', 'file']
)
```

### With test-driven-development

When fixing bugs:
1. Write a test that reproduces the bug (RED)
2. Debug systematically to find root cause
3. Fix the root cause (GREEN)
4. The test proves the fix and prevents regression

## Real-World Impact

From debugging sessions:
- Systematic approach: 15-30 minutes to fix
- Random fixes approach: 2-3 hours of thrashing
- First-time fix rate: 95% vs 40%
- New bugs introduced: Near zero vs common

**No shortcuts. No guessing. Systematic always wins.**
