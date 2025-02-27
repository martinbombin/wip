"""Provides utility functions for web scraping.

Functions:
extract_dl_text(dl_tag: BeautifulSoup) -> str:
Extract and concatenate text from <dl> tags, including <dt> and <dd> items.
"""


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
