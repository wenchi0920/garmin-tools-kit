from __future__ import annotations
from typing import Optional, Dict, List, Any
from pydantic import BaseModel, ConfigDict, Field
from datetime import date

class SleepScoreDetail(BaseModel):
    value: Optional[int] = None
    qualifierKey: Optional[str] = None
    optimalStart: Optional[float] = None
    optimalEnd: Optional[float] = None

class SleepScores(BaseModel):
    overall: Optional[SleepScoreDetail] = None
    totalDuration: Optional[SleepScoreDetail] = None
    stress: Optional[SleepScoreDetail] = None
    awakeCount: Optional[SleepScoreDetail] = None
    remPercentage: Optional[SleepScoreDetail] = None
    restlessness: Optional[SleepScoreDetail] = None
    lightPercentage: Optional[SleepScoreDetail] = None
    deepPercentage: Optional[SleepScoreDetail] = None

class SleepNeed(BaseModel):
    baseline: Optional[int] = None
    actual: Optional[int] = None
    feedback: Optional[str] = None

class DailySleepDTO(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    
    id: Optional[int] = None
    calendarDate: date
    sleepTimeSeconds: Optional[int] = None
    deepSleepSeconds: Optional[int] = None
    lightSleepSeconds: Optional[int] = None
    remSleepSeconds: Optional[int] = None
    awakeSleepSeconds: Optional[int] = None
    averageRespirationValue: Optional[float] = None
    avgSleepStress: Optional[float] = None
    avgHeartRate: Optional[float] = None
    sleepScoreFeedback: Optional[str] = None
    sleepScores: Optional[SleepScores] = None
    sleepNeed: Optional[SleepNeed] = None

class SleepData(BaseModel):
    """Root model for Garmin Sleep Data API"""
    dailySleepDTO: Optional[DailySleepDTO] = None
    avgOvernightHrv: Optional[float] = None
    hrvStatus: Optional[str] = None
    restingHeartRate: Optional[int] = None
