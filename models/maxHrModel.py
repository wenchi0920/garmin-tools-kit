from __future__ import annotations
from typing import Optional, List, Any
from pydantic import BaseModel, ConfigDict, Field
from datetime import date

class MaxHrMetrics(BaseModel):
    """Heart Rate metrics from various sources"""
    model_config = ConfigDict(populate_by_name=True)
    
    calendarDate: date
    observedMaxHr: Optional[int] = None
    restingHr: Optional[int] = None
    lactateThresholdHr: Optional[int] = None
    
class ActivityMaxHr(BaseModel):
    """Max HR from a specific activity"""
    activityId: int
    activityName: str
    startTimeLocal: str
    maxHr: float
    averageHr: float
