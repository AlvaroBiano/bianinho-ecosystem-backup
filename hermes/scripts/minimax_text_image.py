#!/usr/bin/env python3
"""
MiniMax + Texto - Gerador de thumbnails/posts com texto em PT-BR
Composições profissionais com texto sobre imagem
"""
import json
import os
import subprocess
import random
import re
import textwrap
from PIL import Image, ImageDraw, ImageFont
from datetime import datetime

# ==== CONFIG ====
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_BASE = os.path.expanduser("~/Images/generated")

# Ler API key
with open(os.path.expanduser("~/.hermes/.env")) as f:
    for line in f:
        if line.strip().startswith("MINIMAX_API_KEY="):
            API_KEY = line.strip().split("=", 1)[1].split("#")[0].strip()
            break

# Style Lock
STYLE_LOCK = (
    "Photorealistic photography, maximum detail, 8K resolution, cinematic lighting, "
    "shallow depth of field, professional color grading, Canon EOS R5, 85mm lens, f/1.8 aperture, "
    "natural textures, volumetric lighting, desaturated shadows, warm highlights, "
    "anamorphic lens flare, studio lighting setup, clean background with subtle gradient, "
    "high dynamic range, sharp focus, professional retouching"
)

# Fontes disponíveis (prioridade)
FONT_PATHS = [
    "/System/Library/Fonts/Arial Bold.ttf",
    "/System/Library/Fonts/ArialHB.ttc",
    "/Library/Fonts/Arial Bold.ttf",
    "/Library/Fonts/Arial.ttf",
]

def get_font(size, bold=True):
    """Carrega fonte disponível"""
    for path in FONT_PATHS:
        if os.path.exists(path):
            try:
                if bold and "Bold" in path:
                    return ImageFont.truetype(path, size)
                elif bold:
                    # Tentar versão bold
                    bold_path = path.replace(".ttf", " Bold.ttf").replace(".ttc", " Bold.ttc")
                    if os.path.exists(bold_path):
                        return ImageFont.truetype(bold_path, size)
                    return ImageFont.truetype(path, size)
            except:
                continue
    # Fallback
    return ImageFont.load_default()

def add_text_to_image(img_path, texts, fmt="youtube"):
    """
    Adiciona texto(s) à imagem
    texts: lista de dicts com {text, position, font_size, color, stroke_color, stroke_width}
    position: 'top', 'center', 'bottom', 'custom'
    """
    img = Image.open(img_path).convert("RGBA")
    overlay = Image.new("RGBA", img.size, (255, 255, 255, 0))
    draw = ImageDraw.Draw(overlay)
    
    w, h = img.size
    
    for item in texts:
        text = item["text"]
        position = item.get("position", "bottom")
        font_size = item.get("font_size", int(h * 0.08))
        color = item.get("color", (255, 255, 255, 255))
        stroke_color = item.get("stroke_color", (0, 0, 0, 255))
        stroke_width = item.get("stroke_width", 2)
        
        font = get_font(font_size, bold=True)
        
        # Calcular tamanho do texto
        bbox = draw.textbbox((0, 0), text, font=font)
        text_w = bbox[2] - bbox[0]
        text_h = bbox[3] - bbox[1]
        
        # Posição
        if position == "top":
            x = w // 2 - text_w // 2
            y = int(h * 0.05)
        elif position == "center":
            x = w // 2 - text_w // 2
            y = h // 2 - text_h // 2
        elif position == "bottom":
            x = w // 2 - text_w // 2
            y = int(h * 0.78)
        else:  # custom
            x = item.get("x", w // 2 - text_w // 2)
            y = item.get("y", h // 2)
        
        # Desenhar com stroke (borda)
        if stroke_width > 0:
            for stroke_x in range(-stroke_width, stroke_width + 1):
                for stroke_y in range(-stroke_width, stroke_width + 1):
                    if stroke_x == 0 and stroke_y == 0:
                        continue
                    draw.text((x + stroke_x, y + stroke_y), text, font=font, fill=stroke_color)
        
        # Desenhar texto principal
        draw.text((x, y), text, font=font, fill=color)
    
    # Combinar
    result = Image.alpha_composite(img, overlay).convert("RGB")
    result.save(img_path, "JPEG", quality=95)
    return img_path

def process_image_size(img_path, fmt):
    """Redimensiona para o formato correto"""
    img = Image.open(img_path)
    w, h = img.size
    
    if fmt == "youtube":
        # 16:9 - crop e resize para 1920x1080
        target_w, target_h = 1920, 1080
        crop_h = int(w * 9 / 16)
        top = (h - crop_h) // 2
        cropped = img.crop((0, top, w, top + crop_h))
        result = cropped.resize((target_w, target_h), Image.LANCZOS)
    else:  # instagram
        # 4:5 portrait - crop e resize para 1080x1350
        target_w, target_h = 1080, 1350
        crop_w = int(h * 4 / 5)
        left = (w - crop_w) // 2
        cropped = img.crop((left, 0, left + crop_w, h))
        result = cropped.resize((target_w, target_h), Image.LANCZOS)
    
    result.save(img_path)
    return img_path

def generate_with_text(prompt, texts, fmt="youtube"):
    """Gera imagem e adiciona texto"""
    # 1. Gerar imagem base
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
    
    resp = json.loads(result.stdout)
    img_url = resp["data"]["image_urls"][0]
    
    # Download
    now = datetime.now()
    date_str = now.strftime("%Y-%m-%d")
    time_str = now.strftime("%H-%M")
    
    output_dir = os.path.join(OUTPUT_BASE, fmt, date_str)
    os.makedirs(output_dir, exist_ok=True)
    
    filename = f"{fmt}_{time_str}_{random.randint(1000,9999)}.jpg"
    filepath = os.path.join(output_dir, filename)
    
    subprocess.run(["curl", "-s", img_url, "-o", filepath], timeout=60, check=True)
    
    # 2. Processar tamanho
    process_image_size(filepath, fmt)
    
    # 3. Adicionar texto(s)
    add_text_to_image(filepath, texts, fmt)
    
    return filepath

def main():
    import sys
    
    if len(sys.argv) < 3:
        print("Usage: python3 minimax_text_image.py '<prompt>' '<json_texts>' [format]")
        print("Example: python3 minimax_text_image.py 'Beautiful sunset' '[{\"text\":\"Olá Mundo\",\"position\":\"center\",\"font_size\":80}]' youtube")
        sys.exit(1)
    
    prompt = sys.argv[1]
    texts = json.loads(sys.argv[2])
    fmt = sys.argv[3] if len(sys.argv) > 3 else "youtube"
    
    # Se texts for string (JSON), já convertido. Se for dict, envolver em lista
    if isinstance(texts, str):
        texts = json.loads(texts)
    if isinstance(texts, dict):
        texts = [texts]
    
    print(f"Generating {fmt} image...")
    filepath = generate_with_text(prompt, texts, fmt)
    print(f"✅ Saved: {filepath}")

if __name__ == "__main__":
    main()
