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
        self.engine = create_engine(
            f"mysql+pymysql://{settings.DB_USER}:{settings.DB_PASSWORD}@{settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}"
        )
        self.logger.info("Creating tables if they do not exist.")
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)

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

                # Check for duplicates
                if table_name == "buses":
                    existing = session.query(Bus).filter_by(source_url=record["source_url"]).first()
                    if existing:
                        self.logger.info(f"Record with source_url '{record['source_url']}' already exists. Skipping.")
                        continue

                obj = model(**record)
                session.add(obj)

            session.commit()
            self.logger.info(f"Data insertion into table {table_name} completed successfully.")
        except Exception as e:
            session.rollback()
            self.logger.error(f"Error inserting data into table {table_name}: {e}")
            raise e
        finally:
            session.close()
            self.logger.info("Database session closed.")