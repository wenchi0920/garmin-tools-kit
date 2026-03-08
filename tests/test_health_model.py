import os
import sys
import unittest
from datetime import date
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from models.healthModel import HealthSummary

class TestHealthModel(unittest.TestCase):
    def test_health_data_parsing(self):
        mock_json = {
            "calendarDate": "2026-03-08",
            "totalKilocalories": 2500.5,
            "totalSteps": 10000,
            "restingHeartRate": 55,
            "averageStressLevel": 25,
            "bodyBatteryHighestValue": 100,
            "bodyBatteryLowestValue": 20,
            "averageSpo2": 95.5
        }
        
        health_data = HealthSummary(**mock_json)
        
        self.assertEqual(health_data.calendarDate, date(2026, 3, 8))
        self.assertEqual(health_data.totalKilocalories, 2500.5)
        self.assertEqual(health_data.totalSteps, 10000)
        self.assertEqual(health_data.restingHeartRate, 55)
        self.assertEqual(health_data.averageStressLevel, 25)
        self.assertEqual(health_data.bodyBatteryHighestValue, 100)
        self.assertEqual(health_data.averageSpo2, 95.5)

if __name__ == "__main__":
    unittest.main()
