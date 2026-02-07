import unittest
from unittest.mock import AsyncMock, MagicMock
from src.scraper import scrape_amazon

class TestAmazonScraper(unittest.IsolatedAsyncioTestCase):
    async def test_amazon_price_and_fixed_coupon(self):
        # Mock page
        page = AsyncMock()

        # Mock finding price element
        price_el = AsyncMock()
        price_el.inner_text.return_value = "1.700,00 €"

        # Mock finding coupon label
        coupon_label = AsyncMock()
        coupon_label.is_visible.return_value = True
        coupon_label.inner_text.return_value = "Aplicar cupón de 100 €"

        # side_effect for query_selector to return price_el for price selectors
        async def mock_query_selector(sel):
            if 'a-price' in sel or 'price_inside_buybox' in sel:
                return price_el
            return None

        page.query_selector.side_effect = mock_query_selector
        page.query_selector_all.return_value = [coupon_label]

        item = {
            'url': 'http://amazon.es/test',
            'target_ram': '96GB',
            'site_name': 'Amazon ES',
            'target_price': 1500
        }

        result = await scrape_amazon(page, item)

        self.assertIsNotNone(result)
        self.assertEqual(result['price'], 1600.0) # 1700 - 100
        self.assertEqual(result['metadata']['base_price'], 1700.0)
        self.assertEqual(result['metadata']['discount_applied'], 100.0)

    async def test_amazon_price_and_percent_coupon(self):
        # Mock page
        page = AsyncMock()

        # Mock price
        price_el = AsyncMock()
        price_el.inner_text.return_value = "2.000,00 €"

        # Mock coupon
        coupon_label = AsyncMock()
        coupon_label.is_visible.return_value = True
        coupon_label.inner_text.return_value = "Ahorra un 10%"

        async def mock_query_selector(sel):
            if 'a-price' in sel:
                return price_el
            return None

        page.query_selector.side_effect = mock_query_selector
        page.query_selector_all.return_value = [coupon_label]

        item = {
            'url': 'http://amazon.es/test',
            'target_ram': '128GB',
            'site_name': 'Amazon ES'
        }

        result = await scrape_amazon(page, item)

        self.assertIsNotNone(result)
        self.assertEqual(result['price'], 1800.0) # 2000 - 10% (200)
        self.assertEqual(result['metadata']['base_price'], 2000.0)
        self.assertEqual(result['metadata']['discount_applied'], 200.0)

    async def test_amazon_no_coupon(self):
        # Mock page
        page = AsyncMock()

        price_el = AsyncMock()
        price_el.inner_text.return_value = "1.700,00 €"

        async def mock_query_selector(sel):
            if 'a-price' in sel:
                return price_el
            return None

        page.query_selector.side_effect = mock_query_selector
        page.query_selector_all.return_value = [] # No labels

        item = {
            'url': 'http://amazon.es/test',
            'target_ram': '96GB',
            'site_name': 'Amazon ES'
        }

        result = await scrape_amazon(page, item)

        self.assertEqual(result['price'], 1700.0)
        self.assertEqual(result['metadata']['discount_applied'], 0)

if __name__ == '__main__':
    unittest.main()
