"""
Purpose: Data Transfer Object (DTO) for Garmin Race Events.
Author: Gemini CLI
Changelog:
- 2026-03-09: Updated to match /calendar-service/events response.
"""

from typing import List, Optional, Any, Dict
from pydantic import BaseModel, Field

class CompletionTarget(BaseModel):
    value: Optional[float] = None
    unit: Optional[str] = None
    unitType: Optional[str] = None

class EventTimeLocal(BaseModel):
    startTimeHhMm: Optional[str] = None
    timeZoneId: Optional[str] = None

class LocationStartPoint(BaseModel):
    lat: Optional[float] = None
    lon: Optional[float] = None

class RaceEventModel(BaseModel):
    """
    Garmin Race Event Data Model from calendar-service.
    """
    id: int
    event_name: str = Field(alias="eventName")
    date: str  # Format: YYYY-MM-DD
    url: Optional[str] = None
    registration_url: Optional[str] = Field(None, alias="registrationUrl")
    course_id: Optional[int] = Field(None, alias="courseId")
    completion_target: Optional[CompletionTarget] = Field(None, alias="completionTarget")
    event_time_local: Optional[EventTimeLocal] = Field(None, alias="eventTimeLocal")
    note: Optional[str] = None
    workout_id: Optional[int] = Field(None, alias="workoutId")
    location: Optional[str] = None
    location_start_point: Optional[LocationStartPoint] = Field(None, alias="locationStartPoint")
    event_type: Optional[str] = Field(None, alias="eventType")
    race: Optional[bool] = None
    
    class Config:
        populate_by_name = True

class RaceEventListModel(BaseModel):
    """
    List of Race Events.
    """
    events: List[RaceEventModel]
