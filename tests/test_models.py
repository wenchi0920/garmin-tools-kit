import pytest
from models.raceEventModel import RaceEventModel
from pydantic import ValidationError

def test_race_event_model_validation():
    raw_data = {
        "id": 12345,
        "date": "2026-12-31",
        "eventName": "Taipei Marathon",
        "eventType": "running",
        "distance": 42195,
        "location": "Taipei",
        "completionTarget": {"value": 3.5, "unit": "hour"}
    }
    event = RaceEventModel.model_validate(raw_data)
    assert event.id == 12345
    assert event.event_name == "Taipei Marathon"
    assert event.event_date.isoformat() == "2026-12-31"

def test_invalid_date_validation():
    raw_data = {
        "id": 123,
        "date": "invalid-date",
        "eventName": "Bad Date Test"
    }
    with pytest.raises(ValidationError):
        RaceEventModel.model_validate(raw_data)
