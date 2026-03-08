import os
import sys
import unittest
from datetime import date
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from models.hrvModel import HrvData, HrvSummary, HrvBaseline, HrvReading

class TestHrvModel(unittest.TestCase):
    def test_hrv_data_parsing(self):
        mock_json = {
            "userProfilePk": 12345,
            "hrvSummary": {
                "calendarDate": "2026-03-01",
                "weeklyAvg": 57,
                "lastNightAvg": 61,
                "baseline": {
                    "lowUpper": 48,
                    "balancedLow": 52,
                    "balancedUpper": 76,
                },
                "status": "BALANCED",
            },
            "hrvReadings": [
                {
                    "hrvValue": 37,
                    "readingTimeGMT": "2026-02-28T15:37:14.0",
                    "readingTimeLocal": "2026-02-28T23:37:14.0"
                }
            ],
            "startTimestampLocal": "2026-02-28T23:35:14.0",
        }
        
        hrv_data = HrvData(**mock_json)
        
        self.assertEqual(hrv_data.userProfilePk, 12345)
        self.assertEqual(hrv_data.hrvSummary.calendarDate, date(2026, 3, 1))
        self.assertEqual(hrv_data.hrvSummary.weeklyAvg, 57)
        self.assertEqual(hrv_data.hrvSummary.baseline.balancedLow, 52)
        self.assertEqual(hrv_data.hrvSummary.status, "BALANCED")
        self.assertEqual(len(hrv_data.hrvReadings), 1)
        self.assertEqual(hrv_data.hrvReadings[0].hrvValue, 37)
        self.assertEqual(hrv_data.startTimestampLocal, "2026-02-28T23:35:14.0")

if __name__ == "__main__":
    unittest.main()
