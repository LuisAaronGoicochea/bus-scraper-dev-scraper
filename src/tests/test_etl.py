import unittest
from unittest.mock import MagicMock
from src.database.etl import ETL
from src.scraper.models import Bus
from config.settings import Settings

class TestETL(unittest.TestCase):
    def setUp(self):
        """Set up the test case with mocked ETL and settings."""
        self.settings = Settings()
        self.etl = ETL(self.settings)
        self.sample_data = [
            Bus(
                name="Test Bus",
                price=50000,
                year="2020",
                make="Ford",
                model="E450",
                vin="1HGBH41JXMN109186",
                mileage=20000,
                passengers=52,
                wheelchair_accessible=True,
                location="Florida, USA",
                description="Well-maintained bus with low mileage.",
                features=["GPS", "ABS Brakes"],
                specifications={"Engine": "V8", "Transmission": "Automatic"},
                images=[{"url": "http://example.com/image1.jpg", "description": "Front view", "index": 0}]
            )
        ]

    def test_transform(self):
        """Test the transformation step of ETL."""
        transformed = self.etl.transform(self.sample_data)
        self.assertIn("buses", transformed)
        self.assertIn("overview", transformed)
        self.assertIn("images", transformed)
        self.assertEqual(len(transformed["buses"]), 1)
        self.assertEqual(len(transformed["images"]), 1)

    def test_load(self):
        """Test the load step of ETL with mocked DB manager."""
        self.etl.db_manager.insert_data = MagicMock()
        transformed = self.etl.transform(self.sample_data)
        self.etl.load(transformed)
        self.etl.db_manager.insert_data.assert_any_call("buses", transformed["buses"])
        self.etl.db_manager.insert_data.assert_any_call("buses_overview", transformed["overview"])
        self.etl.db_manager.insert_data.assert_any_call("buses_images", transformed["images"])

if __name__ == "__main__":
    unittest.main()