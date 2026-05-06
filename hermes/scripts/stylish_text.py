#!/usr/bin/env python3
"""
Stylish Text Generator — criadores de texto impactante para imagens
Múltiplos estilos: neon, 3D, vintage, glow, gradient, outline, etc.
"""
import os
import math
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance

# ============================================================
# HELPERS
# ============================================================

def get_font(size=80, bold=True):
    """Get a nice bold font on macOS"""
    fonts = [
        '/System/Library/Fonts/Supplemental/Verdana Bold.ttf',
        '/System/Library/Fonts/Helvetica.ttc',
        '/System/Library/Fonts/Supplemental/Arial Bold.ttf',
        '/System/Library/Fonts/SFNS.ttf',
    ]
    for f in fonts:
        if os.path.exists(f):
            try:
                return ImageFont.truetype(f, size)
            except:
                pass
    return ImageFont.load_default(size=size)

def hex_to_rgb(color):
    named = {
        'white': (255,255,255), 'black': (0,0,0),
        'red': (255,50,50), 'green': (50,255,50),
        'blue': (50,100,255), 'yellow': (255,255,50),
        'gold': (255,215,0), 'orange': (255,140,0),
        'purple': (180,50,255), 'pink': (255,100,180),
        'cyan': (0,255,255), 'white': (255,255,255),
        'gray': (128,128,128), 'grey': (128,128,128),
    }
    if isinstance(color, tuple):
        return color[:3]
    c = color.lower().strip('#')
    if c in named:
        return named[c]
    try:
        return tuple(int(c[i:i+2],16) for i in (0,2,4))
    except:
        return (255,255,255)

