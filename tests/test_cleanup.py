import unittest
import datetime
import sys
import os
import json

# Add src to path to import scraper
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

from scraper import clean_price_history

class TestCleanup(unittest.TestCase):
    def setUp(self):
        # Reference date: 2024-06-01 12:00:00
        self.now = datetime.datetime(2024, 6, 1, 12, 0, 0)

        # Helper to create timestamps relative to now
        def days_ago(days, hour=10):
            dt = self.now - datetime.timedelta(days=days)
            dt = dt.replace(hour=hour, minute=0, second=0, microsecond=0)
            return dt.isoformat()

        self.data = [
            # --- RECENT DATA (< 14 days) ---
            # Day 0 (Today)
            {"timestamp": days_ago(0), "variant": "96GB", "price": 1000, "site": "SiteA"},
            {"timestamp": days_ago(0, 11), "variant": "96GB", "price": 1005, "site": "SiteA"}, # Keep both

            # Day 10 (Recent)
            {"timestamp": days_ago(10), "variant": "96GB", "price": 1010, "site": "SiteA"},

            # --- OLD DATA (> 14 days) ---

            # Week of 3 weeks ago (Days 20-26 ago approx)
            # Day 21
            {"timestamp": days_ago(21), "variant": "96GB", "price": 1200, "site": "SiteA"}, # High price
            {"timestamp": days_ago(21, 14), "variant": "96GB", "price": 900, "site": "SiteA"}, # LOWEST for this week/variant
            # Day 22
            {"timestamp": days_ago(22), "variant": "96GB", "price": 1100, "site": "SiteA"},

            # Different variant (128GB) - same week (Day 21)
            {"timestamp": days_ago(21), "variant": "128GB", "price": 2000, "site": "SiteA"},
            {"timestamp": days_ago(22), "variant": "128GB", "price": 1900, "site": "SiteA"}, # LOWEST for this week/variant

            # Week of 5 weeks ago (Days 35+)
            {"timestamp": days_ago(35), "variant": "96GB", "price": 1500, "site": "SiteA"},
            {"timestamp": days_ago(36), "variant": "96GB", "price": 1550, "site": "SiteA"},
        ]

    def test_clean_price_history(self):
        # We expect:
        # Recent (0-13 days ago): 3 records (all preserved)
        # Old Week 1 (Day 21-22):
        #   - 96GB: 1 record (price 900)
        #   - 128GB: 1 record (price 1900)
        # Old Week 2 (Day 35-36):
        #   - 96GB: 1 record (price 1500)

        # Total expected: 3 + 1 + 1 + 1 = 6 records

        cleaned = clean_price_history(self.data, reference_date=self.now)

        self.assertEqual(len(cleaned), 6)

        # Verify specific retained records
        prices_96gb_old_week1 = [
            x['price'] for x in cleaned
            if x['variant'] == "96GB" and x['price'] == 900
        ]
        self.assertEqual(len(prices_96gb_old_week1), 1, "Should keep lowest price 900 for 96GB in old week 1")

        prices_96gb_old_week1_high = [
            x['price'] for x in cleaned
            if x['variant'] == "96GB" and x['price'] == 1200
        ]
        self.assertEqual(len(prices_96gb_old_week1_high), 0, "Should remove higher price 1200 for 96GB in old week 1")

        # Verify recent data is untouched
        recent_count = len([x for x in cleaned if x['price'] in [1000, 1005, 1010]])
        self.assertEqual(recent_count, 3)

if __name__ == '__main__':
    unittest.main()
