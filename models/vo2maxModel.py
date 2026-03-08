from __future__ import annotations
from typing import Optional, List, Any, Dict
from pydantic import BaseModel, ConfigDict, Field
from datetime import date

class Vo2MaxMetrics(BaseModel):
    """VO2 Max Metric details"""
    model_config = ConfigDict(populate_by_name=True)
    
    calendarDate: date
    vo2MaxPreciseValue: Optional[float] = None
    vo2MaxValue: Optional[float] = None
    fitnessAge: Optional[int] = None

class Vo2MaxEntry(BaseModel):
    """Container for VO2 Max per sport type (generic, cycling)"""
    model_config = ConfigDict(populate_by_name=True)
    
    userId: int
    generic: Optional[Vo2MaxMetrics] = None
    cycling: Optional[Vo2MaxMetrics] = None

class AcuteTrainingLoad(BaseModel):
    acwrStatus: Optional[str] = None
    dailyTrainingLoadAcute: Optional[int] = None
    dailyTrainingLoadChronic: Optional[int] = None
    dailyAcuteChronicWorkloadRatio: Optional[float] = None

class TrainingStatusData(BaseModel):
    calendarDate: date
    trainingStatus: Optional[int] = None
    trainingStatusFeedbackPhrase: Optional[str] = None
    acuteTrainingLoadDTO: Optional[AcuteTrainingLoad] = None

class TrainingStatus(BaseModel):
    """Garmin Training Status Model"""
    model_config = ConfigDict(populate_by_name=True)
    
    mostRecentVO2Max: Optional[Vo2MaxEntry] = None
    mostRecentTrainingStatus: Optional[Dict[str, Any]] = None # Contains complex nested dict with deviceId as key
    
    @property
    def latest_status(self) -> Optional[TrainingStatusData]:
        if not self.mostRecentTrainingStatus:
            return None
        data = self.mostRecentTrainingStatus.get("latestTrainingStatusData", {})
        # Pick the first primary device
        for dev_id, status in data.items():
            if status.get("primaryTrainingDevice"):
                return TrainingStatusData(**status)
        # Fallback to any if no primary
        for dev_id, status in data.items():
            return TrainingStatusData(**status)
        return None
