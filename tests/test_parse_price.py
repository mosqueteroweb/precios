import unittest
import sys
import os
from unittest.mock import MagicMock

# Mock requests before importing scraper
sys.modules['requests'] = MagicMock()
sys.modules['playwright'] = MagicMock()
sys.modules['playwright.async_api'] = MagicMock()

# Add src to python path to import scraper
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from scraper import parse_price

class TestParsePrice(unittest.TestCase):
    def test_parse_price_standard(self):
        self.assertEqual(parse_price("1.234,56 €"), 1234.56)
        self.assertEqual(parse_price("€1,234.56"), 1234.56)
        self.assertEqual(parse_price("1234,56"), 1234.56)
        self.assertEqual(parse_price("1.234"), 1.234) # Current behavior
        self.assertEqual(parse_price("1,234"), 1234.0) # Current behavior
        self.assertEqual(parse_price("1,23"), 1.23)

    def test_parse_price_none(self):
        self.assertIsNone(parse_price(None))
        self.assertIsNone(parse_price(""))

    def test_parse_price_invalid(self):
        self.assertIsNone(parse_price("abc"))

if __name__ == '__main__':
    unittest.main()
