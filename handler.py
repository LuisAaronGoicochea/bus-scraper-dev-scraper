import json
import logging
from src.database.etl import ETL
from config.settings import Settings

def initialize_logger():
    """Initialize the logger for CloudWatch."""
    logger = logging.getLogger()
    if not logger.hasHandlers():
        # Use a StreamHandler for Lambda logging (CloudWatch compatible)
        stream_handler = logging.StreamHandler()
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        stream_handler.setFormatter(formatter)
        logger.addHandler(stream_handler)
    logger.setLevel(logging.INFO)
    return logger

def lambda_handler(event, context):
    """
    AWS Lambda entry point to orchestrate the ETL process.
    """
    logger = initialize_logger()
    logger.info("Lambda function invoked.")

    try:
        settings = Settings()
        settings.validate()  # Asegurarse de validar las configuraciones

        etl = ETL(settings)

        # Step 1: Extract data
        logger.info("Starting extraction phase.")
        extracted_data = etl.extract()

        # Step 2: Transform data
        logger.info("Starting transformation phase.")
        transformed_data = etl.transform(extracted_data)

        # Step 3: Load data into the database
        logger.info("Starting loading phase.")
        etl.load(transformed_data)

        # Step 4: Always upload data to S3
        logger.info("Uploading transformed data to S3.")
        etl.load_to_s3(
            data=transformed_data,
            bucket_name=settings.S3_BUCKET_NAME,
            key="scraped_data.json"
        )

        logger.info("ETL process completed successfully.")
        return {
            "statusCode": 200,
            "body": json.dumps({"message": "ETL process completed successfully."})
        }

    except Exception as e:
        logger.error(f"Unhandled error: {e}")
        return {
            "statusCode": 500,
            "body": json.dumps({"error": str(e)})
        }