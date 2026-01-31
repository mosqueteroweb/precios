import unittest
import sys
import os

# Add src to python path to import scraper
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from scraper import COUPON_PATTERN

class TestScraperRegex(unittest.TestCase):
    def test_coupon_regex_matches_expected_patterns(self):
        # Patterns that should match
        text1 = "This text contains GMKCODE1 and GMK20OFF inside."
        matches = COUPON_PATTERN.findall(text1)
        self.assertIn("GMKCODE1", matches)
        self.assertIn("GMK20OFF", matches)
        self.assertEqual(len(matches), 2)

    def test_coupon_regex_ignores_non_matches(self):
        text2 = "This text has no codes, only regular words."
        matches = COUPON_PATTERN.findall(text2)
        self.assertEqual(len(matches), 0)

    def test_coupon_regex_boundaries(self):
        # r'(GMK\w+)' matches GMK followed by word chars.
        text3 = "GMK" # Should not match if \w+ requires at least one char? \w+ means 1 or more.
        # Wait, \w+ is 1 or more. So "GMK" exactly shouldn't match?
        # Or "GMK" matches if \w+ matches "MK"? No, GMK is literal.
        # r'(GMK\w+)' -> Literal "GMK" followed by 1+ word chars.
        # So "GMK1" matches. "GMK" does not.

        matches = COUPON_PATTERN.findall("GMK")
        self.assertEqual(len(matches), 0, "Should not match bare 'GMK'")

        matches = COUPON_PATTERN.findall("GMK1")
        self.assertEqual(matches, ["GMK1"])

    def test_coupon_regex_real_examples(self):
        text = "Save with GMKEVO50OFF today!"
        matches = COUPON_PATTERN.findall(text)
        self.assertEqual(matches, ["GMKEVO50OFF"])

if __name__ == '__main__':
    unittest.main()
