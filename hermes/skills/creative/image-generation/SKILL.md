---
name: image-generation
description: Multi-provider image generation workflow — MiniMax API, Gemini, Leonardo.ai, Ideogram, and other providers. Style lock technique, post-processing crop/resize, format specs (YouTube 16:9, Instagram 4:5), and cron-based batch generation.
triggers:
  - generate image
  - create thumbnail
  - youtube thumbnail
  - instagram post image
  - image cron
  - consistent style image
  - text in image
  - text overlay
---

# Image Generation Workflow

## Providers

### MiniMax (PRIMARY — already configured)
- **Endpoint:** `https://api.minimax.io/v1/image_generation`
- **Model:** `image-01`
- **API Key:** stored in `~/.hermes/.env` as `MINIMAX_API_KEY`
- **Quota:** 50 images/day (Token Plan)
- **IMPORTANT — API Response Format:**
  ```python
  # CORRECT: response['data']['image_urls'][0]
  url = response['data']['image_urls'][0]  # ✅ correct
  # WRONG:  response['data'][0]['url']      # ❌ this fails
  ```
  Response structure: `{"id": "...", "data": {"image_urls": [...]}, "metadata": {...}, "base_resp": {...}}`
  Download with `urllib.request.urlretrieve(url, output_path)`

### Gemini (needs working API key)
- **API Key:** stored in `~/.hermes/.env` as `GEMINI_API_KEY`
- **NOTE:** Gemini API free tier often shows limit:0 quota. Key provided by user (AIzaSyC-FtD8GDJ84OtZ-3drq6rAPXfJe7Rb_Bg) had NO quota available.
- **Models with image gen:** `gemini-2.5-flash-image`, `imagen-4.0-generate-001` (paid only)

### Ideogram (PAID — VERIFY BEFORE RELYING ON)
- **Signup:** https://ideogram.ai
- **Status:** User reported Ideogram is PAID, not free. Free tier may not exist or may have been removed.
- **NOTE:** Cannot create account automatically. DO NOT promise free tier without verification.

## CRITICAL: output_size Workaround (MiniMax)

MiniMax API **ignores** the `output_size` parameter — always returns **1024x1024**.

**Solution:** Crop/resize with PIL after download.

```python
from PIL import Image

def process_image(input_path, fmt):
    img = Image.open(input_path)
    w, h = img.size  # Always 1024x1024 from MiniMax
    
    if fmt == "youtube":
        # 16:9 → 1920x1080
        target_w, target_h = 1920, 1080
        crop_h = int(w * 9 / 16)  # 576
        top = (h - crop_h) // 2
        cropped = img.crop((0, top, w, top + crop_h))
        result = cropped.resize((target_w, target_h), Image.LANCZOS)
    else:  # instagram
        # 4:5 portrait → 1080x1350
        target_w, target_h = 1080, 1350
        crop_w = int(h * 4 / 5)  # 819
        left = (w - crop_w) // 2
        cropped = img.crop((left, 0, left + crop_w, h))
        result = cropped.resize((target_w, target_h), Image.LANCZOS)
    
    result.save(input_path)
    return f"{target_w}x{target_h}"
```

## Style Lock Technique (Consistent Visual Style)

To generate images with consistent style across different themes, use a **fixed style lock prompt** that never changes, combined with a variable theme description.

```python
STYLE_LOCK = (
    "Photorealistic photography, maximum detail, 8K resolution, cinematic lighting, "
    "shallow depth of field, professional color grading, Canon EOS R5, 85mm lens, f/1.8 aperture, "
    "natural textures, volumetric lighting, desaturated shadows, warm highlights, "
    "anamorphic lens flare, studio lighting setup, clean background with subtle gradient, "
    "high dynamic range, sharp focus, professional retouching"
)

# For text-free images:
NO_TEXT_CLAUSE = "NO TEXT, NO WORDS, NO LETTERS, NO NUMBERS. Pure visual composition only."
```

## Text in Images — Stylized Text Overlay

**MiniMax does NOT render text well** — always use MiniMax for base imagery only, then overlay text with PIL.

### Stylish Text Script

```bash
python3 ~/.hermes/scripts/stylish_text.py <image_path> "<texto>" <output_path> <estilo>
```