def parse_pos(position, width, height, tw, th, padding=60):
    if position == 'bottom':
        return (max(50, (width-tw)//2), height - th - padding)
    elif position == 'top':
        return (max(50, (width-tw)//2), padding)
    elif position == 'center':
        return ((width-tw)//2, (height-th)//2)
    return (max(50, (width-tw)//2), (height-th)//2)

# ============================================================
# TEXT STYLES
# ============================================================

def style_neon(image_path, text, output_path, 
               font_size=100, text_color='cyan', glow_color='blue',
               position='bottom', padding=70, intensity=1.0):
    """Neon glow effect"""
    img = Image.open(image_path).convert('RGBA')
    w, h = img.size
    font = get_font(font_size)
    
    txt = Image.new('RGBA', img.size, (0,0,0,0))
    draw = ImageDraw.Draw(txt)
    x, y = parse_pos(position, w, h, 0, 0, padding)
    
    # Measure text
    bbox = draw.textbbox((0,0), text, font=font)
    tw = bbox[2]-bbox[0]
    th = bbox[3]-bbox[1]
    x = max(50, (w-tw)//2)
    if position == 'bottom': y = h - th - padding
    elif position == 'top': y = padding
    
    tc = hex_to_rgb(text_color)
    gc = hex_to_rgb(glow_color)
    
    # Outer glow layers
    for blur in [15, 10, 5]:
        alpha = int(60 * intensity * (20-blur)/20)
        glow = Image.new('RGBA', img.size, (0,0,0,0))
        gdraw = ImageDraw.Draw(glow)
        for dx in range(-blur, blur+1):
            for dy in range(-blur, blur+1):
                d = math.sqrt(dx*dx + dy*dy)
                if d <= blur:
                    gdraw.text((x+dx, y+dy), text, font=font, fill=(*gc, alpha))
        glow = glow.filter(ImageFilter.GaussianBlur(radius=blur//2))
        txt = Image.alpha_composite(txt, glow)
    
    # Core text
    draw.text((x, y), text, font=font, fill=(*tc, 255))
    
    # White inner
    draw.text((x, y), text, font=font, fill=(255,255,255,200))
    
    result = Image.alpha_composite(img, txt).convert('RGB')
    result.save(output_path, quality=95)
    print(f"Neon saved: {output_path}")

def style_3d(image_path, text, output_path,
             font_size=100, depth=8,
             text_color='white', shadow_color=(30,30,30),
             position='bottom', padding=70):
    """3D extruded text effect"""
    img = Image.open(image_path).convert('RGBA')
    w, h = img.size
    font = get_font(font_size)
    
    txt = Image.new('RGBA', img.size, (0,0,0,0))
    draw = ImageDraw.Draw(txt)
    
    bbox = draw.textbbox((0,0), text, font=font)
    tw = bbox[2]-bbox[0]
    th = bbox[3]-bbox[1]
    x = max(50, (w-tw)//2)
    if position == 'bottom': y = h - th - padding
    elif position == 'top': y = padding
    else: y = (h-th)//2
    
    tc = hex_to_rgb(text_color)
    sc = hex_to_rgb(shadow_color) if isinstance(shadow_color, str) else shadow_color
    
    # Depth layers (back to front)
    for i in range(depth, 0, -1):
        shade = tuple(max(0, c - i*3) for c in sc)
        offset = i // 2
        draw.text((x+offset, y+offset), text, font=font, fill=(*shade, 255))
    
    # Main text
    draw.text((x, y), text, font=font, fill=(*tc, 255))
    
    result = Image.alpha_composite(img, txt).convert('RGB')
    result.save(output_path, quality=95)
    print(f"3D saved: {output_path}")

def style_vintage(image_path, text, output_path,
                  font_size=100, text_color=(210,180,140),
                  position='bottom', padding=70):
    """Vintage / old paper look"""
    img = Image.open(image_path).convert('RGB')
    w, h = img.size
    font = get_font(font_size)
    
    # Slightly desaturate and warm
    enhancer = ImageEnhance.Color(img)
    img = enhancer.enhance(0.7)
    enhancer = ImageEnhance.Brightness(img)
    img = enhancer.enhance(0.85)
    
    img = img.convert('RGBA')
    txt = Image.new('RGBA', img.size, (0,0,0,0))
    draw = ImageDraw.Draw(txt)
    
    bbox = draw.textbbox((0,0), text, font=font)
    tw = bbox[2]-bbox[0]
    th = bbox[3]-bbox[1]
    x = max(50, (w-tw)//2)
    if position == 'bottom': y = h - th - padding
    elif position == 'top': y = padding
    else: y = (h-th)//2
    
    # Dark shadow
    for dx in range(-3,4):
        for dy in range(-3,4):
            if dx*dx+dy*dy <= 10:
                draw.text((x+dx*2, y+dy*2), text, font=font, fill=(50,30,10,120))
    
    # Main text
    draw.text((x, y), text, font=font, fill=(*text_color, 255))
    
    result = Image.alpha_composite(img, txt).convert('RGB')
    result.save(output_path, quality=95)
    print(f"Vintage saved: {output_path}")

def style_outline_glow(image_path, text, output_path,
                       font_size=100, text_color='white',
                       outline_color='black', outline_width=5,
                       glow=True, glow_color=(255,255,100),
                       position='bottom', padding=70):
    """Text with outline + optional glow"""
    img = Image.open(image_path).convert('RGBA')
    w, h = img.size
    font = get_font(font_size)
    
    txt = Image.new('RGBA', img.size, (0,0,0,0))
    draw = ImageDraw.Draw(txt)
    
    bbox = draw.textbbox((0,0), text, font=font)
    tw = bbox[2]-bbox[0]
    th = bbox[3]-bbox[1]
    x = max(50, (w-tw)//2)
    if position == 'bottom': y = h - th - padding
    elif position == 'top': y = padding
    else: y = (h-th)//2
    
    tc = hex_to_rgb(text_color)
    oc = hex_to_rgb(outline_color)
    
    # Glow
    if glow:
        glw = Image.new('RGBA', img.size, (0,0,0,0))
        gdraw = ImageDraw.Draw(glw)
        for gx in range(-8,9):
            for gy in range(-8,9):
                if gx*gx + gy*gy <= 64:
                    gdraw.text((x+gx, y+gy), text, font=font, fill=(*glow_color, 30))
        glw = glw.filter(ImageFilter.GaussianBlur(radius=6))
        txt = Image.alpha_composite(txt, glw)
    
    # Outline
    ol = Image.new('RGBA', img.size, (0,0,0,0))
    odraw = ImageDraw.Draw(ol)
    for ox in range(-outline_width, outline_width+1):
        for oy in range(-outline_width, outline_width+1):
            if ox*ox + oy*oy <= outline_width*outline_width:
                odraw.text((x+ox, y+oy), text, font=font, fill=(*oc, 255))
    txt = Image.alpha_composite(txt, ol)
    
    # Main text
    draw.text((x, y), text, font=font, fill=(*tc, 255))
    
    result = Image.alpha_composite(img, txt).convert('RGB')
    result.save(output_path, quality=95)
    print(f"Outline+Glow saved: {output_path}")

def style_gradient_text(image_path, text, output_path,
                        font_size=100, color1='gold', color2='orange',
                        stroke_color='black', stroke_width=4,
                        position='bottom', padding=70):
    """Text with gradient fill"""
    img = Image.open(image_path).convert('RGBA')
    w, h = img.size
    font = get_font(font_size)
    
    txt = Image.new('RGBA', img.size, (0,0,0,0))
    draw = ImageDraw.Draw(txt)
    
    bbox = draw.textbbox((0,0), text, font=font)
    tw = bbox[2]-bbox[0]
    th = bbox[3]-bbox[1]
    x = max(50, (w-tw)//2)
    if position == 'bottom': y = h - th - padding
    elif position == 'top': y = padding
    else: y = (h-th)//2
    
    c1 = hex_to_rgb(color1)
    c2 = hex_to_rgb(color2)
    
    # Gradient layer
    grad = Image.new('RGB', (tw+20, th+20), (0,0,0))
    gd = ImageDraw.Draw(grad)
    for i in range(th+20):
        t = i / max(th, 1)
        r = int(c1[0]*(1-t) + c2[0]*t)
        g = int(c1[1]*(1-t) + c2[1]*t)
        b = int(c1[2]*(1-t) + c2[2]*t)
        gd.line([(0,i),(tw+20,i)], fill=(r,g,b))
    
    # Mask
    mask = Image.new('L', (tw+20, th+20), 0)
    mdraw = ImageDraw.Draw(mask)
    mdraw.text((10,5), text, font=font, fill=255)
    
    grad.putalpha(mask)
    
    # Shadow
    shd = Image.new('RGBA', grad.size, (0,0,0,0))
    sdraw = ImageDraw.Draw(shd)
    for sx in range(-3,4):
        for sy in range(-3,4):
            if sx*sx+sy*sy <= 10:
                sdraw.text((10+sx+2, 5+sy+2), text, font=font, fill=(0,0,0,150))
    shd = shd.filter(ImageFilter.GaussianBlur(radius=2))
    grad = Image.alpha_composite(shd, grad)
    
    # Stroke
    if stroke_width > 0:
        strk = Image.new('RGBA', grad.size, (0,0,0,0))
        sdraw = ImageDraw.Draw(strk)
        sc = hex_to_rgb(stroke_color)
        for sx in range(-stroke_width, stroke_width+1):
            for sy in range(-stroke_width, stroke_width+1):
                if abs(sx)==stroke_width or abs(sy)==stroke_width:
                    sdraw.text((10+sx, 5+sy), text, font=font, fill=(*sc,255))
        grad = Image.alpha_composite(strk, grad)
    
    txt_layer = Image.new('RGBA', img.size, (0,0,0,0))
    txt_layer.paste(grad, (x-10, y-5), grad)
    
    result = Image.alpha_composite(img, txt_layer).convert('RGB')
    result.save(output_path, quality=95)
    print(f"Gradient saved: {output_path}")

def style_solid_box(image_path, text, output_path,
                    font_size=100, text_color='white',
                    box_color=(0,0,0,200), box_padding=30,
                    position='bottom', padding=70):
    """Text with solid background box"""
    img = Image.open(image_path).convert('RGBA')
    w, h = img.size
    font = get_font(font_size)
    
    txt = Image.new('RGBA', img.size, (0,0,0,0))
    draw = ImageDraw.Draw(txt)
    
    bbox = draw.textbbox((0,0), text, font=font)
    tw = bbox[2]-bbox[0]
    th = bbox[3]-bbox[1]
    x = max(50, (w-tw)//2)
    if position == 'bottom': y = h - th - padding
    elif position == 'top': y = padding
    else: y = (h-th)//2
    
    tc = hex_to_rgb(text_color)
    
    # Background box
    bx = x - box_padding
    by = y - box_padding//2
    bw = tw + box_padding*2
    bh = th + box_padding
    
    # Draw box
    box_img = Image.new('RGBA', img.size, (0,0,0,0))
    box_draw = ImageDraw.Draw(box_img)
    box_draw.rectangle([bx, by, bx+bw, by+bh], fill=box_color)
    txt = Image.alpha_composite(txt, box_img)
    
    # Text
    draw = ImageDraw.Draw(txt)
    draw.text((x, y), text, font=font, fill=(*tc, 255))
    
    result = Image.alpha_composite(img, txt).convert('RGB')
    result.save(output_path, quality=95)
    print(f"Solid box saved: {output_path}")

def style_mirror_reflection(image_path, text, output_path,
                            font_size=100, text_color='white',
                            reflection_opacity=0.3,
                            position='bottom', padding=70):
    """Text with mirror reflection below"""
    img = Image.open(image_path).convert('RGBA')
    w, h = img.size
    font = get_font(font_size)
    
    txt = Image.new('RGBA', img.size, (0,0,0,0))
    draw = ImageDraw.Draw(txt)
    
    bbox = draw.textbbox((0,0), text, font=font)
    tw = bbox[2]-bbox[0]
    th = bbox[3]-bbox[1]
    x = max(50, (w-tw)//2)
    if position == 'bottom': y = h - th*2 - padding
    elif position == 'top': y = padding
    else: y = (h-th)//2
    
    tc = hex_to_rgb(text_color)
    
    # Shadow
    shd = Image.new('RGBA', img.size, (0,0,0,0))
    sdraw = ImageDraw.Draw(shd)
    for dx in range(-4,5):
        for dy in range(-4,5):
            if dx*dx+dy*dy <= 20:
                sdraw.text((x+dx+3, y+dy+3), text, font=font, fill=(0,0,0,160))
    shd = shd.filter(ImageFilter.GaussianBlur(radius=3))
    txt = Image.alpha_composite(txt, shd)
    
    # Main text
    draw.text((x, y), text, font=font, fill=(*tc, 255))
    
    # Reflection
    ref = Image.new('RGBA', img.size, (0,0,0,0))
    rdraw = ImageDraw.Draw(ref)
    rdraw.text((x, y + th), text, font=font, fill=(*tc, int(255*reflection_opacity)))
    # Flip and blur
    ref_section = ref.crop((0, y+th, w, y+th+th))
    ref_section = ref_section.transpose(Image.FLIP_TOP_BOTTOM)
    ref_section = ref_section.filter(ImageFilter.GaussianBlur(radius=2))
    
    ref_mask = Image.new('L', ref_section.size, 0)
    rm = ImageDraw.Draw(ref_mask)
    # Fade gradient
    for i in range(ref_section.height):
        alpha = int(255 * (1 - i/ref_section.height * 1.5))
        alpha = max(0, min(255, alpha))
        rm.line([(0,i),(ref_section.width,i)], fill=alpha)
    
    ref_section.putalpha(ref_mask)
    ref.paste(ref_section, (0, y+th), ref_section)
    txt = Image.alpha_composite(txt, ref)
    
    result = Image.alpha_composite(img, txt).convert('RGB')
    result.save(output_path, quality=95)
    print(f"Mirror reflection saved: {output_path}")

# ============================================================
# DEMO
# ============================================================

if __name__ == '__main__':
    import sys
    if len(sys.argv) < 3:
        print("Usage: stylish_text.py <image_path> <text> <output_path> [style]")
        print("Styles: neon, 3d, vintage, outline_glow, gradient, solid_box, mirror")
        sys.exit(1)
    
    img_path = sys.argv[1]
    txt = sys.argv[2]
    out_path = sys.argv[3]
    style = sys.argv[4] if len(sys.argv) > 4 else 'outline_glow'
    
    if style == 'neon':
        style_neon(img_path, txt, out_path, font_size=110, text_color='cyan', glow_color='blue')
    elif style == '3d':
        style_3d(img_path, txt, out_path, font_size=110)
    elif style == 'vintage':
        style_vintage(img_path, txt, out_path, font_size=100)
    elif style == 'outline_glow':
        style_outline_glow(img_path, txt, out_path, font_size=100)
    elif style == 'gradient':
        style_gradient_text(img_path, txt, out_path, font_size=100)
    elif style == 'solid_box':
        style_solid_box(img_path, txt, out_path, font_size=100)
    elif style == 'mirror':
        style_mirror_reflection(img_path, txt, out_path, font_size=100)
    else:
        style_outline_glow(img_path, txt, out_path, font_size=100)
