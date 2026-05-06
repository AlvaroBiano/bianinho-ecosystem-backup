#!/usr/bin/env python3
"""
Browser automation for Raphael.app - generates images via web interface
Uses Playwright with stealth mode to bypass bot detection
"""
import asyncio
import os
import sys
from datetime import datetime

async def generate_image_raphael(prompt: str, output_path: str = None):
    """Generate image using Raphael.app via browser automation"""
    from playwright.async_api import async_playwright
    from playwright_stealth import stealth as stealth_module
    
    if output_path is None:
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        safe_prompt = prompt[:50].replace(" ", "_").replace("/", "-")
        output_dir = os.path.expanduser("~/Images/generated/raphael")
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, f"{safe_prompt}_{timestamp}.png")
    
    async with stealth_module.Stealth().use_async(async_playwright()) as p:
        print(f"Launching browser (stealth mode)...")
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            viewport={"width": 1920, "height": 1080},
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = await context.new_page()
        
        print(f"Navigating to raphael.app/pt...")
        await page.goto("https://raphael.app/pt", timeout=60000, wait_until="domcontentloaded")
        
        # Wait for page to stabilize
        await asyncio.sleep(3)
        
        # Check for Cloudflare challenge
        page_title = await page.title()
        print(f"Page title: {page_title}")
        
        # Save screenshot for debugging
        debug_path = os.path.expanduser("~/Images/generated/raphael/stealth_debug.png")
        await page.screenshot(path=debug_path)
        print(f"Screenshot saved: {debug_path}")
        
        # Look for the main content/input area
        try:
            # Wait for page to fully load
            await page.wait_for_load_state("networkidle", timeout=30000)
            
            # Try to find the prompt input field
            selectors_to_try = [
                "textarea",
                "input[type='text']",
                "[placeholder*='prompt' i]",
                "[placeholder*='imagem' i]",
                "[placeholder*='image' i]",
                ".prompt-input",
                "#prompt"
            ]
            
            input_field = None
            for selector in selectors_to_try:
                try:
                    input_field = await page.wait_for_selector(selector, timeout=3000)
                    if input_field:
                        print(f"Found input field: {selector}")
                        break
                except:
                    continue
            
            if input_field:
                # Type the prompt
                print(f"Entering prompt: {prompt}")
                await input_field.fill(prompt)
                
                # Look for generate button
                generate_selectors = ["button:has-text('Generate')", "button:has-text('Criar')", "button[type='submit']", ".generate-btn"]
                generate_btn = None
                for sel in generate_selectors:
                    try:
                        generate_btn = await page.wait_for_selector(sel, timeout=3000)
                        if generate_btn:
                            print(f"Found generate button: {sel}")
                            break
                    except:
                        continue
                
                if generate_btn:
                    # Click generate and wait for image
                    await generate_btn.click()
                    print("Clicked generate, waiting for image...")
                    
                    # Wait for image to appear
                    await asyncio.sleep(10)
                    
                    # Try to find the generated image
                    img_selectors = ["img[src*='data:image']", "img[src*='blob']", ".result-img", "img"]
                    for img_sel in img_selectors:
                        try:
                            img = await page.wait_for_selector(img_sel, timeout=5000)
                            if img:
                                src = await img.get_attribute("src")
                                if src and (src.startswith("data:image") or src.startswith("blob:")):
                                    print(f"Found generated image!")
                                    # Download the image
                                    if src.startswith("data:image"):
                                        import base64
                                        # Extract base64 data
                                        header, data = src.split(",", 1)
                                        img_data = base64.b64decode(data)
                                        with open(output_path, "wb") as f:
                                            f.write(img_data)
                                        print(f"Image saved: {output_path}")
                                        return {"success": True, "path": output_path}
                                    elif src.startswith("blob:"):
                                        # Handle blob URLs
                                        print(f"Blob URL found: {src}")
                        except:
                            continue
                
                print("Could not find generate button or image")
            else:
                print("Could not find input field")
                
        except Exception as e:
            print(f"Error during page interaction: {e}")
        
        # Take final screenshot
        final_path = os.path.expanduser("~/Images/generated/raphael/final_state.png")
        await page.screenshot(path=final_path)
        print(f"Final screenshot: {final_path}")
        
        await browser.close()
        return {"success": False, "debug_path": debug_path}

if __name__ == "__main__":
    prompt = sys.argv[1] if len(sys.argv) > 1 else "A beautiful sunset over the ocean"
    print(f"Generating image with prompt: {prompt}")
    result = asyncio.run(generate_image_raphael(prompt))
    print(f"Result: {result}")
