import time

import undetected_chromedriver as uc
from pydantic import HttpUrl

# import schedule
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from .model import Category, Page


def click_proceed_button(browser: uc.Chrome) -> WebDriverWait:
    try:
        # Wait for the button to appear
        wait = WebDriverWait(browser, 20)
        button = wait.until(
            EC.element_to_be_clickable(
                (By.XPATH, "//button[contains(text(), 'Proceed')]"),
            ),
        )

        # Click the button
        button.click()
        print("Button clicked successfully!")

    except Exception as e:
        print(f"Error clicking button: {e}")
        raise
    else:
        return wait


def get_main_page_content(wait: WebDriverWait) -> list[WebElement]:
    wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
    mw_category_div = wait.until(
        EC.presence_of_element_located(
            (
                By.XPATH,
                "//div[@id='mw-pages']//div[@class='mw-category']",
            ),
        ),
    )

    return mw_category_div.find_elements(
        By.CSS_SELECTOR,
        "div.mw-category-group",
    )  # Find all category groups


def parse_categories(
    category_groups: list[WebElement],
) -> list[Category]:
    # List to store categories
    categories: list[Category] = []

    # Loop through each category group
    for group in category_groups:
        # Get the category name from the <h3> tag
        category_name = group.find_element(
            By.TAG_NAME,
            "h3",
        ).text.strip()

        # Get all the links inside the <ul> list
        links = group.find_elements(By.CSS_SELECTOR, "ul li a")

        # Create a list of Page objects
        pages = []
        for link in links:
            url = link.get_attribute("href")
            if url is not None:
                pages.append(
                    Page(
                        title=link.text,
                        url=HttpUrl(url),
                    ),
                )

        # Create a Category object and add it to the list
        categories.append(Category(name=category_name, pages=pages))

    return categories


def get_categories(
    browser: uc.Chrome,
    load_time: int = 2,
) -> list[Category]:
    target_url = "https://coppermind.net/wiki/Category:Cosmere"
    browser.get(target_url)
    time.sleep(load_time)

    wait = click_proceed_button(browser)
    category_groups = get_main_page_content(wait)
    return parse_categories(category_groups)


def main():
    opts = Options()
    opts.add_argument(
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36",
    )
    # opts.add_argument("--headless")

    browser = uc.Chrome(
        driver_executable_path="chromedriver",
        options=opts,
    )

    categories = get_categories(browser)

    # browser.quit()

    page = categories[1].pages[0]
    page.set_content(browser)
    if page.content is not None:
        for section in page.content.content_sections:
            print(f"{section.title}\n{section.content}\n")
    else:
        print("Page content is None")


if __name__ == "__main__":
    main()
