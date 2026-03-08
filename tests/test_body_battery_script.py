import os
import sys
import json
import unittest
from unittest.mock import patch, MagicMock
from datetime import date

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from body_battery import main as bb_main

class TestBodyBatteryScript(unittest.TestCase):
    def setUp(self):
        with open(".env_test_bb", "w") as f:
            f.write("GARMIN_USERNAME=testuser\nGARMIN_PASSWORD=testpass\n")

    def tearDown(self):
        if os.path.exists(".env_test_bb"):
            os.remove(".env_test_bb")
        if os.path.exists("test_bb_output.json"):
            os.remove("test_bb_output.json")
        
    @patch('body_battery.BodyBatteryClient')
    @patch('body_battery.parse_args')
    def test_bb_main_single_date(self, mock_parse_args, mock_client_class):
        args = MagicMock()
        args.verbosity = 0
        args.username = None
        args.password = None
        args.env_file = ".env_test_bb"
        args.date = "2026-03-08"
        args.start_date = None
        args.end_date = None
        args.output = "test_bb_output.json"
        args.session = ".garth_test"
        args.summary = False
        mock_parse_args.return_value = args
        
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        
        mock_report = MagicMock()
        mock_report.model_dump.return_value = {"calendarDate": "2026-03-08", "charged": 70}
        mock_client.get_body_battery_report.return_value = mock_report
        
        bb_main()
        
        mock_client_class.assert_called_once_with(email="testuser", password="testpass", session_dir=".garth_test")
        mock_client.get_body_battery_report.assert_called_once_with("2026-03-08")
        
        self.assertTrue(os.path.exists("test_bb_output.json"))
        with open("test_bb_output.json", "r") as f:
            data = json.load(f)
            self.assertEqual(data["data"]["charged"], 70)

    @patch('body_battery.BodyBatteryClient')
    @patch('body_battery.parse_args')
    @patch('builtins.print')
    def test_bb_main_summary(self, mock_print, mock_parse_args, mock_client_class):
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
        
        mock_report = MagicMock()
        mock_report.model_dump.return_value = {
            "calendarDate": "2026-03-08",
            "charged": 80,
            "drained": 30,
            "bodyBatteryActivityEvent": []
        }
        mock_client.get_body_battery_report.return_value = mock_report
        
        bb_main()
        
        self.assertTrue(mock_print.called)

if __name__ == "__main__":
    unittest.main()
