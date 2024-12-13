import logging
import re
import json
from bs4 import BeautifulSoup
import requests
from sqlalchemy.exc import SQLAlchemyError
from src.database.models import Bus, BusOverview, BusImage
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import urljoin

class BusScraper:
    def __init__(self, base_url, session, max_retries=3):
        self.base_url = base_url.rstrip('/')
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
        if not logger.handlers:
            logger.addHandler(handler)
        return logger

    def fetch_data(self, page_number=1):
        if page_number > 1:
            url = f"{self.base_url}/inventory/bus-for-sale/page/{page_number}/?posts_per_page=10"
        else:
            url = f"{self.base_url}/inventory/bus-for-sale/?posts_per_page=10"
        
        self.logger.debug(f"Constructed URL for page {page_number}: {url}")
        
        retries = 0
        while retries < self.max_retries:
            try:
                response = requests.get(url, headers=self.headers)
                response.raise_for_status()
                self.logger.debug(f"Fetched data from page {page_number}: {url}")
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
                response = requests.get(detail_url, headers=self.headers)
                response.raise_for_status()
                soup = BeautifulSoup(response.text, "html.parser")
                details = self.extract_details(soup)
                self.logger.debug(f"Fetched details from URL: {detail_url}")
                return details
            except requests.exceptions.RequestException as e:
                retries += 1
                self.logger.warning(f"Retrying ({retries}/{self.max_retries}) for detail URL {detail_url}: {e}")
        self.logger.error(f"Failed to fetch details after {self.max_retries} retries: {detail_url}")
        return None

    def extract_details(self, soup):
        try:
            specs = self.extract_table_data(soup)
            details = {
                "mdesc": self.extract_main_description(soup),
                "specs": specs,
                "vin": None,
                "dimensions": None,
                "luggage": None,
                "state_bus_standard": None,
                "contact_email": None,
                "contact_phone": None,
                "images": self.extract_all_images(soup),
                "year": specs.get("year")  # Asignar directamente el year desde specs
            }
            location = specs.get("location")
            contact_phone = self.extract_contact_phone(soup, location)
            details["contact_phone"] = contact_phone
            details = self.enhance_details(details)
            self.logger.debug(f"Extracted details: {json.dumps(details, indent=2)}")
            return details
        except Exception as e:
            self.logger.error(f"Error extracting details: {e}")
            return None

    def extract_main_description(self, soup):
        description = None
        options_tab = soup.find("div", class_="vc_tta-panel", id=lambda x: x and "Options" in x)
        if options_tab:
            paragraph = options_tab.find("p")
            if paragraph:
                description = paragraph.get_text(strip=True)
        else:
            self.logger.debug("No Options tab found, attempting alternative selectors for main description.")
            description = self.extract_text(soup, ".wpb_wrapper > p")
        return description

    def extract_text(self, soup, selector):
        element = soup.select_one(selector)
        return element.get_text(strip=True) if element else None

    def extract_table_data(self, soup):
        specs = {}
        tables = soup.find_all("table")
        for table in tables:
            if table.find("td", class_="t-label") and table.find("td", class_="t-value"):
                rows = table.find_all("tr")
                self.logger.debug(f"Number of table rows found: {len(rows)} in table: {table}")
                for row in rows:
                    key_td = row.find("td", class_="t-label")
                    value_td = row.find("td", class_="t-value")
                    if key_td and value_td:
                        key_text = key_td.get_text(strip=True).lower().replace(" ", "_")
                        value_text = value_td.get_text(strip=True)
                        if key_text in ["wheel_chair_accessible", "air_conditioning", "manufacturer_warranty_remaining"]:
                            specs[key_text] = True if value_text.lower() == "yes" else False
                        elif key_text in ["price", "mileage", "capacity"]:
                            specs[key_text] = self.format_numeric(value_text)
                        elif key_text == "year":
                            specs[key_text] = self.format_year(value_text)
                        else:
                            specs[key_text] = value_text
                    else:
                        if key_td:
                            key_text = key_td.get_text(strip=True).lower().replace(" ", "_")
                            specs[key_text] = None
        if not specs:
            self.logger.warning("No specs found in any tables.")
        else:
            self.logger.debug(f"Extracted specs: {specs}")
        return specs

    def extract_contact_phone(self, soup, location):
        try:
            widgets_div = soup.find("div", class_="widgets cols_3 clearfix")
            if not widgets_div:
                self.logger.warning("No widgets section found for contact information.")
                return None
            
            for aside in widgets_div.find_all("aside", class_="extendedwopts-md-center widget widget_text"):
                state_header = aside.find("div", class_="widget-title").find("h6")
                if state_header and state_header.get_text(strip=True).lower() == location.lower():
                    phone_link = aside.find("a", href=re.compile(r"tel:"))
                    if phone_link:
                        phone_number = re.sub(r"[^0-9\-]", "", phone_link.get_text(strip=True))
                        self.logger.debug(f"Found phone number for {location}: {phone_number}")
                        return phone_number
            self.logger.warning(f"No phone number found for location: {location}")
            return None
        except Exception as e:
            self.logger.warning(f"Failed to extract contact phone for location {location}: {e}")
            return None

    def extract_all_images(self, soup):
        images = []
        for img_tag in soup.select(".stm-big-car-gallery img, .stm-thumbs-car-gallery img"):
            url = img_tag.get("src")
            description = img_tag.get("alt", "")
            if url:
                images.append({"url": url, "description": description})
        self.logger.debug(f"Number of images extracted: {len(images)}")
        return images

    def parse_data(self, html):
        if not html:
            self.logger.warning("No HTML content to parse.")
            return []
        
        soup = BeautifulSoup(html, "html.parser")
        buses = []

        for item in soup.select(".listing-list-loop.stm-listing-directory-list-loop"):
            try:
                title_tag = item.select_one(".title.heading-font a")
                title = title_tag.get_text(strip=True) if title_tag else None
                source_url = title_tag["href"] if title_tag and title_tag.has_attr("href") else None

                price_tag = item.select_one(".price .heading-font")
                price_text = price_tag.get_text(strip=True) if price_tag else "0"
                price = self.format_price(price_text)

                self.logger.debug(f"Extracted title: {title}, price: {price}, URL: {source_url}")
                
                if not title or not price or not source_url:
                    self.logger.warning(f"Missing title, price, or source URL for item: {item}")
                    continue

                details = self.fetch_details(source_url)
                if not details:
                    self.logger.warning(f"No details extracted for URL: {source_url}")
                    continue

                bus = Bus(
                    title=title,
                    price=str(price),  # Asegurar que price es una cadena
                    source_url=source_url,
                    vin=details.get("vin"),
                    dimensions=details.get("dimensions"),
                    luggage=details.get("luggage"),
                    state_bus_standard=details.get("state_bus_standard"),
                    contact_email=details.get("contact_email"),
                    contact_phone=details.get("contact_phone"),
                    make=details.get("specs", {}).get("make"),
                    model=details.get("specs", {}).get("model"),
                    body=details.get("specs", {}).get("body"),
                    chassis=details.get("specs", {}).get("chassis"),
                    engine=details.get("specs", {}).get("engine"),
                    transmission=details.get("specs", {}).get("transmission"),
                    mileage=details.get("specs", {}).get("mileage"),
                    passengers=details.get("specs", {}).get("capacity"),
                    wheelchair="Yes" if details.get("specs", {}).get("wheel_chair_accessible") else "No",
                    color=details.get("specs", {}).get("color"),
                    interior_color=details.get("specs", {}).get("interior_color"),
                    exterior_color=details.get("specs", {}).get("exterior_color"),
                    gvwr=details.get("specs", {}).get("gvwr"),
                    brake=details.get("specs", {}).get("brake"),
                    airconditioning=details.get("airconditioning"),  # Usar el campo mapeado
                    location=details.get("specs", {}).get("location"),
                    us_region=self.map_us_region(details.get("specs", {}).get("location")),
                    year=details.get("year"),  # Asegurar que 'year' está asignado correctamente
                )
                self.session.add(bus)
                self.session.commit()

                overview = BusOverview(
                    bus_id=bus.id,
                    mdesc=details.get("mdesc"),
                    features=json.dumps(details.get("specs", {})),
                    specs=json.dumps(details.get("specs", {})),
                )
                self.session.add(overview)

                for idx, img in enumerate(details.get("images", [])):
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

                self.logger.info(f"Successfully scraped bus: {title}")

            except SQLAlchemyError as e:
                self.logger.error(f"Database error: {e}")
                self.session.rollback()
            except Exception as e:
                self.logger.warning(f"Error parsing item: {e}")

        return buses

    def enhance_details(self, details):
        model = details.get("specs", {}).get("model")
        if not model:
            self.logger.warning("No model information available to enhance details.")
            return details
        
        try:
            # Solo extraer año si no está presente
            if not details.get("year"):
                year_match = re.search(r"\b(19|20)\d{2}\b", model)
                year = year_match.group() if year_match else None
                details["year"] = year if year else details.get("year")
            
            engine_match = re.search(r"(Diesel|Gasoline|Electric)\s+([A-Za-z0-9\.\-]+)", model)
            if engine_match:
                fuel_type = engine_match.group(1)
                engine_info = engine_match.group(2)
                details["specs"]["fuel_type"] = fuel_type
                details["specs"]["engine"] = engine_info
            
            details["vin"] = "UNKNOWN"
            details["dimensions"] = "UNKNOWN"
            details["state_bus_standard"] = "STANDARD"
            
            # Mapear air_conditioning a los valores del Enum
            is_air_conditioning = details.get("specs", {}).get("air_conditioning")
            details["airconditioning"] = self.map_airconditioning_option(is_air_conditioning)
            
            self.logger.debug(f"Enhanced details: {json.dumps(details, indent=2)}")
        except Exception as e:
            self.logger.warning(f"Failed to enhance details based on model: {e}")
        
        return details

    def map_us_region(self, location):
        regions = {
            'Missouri': 'MIDWEST',
            'Illinois': 'MIDWEST',
            'Tennessee': 'SOUTH',
            'Kentucky': 'SOUTH',
            'Arkansas': 'SOUTH',
            'Alabama': 'SOUTH',
        }
        return regions.get(location, 'OTHER')

    def map_airconditioning_option(self, is_air_conditioning):
        if is_air_conditioning:
            return 'DASH'  # O 'BOTH' según corresponda
        else:
            return 'NONE'

    @staticmethod
    def format_price(price_str):
        try:
            return float(re.sub(r"[^\d.]", "", price_str))
        except ValueError:
            return 0.0

    @staticmethod
    def format_numeric(value_str):
        try:
            return int(re.sub(r"[^\d]", "", value_str))
        except ValueError:
            return None

    @staticmethod
    def format_year(year_str):
        match = re.search(r"\b(19|20)\d{2}\b", year_str)
        return match.group() if match else None  # Devuelve una cadena

    def scrape_all_pages(self):
        self.logger.info("Starting scraping process.")
        first_page_html = self.fetch_data()
        if not first_page_html:
            self.logger.error("No data fetched for the first page.")
            return []

        soup = BeautifulSoup(first_page_html, "html.parser")
        pagination = soup.select(".stm_ajax_pagination .page-numbers")
        if pagination:
            page_numbers = [int(link.get_text()) for link in pagination if link.get_text().isdigit()]
            total_pages = max(page_numbers) if page_numbers else 1
        else:
            total_pages = 1

        self.logger.info(f"Total pages found: {total_pages}")

        all_buses = []
        with ThreadPoolExecutor(max_workers=5) as executor:
            future_to_page = {executor.submit(self.fetch_data, page): page for page in range(1, total_pages + 1)}
            for future in future_to_page:
                page = future_to_page[future]
                try:
                    page_html = future.result()
                    if page_html:
                        buses = self.parse_data(page_html)
                        all_buses.extend(buses)
                        self.logger.info(f"Scraped {len(buses)} buses from page {page}.")
                except Exception as e:
                    self.logger.error(f"Error scraping page {page}: {e}")

        self.logger.info(f"Scraping completed. Total buses scraped: {len(all_buses)}")
        return all_buses
