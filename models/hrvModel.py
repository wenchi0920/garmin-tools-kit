from __future__ import annotations
from typing import Optional, List, Any
from pydantic import BaseModel, ConfigDict, Field
from datetime import date, datetime

class HrvBaseline(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    
    lowUpper: Optional[int] = None
    balancedLow: Optional[int] = None
    balancedUpper: Optional[int] = None
    markerValue: Optional[float] = None

class HrvSummary(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    
    calendarDate: date
    weeklyAvg: Optional[int] = None
    lastNightAvg: Optional[int] = None
    lastNight5MinHigh: Optional[int] = None
    baseline: Optional[HrvBaseline] = None
    status: Optional[str] = None
    feedbackPhrase: Optional[str] = None
    createTimeStamp: Optional[str] = None

class HrvReading(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    
    hrvValue: int
    readingTimeGMT: str
    readingTimeLocal: str

class HrvData(BaseModel):
    """Combined HRV data returned by Garmin endpoint"""
    model_config = ConfigDict(populate_by_name=True)
    
    userProfilePk: int
    hrvSummary: Optional[HrvSummary] = None
    hrvReadings: Optional[List[HrvReading]] = None
    startTimestampGMT: Optional[str] = None
    endTimestampGMT: Optional[str] = None
    startTimestampLocal: Optional[str] = None
    endTimestampLocal: Optional[str] = None
    sleepStartTimestampGMT: Optional[str] = None
    sleepEndTimestampGMT: Optional[str] = None
    sleepStartTimestampLocal: Optional[str] = None
    sleepEndTimestampLocal: Optional[str] = None
