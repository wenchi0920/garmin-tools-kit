import pytest
from unittest.mock import patch, MagicMock
from client.activity_client import ActivityClient
from client.health_client import HealthClient
from client.workout_client import WorkoutClient

@pytest.fixture
def mock_client_init():
    with patch('client.client.Client.login', return_value=True):
        yield

def test_activity_list_random_delay(mock_client_init):
    """測試抓取活動列表後是否有隨機延遲"""
    client = ActivityClient(email="test@test.com", password="password")
    mock_activities = [{"activityId": 123}]
    with patch('garth.client.connectapi', return_value=mock_activities) as mock_api:
        with patch('time.sleep') as mock_sleep:
            with patch('random.uniform', return_value=1.0):
                client.list_activities(count=1)
                assert mock_api.called
                assert mock_sleep.call_count == 1
                mock_sleep.assert_called_with(1.0)

def test_download_activity_random_delay(mock_client_init):
    """測試下載活動後是否有隨機延遲"""
    client = ActivityClient(email="test@test.com", password="password")
    activity = {"activityId": 123, "startTimeLocal": "2023-01-01 10:00:00", "startTimeGMT": "2023-01-01 02:00:00Z"}
    with patch('garth.client.connectapi', return_value={"id": 123}) as mock_api:
        with patch('time.sleep') as mock_sleep:
            with patch('random.uniform', return_value=1.2):
                with patch('os.path.exists', return_value=False):
                    with patch('os.makedirs'):
                        with patch('builtins.open', MagicMock()):
                            client.download_activity(activity, format="json")
                            assert mock_api.called
                            assert mock_sleep.call_count == 1
                            mock_sleep.assert_called_with(1.2)

def test_workout_list_random_delay(mock_client_init):
    """測試抓取訓練計畫列表後是否有隨機延遲"""
    client = WorkoutClient(email="test@test.com", password="password")
    with patch('garth.client.request') as mock_req:
        mock_req.return_value.json.return_value = []
        with patch('time.sleep') as mock_sleep:
            with patch('random.uniform', return_value=0.5):
                client.list_workouts()
                assert mock_req.called
                assert mock_sleep.call_count == 1
                mock_sleep.assert_called_with(0.5)

def test_health_summary_random_delay(mock_client_init):
    """測試獲取健康摘要後是否有隨機延遲"""
    client = HealthClient(email="test@test.com", password="password")
    with patch.object(HealthClient, 'get_display_name', return_value="user123"):
        with patch('garth.client.connectapi', return_value={"userHash": "abc"}) as mock_api:
            with patch('time.sleep') as mock_sleep:
                with patch('random.uniform', return_value=0.5):
                    client.get_daily_summary("2023-01-01")
                    assert mock_api.called
                    assert mock_sleep.call_count == 1
                    mock_sleep.assert_called_with(0.5)
