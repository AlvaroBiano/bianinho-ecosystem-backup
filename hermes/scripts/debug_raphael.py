#!/usr/bin/env python3
"""Debug Raphael page structure"""
import asyncio
from playwright.async_api import async_playwright

async def debug_raphael():
    from playwright.async_api import async_playwright
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        print("Navigating to raphael.app/pt...")
        await page.goto("https://raphael.app/pt", timeout=60000)
        await page.wait_for_load_state("networkidle", timeout=30000)
        
        print("Getting page HTML structure...")
        
        # Get textarea info
        textareas = await page.query_selector_all("textarea")
        print(f"\nFound {len(textareas)} textarea(s)")
        for i, ta in enumerate(textareas):
            id_ = await ta.get_attribute("id")
            placeholder = await ta.get_attribute("placeholder")
            print(f"  Textarea {i}: id={id_}, placeholder={placeholder}")
        
        # Get button info
        buttons = await page.query_selector_all("button")
        print(f"\nFound {len(buttons)} button(s)")
        for i, btn in enumerate(buttons):
            text = await btn.inner_text()
            disabled = await btn.get_attribute("disabled")
            print(f"  Button {i}: text='{text[:50]}', disabled={disabled}")
        
        # Get all images
        imgs = await page.query_selector_all("img")
        print(f"\nFound {len(imgs)} img(s)")
        for i, img in enumerate(imgs):
            src = await img.get_attribute("src")
            if src:
                print(f"  Img {i}: src={src[:100]}...")
        
        # Save HTML for inspection
        html = await page.content()
        with open("/Users/alvarobiano/Images/generated/raphael/page.html", "w") as f:
            f.write(html)
        print("\nPage HTML saved to page.html")
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(debug_raphael())