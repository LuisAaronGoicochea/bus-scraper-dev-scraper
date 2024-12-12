import json
import boto3
from typing import List, Dict
from src.scraper.main_scraper import BusScraper
from src.database.models import Bus, BusOverview, BusImage
from src.database.db_manager import DatabaseManager
from src.database.connection import DatabaseConnection
from config.settings import Settings
import logging

class ETL:
    """ETL class to manage the extraction, transformation, and loading of data."""

    def __init__(self, settings: Settings):
        self.settings = settings
        db_connection = DatabaseConnection()
        self.session = db_connection.get_session()
        self.scraper = BusScraper(settings.BASE_URL, self.session)
        self.s3_client = boto3.client("s3", region_name=settings.AWS_REGION)
        self.db_manager = DatabaseManager()
        self.logger = logging.getLogger(__name__)

    def extract(self) -> List[Bus]:
        """Extract data from the source URL using the scraper."""
        try:
            self.logger.info("Starting data extraction from source.")
            html = self.scraper.fetch_data()
            buses = self.scraper.parse_data(html)
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
                # Convert Bus object to dictionary
                bus_dict = {
                    "id": bus.id,
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
                    "location": bus.location,
                    "price": bus.price,
                    "vin": bus.vin,
                    "description": bus.description,
                    "source_url": bus.source_url,  # Incluir source_url
                    "airconditioning": bus.airconditioning.value if bus.airconditioning else None,
                }

                buses_data.append(bus_dict)

                # Prepare overview data
                if bus.overview:  # Verificar que existan datos en `overview`
                    for overview in bus.overview:  # Iterar sobre los elementos de `overview`
                        overview_dict = {
                            "bus_id": bus.id,
                            "mdesc": overview.mdesc,
                            "intdesc": overview.intdesc,
                            "extdesc": overview.extdesc,
                            "features": overview.features,
                            "specs": overview.specs,
                        }
                        overview_data.append(overview_dict)

                # Prepare image data
                for image in bus.images:
                    image_dict = {
                        "bus_id": bus.id,
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
            self.db_manager.insert_data("buses", data["buses"])
            self.db_manager.insert_data("buses_overview", data["overview"])
            self.db_manager.insert_data("buses_images", data["images"])
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
            if self.settings.UPLOAD_TO_S3:
                self.load_to_s3(
                    transformed_data, self.settings.S3_BUCKET_NAME, self.settings.S3_KEY
                )
            self.logger.info("ETL pipeline completed successfully.")
        except Exception as e:
            self.logger.error(f"ETL pipeline failed: {e}")
            raise
