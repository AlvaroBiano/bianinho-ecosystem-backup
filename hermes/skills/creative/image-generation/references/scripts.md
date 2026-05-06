# Image Generation Scripts Reference

## Location
All scripts are in `~/.hermes/scripts/`

## Files
- `image_generator.py` — Main batch generator with style lock, themes, and cron
- `themes.json` — List of themes (edit to add/remove topics)

## Usage

```bash
# Run manually
python3 ~/.hermes/scripts/image_generator.py

# Check output
ls ~/Images/generated/{youtube,instagram}/
```

## Themes Format
```json
[
  {
    "name": "Theme Name",
    "description": "Visual description for the AI (no text instructions)"
  }
]
```

## Adding a Custom Image Generation

For one-off images (like YouTube live thumbnails):

```python
import subprocess
import json
from PIL import Image

API_KEY = "your_key"  # or read from ~/.hermes/.env

prompt = "Photorealistic photography, maximum detail... NO TEXT..."

# Generate via MiniMax
payload = {"model": "image-01", "prompt": prompt, "output_format": "url", "output_size": "1k"}
result = subprocess.run([
    "curl", "-s", "-X", "POST",
    "https://api.minimax.io/v1/image_generation",
    "-H", f"Authorization: Bearer {api_key}",
    "-H", "Content-Type: application/json",
    "-d", json.dumps(payload)
], capture_output=True, text=True, timeout=120)

resp = json.loads(result.stdout)
img_url = resp["data"]["image_urls"][0]

# Download
subprocess.run(["curl", "-s", img_url, "-o", "/tmp/image.jpg"], timeout=60)

# Crop to 16:9 for YouTube
img = Image.open("/tmp/image.jpg")
w, h = img.size
crop_h = int(w * 9 / 16)
top = (h - crop_h) // 2
cropped = img.crop((0, top, w, top + crop_h))
cropped.resize((1920, 1080), Image.LANCZOS).save("/tmp/youtube_thumb.jpg")
```
