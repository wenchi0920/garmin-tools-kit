import os
import sys
import unittest
from datetime import date
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from models.sleepModel import SleepData

class TestSleepModel(unittest.TestCase):
    def test_sleep_data_parsing(self):
        mock_json = {
            "dailySleepDTO": {
                "id": 1772900718000,
                "calendarDate": "2026-03-08",
                "sleepTimeSeconds": 23686,
                "deepSleepSeconds": 4260,
                "lightSleepSeconds": 16560,
                "remSleepSeconds": 2880,
                "awakeSleepSeconds": 720,
                "sleepScoreFeedback": "POSITIVE_DEEP",
                "sleepScores": {
                    "overall": {"value": 76, "qualifierKey": "FAIR"},
                    "deepPercentage": {"value": 18, "qualifierKey": "EXCELLENT"}
                }
            },
            "avgOvernightHrv": 56.0,
            "hrvStatus": "BALANCED"
        }
        
        sleep_data = SleepData(**mock_json)
        dto = sleep_data.dailySleepDTO
        
        self.assertEqual(dto.calendarDate, date(2026, 3, 8))
        self.assertEqual(dto.sleepTimeSeconds, 23686)
        self.assertEqual(dto.sleepScores.overall.value, 76)
        self.assertEqual(dto.sleepScores.deepPercentage.qualifierKey, "EXCELLENT")
        self.assertEqual(sleep_data.hrvStatus, "BALANCED")

if __name__ == "__main__":
    unittest.main()
