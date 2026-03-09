import os
import sys
import unittest
from datetime import date
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from models.maxHrModel import MaxHrMetrics, ActivityMaxHr

class TestMaxHrModel(unittest.TestCase):
    def test_daily_hr_metrics_parsing(self):
        mock_json = {
            "calendarDate": "2026-03-08",
            "observedMaxHr": 185,
            "restingHr": 55,
            "lactateThresholdHr": 174
        }
        metrics = MaxHrMetrics(**mock_json)
        self.assertEqual(metrics.calendarDate, date(2026, 3, 8))
        self.assertEqual(metrics.observedMaxHr, 185)
        self.assertEqual(metrics.restingHr, 55)
        self.assertEqual(metrics.lactateThresholdHr, 174)

    def test_activity_max_hr_parsing(self):
        mock_json = {
            "activityId": 123456789,
            "activityName": "Test Run",
            "startTimeLocal": "2026-03-07 20:47:38",
            "maxHr": 167.0,
            "averageHr": 156.0
        }
        activity = ActivityMaxHr(**mock_json)
        self.assertEqual(activity.activityId, 123456789)
        self.assertEqual(activity.maxHr, 167.0)

if __name__ == "__main__":
    unittest.main()
