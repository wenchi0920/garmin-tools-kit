from .client import Client
from .activity_client import ActivityClient
from .workout_client import WorkoutClient
from .workout_parser import WorkoutDSLParser
from .hrv_client import HrvClient
from .sleep_client import SleepClient
from .health_client import HealthClient
from .body_battery_client import BodyBatteryClient
from .weight_client import WeightClient
from .vo2max_client import Vo2MaxClient
from .max_hr_client import MaxHrClient
from .race_event_client import RaceEventClient

VERSION = "1.5.3"


__all__ = ["Client", "ActivityClient", "WorkoutClient", "WorkoutDSLParser", "HrvClient", "SleepClient", "HealthClient", "BodyBatteryClient", "WeightClient", "Vo2MaxClient", "MaxHrClient", "RaceEventClient", "VERSION"]
