import os
import sys
import json
import unittest
from unittest.mock import patch, MagicMock
from datetime import date

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from vo2max import main as vo2max_main

class TestVo2MaxScript(unittest.TestCase):
    def setUp(self):
        with open(".env_test_vo2", "w") as f:
            f.write("GARMIN_USERNAME=testuser\nGARMIN_PASSWORD=testpass\n")

    def tearDown(self):
        if os.path.exists(".env_test_vo2"):
            os.remove(".env_test_vo2")
        if os.path.exists("test_vo2_output.json"):
            os.remove("test_vo2_output.json")
        
    @patch('vo2max.Vo2MaxClient')
    @patch('vo2max.parse_args')
    def test_vo2_main_flow(self, mock_parse_args, mock_client_class):
        args = MagicMock()
        args.verbosity = 0
        args.username = None
        args.password = None
        args.env_file = ".env_test_vo2"
        args.date = "2026-03-08"
        args.start_date = "2026-01-01"
        args.end_date = None
        args.output = "test_vo2_output.json"
        args.session = ".garth_test"
        args.summary = False
        mock_parse_args.return_value = args
        
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        
        mock_entry = MagicMock()
        mock_entry.model_dump.return_value = {"generic": {"vo2MaxValue": 43.0}}
        mock_client.get_vo2max_history.return_value = [mock_entry]
        
        mock_status = MagicMock()
        mock_status.model_dump.return_value = {"mostRecentVO2Max": {}}
        mock_status.latest_status = None
        mock_client.get_training_status.return_value = mock_status
        
        vo2max_main()
        
        mock_client.get_vo2max_history.assert_called_once_with("2026-01-01", "2026-03-08")
        self.assertTrue(os.path.exists("test_vo2_output.json"))

if __name__ == "__main__":
    unittest.main()
