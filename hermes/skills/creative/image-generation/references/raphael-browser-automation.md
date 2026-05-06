# Raphael.app Browser Automation — Attempt Log

## Date: 2026-05-04

## Goal
Automate image generation on Raphael.app using Playwright to bypass lack of API.

## Setup
```bash
pip3 install playwright
playwright install chromium
```

## Script Location
`~/.hermes/scripts/raphael_browser.py`

## What Worked
- Page navigation ✓
- Prompt filling ✓
- Button clicking ✓

## What Failed
- Image generation results never appeared
- Cloudflare detected headless browser and blocked generation
- No base64 or blob images returned

## Symptoms
- Page loads correctly
- Textarea and buttons found
- Generation appears to start but never completes
- After ~2 minutes, no new images compared to baseline

## Possible Solutions (Not Tested)
1. **playwright-stealth** package — masks headless browser fingerprints
2. **undetected-chromedriver** — alternative to Playwright
3. **Manual operation** — user opens site, generates, downloads

## Updated: 2026-05-04 (Hermes browser tools test)

### What Works
- **Hermes browser tools with stealth mode CAN access raphael.app** — page loads fully with all elements
- Prompt filling works (textbox selector: `textarea` or `textbox[placeholder*='prompt']`)
- "Gerar" button clickable (ref=e18 or find by text content)
- Style selection buttons available (1:1, Sem Estilo, etc.)
- Page title: "Raphael AI - Gerador de Imagem AI Gratuito e Ilimitado"

### What Still Fails
- After clicking "Gerar", the generated image does NOT appear in the DOM
- No base64 data: or blob: URLs returned for generated images
- Generation appears to start (no error) but result is never exposed to automation
- This means automated download of the generated image is NOT possible

### Hermes Browser Tool Commands That Work
```
browser_navigate("https://raphael.app/pt")
browser_type(ref="e64", text="your prompt")
browser_click(ref="e18")  # Gerar button
browser_snapshot(full=false)  # Check state
```

### Conclusion
Raphael.app is PARTIALLY automatable — you can navigate, fill prompts, and trigger generation, but you cannot programmatically retrieve the result image. Use MiniMax API for fully automated image generation. Use Raphael manually when text-in-image is required.

### Script Location
`~/.hermes/scripts/raphael_browser.py` — old Playwright-only attempt (superseded by Hermes browser tools)

## Relevant Code
See `~/.hermes/scripts/raphael_browser.py` for the attempt.
