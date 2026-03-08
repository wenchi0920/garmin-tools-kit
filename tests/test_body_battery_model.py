import os
import sys
import unittest
from datetime import date
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from models.bodyBatteryModel import BodyBatteryReport

class TestBodyBatteryModel(unittest.TestCase):
    def test_bb_report_parsing(self):
        mock_json = {
            "date": "2026-03-08",
            "charged": 78,
            "drained": 24,
            "bodyBatteryValuesArray": [[1772899560000, 5], [1772915400000, 52]],
            "bodyBatteryActivityEvent": [
                {
                    "eventType": "SLEEP",
                    "bodyBatteryImpact": 67,
                    "durationInMilliseconds": 24360000
                }
            ]
        }
        
        report = BodyBatteryReport(**mock_json)
        
        self.assertEqual(report.calendarDate, date(2026, 3, 8))
        self.assertEqual(report.charged, 78)
        self.assertEqual(len(report.bodyBatteryValuesArray), 2)
        self.assertEqual(report.bodyBatteryActivityEvent[0].eventType, "SLEEP")
        self.assertEqual(report.bodyBatteryActivityEvent[0].bodyBatteryImpact, 67)

if __name__ == "__main__":
    unittest.main()
