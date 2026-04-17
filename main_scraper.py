import asyncio
import json
import logging
import re
from playwright.async_api import async_playwright
from playwright_stealth import Stealth
from scraper_config import get_random_headers, TARGET_URLS

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

async def scrape_otodom(page):
    logging.info(f"Navigating to Otodom: {TARGET_URLS['otodom']}")
    await page.goto(TARGET_URLS['otodom'], wait_until="domcontentloaded", timeout=60000)
    
    results = []
    
    try:
        # Wait for either __NEXT_DATA__ or main content
        next_data_locator = page.locator("#__NEXT_DATA__")
        await next_data_locator.wait_for(state="attached", timeout=15000)
        next_data_content = await next_data_locator.text_content()
        data = json.loads(next_data_content)
        
        props = data.get("props") or {}
        pageProps = props.get("pageProps") or {}
        data_block = pageProps.get("data") or {}
        search_ads = data_block.get("searchAds") or {}
        items = search_ads.get("items") or []
        
        for item in items:
            total_price = (item.get("totalPrice") or {}).get("value")
            price_per_m2 = (item.get("pricePerSquareMeter") or {}).get("value")
            
            location = item.get("location") or {}
            coordinates = location.get("coordinates") or {}
            lat = coordinates.get("latitude")
            lon = coordinates.get("longitude")
            
            # Additional extracting
            floor = item.get("floor", "N/A")
            developer = (item.get("agency") or {}).get("name", "N/A")
            
            results.append({
                "source": "otodom",
                "id": str(item.get("id")),
                "title": item.get("title", "N/A"),
                "total_price": total_price,
                "price_per_m2": price_per_m2,
                "latitude": lat,
                "longitude": lon,
                "floor": floor,
                "developer": developer
            })
            
        logging.info(f"Extracted {len(results)} items from Otodom __NEXT_DATA__")

    except Exception as e:
        logging.error(f"Error extracting Otodom data via JSON: {e}")
        # Try DOM extraction as fallback
        
    return results

async def scrape_rynekpierwotny(page):
    logging.info(f"Navigating to RynekPierwotny: {TARGET_URLS['rynekpierwotny']}")
    await page.goto(TARGET_URLS['rynekpierwotny'], wait_until="domcontentloaded", timeout=60000)
    
    results = []
    
    try:
        await page.wait_for_timeout(3000)  # Wait for JS hydration
        
        # Attempt to grab Nuxt state
        rynek_state = await page.evaluate('''() => {
            try {
                if (window.__NUXT__) return "nuxt";
                if (window.__INITIAL_STATE__) return "initial_state";
            } catch (err) {}
            return null;
        }''')
        
        logging.info(f"RynekPierwotny data state strategy: {rynek_state}")
        
        # Fallback to pure DOM generic scraping since JSON tree is deeply nested and changes per build
        cards = await page.locator("article, [data-test='offer-item'], div[class*='OfferItem']").all()
        
        for card in cards:
            title = await card.inner_text() 
            if not title: continue
            
            # Replace nb-spaces
            clean_title = title.replace('\xa0', ' ')
            
            # Basic parsing
            price_match = re.search(r'([\d\s]+,?\d*)\s*(zł|PLN)', clean_title)
            total_price = float(price_match.group(1).replace(' ', '').replace(',', '.')) if price_match else None
            
            m2_match = re.search(r'([\d\s]+,?\d*)\s*(zł/m|PLN/m)', clean_title)
            price_per_m2 = float(m2_match.group(1).replace(' ', '').replace(',', '.')) if m2_match else None
            
            # Attempt to extract location/developer from text or specific selectors
            developer = "N/A"
            dev_match = re.search(r'Deweloper:\s*(.+)', clean_title, re.IGNORECASE)
            if dev_match:
                developer = dev_match.group(1).strip()
                
            results.append({
                "source": "rynekpierwotny",
                "title": title.split('\\n')[0] if title else "N/A",
                "total_price": total_price,
                "price_per_m2": price_per_m2,
                "latitude": None, 
                "longitude": None,
                "floor": "N/A", 
                "developer": developer 
            })
            
        logging.info(f"Extracted {len(results)} items from RynekPierwotny DOM")
    except Exception as e:
        logging.error(f"Error extracting RynekPierwotny data: {e}")
        
    return results

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=["--disable-blink-features=AutomationControlled"]
        )
        
        headers = get_random_headers()
        
        context = await browser.new_context(
            user_agent=headers["User-Agent"],
            viewport={"width": 1920, "height": 1080},
            extra_http_headers={
                "Accept-Language": headers["Accept-Language"],
                "Accept": headers["Accept"]
            }
        )
        
        page = await context.new_page()
        await Stealth().apply_stealth_async(page)
        
        otodom_data = await scrape_otodom(page)
        rp_data = await scrape_rynekpierwotny(page)
        
        all_data = otodom_data + rp_data
        
        with open("warsaw_apartments_2027.json", "w", encoding="utf-8") as f:
            json.dump(all_data, f, indent=4, ensure_ascii=False)
            
        logging.info("Scraping completed and saved to warsaw_apartments_2027.json")
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
