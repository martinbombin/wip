import asyncio
import logging
from concurrent.futures import ThreadPoolExecutor

from . import utils
from .crawler import Crawler

# import schedule

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)


def set_page_content(page):
    """Set content for a page using a threadpool executor."""
    try:
        browser = init_browser()
        try:
            page.set_content(browser)
        except Exception as e:
            logging.exception(
                "Error processing page %s: %s",
                page.url,
                e,
            )
        finally:
            browser.quit()
    except Exception as e:
        logging.exception(
            "Error with browser initialization for page %s: %s",
            page.url,
            e,
        )


async def scrap_categories(max_workers: int = 5):
    crawler = Crawler()
    # crawler.set_categories(browser)
    # crawler.save_categories("categories.json")
    crawler.load_categories("categories.json")

    pages = [page for cat in crawler.categories for page in cat.pages]
    max_workers = min(5, len(pages))

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        list(executor.map(set_page_content, pages))

    crawler.save_categories("scrapped_test.json")


async def main():
    """Main async function to initialize the browser and process pages in parallel."""
    crawler = Crawler()
    crawler.load_categories("categories.json")

    # async with utils.async_timer():
    #     await crawler.scrape_categories(
    #         max_workers=3,
    #         max_workers_page=5,
    #     )
    # crawler.save_categories("scrapped_test.json")

    with utils.timer():
        crawler.scrape_page(page_title="Glyphward")

    crawler.log_page(page_title="Glyphward")


if __name__ == "__main__":
    asyncio.run(main())
