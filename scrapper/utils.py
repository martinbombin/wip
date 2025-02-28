"""Provides utility functions for web scraping.

Functions:
extract_dl_text(dl_tag: BeautifulSoup) -> str:
Extract and concatenate text from <dl> tags, including <dt> and <dd> items.
"""

import logging
import time

logging.basicConfig(level=logging.INFO)


def async_timer(func):
    async def wrapper(*args, **kwargs):
        start_time = time.time()
        result = await func(*args, **kwargs)
        end_time = time.time()
        elapsed_time = end_time - start_time
        logging.info(
            "Function '%s' executed in %.4f seconds",
            func.__name__,
            elapsed_time,
        )
        return result

    return wrapper


def timer(func):
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        elapsed_time = end_time - start_time
        logging.info(
            "Function '%s' executed in %.4f seconds",
            func.__name__,
            elapsed_time,
        )
        return result

    return wrapper


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
