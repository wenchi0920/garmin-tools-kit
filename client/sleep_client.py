import garth
from datetime import datetime, date, timedelta
from typing import List, Optional, Union
from loguru import logger
from .client import Client
from models.sleepModel import SleepData

class SleepClient(Client):
    """
    Garmin Sleep Client to fetch sleep records and scores.
    """
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def get_sleep_data(self, calendar_date: Union[str, date]) -> Optional[SleepData]:
        """
        Get sleep records and scores for a specific date (YYYY-MM-DD).
        """
        if isinstance(calendar_date, date):
            date_str = calendar_date.isoformat()
        else:
            date_str = calendar_date
            
        logger.debug(f"正在獲取睡眠數據: {date_str}")
        try:
            username = garth.client.username
            # Endpoint: /wellness-service/wellness/dailySleepData/<username>
            data = garth.client.connectapi(
                f"/wellness-service/wellness/dailySleepData/{username}", 
                params={"date": date_str}
            )
            if not data or not data.get("dailySleepDTO"):
                logger.warning(f"日期 {date_str} 沒有睡眠資料。")
                return None
            return SleepData(**data)
        except Exception as e:
            logger.error(f"獲取日期 {date_str} 的睡眠數據失敗: {e}")
            return None

    def get_sleep_data_range(self, start_date: Union[str, date], end_date: Union[str, date], show_progress: bool = False) -> List[SleepData]:
        """
        Get sleep data for a date range.
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
            iterable = tqdm(iterable, desc="獲取睡眠數據", unit="天")
            
        for i in iterable:
            current_date = start_date + timedelta(days=i)
            data = self.get_sleep_data(current_date)
            if data:
                results.append(data)
            
        return results
