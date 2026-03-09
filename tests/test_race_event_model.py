import pytest
from models.raceEventModel import RaceEventModel, RaceEventListModel

def test_race_event_model_parsing():
    """
    測試從 API 回傳的 JSON 資料解析為 RaceEventModel。
    """
    data = {
        'id': 14947813,
        'eventName': '2024 11th長堤曙光元旦馬拉松',
        'date': '2024-01-01',
        'eventType': 'running',
        'race': True,
        'location': 'Taipei, Taiwan',
        'completionTarget': {
            'value': 5.0,
            'unit': 'kilometer',
            'unitType': 'distance'
        },
        'eventTimeLocal': {
            'startTimeHhMm': '06:00',
            'timeZoneId': 'Asia/Taipei'
        }
    }
    
    event = RaceEventModel.model_validate(data)
    assert event.id == 14947813
    assert event.event_name == '2024 11th長堤曙光元旦馬拉松'
    assert event.date == '2024-01-01'
    assert event.event_type == 'running'
    assert event.race is True
    assert event.completion_target.value == 5.0
    assert event.event_time_local.startTimeHhMm == '06:00'

def test_race_event_list_model():
    """
    測試解析多筆賽事。
    """
    data = [
        {
            'id': 1,
            'eventName': 'Event 1',
            'date': '2024-01-01'
        },
        {
            'id': 2,
            'eventName': 'Event 2',
            'date': '2024-02-01'
        }
    ]
    
    events = [RaceEventModel.model_validate(item) for item in data]
    assert len(events) == 2
    assert events[0].id == 1
    assert events[1].event_name == 'Event 2'
