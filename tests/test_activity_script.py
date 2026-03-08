import os
import sys
import unittest
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from unittest.mock import patch, MagicMock
from activity import main as activity_main

class TestActivityScript(unittest.TestCase):
    def setUp(self):
        # 準備暫時的 .env 檔案
        with open(".env_test", "w") as f:
            f.write("GARMIN_USERNAME=testuser\nGARMIN_PASSWORD=testpass\n")

    def tearDown(self):
        if os.path.exists(".env_test"):
            os.remove(".env_test")
        # 清理可能產生的 data 目錄 (測試中會 mock)
        
    @patch('activity.ActivityClient')
    @patch('activity.parse_args')
    @patch('activity.tqdm')
    def test_activity_main_flow(self, mock_tqdm, mock_parse_args, mock_client_class):
        # 設定 tqdm Mock 使其回傳第一個參數 (activities)
        mock_tqdm.side_effect = lambda x, **kwargs: x
        # 設定 Mock 參數
        args = MagicMock()
        args.verbosity = 0
        args.username = None
        args.password = None
        args.env_file = ".env_test"
        args.count = "1"
        args.start_date = None
        args.end_date = None
        args.format = "original"
        args.directory = "./test_data"
        args.originaltime = False
        args.desc = None
        args.session = ".garth_test"
        mock_parse_args.return_value = args
        
        # 設定 Mock Client
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        mock_client.list_activities.return_value = [
            {"activityId": "123", "activityName": "Test Run", "startTimeLocal": "2026-03-08 10:00:00"}
        ]
        
        # 執行 main()
        with patch('builtins.input', side_effect=["testuser"]), \
             patch('getpass.getpass', side_effect=["testpass"]):
            activity_main()
            
        # 驗證 Client 是否正確初始化與呼叫
        mock_client_class.assert_called_once_with(email="testuser", password="testpass", session_dir=".garth_test")
        mock_client.list_activities.assert_called_once_with(count="1", start_date=None, end_date=None)
        mock_client.download_activity.assert_called_once()
        
    @patch('activity.ActivityClient')
    @patch('activity.parse_args')
    def test_activity_no_results(self, mock_parse_args, mock_client_class):
        # 設定 Mock 參數
        args = MagicMock()
        args.verbosity = 0
        args.username = "user"
        args.password = "pass"
        args.env_file = None
        args.count = "1"
        args.start_date = None
        args.end_date = None
        args.format = "original"
        args.directory = "./test_data"
        args.originaltime = False
        args.desc = None
        args.session = ".garth_test"
        mock_parse_args.return_value = args
        
        # 設定 Mock Client 回傳空列表
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        mock_client.list_activities.return_value = []
        
        # 執行 main() 並確認不會報錯
        activity_main()
        
        # 驗證沒呼叫 download_activity
        mock_client.download_activity.assert_not_called()

if __name__ == "__main__":
    unittest.main()
