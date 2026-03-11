import garth
from datetime import datetime, date, timedelta
from typing import List, Optional, Union, Dict
from loguru import logger
from .client import Client
from models.maxHrModel import MaxHrMetrics, ActivityMaxHr

class MaxHrClient(Client):
    """
    Garmin Heart Rate Metrics Client.
    """
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def get_daily_hr_metrics(self, calendar_date: Union[str, date]) -> Optional[MaxHrMetrics]:
        """
        Get daily heart rate metrics (Observed Max, Resting HR).
        """
        if isinstance(calendar_date, date):
            date_str = calendar_date.isoformat()
        else:
            date_str = calendar_date
            
        logger.debug(f"正在獲取每日心率指標: {date_str}")
        try:
            display_name = self.get_display_name()
            # Endpoint: /wellness-service/wellness/dailyHeartRate/<displayName>
            data = garth.client.connectapi(f"/wellness-service/wellness/dailyHeartRate/{display_name}", params={"date": date_str})
            self._random_delay()
            
            # Also fetch lactate threshold from profile
            profile = garth.client.connectapi("/userprofile-service/userprofile/personal-information")
            self._random_delay()
            lt_hr = profile.get("biometricProfile", {}).get("lactateThresholdHeartRate")
            
            return MaxHrMetrics(
                calendarDate=date.fromisoformat(date_str),
                observedMaxHr=data.get("maxHeartRate"),
                restingHr=data.get("restingHeartRate"),
                lactateThresholdHr=lt_hr
            )
        except Exception as e:
            logger.error(f"獲取日期 {date_str} 的心率指標失敗: {e}")
            return None

    def get_display_name(self) -> str:
        """Fetch or return cached display name (GUID)."""
        try:
            social = garth.client.connectapi("/userprofile-service/socialProfile")
            return social.get("displayName")
        except Exception as e:
            logger.error(f"獲取 displayName 失敗: {e}")
            raise

    def get_recent_activity_max_hr(self, limit: int = 5) -> List[ActivityMaxHr]:
        """
        Get max heart rate from recent activities.
        """
        logger.debug(f"正在獲取最近 {limit} 筆活動的心率紀錄...")
        try:
            activities = garth.client.connectapi("/activitylist-service/activities/search/activities", params={"limit": limit})
            results = []
            for act in activities:
                if act.get("maxHR"):
                    results.append(ActivityMaxHr(
                        activityId=act.get("activityId"),
                        activityName=act.get("activityName"),
                        startTimeLocal=act.get("startTimeLocal"),
                        maxHr=act.get("maxHR"),
                        averageHr=act.get("averageHR")
                    ))
            return results
        except Exception as e:
            logger.error(f"獲取最近活動心率失敗: {e}")
            return []
