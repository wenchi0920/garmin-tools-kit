import garth
from datetime import datetime, date, timedelta
from typing import List, Optional, Union
from loguru import logger
from .client import Client
from models.healthSnapshotModel import HealthSnapshot

class HealthSnapshotClient(Client):
    """
    Garmin Health Snapshot Client to fetch 2-minute health snapshot sessions.
    """
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._display_name = None

    def get_display_name(self) -> str:
        """Fetch or return cached display name (GUID)."""
        if self._display_name:
            return self._display_name
        
        logger.debug("正在獲取使用者的 displayName (GUID)...")
        try:
            social = garth.client.connectapi("/userprofile-service/socialProfile")
            self._display_name = social.get("displayName")
            return self._display_name
        except Exception as e:
            logger.error(f"獲取 displayName 失敗: {e}")
            raise

    def get_health_snapshots(self, calendar_date: Union[str, date]) -> List[HealthSnapshot]:
        """
        Get all health snapshots for a specific date (YYYY-MM-DD).
        """
        if isinstance(calendar_date, date):
            date_str = calendar_date.isoformat()
        else:
            date_str = calendar_date

        logger.debug(f"正在獲取健康快照: {date_str}")
        try:
            # Endpoint based on user's curl: /wellnessactivity-service/activity/summary/list
            # We use 'until' to filter by date.
            data = garth.client.connectapi(
                "/wellnessactivity-service/activity/summary/list", 
                params={"limit": 20, "start": 1, "until": date_str}
            )
            self._random_delay()

            if not data or not isinstance(data, list):
                logger.warning(f"日期 {date_str} 沒有健康快照或回傳格式錯誤。")
                return []

            # Filter results that match the exact date
            snapshots = []
            for item in data:
                # Check if the start date matches
                start_time = item.get("startTimeLocal", "")
                if start_time.startswith(date_str):
                    snapshots.append(HealthSnapshot(**item))

            if not snapshots:
                logger.warning(f"日期 {date_str} 在列表中找不到匹配的快照。")

            return snapshots
        except Exception as e:
            logger.error(f"獲取日期 {date_str} 的健康快照失敗: {e}")
            return []


    def get_health_snapshot_range(self, start_date: Union[str, date], end_date: Union[str, date], show_progress: bool = False) -> List[HealthSnapshot]:
        """
        Get health snapshots for a date range.
        """
        if isinstance(start_date, str):
            start_date = date.fromisoformat(start_date)
        if isinstance(end_date, str):
            end_date = date.fromisoformat(end_date)
            
        results = []
        total_days = (end_date - start_date).days + 1
        
        iterable = range(total_days)
        if show_progress:
            from tqdm import tqdm
            iterable = tqdm(iterable, desc="獲取健康快照", unit="天")
            
        for i in iterable:
            current_date = start_date + timedelta(days=i)
            data = self.get_health_snapshots(current_date)
            if data:
                results.extend(data)
            
        return results
