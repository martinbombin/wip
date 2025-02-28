import asyncio
import logging
from concurrent.futures import ThreadPoolExecutor

import undetected_chromedriver as uc
from selenium.webdriver.chrome.options import Options

from .crawler import Crawler
from .utils import async_timer

# import schedule

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)


def init_browser():
    """Initialize and return a Chrome browser instance."""
    opts = Options()
    opts.add_argument(
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36",
    )
    # opts.add_argument("--headless")

    return uc.Chrome(
        driver_executable_path="chromedriver",
        options=opts,
    )


async def set_page_content(page, browser, loop):
    """Set content for a page using a threadpool executor."""
    # Run blocking function in a thread
    await loop.run_in_executor(None, page.set_content, browser)


@async_timer
async def crawl_all_categories():
    loop = asyncio.get_running_loop()

    # Start browser in a separate thread
    with ThreadPoolExecutor(max_workers=1) as executor:
        browser = await loop.run_in_executor(executor, init_browser)

        try:
            crawler = Crawler(chrome_driver=browser)
            crawler.load_categories("categories.json")

            # Gather all tasks
            tasks = [
                set_page_content(page, browser, loop)
                for cat in crawler.categories
                for page in cat.pages
            ]
            await asyncio.gather(*tasks)

            # Logging after all pages are processed
            for cat in crawler.categories:
                for page in cat.pages:
                    if page.content is None:
                        logging.info(
                            "Page content is None for page: %s",
                            page.url,
                        )

            crawler.save_categories("scrapped_async_100.json")

        finally:
            browser.quit()


@async_timer
async def main():
    """Main async function to initialize the browser and process pages in parallel."""
    await crawl_all_categories()


if __name__ == "__main__":
    asyncio.run(main())
