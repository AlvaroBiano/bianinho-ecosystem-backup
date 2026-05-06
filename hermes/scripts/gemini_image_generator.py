#!/usr/bin/env python3
"""
Gemini Image Generator - supports TEXT in images!
Uses curl to call Gemini API via OpenAI-compatible endpoint
"""
import json
import os
import subprocess
import random
import re
from PIL import Image
from datetime import datetime

GEMINI_API_KEY = "AIzaSyC-FtD8GDJ84OtZ-3drq6rAPXfJe7Rb_Bg"

STYLE_LOCK = (
    "Photorealistic photography, maximum detail, 8K resolution, cinematic lighting, "
    "shallow depth of field, professional color grading, Canon EOS R5, 85mm lens, f/1.8 aperture, "
    "natural textures, volumetric lighting, desaturated shadows, warm highlights, "
    "anamorphic lens flare, studio lighting setup, clean background with subtle gradient, "
    "high dynamic range, sharp focus, professional retouching"
)

def generate_gemini_image(prompt, output_path, fmt="youtube"):
    """Generate image using Gemini 2.0 Flash with text support"""
    
    # Gemini API via OpenAI-compatible endpoint
    payload = json.dumps({
        "model": "gemini-2.0-flash-thinking-exp-01-21",
        "prompt": prompt,
        "image_size": "1024x1024" if fmt == "instagram" else "1024x1024"
    })
    
    # Try OpenAI-compatible endpoint first
    result = subprocess.run([
        "curl", "-s", "-X", "POST",
        "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions",
        "-H", f"Authorization: Bearer {GEMINI_API_KEY}",
        "-H", "Content-Type: application/json",
        "-d", payload
    ], capture_output=True, text=True, timeout=60)
    
    print(f"Response: {result.stdout[:500]}")
    return None

# Test
print("Testing Gemini API...")
generate_gemini_image("A beautiful sunset over the ocean", "/tmp/test.jpg")
