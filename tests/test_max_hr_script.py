import os
import sys
import json
import unittest
from unittest.mock import patch, MagicMock
from datetime import date

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from max_hr import main as max_hr_main

class TestMaxHrScript(unittest.TestCase):
    def setUp(self):
        with open(".env_test_maxhr", "w") as f:
            f.write("GARMIN_USERNAME=testuser\nGARMIN_PASSWORD=testpass\n")

    def tearDown(self):
        if os.path.exists(".env_test_maxhr"):
            os.remove(".env_test_maxhr")
        if os.path.exists("test_maxhr_output.json"):
            os.remove("test_maxhr_output.json")
        
    @patch('max_hr.MaxHrClient')
    @patch('max_hr.parse_args')
    def test_max_hr_main_flow(self, mock_parse_args, mock_client_class):
        args = MagicMock()
        args.verbosity = 0
        args.username = None
        args.password = None
        args.env_file = ".env_test_maxhr"
        args.date = "2026-03-08"
        args.limit = 5
        args.output = "test_maxhr_output.json"
        args.session = ".garth_test"
        args.summary = False
        mock_parse_args.return_value = args
        
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        
        mock_daily = MagicMock()
        mock_daily.model_dump.return_value = {"observedMaxHr": 185}
        mock_client.get_daily_hr_metrics.return_value = mock_daily
        
        mock_act = MagicMock()
        mock_act.model_dump.return_value = {"maxHr": 167.0}
        mock_client.get_recent_activity_max_hr.return_value = [mock_act]
        
        max_hr_main()
        
        mock_client.get_daily_hr_metrics.assert_called_once_with("2026-03-08")
        mock_client.get_recent_activity_max_hr.assert_called_once_with(limit=5)
        
        self.assertTrue(os.path.exists("test_maxhr_output.json"))
        with open("test_maxhr_output.json", "r") as f:
            data = json.load(f)
            self.assertEqual(data["daily_metrics"]["observedMaxHr"], 185)
            self.assertEqual(data["recent_activities"][0]["maxHr"], 167.0)

    @patch('max_hr.MaxHrClient')
    @patch('max_hr.parse_args')
    @patch('builtins.print')
    def test_max_hr_main_summary(self, mock_print, mock_parse_args, mock_client_class):
        args = MagicMock()
        args.verbosity = 0
        args.username = "user"
        args.password = "pass"
        args.env_file = None
        args.date = "2026-03-08"
        args.limit = 5
        args.output = None
        args.session = ".garth_test"
        args.summary = True
        mock_parse_args.return_value = args
        
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        
        mock_daily = MagicMock()
        mock_daily.model_dump.return_value = {"observedMaxHr": 185, "calendarDate": "2026-03-08"}
        mock_client.get_daily_hr_metrics.return_value = mock_daily
        mock_client.get_recent_activity_max_hr.return_value = []
        
        max_hr_main()
        
        self.assertTrue(mock_print.called)

if __name__ == "__main__":
    unittest.main()
