import unittest
from src.scraper.main_scraper import BusScraper
from config.settings import Settings

class TestBusScraper(unittest.TestCase):
    def setUp(self):
        """Set up the test case with a scraper instance."""
        self.settings = Settings()
        self.scraper = BusScraper(self.settings.BASE_URL)

    def test_fetch_data(self):
        """Test that data is fetched from the source URL."""
        html = self.scraper.fetch_data()
        self.assertTrue(html.startswith("<!DOCTYPE html>"), "HTML content should start with DOCTYPE.")

    def test_parse_data(self):
        """Test that the scraper parses bus data correctly."""
        html = self.scraper.fetch_data()
        buses = self.scraper.parse_data(html)
        self.assertIsInstance(buses, list, "Parsed data should be a list.")
        self.assertTrue(len(buses) > 0, "There should be at least one bus parsed.")
        self.assertTrue(all(hasattr(bus, 'name') for bus in buses), "Each bus should have a 'name' attribute.")

if __name__ == "__main__":
    unittest.main()
