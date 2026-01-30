import json
import re
import datetime
import asyncio
from playwright.async_api import async_playwright
import os

CONFIG_FILE = 'config.json'
DATA_FILE = 'data/prices.json'

def parse_price(price_str):
    """
    Cleans a price string and returns a float.
    Handles formats like '1.234,56 €', '€1,234.56', etc.
    """
    if not price_str:
        return None

    # Remove non-numeric characters except potential decimal/thousand separators
    # This is tricky because 1.234,56 (EU) vs 1,234.56 (US)
    # We assume EU format (comma for decimals) if it's a Spanish site, but let's try to be generic.
    # A common approach is to remove all non-digits, then divide by 100 if it looks like cents,
    # but that's dangerous.

    # Better approach:
    # 1. Remove currency symbols and whitespace.
    clean_str = re.sub(r'[^\d.,]', '', price_str)

    # If both , and . are present:
    if ',' in clean_str and '.' in clean_str:
        if clean_str.find(',') > clean_str.find('.'): # 1.234,56
            clean_str = clean_str.replace('.', '').replace(',', '.')
        else: # 1,234.56
            clean_str = clean_str.replace(',', '')
    elif ',' in clean_str: # 1234,56 or 123,456
        # Assume comma is decimal if it's at the end-ish
        if len(clean_str) - clean_str.rfind(',') <= 3:
            clean_str = clean_str.replace(',', '.')
        else:
            clean_str = clean_str.replace(',', '')

    try:
        return float(clean_str)
    except ValueError:
        return None

async def scrape_site(page, item):
    """
    Scrapes a single item.
    """
    url = item.get('url')
    selector = item.get('selector')
    variant = item.get('variant')
    site_name = item.get('site_name')

    print(f"Scraping {site_name} ({variant})...")

    try:
        await page.goto(url, timeout=60000) # 60s timeout
        # Wait for selector to appear
        try:
            await page.wait_for_selector(selector, timeout=10000)
        except Exception:
            print(f"Selector {selector} not found on {url}")
            # Try to get full page text for debugging if needed, or just return None
            return None

        element = await page.query_selector(selector)
        if element:
            text = await element.inner_text()
            price = parse_price(text)
            print(f"Found price: {price} (Raw: {text})")
            return {
                "timestamp": datetime.datetime.now().isoformat(),
                "variant": variant,
                "site": site_name,
                "price": price,
                "url": url
            }
        else:
            print(f"Element not found for selector: {selector}")
            return None

    except Exception as e:
        print(f"Error scraping {url}: {e}")
        return None

async def main():
    # Load config
    if not os.path.exists(CONFIG_FILE):
        print(f"Config file {CONFIG_FILE} not found.")
        return

    with open(CONFIG_FILE, 'r') as f:
        config = json.load(f)

    # Filter active items
    active_items = [item for item in config if item.get('active', True)]

    if not active_items:
        print("No active items to scrape.")
        return

    # Load existing data
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r') as f:
            try:
                history = json.load(f)
            except json.JSONDecodeError:
                history = []
    else:
        history = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        # Create a context with a realistic user agent to avoid blocks
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )

        page = await context.new_page()

        new_data = []
        for item in active_items:
            result = await scrape_site(page, item)
            if result:
                new_data.append(result)
            # Sleep a bit to be polite
            await asyncio.sleep(2)

        await browser.close()

    # Append new data
    if new_data:
        history.extend(new_data)
        # Sort by timestamp just in case
        history.sort(key=lambda x: x['timestamp'])

        with open(DATA_FILE, 'w') as f:
            json.dump(history, f, indent=2)
        print(f"Saved {len(new_data)} new price records.")
    else:
        print("No new data found.")

if __name__ == "__main__":
    asyncio.run(main())
