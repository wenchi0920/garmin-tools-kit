from __future__ import annotations
from typing import Optional, List, Any
from pydantic import BaseModel, ConfigDict, Field
from datetime import date

class BbEvent(BaseModel):
    eventType: Optional[str] = None
    eventStartTimeGmt: Optional[str] = None
    durationInMilliseconds: Optional[int] = None
    bodyBatteryImpact: Optional[int] = None
    shortFeedback: Optional[str] = None

class BbFeedback(BaseModel):
    eventTimestampGmt: Optional[str] = None
    bodyBatteryLevel: Optional[str] = None
    feedbackShortType: Optional[str] = None

class BodyBatteryReport(BaseModel):
    """Garmin Body Battery Daily Report Model"""
    model_config = ConfigDict(populate_by_name=True)
    
    calendarDate: date = Field(alias="date")
    charged: Optional[int] = None
    drained: Optional[int] = None
    startTimestampLocal: Optional[str] = None
    endTimestampLocal: Optional[str] = None
    # Array of [timestamp_ms, value]
    bodyBatteryValuesArray: Optional[List[List[int]]] = None
    bodyBatteryActivityEvent: Optional[List[BbEvent]] = None
    bodyBatteryDynamicFeedbackEvent: Optional[BbFeedback] = None
