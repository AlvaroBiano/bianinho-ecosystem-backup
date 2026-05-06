---
name: dogfood
description: Systematic exploratory QA testing of web applications — find bugs, capture evidence, and generate structured reports
version: 1.0.0
metadata:
  hermes:
    tags: [qa, testing, browser, web, dogfood]
    related_skills: []
---

# Dogfood: Systematic Web Application QA Testing

## Overview

This skill guides you through systematic exploratory QA testing of web applications using the browser toolset. You will navigate the application, interact with elements, capture evidence of issues, and produce a structured bug report.

## Prerequisites

- Browser toolset must be available (`browser_navigate`, `browser_snapshot`, `browser_click`, `browser_type`, `browser_vision`, `browser_console`, `browser_scroll`, `browser_back`, `browser_press`)
- A target URL and testing scope from the user

## Inputs

The user provides:
1. **Target URL** — the entry point for testing
2. **Scope** — what areas/features to focus on (or "full site" for comprehensive testing)
3. **Output directory** (optional) — where to save screenshots and the report (default: `./dogfood-output`)

## Workflow

Follow this 5-phase systematic workflow:

### Phase 1: Plan

1. Create the output directory structure:
   ```
   {output_dir}/
   ├── screenshots/       # Evidence screenshots
   └── report.md          # Final report (generated in Phase 5)
   ```
2. Identify the testing scope based on user input.
3. Build a rough sitemap by planning which pages and features to test:
   - Landing/home page
   - Navigation links (header, footer, sidebar)
   - Key user flows (sign up, login, search, checkout, etc.)
   - Forms and interactive elements
   - Edge cases (empty states, error pages, 404s)

### Phase 2: Explore

For each page or feature in your plan:

1. **Navigate** to the page:
   ```
   browser_navigate(url="https://example.com/page")
   ```

2. **Take a snapshot** to understand the DOM structure:
   ```
   browser_snapshot()
   ```

3. **Check the console** for JavaScript errors:
   ```
   browser_console(clear=true)
   ```
   Do this after every navigation and after every significant interaction. Silent JS errors are high-value findings.

4. **Take an annotated screenshot** to visually assess the page and identify interactive elements:
   ```
   browser_vision(question="Describe the page layout, identify any visual issues, broken elements, or accessibility concerns", annotate=true)
   ```
   The `annotate=true` flag overlays numbered `[N]` labels on interactive elements. Each `[N]` maps to ref `@eN` for subsequent browser commands.

5. **Test interactive elements** systematically:
   - Click buttons and links: `browser_click(ref="@eN")`
   - Fill forms: `browser_type(ref="@eN", text="test input")`
   - Test keyboard navigation: `browser_press(key="Tab")`, `browser_press(key="Enter")`
   - Scroll through content: `browser_scroll(direction="down")`
   - Test form validation with invalid inputs
   - Test empty submissions

6. **After each interaction**, check for:
   - Console errors: `browser_console()`
   - Visual changes: `browser_vision(question="What changed after the interaction?")`
   - Expected vs actual behavior

### Phase 3: Collect Evidence

For every issue found:

1. **Take a screenshot** showing the issue:
   ```
   browser_vision(question="Capture and describe the issue visible on this page", annotate=false)
   ```
   Save the `screenshot_path` from the response — you will reference it in the report.

2. **Record the details**:
   - URL where the issue occurs
   - Steps to reproduce
   - Expected behavior
   - Actual behavior
   - Console errors (if any)
   - Screenshot path

3. **Classify the issue** using the issue taxonomy (see `references/issue-taxonomy.md`):
   - Severity: Critical / High / Medium / Low
   - Category: Functional / Visual / Accessibility / Console / UX / Content

### Phase 4: Categorize

1. Review all collected issues.
2. De-duplicate — merge issues that are the same bug manifesting in different places.
3. Assign final severity and category to each issue.
4. Sort by severity (Critical first, then High, Medium, Low).
5. Count issues by severity and category for the executive summary.

### Phase 5: Report

Generate the final report using the template at `templates/dogfood-report-template.md`.

The report must include:
1. **Executive summary** with total issue count, breakdown by severity, and testing scope
2. **Per-issue sections** with:
   - Issue number and title
   - Severity and category badges
   - URL where observed
   - Description of the issue
   - Steps to reproduce
   - Expected vs actual behavior
   - Screenshot references (use `MEDIA:<screenshot_path>` for inline images)
   - Console errors if relevant
3. **Summary table** of all issues
4. **Testing notes** — what was tested, what was not, any blockers

Save the report to `{output_dir}/report.md`.

## Tools Reference

| Tool | Purpose |
|------|---------|
| `browser_navigate` | Go to a URL |
| `browser_snapshot` | Get DOM text snapshot (accessibility tree) |
| `browser_click` | Click an element by ref (`@eN`) or text |
| `browser_type` | Type into an input field |
| `browser_scroll` | Scroll up/down on the page |
| `browser_back` | Go back in browser history |
| `browser_press` | Press a keyboard key |
| `browser_vision` | Screenshot + AI analysis; use `annotate=true` for element labels |
| `browser_console` | Get JS console output and errors |

## Additional Pitfalls Found in SAC Admin Testing

