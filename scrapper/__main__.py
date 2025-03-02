import asyncio
import logging

from . import utils
from .crawler import Crawler

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)


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
