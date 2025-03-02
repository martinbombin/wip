"""Models for representing and extracting information from web pages.

Classes:
    InfoBoxSection: Represents a section of an information box with a title and description.
    InfoBox: Represents an information box with a title and multiple sections.
    ContentSection: Represents a section of content with a title and content.
    Content: Represents content with multiple sections.
    Page: Represents a web page with a title, URL, optional info box, and optional content.
    Category: Represents a category that contains a list of pages.

"""

import asyncio
import logging
import time

import undetected_chromedriver as uc
from bs4 import BeautifulSoup
from pydantic import BaseModel, ConfigDict, Field, HttpUrl

from . import utils

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)


class InfoBoxSection(BaseModel):
    """InfoBoxSection represents a section of an information box with a title and description.

    Attributes:
        title (str): The title of the information box section.
        description (str): The description of the information box section.

    """

    title: str
    description: str


class InfoBox(BaseModel):
    """A model representing an information box with a title and multiple sections.

    Attributes:
        title (str): The title of the information box.
        info_box_sections (list[InfoBoxSection]): A list of sections within the information box.

    Methods:
        set_info_box_sections(infobox_table: BeautifulSoup) -> None:
            Populates the info_box_sections attribute by extracting key-value pairs from the given infobox_table.

    """

    title: str
    info_box_sections: list[InfoBoxSection] = Field(
        default_factory=list,
    )

    def set_info_box_sections(self, infobox_table) -> None:
        """Extract key-value pairs from an infobox table and appends them as InfoBoxSection objects to the info_box_sections attribute.

        Args:
            infobox_table (bs4.element.Tag): A BeautifulSoup Tag object representing the infobox table.

        """
        rows = infobox_table.find_all("tr")
        for row in rows:
            header = row.find("th")
            data = row.find("td")
            # Skip if this row is the title row (already processed)
            if header and "title" in header.get("class", []):
                continue
            if header and data:
                key = header.get_text(strip=True)
                # Extract text from <td> while handling links properly
                links = data.find_all("a")
                if links:
                    value = ", ".join(
                        [link.get_text(strip=True) for link in links],
                    )
                else:
                    value = data.get_text(strip=True)

                info_box_section = InfoBoxSection(
                    title=key,
                    description=value,
                )
                self.info_box_sections.append(info_box_section)


class ContentSection(BaseModel):
    """A model representing a section of content with a title and content.

    Attributes:
        title (str): The title of the content section.
        content (str): The body content of the section.

    """

    title: str
    content: str

    def __str__(self):
        return f"{self.title}\n{self.content}"


class Content(BaseModel):
    """A model representing content with multiple sections.

    Attributes:
        content_sections (list[ContentSection]): A list of content sections.

    Methods:
        set_info_content_sections(content_container: Any) -> None:
            Parses the content container and sets the content sections.

    """

    content_sections: list[ContentSection] = Field(default_factory=list)

    def __str__(self):
        return "\n".join(
            [str(section) for section in self.content_sections],
        )

    def set_info_content_sections(self, content_container) -> None:
        """Parse the content container and sets the content sections.

        Args:
            content_container (Any): The container holding the content sections.

        """

        def _get_title_from_h2(child) -> str:
            headline = child.find("span", class_="mw-headline")
            if headline:
                return headline.get_text(strip=True)
            return child.get_text(strip=True)

        def _get_content_section(
            current_title: str,
            current_texts: list[str],
        ) -> ContentSection:
            return ContentSection(
                title=current_title,
                content="".join(current_texts).replace("[edit]", ""),
            )

        current_title = ""
        current_texts = []
        have_text = False
        for child in content_container.children:
            if not hasattr(child, "name"):
                continue

            if child.name == "h2":
                if have_text:
                    self.content_sections.append(
                        _get_content_section(
                            current_title,
                            current_texts,
                        ),
                    )
                current_texts = []
                current_title = _get_title_from_h2(child)
                have_text = False
            elif child.name in ["p"]:
                current_texts.append(child.get_text())
                have_text = True
            elif child.name in ["h3", "h4"]:
                current_texts.append("\n" + child.get_text() + "\n")
            elif child.name == "dl":
                dl_text = utils.extract_dl_text(child)
                if dl_text:
                    current_texts.append(dl_text)

        if have_text:
            self.content_sections.append(
                _get_content_section(current_title, current_texts),
            )


