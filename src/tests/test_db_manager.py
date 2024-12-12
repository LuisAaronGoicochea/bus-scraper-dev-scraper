import unittest
from unittest.mock import MagicMock
from src.database.db_manager import DatabaseManager

class TestDatabaseManager(unittest.TestCase):
    def setUp(self):
        """Set up the test case with a mocked database manager."""
        self.db_manager = DatabaseManager()
        self.db_manager.engine = MagicMock()
        self.db_manager.Session = MagicMock()

    def test_insert_data(self):
        """Test the insertion of data into a mocked database table."""
        session_mock = MagicMock()
        self.db_manager.Session.return_value = session_mock

        sample_data = [{"title": "Test Bus", "year": "2020", "make": "Ford"}]
        self.db_manager.insert_data("buses", sample_data)

        session_mock.bulk_save_objects.assert_called_once()
        session_mock.commit.assert_called_once()

    def test_insert_no_data(self):
        """Test insertion with no data provided."""
        session_mock = MagicMock()
        self.db_manager.Session.return_value = session_mock

        self.db_manager.insert_data("buses", [])

        session_mock.bulk_save_objects.assert_not_called()
        session_mock.commit.assert_not_called()

if __name__ == "__main__":
    unittest.main()
