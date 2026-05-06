#!/usr/bin/env python3
"""
MiniMax Image Generator - YouTube Thumbnails & Instagram Posts
Style-consistent generation with rotating themes
"""
import json
import os
import random
import subprocess
from datetime import datetime
from PIL import Image

# ==== CONFIG ====
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
THEMES_FILE = os.path.join(SCRIPT_DIR, "themes.json")
STATE_FILE = os.path.join(SCRIPT_DIR, ".image_generator_state.json")
OUTPUT_BASE = os.path.expanduser("~/Images/generated")

# Ler API key do .env
ENV_FILE = os.path.expanduser("~/.hermes/.env")
API_KEY = None
with open(ENV_FILE) as f:
    for line in f:
        if line.strip().startswith("MINIMAX_API_KEY="):
            API_KEY = line.strip().split("=", 1)[1].split("#")[0].strip()
            break

# Style Lock - ESTE É O SEGREDO DA CONSISTÊNCIA
STYLE_LOCK = (
    "Photorealistic photography, maximum detail, 8K resolution, cinematic lighting, "
    "shallow depth of field, professional color grading, Canon EOS R5, 85mm lens, f/1.8 aperture, "
    "natural textures, volumetric lighting, desaturated shadows, warm highlights, "
    "anamorphic lens flare, studio lighting setup, clean background with subtle gradient, "
    "high dynamic range, sharp focus, professional retouching"
)

# Prompt templates por formato — SEM TEXTO
PROMPT_TEMPLATES = {
    "youtube": (
        "{style_lock}. "
        "YouTube thumbnail format. "
        "NO TEXT, NO WORDS, NO LETTERS, NO NUMBERS. "
        "Pure visual composition only. "
        "Topic: {theme}. "
        "Engaging thumbnail with expressive composition, bright and attractive for click-through."
    ),
    "instagram": (
        "{style_lock}. "
        "Instagram post format. "
        "NO TEXT, NO WORDS, NO LETTERS, NO NUMBERS. "
        "Pure visual composition only. "
        "Topic: {theme}. "
        "Professional social media aesthetic, visually striking composition."
    )
}

def load_themes():
    with open(THEMES_FILE) as f:
        return json.load(f)

def load_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE) as f:
            return json.load(f)
    return {"last_index": -1, "last_format": None}

def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f)

def build_prompt(theme, fmt):
    template = PROMPT_TEMPLATES[fmt]
    return template.format(style_lock=STYLE_LOCK, theme=theme)

def process_image(input_path, fmt):
    """Crop and resize to target format"""
    img = Image.open(input_path)
    w, h = img.size
    
    if fmt == "youtube":
        # 16:9 -> 1920x1080 (crop center from square to 16:9)
        target_w, target_h = 1920, 1080
        crop_h = int(w * 9 / 16)
        top = (h - crop_h) // 2
        cropped = img.crop((0, top, w, top + crop_h))
        result = cropped.resize((target_w, target_h), Image.LANCZOS)
    else:  # instagram
        # 4:5 portrait -> 1080x1350 (Instagram portrait)
        target_w, target_h = 1080, 1350
        # Crop from center to get 4:5 ratio, then resize
        crop_w = int(h * 4 / 5)  # width for 4:5 from square
        left = (w - crop_w) // 2
        cropped = img.crop((left, 0, left + crop_w, h))
        result = cropped.resize((target_w, target_h), Image.LANCZOS)
    
    # Save over original
    result.save(input_path)
    return f"{target_w}x{target_h}"

def generate_image(prompt, fmt):
    # API always returns 1024x1024, we crop/resize after
    payload = json.dumps({
        "model": "image-01",
        "prompt": prompt,
        "output_format": "url",
        "output_size": "1k"
    })
    
    result = subprocess.run([
        "curl", "-s", "-X", "POST",
        "https://api.minimax.io/v1/image_generation",
        "-H", f"Authorization: Bearer {API_KEY}",
        "-H", "Content-Type: application/json",
        "-d", payload
    ], capture_output=True, text=True, timeout=120)
    
    if result.returncode != 0:
        raise Exception(f"curl failed: {result.stderr}")
    
    response = json.loads(result.stdout)
    
    if "data" not in response or not response["data"].get("image_urls"):
        raise Exception(f"API error: {response}")
    
    img_url = response["data"]["image_urls"][0]
    
    # Download
    now = datetime.now()
    date_str = now.strftime("%Y-%m-%d")
    time_str = now.strftime("%H-%M")
    
    output_dir = os.path.join(OUTPUT_BASE, fmt, date_str)
    os.makedirs(output_dir, exist_ok=True)
    
    filename = f"{fmt}_{time_str}_{random.randint(1000,9999)}.jpg"
    filepath = os.path.join(output_dir, filename)
    
    subprocess.run([
        "curl", "-s", img_url, "-o", filepath
    ], timeout=60, check=True)
    
    # Process to correct format
    dims = process_image(filepath, fmt)
    
    return filepath, dims

def main():
    themes = load_themes()
    state = load_state()
    
    # Pick next theme (round-robin)
    next_index = (state["last_index"] + 1) % len(themes)
    theme = themes[next_index]
    
    # Alternate formats
    if state["last_format"] == "youtube":
        fmt = "instagram"
    else:
        fmt = "youtube"
    
    # Build prompt
    prompt = build_prompt(theme["description"], fmt)
    
    print(f"[{datetime.now().isoformat()}] Generating {fmt} for theme: {theme['name']}")
    
    # Generate
    filepath, dims = generate_image(prompt, fmt)
    
    # Update state
    state["last_index"] = next_index
    state["last_format"] = fmt
    save_state(state)
    
    print(f"✅ Saved: {filepath} ({dims})")

if __name__ == "__main__":
    main()
