import asyncio
import json
import logging
import time
from pathlib import Path

import undetected_chromedriver as uc
from pydantic import HttpUrl

# import schedule
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.support.ui import WebDriverWait

from scrapper.model import Category

from . import model

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)


class Crawler:
    def __init__(self) -> None:
        self.categories: list[Category] = []

    def save_categories(self, filename: str) -> None:
        """Save the list of Category objects to a file using pickle.

        Args:
            filename (str): The name of the file to save the categories to.

        """
        with Path(filename).open("w") as file:
            json.dump(
                [
                    category.model_dump(mode="json")
                    for category in self.categories
                ],
                file,
                indent=4,
            )
        logging.info("Categories saved to %s", filename)

    def load_categories(self, filename: str) -> None:
        """Load the list of Category objects from a file using pickle.

        Args:
            filename (str): The name of the file to load the categories from.

        """
        with Path(filename).open("r") as file:
            categories_data = json.load(file)
        self.categories = [Category(**data) for data in categories_data]
        logging.info("Categories loaded from %s", filename)

    def set_categories(
        self,
        chrome_driver: uc.Chrome,
        load_time: int = 2,
    ) -> None:
        """Fetch categories from the specified target URL using the provided self.chrome_driver instance.

        Args:
            load_time (int, optional): The time to wait for the page to load. Defaults to 2 seconds.

        Returns:
            list[Category]: A list of Category objects parsed from the main page content.

        """

        def _click_proceed_button(
            chrome_driver: uc.Chrome,
            load_time: int = 5,
        ) -> None:
            """Wait for the 'Proceed' button to become clickable and clicks it.

            Args:
                load_time (int, optional): The time to wait for the page to load. Defaults to 5 seconds.

            Raises:
                Exception: If there is an error clicking the button.

            """
            try:
                # Wait for the button to appear
                wait = WebDriverWait(chrome_driver, load_time)
                button = wait.until(
                    expected_conditions.element_to_be_clickable(
                        (
                            By.XPATH,
                            "//button[contains(text(), 'Proceed')]",
                        ),
                    ),
                )

                # Click the button
                button.click()
                logging.info("Button clicked successfully!")

            except Exception as e:
                logging.info("Error clicking button: %s", e)
                raise

        def _get_main_page_content(
            chrome_driver: uc.Chrome,
            load_time: int = 5,
        ) -> list[WebElement]:
            """Retrieve the main page content by waiting for the presence of specific elements.

            Args:
                load_time (int, optional): The time to wait for the page to load. Defaults to 5 seconds.

            Returns:
                list[WebElement]: A list of WebElement objects representing the category groups found on the main page.

            """
            wait = WebDriverWait(chrome_driver, load_time)
            wait.until(
                expected_conditions.presence_of_element_located(
                    (By.TAG_NAME, "body"),
                ),
            )
            mw_category_div = wait.until(
                expected_conditions.presence_of_element_located(
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

        def _set_categories(
            crawler: Crawler,
            category_groups: list[WebElement],
        ) -> None:
            """Parse a list of category groups and extracts category names and their associated pages.

            Args:
                category_groups (list[WebElement]): A list of WebElement objects representing category groups.


            """
            # Loop through each category group
            for group in category_groups:
                # Get the category name from the <h3> tag
                category_name = group.find_element(
                    By.TAG_NAME,
                    "h3",
                ).text.strip()

                # Get all the links inside the <ul> list
                links = group.find_elements(By.CSS_SELECTOR, "ul li a")

                # Create a list of model.Page objects
                pages = []
                for link in links:
                    url = link.get_attribute("href")
                    if url is not None:
                        pages.append(
                            model.Page(
                                title=link.text,
                                url=HttpUrl(url),
                            ),
                        )

                # Create a Category object and add it to the list
                crawler.categories.append(
                    Category(name=category_name, pages=pages),
                )

        target_url = "https://coppermind.net/wiki/Category:Cosmere"
        chrome_driver.get(target_url)
        time.sleep(load_time)

        _click_proceed_button(chrome_driver=chrome_driver)

        category_groups = _get_main_page_content(
            chrome_driver=chrome_driver,
        )

        _set_categories(
            crawler=self,
            category_groups=category_groups,
        )
        logging.info("Categories set suscesfully")

    def get_category(self, name: str) -> Category | None:
        """Get a category by name.

        Args:
            name (str): The name of the category to retrieve.

        Returns:
            Category | None: The Category object if found, else None.

        """
        for category in self.categories:
            if category.name == name:
                return category
        return None

    def scrape_page(self, page_title: str):
        category = self.get_category(page_title[0])
        if category is not None:
            category.scrape_page(page_title)

    def log_page(self, page_title: str):
        category = self.get_category(page_title[0])
        if category is not None:
            page = category.get_page(page_title)
            logging.info(
                "Page: %s\n",
                str(page),
            )

    async def scrape_categories(
        self,
        max_workers: int = 1,
        max_workers_page: int = 5,
    ):
        """Scrape all categories asynchronously."""
        semaphore = asyncio.Semaphore(
            max_workers,
        )  # Limit categories

        async def scrape_with_limit(category: Category):
            async with semaphore:
                await category.scrape_pages(
                    max_workers=max_workers_page,
                )

        await asyncio.gather(
            *(
                scrape_with_limit(category)
                for category in self.categories
            ),
        )
