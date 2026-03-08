import os
import sys
import json
import unittest
from unittest.mock import patch, MagicMock
from datetime import date

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from health import main as health_main

class TestHealthScript(unittest.TestCase):
    def setUp(self):
        with open(".env_test_health", "w") as f:
            f.write("GARMIN_USERNAME=testuser\nGARMIN_PASSWORD=testpass\n")

    def tearDown(self):
        if os.path.exists(".env_test_health"):
            os.remove(".env_test_health")
        if os.path.exists("test_health_output.json"):
            os.remove("test_health_output.json")
        
    @patch('health.HealthClient')
    @patch('health.parse_args')
    def test_health_main_single_date(self, mock_parse_args, mock_client_class):
        args = MagicMock()
        args.verbosity = 0
        args.username = None
        args.password = None
        args.env_file = ".env_test_health"
        args.date = "2026-03-08"
        args.start_date = None
        args.end_date = None
        args.output = "test_health_output.json"
        args.session = ".garth_test"
        args.summary = False
        mock_parse_args.return_value = args
        
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        
        mock_health_data = MagicMock()
        mock_health_data.model_dump.return_value = {"calendarDate": "2026-03-08"}
        mock_client.get_daily_summary.return_value = mock_health_data
        
        health_main()
        
        mock_client_class.assert_called_once_with(email="testuser", password="testpass", session_dir=".garth_test")
        mock_client.get_daily_summary.assert_called_once_with("2026-03-08")
        
        self.assertTrue(os.path.exists("test_health_output.json"))
        with open("test_health_output.json", "r") as f:
            data = json.load(f)
            self.assertEqual(data["data"]["calendarDate"], "2026-03-08")

    @patch('health.HealthClient')
    @patch('health.parse_args')
    @patch('builtins.print')
    def test_health_main_summary(self, mock_print, mock_parse_args, mock_client_class):
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
        mock_parse_args.return_value = args
        
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        
        mock_health_data = MagicMock()
        mock_health_data.model_dump.return_value = {
            "calendarDate": "2026-03-08",
            "totalSteps": 8000,
            "totalKilocalories": 2000
        }
        mock_client.get_daily_summary.return_value = mock_health_data
        
        health_main()
        
        # 驗證 print 是否被呼叫（摘要模式會輸出格式化資料）
        self.assertTrue(mock_print.called)

if __name__ == "__main__":
    unittest.main()
