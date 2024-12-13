import json
import boto3
from typing import List, Dict
from src.scraper.main_scraper import BusScraper
from src.database.models import Bus, BusOverview, BusImage
from src.database.db_manager import DatabaseManager
from config.settings import Settings
import logging

class ETL:
    """ETL class to manage the extraction, transformation, and loading of data."""

    def __init__(self, settings: Settings):
        self.settings = settings
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)
        handler = logging.StreamHandler()
        formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
        handler.setFormatter(formatter)
        if not self.logger.handlers:
            self.logger.addHandler(handler)

        try:
            self.db_manager = DatabaseManager()
            self.scraper = BusScraper(settings.BASE_URL, self.db_manager.Session())
            self.s3_client = boto3.client("s3", region_name=settings.AWS_REGION)
            self.logger.info("ETL class initialized successfully.")
        except Exception as e:
            self.logger.error(f"Error initializing ETL class: {e}")
            raise

    def extract(self) -> List[Bus]:
        """Extract data from the source URL using the scraper."""
        try:
            self.logger.info("Starting data extraction from source.")
            buses = self.scraper.scrape_all_pages()
            if not buses:
                raise ValueError("No data extracted from source.")
            self.logger.info(f"Extracted {len(buses)} buses from source.")
            return buses
        except Exception as e:
            self.logger.error(f"Error during data extraction: {e}")
            raise

    def transform(self, buses: List[Bus]) -> Dict[str, List[dict]]:
        """Transform data into separate JSON-serializable formats for each table."""
        try:
            self.logger.info("Starting data transformation.")
            buses_data = []
            overview_data = []
            images_data = []

            for bus in buses:
                # Asignar 0 a 'price' si está ausente o es None
                price = bus.price if bus.price else "0"

                # Convert Bus object to dictionary sin incluir 'id'
                bus_dict = {
                    # "id": bus.id,  # Excluir 'id' para evitar problemas al actualizar
                    "title": bus.title,
                    "year": bus.year,
                    "make": bus.make,
                    "model": bus.model,
                    "body": bus.body,
                    "chassis": bus.chassis,
                    "engine": bus.engine,
                    "transmission": bus.transmission,
                    "mileage": bus.mileage,
                    "passengers": bus.passengers,
                    "wheelchair": bus.wheelchair,
                    "color": bus.color,
                    "interior_color": bus.interior_color,
                    "exterior_color": bus.exterior_color,
                    "gvwr": bus.gvwr,
                    "dimensions": bus.dimensions,
                    "luggage": bus.luggage,
                    "state_bus_standard": bus.state_bus_standard,
                    "airconditioning": bus.airconditioning.value if bus.airconditioning else None,
                    "location": bus.location,
                    "price": price,  # Asegurar que price es una cadena, asignar '0' si es None
                    "vin": bus.vin,
                    "description": bus.description,
                    "source_url": bus.source_url,
                    "contact_email": bus.contact_email,
                    "contact_phone": bus.contact_phone,
                    "us_region": bus.us_region.value if bus.us_region else None,
                }

                buses_data.append(bus_dict)

                # Preparar datos de BusOverview
                for overview in bus.overview:
                    overview_dict = {
                        "bus_id": bus.id,  # Necesita 'id' para la relación
                        "mdesc": overview.mdesc,
                        "intdesc": overview.intdesc,
                        "extdesc": overview.extdesc,
                        "features": overview.features,
                        "specs": overview.specs,
                    }
                    overview_data.append(overview_dict)

                # Preparar datos de BusImage
                for image in bus.images:
                    image_dict = {
                        "bus_id": bus.id,  # Necesita 'id' para la relación
                        "name": image.name,
                        "url": image.url,
                        "description": image.description,
                        "image_index": image.image_index,
                    }
                    images_data.append(image_dict)

            self.logger.info("Data transformation complete.")
            return {
                "buses": buses_data,
                "overview": overview_data,
                "images": images_data,
            }
        except Exception as e:
            self.logger.error(f"Error during data transformation: {e}")
            raise

    def load(self, data: Dict[str, List[dict]]) -> None:
        """Load the transformed data into the database."""
        try:
            self.logger.info("Loading data into the database.")
            # Insert or update buses
            for bus in data["buses"]:
                self.db_manager.insert_or_update_bus(bus)

            # Insert overviews
            self.db_manager.insert_overviews(data["overview"])

            # Insert images
            self.db_manager.insert_images(data["images"])

            self.logger.info("Data successfully loaded into the database.")
        except Exception as e:
            self.logger.error(f"Error during data loading: {e}")
            raise

    def load_to_s3(self, data: Dict[str, List[dict]], bucket_name: str, key: str) -> None:
        """Load the transformed data to an S3 bucket."""
        try:
            self.logger.info(f"Uploading data to S3 bucket: {bucket_name}, key: {key}.")
            self.s3_client.put_object(
                Bucket=bucket_name,
                Key=key,
                Body=json.dumps(data, indent=2),
                ContentType="application/json",
            )
            self.logger.info("Data successfully uploaded to S3.")
        except boto3.exceptions.Boto3Error as e:
            self.logger.error(f"Error uploading data to S3: {e}")
            raise
        except Exception as e:
            self.logger.error(f"Unexpected error during S3 upload: {e}")
            raise

    def run(self):
        """Execute the full ETL pipeline."""
        try:
            self.logger.info("Starting ETL pipeline.")
            extracted_data = self.extract()
            transformed_data = self.transform(extracted_data)
            self.load(transformed_data)
            self.load_to_s3(
                data=transformed_data,
                bucket_name=self.settings.S3_BUCKET_NAME,
                key="scraped_data.json"
            )
            self.logger.info("ETL pipeline completed successfully.")
        except Exception as e:
            self.logger.error(f"ETL pipeline failed: {e}")
            raise