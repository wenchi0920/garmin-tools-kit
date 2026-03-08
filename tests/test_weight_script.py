import os
import sys
import json
import unittest
from unittest.mock import patch, MagicMock
from datetime import date

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from weight import main as weight_main

class TestWeightScript(unittest.TestCase):
    def setUp(self):
        with open(".env_test_weight", "w") as f:
            f.write("GARMIN_USERNAME=testuser\nGARMIN_PASSWORD=testpass\n")

    def tearDown(self):
        if os.path.exists(".env_test_weight"):
            os.remove(".env_test_weight")
        if os.path.exists("test_weight_output.json"):
            os.remove("test_weight_output.json")
        
    @patch('weight.WeightClient')
    @patch('weight.parse_args')
    def test_weight_main_latest(self, mock_parse_args, mock_client_class):
        args = MagicMock()
        args.verbosity = 0
        args.username = None
        args.password = None
        args.env_file = ".env_test_weight"
        args.date = "2026-03-08"
        args.start_date = None
        args.end_date = None
        args.output = "test_weight_output.json"
        args.session = ".garth_test"
        args.summary = False
        args.upload = None # 修正: 顯式設為 None
        mock_parse_args.return_value = args
        
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        
        mock_entry = MagicMock()
        mock_entry.model_dump.return_value = {"weight": 72000.0, "timestamp": 1773011400000}
        mock_client.get_latest_weight.return_value = mock_entry
        
        weight_main()
        
        mock_client_class.assert_called_once_with(email="testuser", password="testpass", session_dir=".garth_test")
        mock_client.get_latest_weight.assert_called_once_with("2026-03-08")
        
        self.assertTrue(os.path.exists("test_weight_output.json"))
        with open("test_weight_output.json", "r") as f:
            data = json.load(f)
            self.assertEqual(data["data"]["weight"], 72000.0)

    @patch('weight.WeightClient')
    @patch('weight.parse_args')
    @patch('builtins.print')
    def test_weight_main_summary(self, mock_print, mock_parse_args, mock_client_class):
        args = MagicMock()
        args.verbosity = 0
        args.username = "user"
        args.password = "pass"
        args.env_file = None
        args.date = "2026-03-08"
        args.start_date = None
        args.end_date = None
        args.output = None
        args.session = ".garth_test"
        args.summary = True
        args.upload = None # 修正: 顯式設為 None
        mock_parse_args.return_value = args
        
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        
        mock_entry = MagicMock()
        mock_entry.model_dump.return_value = {
            "weight": 72000.0,
            "timestamp": 1773011400000,
            "bmi": 23.0
        }
        mock_client.get_latest_weight.return_value = mock_entry
        
        weight_main()
        
        self.assertTrue(mock_print.called)

    @patch('weight.WeightClient')
    @patch('weight.parse_args')
    def test_weight_main_upload(self, mock_parse_args, mock_client_class):
        # 新增: 上傳測試
        args = MagicMock()
        args.verbosity = 0
        args.username = "user"
        args.password = "pass"
        args.env_file = None
        args.date = "2026-03-08"
        args.upload = 72.5
        args.session = ".garth_test"
        mock_parse_args.return_value = args
        
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        mock_client.upload_weight.return_value = True
        
        weight_main()
        
        mock_client.upload_weight.assert_called_once_with(72.5, "2026-03-08")

if __name__ == "__main__":
    unittest.main()
