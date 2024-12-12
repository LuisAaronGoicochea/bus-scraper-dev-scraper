from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from config.settings import Settings
import logging

class DatabaseConnection:
    """
    Handles the connection to the MySQL database using SQLAlchemy.
    """

    def __init__(self):
        settings = Settings()
        self.logger = logging.getLogger(__name__)
        try:
            self.engine = create_engine(
                f"mysql+pymysql://{settings.DB_USER}:{settings.DB_PASSWORD}@{settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}"
            )
            self.Session = sessionmaker(bind=self.engine)
            self.logger.info("Database engine successfully created.")
        except Exception as e:
            self.logger.error(f"Error creating database connection: {e}")
            raise

    def get_session(self):
        """
        Get a new database session.

        Returns:
            session: A SQLAlchemy database session.
        """
        try:
            self.logger.info("Creating a new database session.")
            return self.Session()
        except Exception as e:
            self.logger.error(f"Error creating database session: {e}")
            raise

    def test_connection(self):
        """
        Test the database connection.

        Returns:
            bool: True if the connection is successful, False otherwise.
        """
        try:
            with self.engine.connect() as connection:
                self.logger.info("Database connection successful.")
                return True
        except Exception as e:
            self.logger.error(f"Database connection failed: {e}")
            return False