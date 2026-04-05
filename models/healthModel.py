from __future__ import annotations
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, ConfigDict, Field
from datetime import date

class BodyBatteryEvent(BaseModel):
    eventType: Optional[str] = None
    eventStartTimeGmt: Optional[str] = None
    bodyBatteryImpact: Optional[int] = None
    shortFeedback: Optional[str] = None

class HealthSummary(BaseModel):
    """Garmin Daily Health Summary Model"""
    model_config = ConfigDict(populate_by_name=True)
    
    calendarDate: date
    # Calories
    totalKilocalories: Optional[float] = None
    activeKilocalories: Optional[float] = None
    bmrKilocalories: Optional[float] = None
    # Steps & Distance
    totalSteps: Optional[int] = None
    totalDistanceMeters: Optional[int] = None
    floorsAscended: Optional[float] = None
    dailyStepGoal: Optional[int] = None
    # Heart Rate
    minHeartRate: Optional[int] = None
    maxHeartRate: Optional[int] = None
    restingHeartRate: Optional[int] = None
    lastSevenDaysAvgRestingHeartRate: Optional[int] = None
    # Stress
    averageStressLevel: Optional[int] = None
    maxStressLevel: Optional[int] = None
    stressPercentage: Optional[float] = None
    restStressPercentage: Optional[float] = None
    # Body Battery
    bodyBatteryHighestValue: Optional[int] = None
    bodyBatteryLowestValue: Optional[int] = None
    bodyBatteryMostRecentValue: Optional[int] = None
    bodyBatteryDuringSleep: Optional[int] = None
    # SpO2 & Respiration
    averageSpo2: Optional[float] = None
    lowestSpo2: Optional[int] = None
    avgWakingRespirationValue: Optional[float] = None
    # Intensity Minutes
    intensityMinutesGoal: Optional[int] = None
    activeIntensityMinutes: Optional[int] = None
    moderateIntensityMinutes: Optional[int] = None
    vigorousIntensityMinutes: Optional[int] = None
    # Events
    bodyBatteryActivityEventList: Optional[List[BodyBatteryEvent]] = None
