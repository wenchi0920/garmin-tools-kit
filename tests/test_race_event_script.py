import os
import sys
import unittest
from unittest.mock import patch, MagicMock
import io

# 確保可以匯入根目錄的模組
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from race_event import main as race_event_main

class TestRaceEventScript(unittest.TestCase):
    
    @patch('race_event.RaceEventClient')
    @patch('race_event.parse_args')
    def test_race_event_main_flow(self, mock_parse_args, mock_client_class):
        # 設定 Mock 參數
        args = MagicMock()
        args.verbosity = 0
        args.username = "testuser"
        args.password = "testpass"
        args.env_file = None
        args.date = None
        args.start_date = "2024-01-01"
        args.end_date = "2024-12-31"
        args.summary = False
        args.output = None
        args.directory = "./test_data_race"
        args.session = ".garth_test"
        mock_parse_args.return_value = args
        
        # 設定 Mock Client
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        mock_client.list_events.return_value = [
            {
                "id": 12345,
                "eventName": "Mock Race",
                "date": "2024-06-01",
                "eventType": "running",
                "race": True
            }
        ]
        
        # 執行 main()
        if not os.path.exists(args.directory):
            os.makedirs(args.directory)
            
        try:
            race_event_main()
            
            # 驗證 Client 是否正確初始化與呼叫
            mock_client_class.assert_called_once_with(email="testuser", password="testpass", session_dir=".garth_test")
            mock_client.list_events.assert_called_once_with(start_date="2024-01-01", end_date="2024-12-31")
            
            # 檢查檔案是否產生
            files = os.listdir(args.directory)
            race_files = [f for f in files if f.startswith("race_events_")]
            self.assertTrue(len(race_files) > 0)
            
        finally:
            import shutil
            if os.path.exists(args.directory):
                shutil.rmtree(args.directory)

    @patch('race_event.RaceEventClient')
    @patch('race_event.parse_args')
    @patch('sys.stdout', new_callable=io.StringIO)
    def test_race_event_summary_flag(self, mock_stdout, mock_parse_args, mock_client_class):
        # 設定 Mock 參數，包含 --summary
        args = MagicMock()
        args.verbosity = 0
        args.username = "user"
        args.password = "pass"
        args.env_file = None
        args.date = None
        args.start_date = None
        args.end_date = None
        args.summary = True
        args.output = "./test_output.json"
        args.directory = "./data"
        args.session = ".garth_test"
        mock_parse_args.return_value = args
        
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        mock_client.list_events.return_value = [
            {
                "id": 999,
                "eventName": "Summary Test Race",
                "date": "2026-01-01",
                "eventType": "running",
                "completionTarget": {"value": 10, "unit": "km"}
            }
        ]
        
        try:
            race_event_main()
            
            output = mock_stdout.getvalue()
            self.assertIn("Garmin Race Events Summary", output)
            self.assertIn("Summary Test Race", output)
            self.assertIn("10.0 km", output)
            self.assertTrue(os.path.exists("./test_output.json"))
            
        finally:
            if os.path.exists("./test_output.json"):
                os.remove("./test_output.json")

    @patch('race_event.RaceEventClient')
    @patch('race_event.parse_args')
    def test_race_event_single_date(self, mock_parse_args, mock_client_class):
        # 設定 Mock 參數，使用 -d
        args = MagicMock()
        args.verbosity = 0
        args.username = "user"
        args.password = "pass"
        args.env_file = None
        args.date = "2025-05-20"
        args.start_date = None
        args.end_date = None
        args.summary = False
        args.output = None
        args.directory = "./test_data_race_single"
        args.session = ".garth_test"
        mock_parse_args.return_value = args
        
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        mock_client.list_events.return_value = []
        
        try:
            race_event_main()
            # 驗證 list_events 呼叫時，start_date 與 end_date 均為指定日期
            mock_client.list_events.assert_called_once_with(start_date="2025-05-20", end_date="2025-05-20")
        finally:
            if os.path.exists(args.directory):
                import shutil
                shutil.rmtree(args.directory)

if __name__ == "__main__":
    unittest.main()
