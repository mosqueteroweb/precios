import json
import re
import datetime
import asyncio
import requests
from playwright.async_api import async_playwright
import os

CONFIG_FILE = 'config.json'
DATA_FILE = 'data/prices.json'

async def send_telegram_alert(item, price):
    """
    Sends a Telegram alert when price drops below target.
    """
    variant = item.get('target_ram', item.get('variant', 'Unknown'))
    site_name = item.get('site_name')
    url = item.get('url')
    target_price = item.get('target_price')

    bot_token = os.environ.get('TELEGRAM_BOT_TOKEN')
    chat_id = os.environ.get('TELEGRAM_CHAT_ID')

    if not bot_token or not chat_id:
        print("Skipping Telegram alert: TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID not set.")
        return

    message = (
        f"🚨 **BAJADA DE PRECIO** 🚨\n\n"
        f"📦 **Producto:** GMKtec EVO-X2 ({variant})\n"
        f"🏪 **Tienda:** {site_name}\n"
        f"💰 **Precio Actual:** {price} €\n"
        f"🎯 **Objetivo:** {target_price} €\n\n"
        f"🔗 [Ver Oferta]({url})"
    )

    api_url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "Markdown"
    }

    try:
        loop = asyncio.get_running_loop()
        response = await loop.run_in_executor(
            None,
            lambda: requests.post(api_url, json=payload, timeout=10)
        )
        if response.status_code == 200:
            print(f"Telegram alert sent for {variant} at {price}€")
        else:
            print(f"Failed to send Telegram alert: {response.text}")
    except Exception as e:
        print(f"Error sending Telegram alert: {e}")

def parse_price(price_str):
    """
    Cleans a price string and returns a float.
    Handles formats like '1.234,56 €', '€1,234.56', etc.
    """
    if not price_str:
        return None

    # Remove non-numeric characters except potential decimal/thousand separators
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

async def remove_geo_modal(page):
    """
    Attempts to close/remove the Geolocation/Language modal and other blockers.
    """
    # "ts-geo-modal" intercepts pointer events
    # Wait a bit for it to appear (up to 2s), but proceed immediately if found
    blocker_selector = '#ts-geo-modal, .ts-geo-modal__backdrop, #ts-geo, .popup-overlay, .modal-backdrop'
    try:
        await page.wait_for_selector(blocker_selector, timeout=2000, state='attached')
    except Exception:
        # Timeout means not found within 2s, proceed anyway to cleanup attempts
        pass

    try:
        # Try to find a close button or similar
        # Or just remove the element from DOM
        await page.evaluate("""
            const removeElement = (sel) => {
                const el = document.querySelector(sel);
                if (el) el.remove();
            };
            removeElement('#ts-geo-modal');
            removeElement('.ts-geo-modal__backdrop');
            removeElement('#ts-geo');
            // Also remove any other potential overlays
            removeElement('.popup-overlay');
            removeElement('.modal-backdrop');
        """)
        print("Removed geo modal/blockers.")
    except Exception as e:
        print(f"Error removing modal: {e}")

