from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from .models import Base, Bus, BusOverview, BusImage
from config.settings import Settings
import logging

class DatabaseManager:
    """Handles database operations using SQLAlchemy."""

    def __init__(self):
        settings = Settings()
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)
        handler = logging.StreamHandler()
        formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
        handler.setFormatter(formatter)
        if not self.logger.handlers:
            self.logger.addHandler(handler)

        try:
            self.engine = create_engine(
                f"mysql+pymysql://{settings.DB_USER}:{settings.DB_PASSWORD}@{settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}",
                pool_recycle=3600  # Opcional: para manejar conexiones inactivas
            )
            self.logger.info("Database engine created successfully.")
            self.logger.info("Creating tables if they do not exist.")
            Base.metadata.create_all(self.engine)
            self.Session = sessionmaker(bind=self.engine)
        except Exception as e:
            self.logger.error(f"Error initializing DatabaseManager: {e}")
            raise

    def insert_or_update_bus(self, bus_data: dict):
        """
        Insert a new bus or update an existing one based on source_url.

        Args:
            bus_data (dict): Dictionary containing bus data.

        Returns:
            None
        """
        session = self.Session()
        try:
            existing_bus = session.query(Bus).filter_by(source_url=bus_data["source_url"]).first()
            if existing_bus:
                self.logger.info(f"Updating existing bus with source_url: {bus_data['source_url']}")
                # Excluir 'id' si está presente en bus_data
                bus_data.pop("id", None)
                for key, value in bus_data.items():
                    setattr(existing_bus, key, value)
            else:
                self.logger.info(f"Inserting new bus with source_url: {bus_data['source_url']}")
                new_bus = Bus(**bus_data)
                session.add(new_bus)
            session.commit()
            self.logger.info(f"Bus with source_url '{bus_data['source_url']}' processed successfully.")
        except Exception as e:
            session.rollback()
            self.logger.error(f"Error in insert_or_update_bus for source_url '{bus_data.get('source_url', 'UNKNOWN')}': {e}")
            raise e
        finally:
            session.close()
            self.logger.info("Database session closed.")

    def insert_data(self, table_name: str, data: list):
        """
        Insert a list of records into the specified table.

        Args:
            table_name (str): Name of the table (must match SQLAlchemy model).
            data (list): List of dictionaries representing rows to insert.

        Raises:
            Exception: If an error occurs during insertion.
        """
        session = self.Session()
        try:
            if not data:
                self.logger.warning(f"No data provided for table {table_name}. Skipping insertion.")
                return

            model_map = {
                "buses": Bus,
                "buses_overview": BusOverview,
                "buses_images": BusImage
            }

            model = model_map.get(table_name)
            if not model:
                raise ValueError(f"Invalid table name: {table_name}")

            self.logger.info(f"Preparing to insert {len(data)} records into table {table_name}.")

            for record in data:
                # Remove 'id' field if it exists to let the database handle it
                record.pop("id", None)

                if table_name == "buses":
                    self.insert_or_update_bus(record)
                else:
                    obj = model(**record)
                    session.add(obj)

            if table_name != "buses":
                session.commit()
                self.logger.info(f"Data insertion into table {table_name} completed successfully.")
        except Exception as e:
            session.rollback()
            self.logger.error(f"Error inserting data into table {table_name}: {e}")
            raise e
        finally:
            session.close()
            self.logger.info("Database session closed.")

    def insert_overviews(self, overviews: list):
        """
        Insert bus overviews into the buses_overview table.

        Args:
            overviews (list): List of dictionaries representing bus overviews.

        Returns:
            None
        """
        self.insert_data("buses_overview", overviews)

    def insert_images(self, images: list):
        """
        Insert bus images into the buses_images table.

        Args:
            images (list): List of dictionaries representing bus images.

        Returns:
            None
        """
        self.insert_data("buses_images", images)