import garth
from datetime import datetime, date, timedelta
from typing import List, Optional, Union
from loguru import logger
from .client import Client
from models.hrvModel import HrvData

class HrvClient(Client):
    """
    Garmin HRV Client to fetch Heart Rate Variability data.
    """
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def get_hrv_data(self, calendar_date: Union[str, date]) -> Optional[HrvData]:
        """
        Get combined HRV summary and readings for a specific date (YYYY-MM-DD).
        """
        if isinstance(calendar_date, date):
            date_str = calendar_date.isoformat()
        else:
            date_str = calendar_date
            
        logger.debug(f"正在獲取 HRV 資料: {date_str}")
        try:
            # Endpoint: /hrv-service/hrv/<YYYY-MM-DD>
            data = garth.client.connectapi(f"/hrv-service/hrv/{date_str}")
            if not data:
                logger.warning(f"日期 {date_str} 沒有 HRV 資料。")
                return None
            return HrvData(**data)
        except Exception as e:
            logger.error(f"獲取日期 {date_str} 的 HRV 資料失敗: {e}")
            return None

    def get_hrv_data_range(self, start_date: Union[str, date], end_date: Union[str, date], show_progress: bool = False) -> List[HrvData]:
        """
        Get HRV data for a date range.
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
            iterable = tqdm(iterable, desc="獲取 HRV 數據", unit="天")
            
        for i in iterable:
            current_date = start_date + timedelta(days=i)
            data = self.get_hrv_data(current_date)
            if data:
                results.append(data)
            
        return results
