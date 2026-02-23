import timeit
import re
import sys
import os
from unittest.mock import MagicMock

# Mock requests before importing scraper
sys.modules['requests'] = MagicMock()
sys.modules['playwright'] = MagicMock()
sys.modules['playwright.async_api'] = MagicMock()

# Add src to python path to import scraper
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from scraper import parse_price, PRICE_CLEAN_PATTERN

def benchmark():
    test_data = [
        "1.234,56 €",
        "€1,234.56",
        "1234,56",
        "Price: 1.234,56 EUR",
        "Approx. 1.200,00€ (inc. VAT)",
        "FREE",
        None,
        ""
    ] * 1000

    def run_original_re_sub():
        for s in test_data:
            if s:
                re.sub(r'[^\d.,]', '', s)

    def run_current_re_sub():
        for s in test_data:
            if s:
                PRICE_CLEAN_PATTERN.sub('', s)

    def run_parse_price():
        for s in test_data:
            parse_price(s)

    # Measure
    t_orig = timeit.timeit(run_original_re_sub, number=100)
    t_curr = timeit.timeit(run_current_re_sub, number=100)
    t_full = timeit.timeit(run_parse_price, number=100)

    print(f"Original re.sub (inline): {t_orig:.4f}s")
    print(f"Current re.sub (precompiled): {t_curr:.4f}s")
    print(f"Regex Improvement: {(t_orig - t_curr) / t_orig * 100:.2f}%")
    print(f"Full parse_price (current): {t_full:.4f}s")

    # To estimate the improvement on parse_price, we compare with the baseline from previous run
    # Previous Full parse_price (baseline): 2.1398s
    # (I'll hardcode it for comparison if I want to be fancy, but running it again is enough)

if __name__ == '__main__':
    benchmark()
