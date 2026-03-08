import os
import sys
import unittest
from datetime import date
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from models.vo2maxModel import TrainingStatus, Vo2MaxEntry

class TestVo2MaxModel(unittest.TestCase):
    def test_vo2max_entry_parsing(self):
        mock_json = {
            "userId": 12345,
            "generic": {
                "calendarDate": "2026-03-07",
                "vo2MaxPreciseValue": 42.9,
                "vo2MaxValue": 43.0
            }
        }
        entry = Vo2MaxEntry(**mock_json)
        self.assertEqual(entry.generic.calendarDate, date(2026, 3, 7))
        self.assertEqual(entry.generic.vo2MaxPreciseValue, 42.9)

    def test_training_status_parsing(self):
        mock_json = {
            "userId": 12345,
            "mostRecentTrainingStatus": {
                "latestTrainingStatusData": {
                    "device1": {
                        "calendarDate": "2026-03-08",
                        "trainingStatusFeedbackPhrase": "MAINTAINING",
                        "primaryTrainingDevice": True,
                        "acuteTrainingLoadDTO": {
                            "dailyTrainingLoadAcute": 365
                        }
                    }
                }
            }
        }
        status = TrainingStatus(**mock_json)
        latest = status.latest_status
        self.assertEqual(latest.trainingStatusFeedbackPhrase, "MAINTAINING")
        self.assertEqual(latest.acuteTrainingLoadDTO.dailyTrainingLoadAcute, 365)

if __name__ == "__main__":
    unittest.main()
