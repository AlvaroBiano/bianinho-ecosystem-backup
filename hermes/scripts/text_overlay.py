#!/usr/bin/env python3
"""
Add stylish styled text to images using PIL
Works on macOS with system fonts
"""
import sys
import os
from PIL import Image, ImageDraw, ImageFont, ImageFilter

def get_stylish_font():
    """Find a good bold font on macOS"""
    font_paths = [
        '/System/Library/Fonts/Supplemental/Verdana Bold.ttf',
        '/System/Library/Fonts/Helvetica.ttc',
        '/System/Library/Fonts/SFNS.ttf',
        '/System/Library/Fonts/Supplemental/Arial Bold.ttf',
    ]
    for fp in font_paths:
        if os.path.exists(fp):
            return fp
    return None

def add_styled_text(
    image_path,
    text,
    output_path=None,
    font_size=80,
    text_color='white',
    stroke_color='black',
    stroke_width=3,
    position='bottom',  # 'center', 'bottom', 'top'
    padding=60,
    shadow=True,
    shadow_blur=5,
    font_path=None
):
    """Add stylish text with shadow and stroke to an image."""
    
    img = Image.open(image_path).convert('RGBA')
    width, height = img.size
    
    # Get font
    if font_path is None:
        font_path = get_stylish_font()
    
    try:
        font = ImageFont.truetype(font_path, font_size) if font_path else ImageFont.load_default(size=font_size)
    except:
        font = ImageFont.load_default(size=font_size)
    
    # Create text layers
    txt_layer = Image.new('RGBA', img.size, (0, 0, 0, 0))
    
    # Calculate text position
    draw = ImageDraw.Draw(txt_layer)
    bbox = draw.textbbox((0, 0), text, font=font)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]
    
    # Horizontal padding - keep text away from edges
    h_padding = width // 10  # 10% margin on each side
    if position == 'bottom':
        x = max(h_padding, (width - tw) // 2)
        y = height - th - padding
    elif position == 'top':
        x = max(h_padding, (width - tw) // 2)
        y = padding
    else:  # center
        x = max(h_padding, (width - tw) // 2)
        y = (height - th) // 2
    
    # Draw shadow
    if shadow:
        shadow_layer = Image.new('RGBA', img.size, (0, 0, 0, 0))
        sdraw = ImageDraw.Draw(shadow_layer)
        rgba = (20, 20, 20, 160)
        for sx in range(-4, 5):
            for sy in range(-4, 5):
                if sx*sx + sy*sy <= 20:
                    sdraw.text((x + sx + 3, y + sy + 3), text, font=font, fill=rgba)
        shadow_layer = shadow_layer.filter(ImageFilter.GaussianBlur(radius=shadow_blur))
        txt_layer = Image.alpha_composite(txt_layer, shadow_layer)
    
    # Draw stroke (outline)
    if stroke_width > 0:
        stroke_layer = Image.new('RGBA', img.size, (0, 0, 0, 0))
        sdraw = ImageDraw.Draw(stroke_layer)
        sr, sg, sb = _hex_to_rgb(stroke_color)
        for sx in range(-stroke_width, stroke_width + 1):
            for sy in range(-stroke_width, stroke_width + 1):
                if sx*sx + sy*sy <= stroke_width * stroke_width:
                    sdraw.text((x + sx, y + sy), text, font=font, fill=(sr, sg, sb, 255))
        txt_layer = Image.alpha_composite(txt_layer, stroke_layer)
    
    # Draw main text
    main_layer = Image.new('RGBA', img.size, (0, 0, 0, 0))
    mdraw = ImageDraw.Draw(main_layer)
    tr, tg, tb = _hex_to_rgb(text_color)
    mdraw.text((x, y), text, font=font, fill=(tr, tg, tb, 255))
    txt_layer = Image.alpha_composite(txt_layer, main_layer)
    
    # Composite onto original
    result = Image.alpha_composite(img, txt_layer)
    result = result.convert('RGB')
    
    # Save
    if output_path is None:
        name, ext = os.path.splitext(image_path)
        output_path = f"{name}_text{ext}"
    
    result.save(output_path, quality=95)
    print(f"Saved: {output_path}")
    return output_path

def add_gradient_text(
    image_path,
    text,
    output_path=None,
    font_size=80,
    color1='gold',
    color2='orange',
    stroke_color='black',
    stroke_width=3,
    position='bottom',
    padding=60
):
    """Add text with gradient fill and stroke."""
    
    img = Image.open(image_path).convert('RGBA')
    width, height = img.size
    
    font_path = get_stylish_font()
    try:
        font = ImageFont.truetype(font_path, font_size) if font_path else ImageFont.load_default(size=font_size)
    except:
        font = ImageFont.load_default(size=font_size)
    
    # Create text to measure
    temp_draw = ImageDraw.Draw(Image.new('RGBA', (1,1)))
    bbox = temp_draw.textbbox((0, 0), text, font=font)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]
    
    if position == 'bottom':
        x = (width - tw) // 2
        y = height - th - padding
    elif position == 'top':
        x = (width - tw) // 2
        y = padding
    else:
        x = (width - tw) // 2
        y = (height - th) // 2
    
    # Create gradient layer
    gradient_layer = Image.new('RGBA', (tw + 20, th + 20), (0, 0, 0, 0))
    gd = ImageDraw.Draw(gradient_layer)
    
    c1 = _hex_to_rgb(color1)
    c2 = _hex_to_rgb(color2)
    
    for i in range(th + 20):
        t = i / max(th, 1)
        r = int(c1[0] * (1-t) + c2[0] * t)
        g = int(c1[1] * (1-t) + c2[1] * t)
        b = int(c1[2] * (1-t) + c2[2] * t)
        gd.line([(0, i), (tw + 20, i)], fill=(r, g, b, 255))
    
    # Create text mask
    text_mask = Image.new('L', (tw + 20, th + 20), 0)
    mdraw = ImageDraw.Draw(text_mask)
    mdraw.text((10, 5), text, font=font, fill=255)
    
    # Apply gradient to text mask
    gradient_layer.putalpha(text_mask)
    
    # Add shadow
    if True:
        shadow_layer = Image.new('RGBA', gradient_layer.size, (0, 0, 0, 0))
        sdraw = ImageDraw.Draw(shadow_layer)
        for sx in range(-3, 4):
            for sy in range(-3, 4):
                if sx*sx + sy*sy <= 12:
                    sdraw.text((10 + sx + 2, 5 + sy + 2), text, font=font, fill=(0, 0, 0, 150))
        shadow_layer = shadow_layer.filter(ImageFilter.GaussianBlur(radius=2))
        gradient_layer = Image.alpha_composite(shadow_layer, gradient_layer)
    
    # Add stroke
    if stroke_width > 0:
        stroke_layer = Image.new('RGBA', gradient_layer.size, (0, 0, 0, 0))
        sdraw = ImageDraw.Draw(stroke_layer)
        sr, sg, sb = _hex_to_rgb(stroke_color)
        for sx in range(-stroke_width, stroke_width + 1):
            for sy in range(-stroke_width, stroke_width + 1):
                if abs(sx) == stroke_width or abs(sy) == stroke_width:
                    sdraw.text((10 + sx, 5 + sy), text, font=font, fill=(sr, sg, sb, 255))
        gradient_layer = Image.alpha_composite(stroke_layer, gradient_layer)
    
    # Composite onto image
    txt_layer = Image.new('RGBA', img.size, (0, 0, 0, 0))
    txt_layer.paste(gradient_layer, (x - 10, y - 5), gradient_layer)
    
    result = Image.alpha_composite(img, txt_layer)
    result = result.convert('RGB')
    
    if output_path is None:
        name, ext = os.path.splitext(image_path)
        output_path = f"{name}_gradient{ext}"
    
    result.save(output_path, quality=95)
    print(f"Saved: {output_path}")
    return output_path

def _hex_to_rgb(color):
    named_colors = {
        'white': (255, 255, 255),
        'black': (0, 0, 0),
        'red': (255, 0, 0),
        'green': (0, 255, 0),
        'blue': (0, 0, 255),
        'yellow': (255, 255, 0),
        'gold': (255, 215, 0),
        'orange': (255, 165, 0),
        'purple': (128, 0, 128),
        'pink': (255, 192, 203),
    }
    if isinstance(color, tuple):
        return color[:3]
    color_lower = color.lower()
    if color_lower in named_colors:
        return named_colors[color_lower]
    color = color.lstrip('#')
    if len(color) != 6:
        return (255, 255, 255)  # default white
    return tuple(int(color[i:i+2], 16) for i in (0, 2, 4))

if __name__ == '__main__':
    if len(sys.argv) < 3:
        print("Usage: text_overlay.py <image_path> <text> [output_path]")
        sys.exit(1)
    
    image_path = sys.argv[1]
    text = sys.argv[2]
    output_path = sys.argv[3] if len(sys.argv) > 3 else None
    
    add_styled_text(
        image_path, text, output_path,
        font_size=90,
        text_color='white',
        stroke_color='black',
        stroke_width=4,
        position='bottom',
        shadow=True,
        padding=80
    )