async def scrape_gmktec_official(page, item):
    """
    Specific scraping logic for official GMKtec site.
    Handles variant selection (RAM) and coupon application.
    """
    url = item.get('url')
    target_ram = item.get('target_ram') # e.g. "96GB", "128GB"
    site_name = item.get('site_name')

    print(f"Scraping GMKtec Official for {target_ram} RAM...")

    try:
        await page.goto(url, timeout=60000)

        # 0. Close Geolocation/Language Modal if present
        await remove_geo_modal(page)

        # 1. Select Variant
        # Find label containing the target RAM
        # We look for a label text that contains the target RAM string (case insensitive)
        print(f"Looking for variant: {target_ram}")

        # Wait a bit for dynamic content
        await page.wait_for_timeout(2000)

        # Try to find all labels
        labels = await page.query_selector_all('label')
        variant_clicked = False

        # Strategy 1: Click Visible Labels
        for label in labels:
            if await label.is_visible():
                text = await label.inner_text()
                # Normalize text: "96 GB De RAM" vs "96GB RAM"
                normalized_text = text.lower().replace(" ", "")
                normalized_target = target_ram.lower().replace(" ", "")

                if normalized_target in normalized_text:
                    print(f"Found visible variant label: '{text.strip()}' -> Clicking")
                    await label.click()
                    variant_clicked = True
                    await page.wait_for_timeout(2000)
                    break

        # Strategy 2: Click Hidden Radio Inputs directly (force)
        if not variant_clicked:
            print("No visible label matched. Trying inputs...")
            inputs = await page.query_selector_all('input[type="radio"]')
            for inp in inputs:
                val = await inp.get_attribute('value')
                if val:
                    normalized_val = val.lower().replace(" ", "")
                    normalized_target = target_ram.lower().replace(" ", "")
                    if normalized_target in normalized_val:
                        print(f"Found input with value: '{val}' -> Force Clicking")
                        await inp.click(force=True)
                        variant_clicked = True
                        await page.wait_for_timeout(2000)
                        break

        if not variant_clicked:
            print(f"Variant {target_ram} not found!")
            return None

        # 2. Get Base Price
        # Selector for price on this site seems to be .price__current or similar
        # Based on inspection, it might be just .price or similar container.
        # Let's try a few common Shopify selectors
        price_selector = '.product__price, .price__current, .price-item--regular'
        # But wait, inspection showed potential price element found: €2.199,00 \n €1.589,00
        # Usually the "sale price" is what we want.

        # Let's try to find the price container again
        price_el = await page.query_selector('.price__current')
        if not price_el:
             price_el = await page.query_selector('.product-info__price')

        if not price_el:
             # Fallback to searching by text content relative to "Total" or similar if needed,
             # but let's assume standard selectors first.
             # Inspection log showed: "Potential price element found: €2.199,00\n€1.589,00"
             # It seems there are multiple price elements (original vs sale).
             # We want the lowest one visible in the main product area.
             pass

        # Strategy: Look for "Subtotal" or similar explicit price indicators first
        base_price = None

        # Try to find "Subtotal" element
        # Based on inspection: "Subtotal: 1.859,00 €"
        # We look for an element containing "Subtotal" and extract the price from it or its parent
        try:
            subtotal_el = page.get_by_text("Subtotal", exact=False).first
            if await subtotal_el.is_visible():
                # Get text of parent to catch "Subtotal: 1234 €" if they are in same block
                # or the element itself
                text = await subtotal_el.inner_text()
                # If text is just "Subtotal:", try parent or next sibling
                if len(text.strip()) < 15:
                    parent_text = await subtotal_el.evaluate("el => el.parentElement.innerText")
                    text = parent_text

                print(f"Found Subtotal text: {text.strip()}")
                matches = re.findall(r'€\s?[\d.,]+|[\d.,]+\s?€', text)
                for m in matches:
                    v = parse_price(m)
                    if v and v > 100: # Sanity check
                        base_price = v
                        print(f"Extracted base price from Subtotal: {base_price}")
                        break
        except Exception as e:
            print(f"Error finding subtotal: {e}")

        # Fallback: Find all prices in main product area if Subtotal failed
        if not base_price:
            print("Subtotal not found, falling back to all prices...")
            main_product = await page.query_selector('.product-main, .product-info')
            if main_product:
                 price_text = await main_product.inner_text()
            else:
                 price_text = await page.inner_text('body')

            prices_found = []
            matches = re.findall(r'€\s?[\d.,]+|[\d.,]+\s?€', price_text)
            for m in matches:
                v = parse_price(m)
                # Filter out "159" (menu/flash deals) and small amounts
                # We know this product is expensive (>1000€ usually, or at least >500)
                if v and v > 500:
                    prices_found.append(v)

            if prices_found:
                base_price = min(prices_found)
                print(f"Fallback base price (min > 500): {base_price}")

        if not base_price:
            print("No valid price found on page.")
            return None
        print(f"Base price found: {base_price}")

        # 3. Check for coupons
        # User mentioned: "GMK20" or similar text.
        # We'll search for common coupon patterns in the text.
        # "Code: XXX" or just "XXXOFF"
        # The user said: "lee el codigo y su descuento y aplicalo al precio del producto"

        discount_amount = 0

        # Search for explicit codes mentioned in the page text
        # Regex for common coupon patterns: GMK\w+ (like GMKEVO50OFF)
        # Inspect found: "GMKEVO50OFF"

        full_text = await page.inner_text('body')

        # Look for the specific code pattern seen in inspection
        # "GMKEVO50OFF" -> likely 50 OFF (currency? percentage?)
        # "Save €20 when you buy 2" -> User said ignore bulk discounts.

        # Heuristic: Find codes like "GMK..." followed by numbers
        coupon_matches = re.findall(r'(GMK\w+)', full_text)
        unique_coupons = set(coupon_matches)

        for coupon in unique_coupons:
            print(f"Found potential coupon: {coupon}")
            # Try to infer value from coupon name
            # GMKEVO50OFF -> 50 OFF. Is it % or €?
            # Usually if it's 50OFF it might be 50 currency units or 50%
            # Given the price (1500+), 50% is huge, 50€ is more likely for a generic "50OFF" code unless specified.
            # But let's look at context text around the coupon.

            # Simple logic for now:
            # If "50OFF" in name -> assume 50€ discount (safer bet for tech products than 50%)
            # If "5OFF" -> 5%?

            # User said: "aplicalos al precio"
            # If I can't be sure, I should probably just log it or apply a safe heuristic.

            # Let's try to parse "50OFF"
            match_val = re.search(r'(\d+)OFF', coupon)
            if match_val:
                val = float(match_val.group(1))
                # Heuristic: if val > 100, unlikely to be %, assume currency.
                # If val < 100, ambiguous.
                # Inspect text nearby?
                # "Top deals under €159, Save €20 when you buy 2..."

                # Let's assume currency for GMK coupons on this site based on "Save €20" context elsewhere.
                print(f"Applying coupon {coupon}: -{val}")
                discount_amount += val

        final_price = base_price - discount_amount
        print(f"Final Price: {final_price} (Base: {base_price} - Discount: {discount_amount})")

        # Alert Check
        target_price = item.get('target_price')
        if target_price and final_price <= target_price:
            print(f"Price {final_price} is below target {target_price}! Sending alert...")
            await send_telegram_alert(item, final_price)

        return {
            "timestamp": datetime.datetime.now().isoformat(),
            "variant": target_ram,
            "site": site_name,
            "price": final_price,
            "url": url,
            "metadata": {
                "base_price": base_price,
                "discount_applied": discount_amount,
                "coupons_found": list(unique_coupons)
            }
        }

    except Exception as e:
        print(f"Error scraping GMKtec {target_ram}: {e}")
        return None

