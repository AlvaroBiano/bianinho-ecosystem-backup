---
name: browser-console-js-error-detection
description: Use browser DevTools console to detect JavaScript errors that cause silent page failures
tags: [browser, debugging, javascript, frontend]
---

# Browser Console JS Error Detection

## When to Use

- Page loads but JavaScript doesn't work (no clicks, no updates)
- Partial rendering (header visible, content missing)
- API calls don't trigger UI updates
- Page is blank or shows only partial content

## How to Use

After navigating to the page:

```javascript
// Check for errors
browser_console()

// Evaluate JS in page context
browser_console(expression="document.getElementById('element-id')?.children.length")

// Check for specific elements
browser_console(expression="document.getElementById('board')?.innerHTML?.substring(0, 100)")
```

## Common Error Patterns

| Error | Cause | Fix |
|-------|-------|-----|
| `Invalid or unexpected token` | Syntax error in inline `<script>` | Check line shown in error source |
| `Cannot read property 'X' of null` | Element not found, script runs before DOM ready | Wrap in `DOMContentLoaded` or move script to end |
| `Unexpected token '<'` | Fetched HTML instead of JSON | Check API response URL and auth |
| `net::ERR_BLOCKED_BY_CLIENT` | Ad/tracker blocker, usually harmless | Ignore for non-ads pages |

## Priority

1. **JS errors first** — these break functionality silently
2. **Failed network requests** — API returning wrong format or 401
3. **Warnings** — usually less critical but can indicate issues

## Pattern: Check DOM State

```javascript
// Is the target element present?
document.getElementById('target') ? 'FOUND' : 'NOT FOUND'

// How many children?
document.querySelectorAll('.column').length

// Any visible content?
document.getElementById('board')?.innerHTML?.trim().length
```

## Pattern: Diagnose Kanban / List Rendering

When a board/kanban/list shows only header but no cards:

```javascript
// Check if data was fetched
fetch('/api/endpoint').then(r=>r.json()).then(d=>console.log('data:', d))

// Check if JS found the container
document.getElementById('board')?.children?.length

// Manually trigger render (if function is global)
typeof renderBoard === 'function' ? 'renderBoard() exists' : 'not found'
```

## Pattern: JS Typo Causing Silent Page Failure

**When: page loads, no JS errors visible except "Unexpected token" or "Unexpected identifier", but data doesn't render and global functions are undefined.**

A space inside a function name (e.g. `renderQA KPIs` instead of `renderQAKPIs`) causes JavaScript to throw `SyntaxError: Unexpected identifier` at parse time. The entire inline `<script>` block fails — NO functions inside it are defined.

**Diagnosis:**
```javascript
// 1. Check if expected global functions are actually defined
typeof renderQAKPIs === 'function' ? 'OK' : 'UNDEFINED - check for JS syntax errors'
typeof renderQAPerfTable === 'function' ? 'OK' : 'UNDEFINED'

// 2. Get full error details from the page
[...document.querySelectorAll('script')].forEach((s, i) => {
  try { new Function(s.textContent); }
  catch(e) { console.error(`Script ${i}: ${e.message} at line ${e.lineNumber}`); }
})
```

**Real example:** `renderQA KPIs(data.global || {})` → space between `QA` and `K` → `SyntaxError: Unexpected identifier 'K'` → `renderQAKPIs` and `renderQAPerfTable` never defined → table empty, KPIs stuck at `—`.
