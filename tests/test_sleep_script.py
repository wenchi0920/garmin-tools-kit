import os
import sys
import json
import unittest
from unittest.mock import patch, MagicMock
from datetime import date

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from sleep import main as sleep_main

class TestSleepScript(unittest.TestCase):
    def setUp(self):
        with open(".env_test_sleep", "w") as f:
            f.write("GARMIN_USERNAME=testuser\nGARMIN_PASSWORD=testpass\n")

    def tearDown(self):
        if os.path.exists(".env_test_sleep"):
            os.remove(".env_test_sleep")
        if os.path.exists("test_sleep_output.json"):
            os.remove("test_sleep_output.json")
        
    @patch('sleep.SleepClient')
    @patch('sleep.parse_args')
    def test_sleep_main_single_date(self, mock_parse_args, mock_client_class):
        args = MagicMock()
        args.verbosity = 0
        args.username = None
        args.password = None
        args.env_file = ".env_test_sleep"
        args.date = "2026-03-08"
        args.start_date = None
        args.end_date = None
        args.output = "test_sleep_output.json"
        args.session = ".garth_test"
        args.summary = False
        mock_parse_args.return_value = args
        
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        
        mock_sleep_data = MagicMock()
        mock_sleep_data.model_dump.return_value = {"dailySleepDTO": {"calendarDate": "2026-03-08"}}
        mock_client.get_sleep_data.return_value = mock_sleep_data
        
        sleep_main()
        
        mock_client_class.assert_called_once_with(email="testuser", password="testpass", session_dir=".garth_test")
        mock_client.get_sleep_data.assert_called_once_with("2026-03-08")
        
        self.assertTrue(os.path.exists("test_sleep_output.json"))
        with open("test_sleep_output.json", "r") as f:
            data = json.load(f)
            self.assertEqual(data["data"]["dailySleepDTO"]["calendarDate"], "2026-03-08")

    @patch('sleep.SleepClient')
    @patch('sleep.parse_args')
    @patch('builtins.print')
    def test_sleep_main_summary(self, mock_print, mock_parse_args, mock_client_class):
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
        
        mock_sleep_data = MagicMock()
        # 建立一個包含基本欄位的字典，供 print_sleep_summary 讀取
        mock_sleep_data.model_dump.return_value = {
            "dailySleepDTO": {
                "calendarDate": "2026-03-08",
                "sleepTimeSeconds": 28800,
                "sleepScores": {"overall": {"value": 85, "qualifierKey": "GOOD"}}
            }
        }
        mock_client.get_sleep_data.return_value = mock_sleep_data
        
        sleep_main()
        
        # 驗證 print 是否被呼叫（摘要模式會輸出格線與資料）
        self.assertTrue(mock_print.called)

if __name__ == "__main__":
    unittest.main()