class Page(BaseModel):
    """Represent a web page with a title, URL, optional info box, and optional content.

    Attributes:
        title (str): The title of the page.
        url (HttpUrl): The URL of the page, validated to be a proper URL.
        info_box (InfoBox | None): An optional info box containing additional information about the page.
        content (Content | None): Optional content of the page.
        _page_source (BeautifulSoup | None): The parsed HTML source of the page.

    Methods:
        _set_page_source(driver: uc.Chrome, load_time: int = 3) -> None:
            Opens the URL in the given Chrome driver, waits for the page to load, and sets the page source.

        set_info_box(driver: uc.Chrome) -> None:
            Sets the info box attribute by parsing the page source for an infobox table.

        set_content(driver: uc.Chrome) -> None:
            Sets the content attribute by parsing the page source for the main content of the page.

    """

    title: str
    url: HttpUrl  # Ensures the URL is valid
    info_box: InfoBox | None = None
    content: Content | None = None

    _page_source: BeautifulSoup | None = None

    model_config = ConfigDict(json_encoders={HttpUrl: str})

    def __str__(self):
        return f"Title: {self.title}\nURL: {self.url}\nInfo Box: {self.info_box}\nContent: {self.content}"

    def _set_page_source(
        self,
        driver: uc.Chrome,
        load_time: int = 3,
    ) -> None:
        # Open the URL
        driver.get(str(self.url))
        # Wait for the page to load fully
        time.sleep(load_time)

        # Get the page source (HTML)
        page_source = driver.page_source

        # Parse the page source with BeautifulSoup
        self._page_source = BeautifulSoup(page_source, "html.parser")

    def _set_info_box(self, driver: uc.Chrome) -> None:
        """Set the information box for the current page using the provided web driver.

        This method retrieves the page source if it is not already set, finds the
        infobox table with the class "infobox side", and extracts the title from
        the table. It then initializes the `info_box` attribute with the extracted
        title and populates its sections.

        Args:
            driver (uc.Chrome): The web driver used to retrieve the page source.

        """
        if self._page_source is None:
            self._set_page_source(driver)

        infobox_table = self._page_source.find(
            "table",
            class_="infobox side",
        )
        if infobox_table:
            # First, try to get the title
            title_cell = infobox_table.find("th", class_="title")
            if title_cell:
                title = title_cell.get_text(strip=True)
                self.info_box = InfoBox(title=title)
            else:
                self.info_box = InfoBox(title="")

            self.info_box.set_info_box_sections(infobox_table)

    def _set_content(self, driver: uc.Chrome) -> None:
        """Set the content of the page by extracting information from the web driver.

        Args:
            driver (uc.Chrome): The web driver instance used to fetch the page source.

        """
        if self._page_source is None:
            self._set_page_source(driver)

        content_container = self._page_source.find(
            "div",
            class_="mw-parser-output",
        )
        self.content = Content()
        self.content.set_info_content_sections(content_container)

    def scrape_content(self) -> None:
        """Scrape the content of the page using a browser instance."""
        try:
            with utils.init_browser() as browser:
                self._set_content(browser)
        except Exception as e:
            logging.exception(
                "Error processing page %s: %s",
                self.url,
                e,
            )


class Category(BaseModel):
    """Represent a category that contains a list of pages.

    Attributes:
        name (str): The name of the category.
        pages (list[Page]): A list of Page objects associated with the category.

    """

    name: str
    pages: list[Page]

    def __str__(self):
        return f"Category: {self.name}\nPages: {', '.join([page.title for page in self.pages])}"

    def get_page(self, title: str) -> Page | None:
        for page in self.pages:
            if page.title == title:
                return page
        return None

    def scrape_page(self, title: str) -> Page | None:
        page = self.get_page(title)
        if page is not None:
            page.scrape_content()

    async def scrape_pages(self, max_workers: int = 5) -> None:
        semaphore = asyncio.Semaphore(max_workers)

        async def scrape_with_limit(page: Page):
            async with semaphore:
                await asyncio.to_thread(
                    page.scrape_content,
                )  # Run in a thread

        await asyncio.gather(
            *(scrape_with_limit(page) for page in self.pages),
        )
