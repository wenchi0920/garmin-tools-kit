
import os
import unittest
from unittest.mock import patch, MagicMock
from workout import main as workout_main
import yaml

class TestWorkoutScript(unittest.TestCase):
    def setUp(self):
        # 建立一個測試用的 DSL 檔案
        self.test_dsl = "tests/test_workout.yaml"
        self.dsl_content = {
            "workouts": [
                {
                    "workoutName": "Test Workout",
                    "sport": "RUNNING",
                    "steps": [{"type": "RUN", "duration": "1km"}]
                }
            ],
            "settings": {"deleteSameNameWorkout": True}
        }
        with open(self.test_dsl, "w") as f:
            yaml.dump(self.dsl_content, f)

    def tearDown(self):
        if os.path.exists(self.test_dsl):
            os.remove(self.test_dsl)

    @patch('workout.WorkoutClient')
    @patch('workout.parse_args')
    def test_workout_list(self, mock_parse_args, mock_client_class):
        args = MagicMock()
        args.verbosity = 0
        args.command = "list"
        args.username = "testuser"
        args.password = "testpass"
        args.env_file = None
        args.session = ".garth_test"
        mock_parse_args.return_value = args
        
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        mock_client.list_workouts.return_value = [
            {"workoutId": "456", "workoutName": "Existing", "sportType": {"sportTypeKey": "RUNNING"}, "createdDate": "2026-03-01"}
        ]
        
        workout_main()
        mock_client.list_workouts.assert_called_once()

    @patch('workout.WorkoutClient')
    @patch('workout.parse_args')
    @patch('workout.WorkoutDSLParser')
    def test_workout_upload_dsl(self, mock_parser_class, mock_parse_args, mock_client_class):
        args = MagicMock()
        args.verbosity = 0
        args.command = "upload"
        args.file = self.test_dsl
        args.username = "testuser"
        args.password = "testpass"
        args.env_file = None
        args.session = ".garth_test"
        mock_parse_args.return_value = args
        
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        mock_client.list_workouts.return_value = [
             {"workoutId": "456", "workoutName": "Test Workout"}
        ]
        mock_client.upload_workout.return_value = {"workoutId": "789", "workoutName": "Test Workout"}
        
        mock_parser = MagicMock()
        mock_parser_class.return_value = mock_parser
        mock_parser.get_all_workouts.return_value = [
            {"workoutName": "Test Workout", "sport": "RUNNING"}
        ]
        
        workout_main()
        
        # 確認因為 deleteSameNameWorkout 為 True，所以呼叫了 delete
        mock_client.delete_workout.assert_called_once_with("456")
        mock_client.upload_workout.assert_called_once()

    @patch('workout.WorkoutClient')
    @patch('workout.parse_args')
    def test_workout_delete(self, mock_parse_args, mock_client_class):
        args = MagicMock()
        args.verbosity = 0
        args.command = "delete"
        args.id = "123"
        args.username = "testuser"
        args.password = "testpass"
        args.env_file = None
        args.session = ".garth_test"
        mock_parse_args.return_value = args
        
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        
        workout_main()
        mock_client.delete_workout.assert_called_once_with("123")

if __name__ == "__main__":
    unittest.main()
