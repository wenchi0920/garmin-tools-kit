from __future__ import annotations
from typing import Optional, List, Any
from pydantic import BaseModel, ConfigDict, Field
from datetime import date, datetime

class WeightEntry(BaseModel):
    """Garmin Weight Entry Model"""
    model_config = ConfigDict(populate_by_name=True)
    
    timestamp: int = Field(alias="date")
    weight: float # in grams
    bmi: Optional[float] = None
    bodyFat: Optional[float] = None
    bodyWater: Optional[float] = None
    boneMass: Optional[float] = None
    muscleMass: Optional[float] = None
    physiqueRating: Optional[float] = None
    visceralFat: Optional[float] = None
    metabolicAge: Optional[float] = None
    sourceType: Optional[str] = None

    @property
    def calendarDate(self) -> date:
        return datetime.fromtimestamp(self.timestamp / 1000).date()

    @property
    def weight_kg(self) -> float:
        return self.weight / 1000.0

class WeightHistory(BaseModel):
    """Garmin Weight History Model (Range)"""
    startDate: date
    endDate: date
    dateWeightList: List[WeightEntry] = Field(default_factory=list)
