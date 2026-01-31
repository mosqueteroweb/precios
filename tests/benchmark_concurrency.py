import asyncio
import time
import random

# Mock config items
ITEMS = [{"id": i} for i in range(10)]
MOCK_SCRAPE_TIME = 1.0  # Simulate 1 second scrape time per item
FIXED_DELAY = 2.0       # The hardcoded delay we are removing

async def mock_scrape_site(page, item):
    # Simulate network/scraping delay
    await asyncio.sleep(MOCK_SCRAPE_TIME)
    return {"id": item["id"], "price": 100}

async def run_sequential():
    print(f"--- Running Sequential (Baseline) ---")
    start_time = time.time()

    # Mocking browser/context/page structure strictly necessary for the loop logic
    results = []
    # In the original code, one page is reused.
    page = "mock_page"

    for item in ITEMS:
        result = await mock_scrape_site(page, item)
        results.append(result)
        # The hardcoded delay
        await asyncio.sleep(FIXED_DELAY)

    duration = time.time() - start_time
    print(f"Sequential finished in {duration:.2f} seconds")
    return duration

async def run_concurrent(concurrency_limit=5):
    print(f"--- Running Concurrent (Optimized) ---")
    start_time = time.time()

    results = []
    sem = asyncio.Semaphore(concurrency_limit)

    async def worker(item):
        async with sem:
            # In optimized code, we create a new page per task
            page = "mock_page_new"
            res = await mock_scrape_site(page, item)
            return res

    tasks = [worker(item) for item in ITEMS]
    results = await asyncio.gather(*tasks)

    duration = time.time() - start_time
    print(f"Concurrent (Limit={concurrency_limit}) finished in {duration:.2f} seconds")
    return duration

async def main():
    print(f"Benchmark: Processing {len(ITEMS)} items")
    print(f"Simulated Scrape Time: {MOCK_SCRAPE_TIME}s")
    print(f"Sequential Delay: {FIXED_DELAY}s")
    print("")

    seq_time = await run_sequential()
    conc_time = await run_concurrent()

    improvement = seq_time - conc_time
    speedup = seq_time / conc_time

    print("")
    print(f"Initial Time: {seq_time:.2f}s")
    print(f"Optimized Time: {conc_time:.2f}s")
    print(f"Total Time Saved: {improvement:.2f}s")
    print(f"Speedup Factor: {speedup:.2f}x")

if __name__ == "__main__":
    asyncio.run(main())
