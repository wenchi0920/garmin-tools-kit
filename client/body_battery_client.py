import garth
from datetime import datetime, date, timedelta
from typing import List, Optional, Union
from loguru import logger
from .client import Client
from models.bodyBatteryModel import BodyBatteryReport

class BodyBatteryClient(Client):
    """
    Garmin Body Battery Client to fetch energy levels and events.
    """
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def get_body_battery_report(self, calendar_date: Union[str, date]) -> Optional[BodyBatteryReport]:
        """
        Get daily Body Battery report for a specific date (YYYY-MM-DD).
        """
        if isinstance(calendar_date, date):
            date_str = calendar_date.isoformat()
        else:
            date_str = calendar_date
            
        logger.debug(f"正在獲取 Body Battery 報告: {date_str}")
        try:
            # Endpoint: /wellness-service/wellness/bodyBattery/reports/daily
            data = garth.client.connectapi(
                "/wellness-service/wellness/bodyBattery/reports/daily", 
                params={"startDate": date_str, "endDate": date_str}
            )
            if not data or not isinstance(data, list):
                logger.warning(f"日期 {date_str} 沒有 Body Battery 報告。")
                return None
            return BodyBatteryReport(**data[0])
        except Exception as e:
            logger.error(f"獲取日期 {date_str} 的 Body Battery 報告失敗: {e}")
            return None

    def get_body_battery_reports(self, start_date: Union[str, date], end_date: Union[str, date]) -> List[BodyBatteryReport]:
        """
        Get Body Battery reports for a date range.
        Note: The API supports ranges directly.
        """
        if isinstance(start_date, date): start_date = start_date.isoformat()
        if isinstance(end_date, date): end_date = end_date.isoformat()
            
        logger.debug(f"正在獲取 Body Battery 報告區間: {start_date} 至 {end_date}")
        try:
            data = garth.client.connectapi(
                "/wellness-service/wellness/bodyBattery/reports/daily", 
                params={"startDate": start_date, "endDate": end_date}
            )
            if not data:
                return []
            return [BodyBatteryReport(**item) for item in data]
        except Exception as e:
            logger.error(f"獲取 Body Battery 報告區間失敗: {e}")
            return []
