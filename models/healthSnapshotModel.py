from __future__ import annotations
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, ConfigDict, Field
from datetime import date

class HealthSnapshotSummary(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    
    averageHeartRate: Optional[int] = None
    averageStress: Optional[int] = None
    averageRespiration: Optional[float] = None
    averageSpo2: Optional[float] = None
    averageHrvRmssd: Optional[int] = None
    averageHrvSdnn: Optional[int] = None

class HealthSnapshot(BaseModel):
    """Garmin Health Snapshot Model"""
    model_config = ConfigDict(populate_by_name=True)
    
    snapshotId: Optional[int] = None
    startTimeLocal: Optional[str] = None
    startTimeGmt: Optional[str] = None
    endTimeLocal: Optional[str] = None
    endTimeGmt: Optional[str] = None
    summary: Optional[HealthSnapshotSummary] = None
