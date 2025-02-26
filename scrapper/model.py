import time

import undetected_chromedriver as uc
from bs4 import BeautifulSoup
from bs4.element import Tag
from pydantic import BaseModel, Field, HttpUrl

from .utils import extract_dl_text


class InfoBoxSection(BaseModel):
    title: str
    description: str


class InfoBox(BaseModel):
    title: str
    info_box_sections: list[InfoBoxSection] = Field(
        default_factory=list,
    )

    def set_info_box_sections(self, infobox_table) -> None:
        # Now iterate over the rows to get other key-value pairs
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
    title: str
    content: str


class Content(BaseModel):
    content_sections: list[ContentSection] = Field(default_factory=list)

    def set_info_content_sections(self, content_container) -> None:
        current_title = ""
        current_texts = []
        have_text = False
        for child in content_container.children:
            child: Tag = child
            if not hasattr(child, "name"):
                continue

            # When encountering an h2, save the current section and reset.
            if child.name == "h2":
                if have_text:
                    content_section = ContentSection(
                        title=current_title,
                        content="".join(current_texts).replace(
                            "[edit]",
                            "",
                        ),
                    )
                    self.content_sections.append(content_section)
                    have_text = False

                current_texts = []
                headline = child.find("span", class_="mw-headline")
                if headline:
                    title = headline.get_text(strip=True)
                else:
                    title = child.get_text(strip=True)
                current_title = title

            # Add text from <p> tags.
            elif child.name in ["p"]:
                current_texts.append(child.get_text())
                have_text = True

            # Add text from <h> tags higuer than 2.
            elif child.name in ["h3", "h4"]:
                text = child.get_text()
                current_texts.append(text + "\n")

            # Add text from <dl> tags (like dt, dd) as well.
            elif child.name == "dl":
                dl_text = extract_dl_text(child)
                if dl_text:
                    current_texts.append(dl_text)

        # Save any trailing content.
        if have_text:
            content_section = ContentSection(
                title=current_title,
                content="".join(current_texts).replace("[edit]", ""),
            )
            self.content_sections.append(content_section)


# Page model: Represents an individual wiki page
class Page(BaseModel):
    title: str
    url: HttpUrl  # Ensures the URL is valid
    info_box: InfoBox | None = None
    content: Content | None = None


class PageBuilder:
    def __init__(self, title: str, url: HttpUrl):
        self._page_data = {
            "title": title,
            "url": url,
        }  # Mandatory field required at creation

    def set_info_box(self, driver: uc.Chrome):
        # Open the URL
        driver.get(str(self._page_data["url"]))
        # Wait for the page to load fully (you can adjust the wait time as necessary)
        time.sleep(
            5,
        )  # Wait for 5 seconds, this can be optimized by using WebDriverWait

        # Get the page source (HTML)
        page_source = driver.page_source

        # Parse the page source with BeautifulSoup
        soup = BeautifulSoup(page_source, "html.parser")

        infobox_table = soup.find("table", class_="infobox side")
        if infobox_table:
            # First, try to get the title
            title_cell = infobox_table.find("th", class_="title")
            if title_cell:
                title = title_cell.get_text(strip=True)
                info_box = InfoBox(title=title)
            else:
                info_box = InfoBox(title="")

            info_box.set_info_box_sections(infobox_table)

            self._page_data["info_box"] = info_box

        return self

    def set_content(self, driver: uc.Chrome):
        # Open the URL
        driver.get(str(self._page_data["url"]))
        # Wait for the page to load fully (you can adjust the wait time as necessary)
        time.sleep(5)

        # Get the page source (HTML)
        page_source = driver.page_source

        # Parse the page source with BeautifulSoup
        soup = BeautifulSoup(page_source, "html.parser")

        content_container = soup.find("div", class_="mw-parser-output")
        content = Content()
        content.set_info_content_sections(content_container)
        self._page_data["content"] = content

        return self

    def build(self) -> Page:
        return Page(**self._page_data)

    def update_page(self, user: Page) -> Page:
        """Update an existing page with new fields."""
        updated_data = user.model_dump(exclude_unset=True)
        updated_data.update(self._page_data)
        return Page(**updated_data)


# Category model: Represents a category containing multiple pages
class Category(BaseModel):
    name: str
    pages: list[Page]  # A list of Page objects
