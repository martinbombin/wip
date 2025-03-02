"""Provides utility functions for web scraping.

Functions:
extract_dl_text(dl_tag: BeautifulSoup) -> str:
Extract and concatenate text from <dl> tags, including <dt> and <dd> items.
"""

import logging
import time
from collections.abc import Generator
from contextlib import asynccontextmanager, contextmanager

import undetected_chromedriver as uc

# import schedule
from selenium.webdriver.chrome.options import Options

logging.basicConfig(level=logging.INFO)


@asynccontextmanager
async def async_timer():
    start_time = time.time()
    try:
        yield  # Execution pauses here while the code inside `async with` runs
    finally:
        elapsed_time = time.time() - start_time
        logging.info(
            "Code block executed in %.4f seconds",
            elapsed_time,
        )


@contextmanager
def timer():
    start_time = time.time()
    yield  # Code inside the "with" block executes here
    elapsed_time = time.time() - start_time
    logging.info("Code block executed in %.4f seconds", elapsed_time)


@contextmanager
def init_browser() -> Generator[uc.Chrome]:
    """Initialize and return a Chrome browser instance."""
    opts = Options()
    opts.add_argument(
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36",
    )
    try:
        browser = uc.Chrome(
            driver_executable_path="chromedriver",
            options=opts,
        )
        yield browser
    except Exception as e:
        logging.exception("Error initializing browser: %s", e)
    else:
        browser.quit()


def extract_dl_text(dl_tag) -> str:
    """Extract and concatenate text from <dl> tags, including <dt> and <dd> items.

    Args:
        dl_tag: A BeautifulSoup tag object representing a <dl> tag.

    Returns:
        A string containing the concatenated text from the <dt> and <dd>
        items.

    """
    texts = [
        item.get_text(strip=True)
        for item in dl_tag.find_all(["dt", "dd"])
    ]

    return "\n".join(texts)
