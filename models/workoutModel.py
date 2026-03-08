from __future__ import annotations
from typing import List, Optional, Union, Dict, Any, Literal, Annotated
from pydantic import BaseModel, Field, ConfigDict, Discriminator

class ExecutableStepDTO(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    
    type: Literal["ExecutableStepDTO"] = "ExecutableStepDTO"
    stepId: Optional[int] = None
    stepOrder: int
    childStepId: Optional[int] = None
    description: Optional[str] = None
    endCondition: Dict[str, Any]
    endConditionValue: Optional[float] = None
    targetType: Dict[str, Any]
    targetValueOne: Optional[float] = None
    targetValueTwo: Optional[float] = None
    zoneNumber: Optional[int] = None
    secondaryTargetType: Optional[Dict[str, Any]] = None
    secondaryTargetValueOne: Optional[float] = None
    secondaryTargetValueTwo: Optional[float] = None
    secondaryZoneNumber: Optional[int] = None
    strokeType: Optional[Dict[str, Any]] = None
    equipmentType: Optional[Dict[str, Any]] = None
    category: Optional[str] = None
    exerciseName: Optional[str] = None
    weightValue: Optional[float] = None
    weightUnit: Optional[str] = None
    stepType: Dict[str, Any]

class RepeatGroupDTO(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    
    type: Literal["RepeatGroupDTO"] = "RepeatGroupDTO"
    stepId: Optional[int] = None
    stepOrder: int
    stepType: Dict[str, Any]
    childStepId: Optional[int] = None
    numberOfIterations: int
    workoutSteps: List[WorkoutStepUnion]
    endCondition: Dict[str, Any]
    endConditionValue: Optional[float] = None
    smartRepeat: bool = False

WorkoutStepUnion = Annotated[Union[ExecutableStepDTO, RepeatGroupDTO], Discriminator("type")]

class WorkoutSegment(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    segmentOrder: int
    sportType: Dict[str, Any]
    workoutSteps: List[WorkoutStepUnion]

class WorkoutModel(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    
    workoutId: Optional[int] = None
    workoutName: str
    sportType: Dict[str, Any]
    workoutSegments: List[WorkoutSegment]

# Need to update RepeatGroupDTO for self-reference
RepeatGroupDTO.model_rebuild()
