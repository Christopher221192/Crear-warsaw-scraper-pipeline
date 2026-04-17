import asyncio
import json
import logging
from playwright.async_api import async_playwright
from playwright_stealth import Stealth
from scraper_config import get_random_headers, TARGET_URLS

logging.basicConfig(level=logging.INFO)

async def probe_page(page, url):
    logging.info(f"Probing {url}")
    await page.goto(url, wait_until="domcontentloaded")
    
    next_data = None
    try:
        next_data = await page.locator('#__NEXT_DATA__').text_content(timeout=5000)
    except Exception as e:
        logging.error(f"No __NEXT_DATA__ found via DOM selector: {e}")
        
    nuxt_data = None
    try:
        nuxt_data = await page.locator('script#__NUXT_DATA__').text_content(timeout=2000)
    except:
        pass
        
    # check standard next block
    if next_data:
        try:
            data = json.loads(next_data)
            return {"type": "next", "data": data}
        except:
            pass
    if nuxt_data:
        return {"type": "nuxt", "data": nuxt_data[:500]}
        
    # otherwise get title & some inner HTML to find structure
    html = await page.content()
    return {"type": "html", "data": html[:2000]}

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent=get_random_headers()["User-Agent"],
            viewport={"width": 1920, "height": 1080}
        )
        page = await context.new_page()
        await Stealth().apply_stealth_async(page)
        
        oto = await probe_page(page, TARGET_URLS['otodom'])
        print(f"Otodom probe result: {oto['type']}")
        if oto['type'] == 'next':
            keys = oto['data'].get("props", {}).get("pageProps", {}).keys()
            print("Otodom pageProps keys:", keys)
            
        rp = await probe_page(page, TARGET_URLS['rynekpierwotny'])
        print(f"RP probe result: {rp['type']}")
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
