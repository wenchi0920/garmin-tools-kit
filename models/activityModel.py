from __future__ import annotations
from typing import Optional, Dict, Any
from pydantic import BaseModel, ConfigDict, field_validator, Field
from datetime import datetime

class ActivityModel(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    
    activityId: int
    activityName: str
    description: Optional[str] = None
    startTimeLocal: str
    startTimeGMT: str
    distance: Optional[float] = None
    duration: Optional[float] = None
    elapsedDuration: Optional[float] = None
    movingDuration: Optional[float] = None
    averageSpeed: Optional[float] = None
    maxSpeed: Optional[float] = None
    calories: Optional[float] = None
    averageHR: Optional[float] = Field(None, alias="averageHR")
    maxHR: Optional[float] = Field(None, alias="maxHR")
    
    @field_validator("startTimeLocal", "startTimeGMT", mode="before")
    @classmethod
    def normalize_garmin_date(cls, v: Any) -> str:
        """解析與標準化 Garmin 日期字串。"""
        if not isinstance(v, str):
            return str(v)
        return v