### 1. Encoding bug in Flask template placeholders
When a Python string with non-ASCII chars is placed in a Jinja2 `placeholder="..."` attribute, it can get double-encoded if the template file itself has encoding issues (e.g. bytes written as literal UTF-8 sequences instead of proper Unicode characters).
**Symptom:** Placeholder shows `sentindo-se绝望ado` instead of `sentindo-se desesperado`.
**Fix:** Re-type the text directly in the template file, ensuring the file is saved as clean UTF-8.
**Rule:** After any `write_file` or `patch` operation on a template that contains non-ASCII Portuguese text, verify placeholders render correctly in the browser.

### 2. Async modal opens before fetch completes
When a modal's `abrirModal(id)` function: (a) opens the modal immediately, then (b) fetches data and populates fields asynchronously — the modal title updates instantly but fields remain empty until the fetch resolves (race condition).
**Symptom:** Modal shows "Editar Story" title but all fields are empty for ~500ms while fetch runs.
**Fix:** Always open the modal and set the title BEFORE the fetch. Populate fields when the fetch promise resolves. For new items (no id), clear fields synchronously before showing the modal.
```javascript
// ✅ Correct pattern:
function abrirModalStory(id) {
    document.getElementById('modal-story-title').textContent = id ? 'Editar Story' : 'Nova Story';
    document.getElementById('modal-story').style.display = 'flex';
    // Always clear first
    fields.forEach(f => document.getElementById('s-' + f).value = '');
    if (!id) return;
    // Then fetch for edit
    fetch('/api/item/' + id).then(d => populateFields(d));
}

// ❌ Wrong pattern — modal opens before fetch:
function abrirModalStory(id) {
    if (!id) { showModal(); return; }
    fetch('/api/item/' + id).then(d => {
        populateFields(d);   // modal title correct but fields empty
        showModal();         // too late
    });
}
```

### 3. Below-fold interactive elements fail browser_click silently
When the browser viewport is small or the page is scrolled, elements below `window.innerHeight` exist in the DOM but `browser_click` cannot interact with them — the click fires but the element is not visible.
**Symptom:** `browser_click` returns `{"clicked": true}` but nothing happens; the browser snapshot shows the element but it has no `onclick` response.
**Fix:** Call `browser_scroll(direction='down')` before clicking below-fold elements. Alternatively, call the element's JS handler directly via `browser_console`: `document.querySelector('button[onclick="fn()"]').click()` or `fn()` directly.
**Verification:** `element.getBoundingClientRect().top < window.innerHeight` → element is in viewport.

### 4. Admin auth cookie may not be shared across browser tabs/ports
The SAC Admin uses `admin_token` cookie set on one port. When testing via `browser_navigate` vs `curl`, cookies may differ. If a `fetch()` from the browser console returns `{"erro": "Não autenticado"}` but the same endpoint works in curl, check that: (a) the browser is on the correct port, (b) the `admin_token` cookie exists via `document.cookie`, and (c) `credentials: 'include'` is set in the fetch options.

## Tips

- **Always check `browser_console()` after navigating and after significant interactions.** Silent JS errors are among the most valuable findings.
- **Use `annotate=true` with `browser_vision`** when you need to reason about interactive element positions or when the snapshot refs are unclear.
- **Test with both valid and invalid inputs** — form validation bugs are common.
- **Scroll through long pages** — content below the fold may have rendering issues.
- **Test navigation flows** — click through multi-step processes end-to-end.
- **Check responsive behavior** by noting any layout issues visible in screenshots.
- **Don't forget edge cases**: empty states, very long text, special characters, rapid clicking.

## Fallback: API/Curl Testing

When `browser_type` fails to fill forms because JavaScript event listeners (`input`, `change`) don't fire from browser automation, **pivot to API/curl testing** — it is often more reliable and faster for validating backend logic.

**Why browser form filling fails:**
- Forms with real-time validation check flags like `nomeValido = false` updated only via `addEventListener('input')`
- Setting `input.value = 'text'` directly in the DOM does NOT trigger the validation event listener
- The button remains disabled even though the value is set

**How to pivot to API testing:**
1. Inspect the form submission via `browser_console` or `browser_snapshot` to find the `fetch()` endpoint
2. Use `terminal(curl)` to POST directly to the API with correct JSON payload
3. Validate the full response: status codes, JSON fields, business logic (CTA flags, evaluation triggers, phase detection)
4. For multi-step flows (chatbots, wizards), script sequential curl calls with session cookies/tokens

**Example — testing a chat webhook:**
```bash
# Init session
INIT=$(curl -s -X POST http://localhost:5123/webhook/sac/init \
  -H 'Content-Type: application/json' \
  -d '{"nome":"Test User","telefone":"(48) 99999-9999","ddd":"48"}')
LEAD_ID=$(echo "$INIT" | python3 -c "import json,sys; print(json.load(sys.stdin)['lead_id'])")

# Send messages and check responses
curl -s -X POST http://localhost:5123/webhook/sac \
  -H 'Content-Type: application/json' \
  -d "{\"lead_id\":$LEAD_ID,\"nome\":\"Test User\",\"telefone\":\"(48) 99999-9999\",\"ddd\":\"48\",\"mensagem\":\"Hello\",\"session_id\":\"test-001\"}"
```

**When to use which approach:**
| Approach | Use when |
|---|---|
| Browser (dogfood) | Visual/UX issues, rendering, console errors, multi-step DOM flows |
| API/curl | Backend logic, webhook handlers, session state, multi-turn conversations |
- When reporting screenshots to the user, include `MEDIA:<screenshot_path>` so they can see the evidence inline.
