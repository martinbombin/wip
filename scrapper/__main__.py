import asyncio
import logging
from concurrent.futures import ThreadPoolExecutor

import undetected_chromedriver as uc
from selenium.webdriver.chrome.options import Options

from .crawler import Crawler
from .utils import async_timer, timer

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
            "Error with browser creation for page %s: %s",
            page.url,
            e,
        )


def get_page(title: str, crawler: Crawler):
    for category in crawler.categories:
        if category.name == title[0]:
            for page in category.pages:
                if page.title == title:
                    return page
    return None


@async_timer
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


@timer
def scrap_page(page_title: str):
    crawler = Crawler()
    crawler.load_categories("categories.json")
    page = get_page(page_title, crawler)
    if page is not None:
        browser = init_browser()
        page.set_content(browser)
        browser.quit()
        for cs in page.content.content_sections:
            logging.info(
                "Tittle: %s\n%s\n",
                cs.title,
                cs.content,
            )


def log_page(page_title: str):
    crawler = Crawler()
    crawler.load_categories("scrapped.json")
    page = get_page(page_title, crawler)
    if page is not None:
        for cs in page.content.content_sections:
            logging.info(
                "Tittle: %s\n%s\n",
                cs.title,
                cs.content,
            )


async def main():
    """Main async function to initialize the browser and process pages in parallel."""
    # await scrap_categories()

    # log_page(page_title="Hoid")

    # scrap_page(page_title="Hoid")


if __name__ == "__main__":
    asyncio.run(main())
