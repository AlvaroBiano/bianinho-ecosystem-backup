---
name: flask-development
description: "Flask development patterns and debugging — route registration order, template file separation for complex JS, and Jinja2 variable substitution. For when: routes return 404 in production but work in test_client, template variables appear literally in HTML, or f-string HTML+JS causes SyntaxError."
triggers:
  - flask route 404 production
  - flask app.run blocking routes
  - flask template variables not substituted
  - flask send_file vs render_template_string
  - flask f-string javascript syntaxerror
  - flask admin template pattern
category: software-development
---

# Flask Development — Patterns and Debugging

Three critical Flask pitfalls: route registration order, template file handling for complex JS, and Jinja2 variable substitution.

---

## ◆ Dead Routes — Routes Defined After `app.run()`

**Source**: `flask-app-run-blocking-routes/` + `debugging-flask-route-after-app-run/`

### Symptom
Endpoint works with `test_client()` but returns 404 on the real running server (systemd, Docker, etc.).

### Root Cause
`app.run()` is **blocking**. Code defined after it is **dead code** — never executed by the production server.
```python
# ❌ DEAD CODE — never executed by the real server
if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5123)

@app.route("/webhook/sac/avaliar", methods=["POST"])
def webhook_sac_avaliar():  # INACCESSIBLE
    ...
```
`test_client()` processes requests in-process WITHOUT starting the HTTP server — that's why it finds routes that `app.run()` blocks.

### Solution
Move ALL routes to **BEFORE** `if __name__ == "__main__":`.

```python
# ✅ ALIVE — executed before server starts
@app.route("/webhook/sac/avaliar", methods=["POST"])
def webhook_sac_avaliar():
    ...

if __name__ == "__main__":
    app.run(host=args.host, port=args.port, debug=args.debug)
```

### Correct Order in app.py
1. Imports
2. `app = Flask(__name__)`
3. Configurations (`CORS`, `rate_limit`, etc.)
4. **ALL** routes and decorators — without exception
5. `if __name__ == "__main__":` with `app.run()`

### Diagnostic
```python
# Add JUST BEFORE app.run()
print(">>> URL_RULES", [r.rule for r in app.url_map.iter_rules()])
# If the target route doesn't appear here → it's registered after app.run()
```

### Secondary Symptoms After Fixing
When moving routes from after to before `app.run()`, additional issues may appear:

**1. Route duplication** (`AssertionError: View function mapping is overwriting an existing endpoint function`)
- Same route defined before AND after `app.run()`
- Fix: identify and remove duplicates — `grep -n "^@app.route" file.py`

**2. `NameError: name 'render_template' is not defined`**
- Code uses `render_template` but Flask only imported `render_template_string`
- Fix: add to import: `from flask import ..., render_template_string, render_template`

**3. Wrong JSON field in login form** (`{ username }` vs `{ login }`)
- Backend expects `{ login }` but HTML sends `{ username }`
- Fix: verify JS sends correct field names

**4. Test with curl first, browser second**
- Browser may have stale session cookies masking real behavior
- Always test with `curl -v`

### Real Bug (25/04/2026)
- `webhook_sac_avaliar` defined after `app.run()` in `~/.hermes/sac_agent/sac_agent.py`
- Fixed: moved route before `if __name__ == "__main__":`
- Commit: `f92d4ab` in bianinho-cerebro repo

### Production Server Note
Gunicorn/uWSGI/hypercorn don't fix this — they read the same `app` object. If the route was registered after `app.run()`, gunicorn also doesn't see it because the code was never executed.

---

## ◆ Template Files — Complex JS and F-String Conflicts

**Source**: `flask-admin-template-pattern/`

### Symptom
Embedding HTML+JS as Python f-string multi-line causes **SyntaxError** when JS contains template literals with `${expression}`.

```python
# THIS BREAKS:
html = f"""
<script>
tb.innerHTML = `{nome}`;  // SyntaxError!
</script>
"""
```

### Solution
Separate into template files:
```python
@app.route("/admin", methods=["GET"])
def admin_page():
    ok, username = verify_admin_token()
    if not ok:
        return redirect("/")
    return send_file(os.path.join(os.path.dirname(__file__), "templates", "admin.html"))
```

### JS Rules in Templates
- ❌ No template literals with `${}` → use `'+var+'`
- ❌ No arrow functions with expressions in template literals
- ❌ No `const { x } =` destructuring in template literal context
- ✅ Use `function(){}` and string concatenation `'+var+'`

```javascript
// GOOD — works inside template file
tb.innerHTML = rows.map(function(l) {
    return '<tr><td>' + escapeHtml(l.nome) + '</td></tr>';
}).join('');

// BAD — breaks inside f-string Python
tb.innerHTML = rows.map(l => `<tr><td>${l.nome}</td></tr>`).join('');
```

### CSS — Navbar Consistency
Problem: nav links with different widths cause layout shift when clicked.

**Solution — CSS standardized:**
```css
.nav-links {
    display: flex;
    gap: 0;
    align-items: stretch;
}

.nav-link {
    min-width: 120px;
    padding: 10px 16px;
    flex-shrink: 0;
    box-shadow: none;  /* SEM shadow on active — causes visual shift */
    text-align: center;
}

.nav-link:hover {
    background: #1e40af;
    color: #fff;
    text-decoration: none;
}

.nav-link.active {
    background: #1e3a8a;
    border-bottom: 3px solid #60a5fa;
    color: #fff;
}
```

**Golden rule**: any transition on `background`, `border`, or `box-shadow` that changes the visual box causes *cumulative layout shift* (CLS). Use `box-shadow: none` in all states.

---

## ◆ Jinja2 Template Debugging — Variables Appearing Literally

**Source**: `flask-jinja2-template-debugging/`

### Symptom
`{{ username }}` appears literally in rendered HTML instead of the actual value.

### Root Cause
Three ways to serve templates in Flask:

1. `render_template("file.html", var=value)` — processes `.html` files from `templates/` through Jinja2 engine ✅
2. `render_template_string(template_content)` — processes a **string** as Jinja2 template ✅
3. `send_file(path)` — serves file **as raw static file**, no Jinja2 processing ❌

**`send_file()` does NOT process Jinja2 variables.**

### The Fix
```python
from flask import render_template_string

# WRONG
tmpl_path = os.path.join(os.path.dirname(__file__), "templates", "admin.html")
return send_file(tmpl_path)  # Variables appear literally

# RIGHT
tmpl_path = os.path.join(os.path.dirname(__file__), "templates", "admin.html")
with open(tmpl_path, encoding="utf-8") as f:
    tmpl = f.read()
return render_template_string(tmpl, username=username, other_var=value)
```

### Detection Checklist
1. Does page show literal `{{ variable_name }}`? → Use `render_template_string`
2. Does page load but JS doesn't run? → Check browser console for syntax errors
3. Does `render_template("file.html")` fail silently? → Template not in `templates/` folder
