import os
import sys
import unittest
from datetime import date
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from models.weightModel import WeightEntry, WeightHistory

class TestWeightModel(unittest.TestCase):
    def test_weight_entry_parsing(self):
        mock_json = {
            "date": 1773011400000,
            "weight": 72000.0,
            "bmi": 23.5,
            "bodyFat": 18.2,
            "sourceType": "MANUAL"
        }
        
        entry = WeightEntry(**mock_json)
        
        self.assertEqual(entry.weight, 72000.0)
        self.assertEqual(entry.weight_kg, 72.0)
        self.assertEqual(entry.bmi, 23.5)
        self.assertEqual(entry.calendarDate, date(2026, 3, 9))

if __name__ == "__main__":
    unittest.main()
