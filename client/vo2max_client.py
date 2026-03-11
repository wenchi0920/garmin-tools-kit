import garth
from datetime import datetime, date, timedelta
from typing import List, Optional, Union
from loguru import logger
from .client import Client
from models.vo2maxModel import Vo2MaxEntry, TrainingStatus

class Vo2MaxClient(Client):
    """
    Garmin VO2 Max and Training Status Client.
    """
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def get_vo2max_history(self, start_date: Union[str, date], end_date: Union[str, date]) -> List[Vo2MaxEntry]:
        """
        Get VO2 Max history for a date range.
        """
        if isinstance(start_date, date): start_date = start_date.isoformat()
        if isinstance(end_date, date): end_date = end_date.isoformat()
            
        logger.debug(f"正在獲取 VO2 Max 歷史: {start_date} 至 {end_date}")
        try:
            # Endpoint: /metrics-service/metrics/maxmet/daily/<start>/<end>
            data = garth.client.connectapi(f"/metrics-service/metrics/maxmet/daily/{start_date}/{end_date}")
            self._random_delay()
            if not data:
                return []
            return [Vo2MaxEntry(**item) for item in data]
        except Exception as e:
            logger.error(f"獲取 VO2 Max 歷史失敗: {e}")
            return []

    def get_training_status(self, calendar_date: Optional[Union[str, date]] = None) -> Optional[TrainingStatus]:
        """
        Get the latest training status.
        """
        if calendar_date is None:
            date_str = date.today().isoformat()
        elif isinstance(calendar_date, date):
            date_str = calendar_date.isoformat()
        else:
            date_str = calendar_date
            
        logger.debug(f"正在獲取訓練狀態: {date_str}")
        try:
            # Endpoint: /metrics-service/metrics/trainingstatus/aggregated/<date>
            data = garth.client.connectapi(f"/metrics-service/metrics/trainingstatus/aggregated/{date_str}")
            if not data:
                return None
            return TrainingStatus(**data)
        except Exception as e:
            logger.error(f"獲取訓練狀態失敗: {e}")
            return None
