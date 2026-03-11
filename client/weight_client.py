import garth
from datetime import datetime, date, timedelta
from typing import List, Optional, Union
from loguru import logger
from .client import Client
from models.weightModel import WeightEntry, WeightHistory

class WeightClient(Client):
    """
    Garmin Weight Client to fetch weight and body composition data.
    """
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def get_latest_weight(self, calendar_date: Optional[Union[str, date]] = None) -> Optional[WeightEntry]:
        """
        Get the latest weight entry relative to a date.
        """
        if calendar_date is None:
            date_str = date.today().isoformat()
        elif isinstance(calendar_date, date):
            date_str = calendar_date.isoformat()
        else:
            date_str = calendar_date
            
        logger.debug(f"正在獲取最新體重資料 (截至 {date_str})")
        try:
            # Endpoint: /weight-service/weight/latest
            data = garth.client.connectapi("/weight-service/weight/latest", params={"date": date_str})
            self._random_delay()
            if not data:
                return None
            return WeightEntry(**data)
        except Exception as e:
            logger.error(f"獲取最新體重失敗: {e}")
            return None

    def get_weight_history(self, start_date: Union[str, date], end_date: Union[str, date]) -> Optional[WeightHistory]:
        """
        Get weight history for a date range.
        """
        if isinstance(start_date, date): start_date = start_date.isoformat()
        if isinstance(end_date, date): end_date = end_date.isoformat()
            
        logger.debug(f"正在獲取體重歷史: {start_date} 至 {end_date}")
        try:
            # Endpoint: /weight-service/weight/dateRange
            data = garth.client.connectapi(
                "/weight-service/weight/dateRange", 
                params={"startDate": start_date, "endDate": end_date}
            )
            if not data:
                return None
            return WeightHistory(**data)
        except Exception as e:
            logger.error(f"獲取體重歷史失敗: {e}")
            return None

    def upload_weight(self, weight_kg: float, calendar_date: Optional[Union[str, date]] = None) -> bool:
        """
        Upload body weight to Garmin Connect.
        """
        if calendar_date is None:
            date_str = date.today().isoformat()
        elif isinstance(calendar_date, date):
            date_str = calendar_date.isoformat()
        else:
            date_str = calendar_date

        logger.info(f"正在上傳體重資料: {weight_kg} kg (日期: {date_str})")
        try:
            payload = {
                "value": weight_kg,
                "unitKey": "kg",
                "date": date_str
            }
            # Endpoint: /weight-service/weight
            garth.client.connectapi("/weight-service/weight", method="POST", json=payload)
            logger.success(f"體重上傳成功: {weight_kg} kg")
            return True
        except Exception as e:
            logger.error(f"上傳體重失敗: {e}")
            return False