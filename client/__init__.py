from .client import Client
from .activity_client import ActivityClient
from .workout_client import WorkoutClient
from .workout_parser import WorkoutDSLParser

VERSION = "1.1.0"

__all__ = ["Client", "ActivityClient", "WorkoutClient", "WorkoutDSLParser", "VERSION"]