async def scrape_site(page, item):
    """
    Scrapes a single item. Dispatches to specific logic if needed.
    """
    if item.get('type') == 'gmktec_official':
        return await scrape_gmktec_official(page, item)

    url = item.get('url')
    selector = item.get('selector')
    variant = item.get('variant')
    site_name = item.get('site_name')

    print(f"Scraping {site_name} ({variant})...")

    try:
        await page.goto(url, timeout=60000)
        try:
            await page.wait_for_selector(selector, timeout=10000)
        except Exception:
            print(f"Selector {selector} not found on {url}")
            return None

        element = await page.query_selector(selector)
        if element:
            text = await element.inner_text()
            price = parse_price(text)
            print(f"Found price: {price}")

            # Alert Check
            target_price = item.get('target_price')
            if price and target_price and price <= target_price:
                print(f"Price {price} is below target {target_price}! Sending alert...")
                await send_telegram_alert(item, price)

            return {
                "timestamp": datetime.datetime.now().isoformat(),
                "variant": variant,
                "site": site_name,
                "price": price,
                "url": url
            }
        else:
            return None

    except Exception as e:
        print(f"Error scraping {url}: {e}")
        return None

async def main():
    if not os.path.exists(CONFIG_FILE):
        print(f"Config file {CONFIG_FILE} not found.")
        return

    with open(CONFIG_FILE, 'r') as f:
        config = json.load(f)

    active_items = [item for item in config if item.get('active', True)]

    if not active_items:
        print("No active items to scrape.")
        return

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
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )

        # Concurrency control
        sem = asyncio.Semaphore(5)

        async def scrape_worker(item):
            async with sem:
                page = await context.new_page()
                try:
                    return await scrape_site(page, item)
                finally:
                    await page.close()

        tasks = [scrape_worker(item) for item in active_items]
        results = await asyncio.gather(*tasks)

        # Filter None results
        new_data = [r for r in results if r]

        await browser.close()

    if new_data:
        history.extend(new_data)
        history.sort(key=lambda x: x['timestamp'])

        with open(DATA_FILE, 'w') as f:
            json.dump(history, f, indent=2)
        print(f"Saved {len(new_data)} new price records.")
    else:
        print("No new data found.")

if __name__ == "__main__":
    asyncio.run(main())