**7 Available styles:**

| Style | Description | Álvaro's Rating |
|-------|-------------|----------------|
| `neon` | Cyan glow on dark, white core | ✅ Loved it |
| `3d` | Extruded depth effect, dark shadow layers | ✅ Loved it |
| `outline_glow` | Yellow glow with black stroke | ✅ Loved it |
| `gradient` | Gold→orange gradient fill | ✅ Loved it |
| `solid_box` | Black semi-transparent box behind text | Good |
| `vintage` | Sépia/warm tones, darkened image | Good |
| `mirror` | Text with reflection below | ❌ Takes too much space — AVOID |

**Parameters:**
- `font_size`: defaults 100, adjust for image size
- `text_color`: white, black, red, green, blue, yellow, gold, orange, purple, pink, cyan
- `glow_color` (neon): blue, cyan, purple, pink
- `position`: 'bottom', 'top', 'center'
- `padding`: distance from edge (default 70 for bottom, 50 for top)
- `bg_color` (solid_box): RGBA tuple, e.g. `(0,0,0,180)` for semi-transparent black

**Horizontal padding (IMPORTANT):** Always use `max(50, (width-tw)//2)` for x position — prevents text from touching edges. The `~/.hermes/scripts/stylish_text.py` already has this fix.

**Font:** Uses macOS Verdana Bold (`/System/Library/Fonts/Supplemental/Verdana Bold.ttf`).

**Output location:** Always save to `~/Desktop/img_test/` or `~/Images/generated/<type>/`. Tell the user exactly where.

### Quick Test:
```bash
python3 ~/.hermes/scripts/stylish_text.py /tmp/test.jpg "HELLO" ~/Desktop/test.jpg neon
```

### All Color Names Supported:
white, black, red, green, blue, yellow, gold, orange, purple, pink, cyan, gray

## Format Specifications

| Platform | Aspect Ratio | Dimensions | Crop/Resize |
|----------|-------------|------------|-------------|
| YouTube Thumbnail | 16:9 | 1920×1080 | Crop center from square to 16:9 |
| Instagram Post | 4:5 | 1080×1350 | Crop center from square to 4:5 |
| Instagram Story | 9:16 | 1080×1920 | Crop center from square to 9:16 |

## Delivering Results to User (CRITICAL)

**Always tell the user WHERE files are saved.** Never just say "done" without a path.
- Save to `~/Desktop/<folder>/` or `~/Images/generated/<type>/` so user can find them
- If generating multiple versions: put them in the same folder with clear names (v1, v2, v3 or descriptive names)
- **Never assume the user can find files in `/tmp`** — only Desktop and ~/Images are visible to them

## Cron-Based Batch Generation

See: `~/.hermes/scripts/image_generator.py`

```bash
# Add to crontab for every 10 minutes:
*/10 * * * * cd ${HOME} && python3 ${HOME}/.hermes/scripts/image_generator.py >> ${HOME}/.hermes/logs/image_generator.log 2>&1
```

Themes are stored in `~/.hermes/scripts/themes.json` — edit to add/remove topics.

## Python 3.14 SSL Workaround

On macOS with Python 3.14, use `curl` instead of `urllib` for API calls:

```python
import subprocess
import json

result = subprocess.run([
    "curl", "-s", "-X", "POST",
    "https://api.minimax.io/v1/image_generation",
    "-H", f"Authorization: Bearer {api_key}",
    "-H", "Content-Type: application/json",
    "-d", json.dumps(payload)
], capture_output=True, text=True, timeout=120)
```

## Limitations

### Account Creation
- **Cannot create external service accounts automatically** — Leonardo.ai, Ideogram, etc. require phone/email verification (CAPTCHA) that needs human interaction
- **Gemini API key must be verified for quota** — free tier often shows limit:0 until billing is configured

### Text Rendering
- **MiniMax:** Does NOT render text well in images — only use for base imagery
- **Raphael.app:** Good text support but automation incomplete — result doesn't appear in DOM. Use PIL `stylish_text.py` instead for text overlays.

### Browser Automation
- **Raphael.app:** Page loads with Hermes browser stealth mode, but generated image result never appears in DOM. Cannot automate download. Use MiniMax + PIL text overlay instead.
