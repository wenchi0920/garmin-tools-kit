import garth
from datetime import datetime, date, timedelta
from typing import List, Optional, Union
from loguru import logger
from .client import Client
from models.healthModel import HealthSummary

class HealthClient(Client):
    """
    Garmin Health Client to fetch daily summaries.
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

    def get_daily_summary(self, calendar_date: Union[str, date]) -> Optional[HealthSummary]:
        """
        Get daily health summary for a specific date (YYYY-MM-DD).
        """
        if isinstance(calendar_date, date):
            date_str = calendar_date.isoformat()
        else:
            date_str = calendar_date
            
        display_name = self.get_display_name()
        logger.debug(f"正在獲取每日健康摘要: {date_str} (User: {display_name})")
        try:
            # Endpoint: /usersummary-service/usersummary/daily/<displayName>
            data = garth.client.connectapi(
                f"/usersummary-service/usersummary/daily/{display_name}", 
                params={"calendarDate": date_str}
            )
            if not data:
                logger.warning(f"日期 {date_str} 沒有健康摘要資料。")
                return None
            return HealthSummary(**data)
        except Exception as e:
            logger.error(f"獲取日期 {date_str} 的健康摘要失敗: {e}")
            return None

    def get_daily_summaries(self, start_date: Union[str, date], end_date: Union[str, date], show_progress: bool = False) -> List[HealthSummary]:
        """
        Get daily health summaries for a date range.
        """
        if isinstance(start_date, str):
            start_date = date.fromisoformat(start_date)
        if isinstance(end_date, str):
            end_date = date.fromisoformat(end_date)
            
        results = []
        current_date = start_date
        total_days = (end_date - start_date).days + 1
        
        iterable = range(total_days)
        if show_progress:
            from tqdm import tqdm
            iterable = tqdm(iterable, desc="獲取每日摘要", unit="天")
            
        for i in iterable:
            current_date = start_date + timedelta(days=i)
            data = self.get_daily_summary(current_date)
            if data:
                results.append(data)
            
        return results
