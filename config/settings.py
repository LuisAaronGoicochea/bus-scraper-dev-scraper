import os

class Settings:
    """Class to handle application settings and environment variables."""

    # Base URL for scraping
    BASE_URL = "https://www.centralstatesbus.com"

    # AWS Configurations
    S3_BUCKET_NAME = os.getenv("S3_BUCKET")
    AWS_REGION = os.getenv("AWS_REGION", "us-east-1")

    # Database Configurations
    DB_HOST = os.getenv("DB_HOST")
    DB_PORT = int(os.getenv("DB_PORT", 3306))
    DB_NAME = os.getenv("DB_NAME")
    DB_USER = os.getenv("DB_USER")
    DB_PASSWORD = os.getenv("DB_PASSWORD")

    # Debug Mode
    DEBUG = os.getenv("DEBUG", "false").lower() in ("true", "1", "yes")

    @staticmethod
    def validate():
        """Validate required environment variables."""
        required_env_vars = ["S3_BUCKET", "DB_HOST", "DB_NAME", "DB_USER", "DB_PASSWORD"]
        missing_vars = [var for var in required_env_vars if not os.getenv(var)]

        if missing_vars:
            raise RuntimeError(
                f"Missing required environment variables: {', '.join(missing_vars)}\n"
                "Ensure these variables are set in your environment or Lambda configuration."
            )

    def __repr__(self):
        return (
            f"Settings(BASE_URL={self.BASE_URL}, DB_HOST={self.DB_HOST}, DB_PORT={self.DB_PORT}, "
            f"DB_NAME={self.DB_NAME}, DB_USER={self.DB_USER}, AWS_REGION={self.AWS_REGION}, "
            f"S3_BUCKET_NAME={self.S3_BUCKET_NAME}, DEBUG={self.DEBUG})"
        )
