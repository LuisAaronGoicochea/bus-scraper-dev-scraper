import logging
import re
import json
from bs4 import BeautifulSoup
import requests
from sqlalchemy.exc import SQLAlchemyError
from src.database.models import Bus, BusOverview, BusImage
from concurrent.futures import ThreadPoolExecutor

class BusScraper:
    def __init__(self, base_url, session, max_retries=3):
        self.base_url = base_url
        self.session = session
        self.max_retries = max_retries
        self.headers = {
            "User-Agent": (
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/114.0.0.0 Safari/537.36"
            )
        }
        self.logger = self.setup_logger()

    @staticmethod
    def setup_logger():
        logger = logging.getLogger("BusScraper")
        logger.setLevel(logging.DEBUG)
        handler = logging.FileHandler("/tmp/bus_scraper.log", mode="w")
        handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
        logger.addHandler(handler)
        return logger

    def fetch_data(self, page_number=1):
        url = f"{self.base_url}/page/{page_number}/?posts_per_page=10"
        retries = 0
        while retries < self.max_retries:
            try:
                response = requests.get(url, headers=self.headers, timeout=10)
                response.raise_for_status()
                return response.text
            except requests.exceptions.RequestException as e:
                retries += 1
                self.logger.warning(f"Retrying ({retries}/{self.max_retries}) for page {page_number}: {e}")
        self.logger.error(f"Failed to fetch data after {self.max_retries} retries: {url}")
        return None

    def fetch_details(self, detail_url):
        retries = 0
        while retries < self.max_retries:
            try:
                response = requests.get(detail_url, headers=self.headers, timeout=10)
                response.raise_for_status()
                soup = BeautifulSoup(response.text, "html.parser")
                return self.extract_details(soup)
            except requests.exceptions.RequestException as e:
                retries += 1
                self.logger.warning(f"Retrying ({retries}/{self.max_retries}) for detail URL {detail_url}: {e}")
        self.logger.error(f"Failed to fetch details after {self.max_retries} retries: {detail_url}")
        return None

    def extract_details(self, soup):
        try:
            details = {
                "mdesc": self.extract_main_description(soup),
                "intdesc": self.extract_interior_description(soup),
                "extdesc": self.extract_exterior_description(soup),
                "specs": self.extract_table_data(soup),
                "vin": self.extract_specific_value(soup, "VIN"),
                "dimensions": self.extract_specific_value(soup, "Dimensions"),
                "luggage": self.extract_specific_value(soup, "Luggage") == "Yes",
                "state_bus_standard": self.extract_specific_value(soup, "State Bus Standard"),
                "contact_email": self.extract_contact(soup, "email"),
                "contact_phone": self.extract_contact(soup, "phone"),
                "images": self.extract_all_images(soup),
            }
            return details
        except Exception as e:
            self.logger.error(f"Error extracting details: {e}")
            return None

    def extract_main_description(self, soup):
        return self.extract_text(soup, ".single-listing-description")

    def extract_interior_description(self, soup):
        return self.extract_text(soup, ".interior-description")

    def extract_exterior_description(self, soup):
        return self.extract_text(soup, ".exterior-description")

    def extract_text(self, soup, selector):
        element = soup.select_one(selector)
        return element.text.strip() if element else None

    def extract_table_data(self, soup):
        specs = {}
        for row in soup.select(".single-car-data table tbody tr"):
            key = row.select_one(".t-label").text.strip() if row.select_one(".t-label") else None
            value = row.select_one(".t-value").text.strip() if row.select_one(".t-value") else None
            if key and value:
                specs[key] = value
        return specs

    def extract_all_images(self, soup):
        images = []
        for img_tag in soup.select(".gallery img"):
            url = img_tag.get("src")
            description = img_tag.get("alt", "")
            if url:
                images.append({"url": url, "description": description})
        return images

    def extract_specific_value(self, soup, label):
        try:
            element = soup.find("td", string=label)
            return element.find_next_sibling("td").text.strip() if element else None
        except Exception as e:
            self.logger.warning(f"Failed to extract value for label {label}: {e}")
            return None

    def extract_contact(self, soup, contact_type):
        try:
            if contact_type == "email":
                return self.extract_text(soup, ".contact-email")
            if contact_type == "phone":
                return self.extract_text(soup, ".contact-phone")
        except Exception as e:
            self.logger.warning(f"Failed to extract contact {contact_type}: {e}")
        return None

    def parse_data(self, html):
        soup = BeautifulSoup(html, "html.parser")
        buses = []

        for item in soup.select(".listing-list-loop.stm-listing-directory-list-loop"):
            try:
                title = self.extract_text(item, ".title a")
                price = self.format_price(self.extract_text(item, ".price .heading-font"))
                source_url = item.select_one(".title a")["href"]

                if not title or not price or not source_url:
                    continue

                details = self.fetch_details(source_url)
                if not details:
                    continue

                bus = Bus(
                    title=title,
                    price=price,
                    source_url=source_url,
                    vin=details.get("vin"),
                    dimensions=details.get("dimensions"),
                    luggage=details.get("luggage"),
                    state_bus_standard=details.get("state_bus_standard"),
                    contact_email=details.get("contact_email"),
                    contact_phone=details.get("contact_phone"),
                    **details.get("specs", {}),
                )
                self.session.add(bus)
                self.session.commit()

                overview = BusOverview(
                    bus_id=bus.id,
                    mdesc=details["mdesc"],
                    intdesc=details["intdesc"],
                    extdesc=details["extdesc"],
                    features=json.dumps(details["specs"]),
                    specs=json.dumps(details["specs"]),
                )
                self.session.add(overview)

                for idx, img in enumerate(details["images"]):
                    image = BusImage(
                        bus_id=bus.id,
                        name=f"{title} Image {idx + 1}",
                        url=img["url"],
                        description=img["description"],
                        image_index=idx,
                    )
                    self.session.add(image)

                self.session.commit()
                buses.append(bus)

            except SQLAlchemyError as e:
                self.logger.error(f"Database error: {e}")
                self.session.rollback()
            except Exception as e:
                self.logger.warning(f"Error parsing item: {e}")

        return buses

    @staticmethod
    def format_price(price_str):
        return re.sub(r"[^\d.]", "", price_str) if price_str else "0"

    def scrape_all_pages(self):
        first_page_html = self.fetch_data()
        if not first_page_html:
            return []

        soup = BeautifulSoup(first_page_html, "html.parser")
        pagination = soup.select(".stm_ajax_pagination .page-numbers")
        total_pages = int(pagination[-2].text) if pagination else 1

        all_buses = []
        with ThreadPoolExecutor(max_workers=5) as executor:
            future_to_page = {executor.submit(self.fetch_data, page): page for page in range(1, total_pages + 1)}
            for future in future_to_page:
                page_html = future.result()
                if page_html:
                    all_buses.extend(self.parse_data(page_html))
        return all_buses