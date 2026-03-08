import os
import sys
import json
import unittest
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from unittest.mock import patch, MagicMock
from hrv import main as hrv_main

class TestHrvScript(unittest.TestCase):
    def setUp(self):
        with open(".env_test_hrv", "w") as f:
            f.write("GARMIN_USERNAME=testuser\nGARMIN_PASSWORD=testpass\n")

    def tearDown(self):
        if os.path.exists(".env_test_hrv"):
            os.remove(".env_test_hrv")
        if os.path.exists("test_hrv_output.json"):
            os.remove("test_hrv_output.json")
        
    @patch('hrv.HrvClient')
    @patch('hrv.parse_args')
    def test_hrv_main_single_date(self, mock_parse_args, mock_client_class):
        args = MagicMock()
        args.verbosity = 0
        args.username = None
        args.password = None
        args.env_file = ".env_test_hrv"
        args.date = "2026-03-01"
        args.start_date = None
        args.end_date = None
        args.detailed = False
        args.output = "test_hrv_output.json"
        args.session = ".garth_test"
        mock_parse_args.return_value = args
        
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        mock_hrv_data = MagicMock()
        mock_hrv_data.model_dump.return_value = {"mock": "data"}
        mock_client.get_hrv_data.return_value = mock_hrv_data
        
        hrv_main()
        
        mock_client_class.assert_called_once_with(email="testuser", password="testpass", session_dir=".garth_test")
        mock_client.get_hrv_data.assert_called_once_with("2026-03-01")
        
        self.assertTrue(os.path.exists("test_hrv_output.json"))
        with open("test_hrv_output.json", "r") as f:
            data = json.load(f)
            self.assertEqual(data["data"], {"mock": "data"})

    @patch('hrv.HrvClient')
    @patch('hrv.parse_args')
    def test_hrv_main_range_date(self, mock_parse_args, mock_client_class):
        args = MagicMock()
        args.verbosity = 0
        args.username = "user"
        args.password = "pass"
        args.env_file = None
        args.date = "2026-03-01"
        args.start_date = "2026-03-01"
        args.end_date = "2026-03-02"
        args.detailed = False
        args.output = None
        args.session = ".garth_test"
        mock_parse_args.return_value = args
        
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        
        mock_hrv_data1 = MagicMock()
        mock_hrv_data1.model_dump.return_value = {"day": "1"}
        mock_hrv_data2 = MagicMock()
        mock_hrv_data2.model_dump.return_value = {"day": "2"}
        
        mock_client.get_hrv_data_range.return_value = [mock_hrv_data1, mock_hrv_data2]
        
        with patch('builtins.print') as mock_print:
            hrv_main()
        
        mock_client.get_hrv_data_range.assert_called_once_with("2026-03-01", "2026-03-02")
        mock_print.assert_called_once()
        output_str = mock_print.call_args[0][0]
        self.assertIn('"day": "1"', output_str)
        self.assertIn('"day": "2"', output_str)

if __name__ == "__main__":
    unittest.main()
