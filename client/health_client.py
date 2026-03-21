import garth
from datetime import datetime, date, timedelta
from typing import List, Optional, Union
from loguru import logger
from .client import Client
from models.healthModel import HealthSummary

class HealthClient(Client):
    """
    Garmin Health Client to fetch daily summaries and specific health metrics.
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
            self._random_delay()
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

    def get_training_readiness(self, calendar_date: Union[str, date]) -> Optional[dict]:
        """Get Training Readiness for a specific date."""
        if isinstance(calendar_date, date): date_str = calendar_date.isoformat()
        else: date_str = calendar_date
        logger.debug(f"正在獲取訓練完備度: {date_str}")
        try:
            return garth.client.connectapi(f"/usersummary-service/usersummary/trainingreadiness/{date_str}")
        except Exception as e:
            logger.error(f"獲取訓練完備度失敗: {e}")
            return None

    def get_fitness_age(self) -> Optional[dict]:
        """Get Fitness Age report."""
        logger.debug("正在獲取體能年齡報告...")
        try:
            return garth.client.connectapi("/usersummary-service/stats/fitness-age")
        except Exception as e:
            logger.error(f"獲取體能年齡失敗: {e}")
            return None

    def get_lactate_threshold(self) -> Optional[dict]:
        """Get Lactate Threshold data."""
        logger.debug("正在獲取乳酸閾值數據...")
        try:
            return garth.client.connectapi("/usersummary-service/stats/lactateThreshold")
        except Exception as e:
            logger.error(f"獲取乳酸閾值失敗: {e}")
            return None

    def get_race_predictions(self) -> Optional[dict]:
        """Get Race Predictions (5k, 10k, Half, Full)."""
        logger.debug("正在獲取賽事預測...")
        try:
            return garth.client.connectapi("/usersummary-service/stats/racePredictions")
        except Exception as e:
            logger.error(f"獲取賽事預測失敗: {e}")
            return None

    def get_intensity_minutes(self, start_date: Union[str, date], end_date: Union[str, date]) -> List[dict]:
        """Get Intensity Minutes for a date range."""
        if isinstance(start_date, date): start_date = start_date.isoformat()
        if isinstance(end_date, date): end_date = end_date.isoformat()
        logger.debug(f"正在獲取熱血時間: {start_date} ~ {end_date}")
        try:
            return garth.client.connectapi(f"/usersummary-service/stats/intensity-minutes/daily/{start_date}/{end_date}")
        except Exception as e:
            logger.error(f"獲取熱血時間失敗: {e}")
            return []

    def get_hydration(self, calendar_date: Union[str, date]) -> Optional[dict]:
        """Get Hydration data for a specific date."""
        if isinstance(calendar_date, date): date_str = calendar_date.isoformat()
        else: date_str = calendar_date
        logger.debug(f"正在獲取補水紀錄: {date_str}")
        try:
            return garth.client.connectapi(f"/usersummary-service/usersummary/hydration/daily/{date_str}")
        except Exception as e:
            logger.error(f"獲取補水紀錄失敗: {e}")
            return None

    def get_personal_records(self) -> List[dict]:
        """Get All Personal Records."""
        logger.debug("正在獲取個人紀錄...")
        try:
            return garth.client.connectapi("/personalrecord-service/personalrecord/all")
        except Exception as e:
            logger.error(f"獲取個人紀錄失敗: {e}")
            return []

    def get_insights(self) -> Optional[dict]:
        """Get Garmin Insights."""
        logger.debug("正在獲取 Garmin Insights...")
        try:
            return garth.client.connectapi("/insights-service/insights/summary/")
        except Exception as e:
            logger.error(f"獲取 Insights 失敗: {e}")
            return None

    def get_blood_pressure(self, start_date: Union[str, date], end_date: Union[str, date]) -> List[dict]:
        """Get Blood Pressure for a date range."""
        if isinstance(start_date, date): start_date = start_date.isoformat()
        if isinstance(end_date, date): end_date = end_date.isoformat()
        logger.debug(f"正在獲取血壓數據: {start_date} ~ {end_date}")
        try:
            return garth.client.connectapi(f"/bloodpressure-service/bloodpressure/range/{start_date}/{end_date}")
        except Exception as e:
            logger.error(f"獲取血壓數據失敗: {e}")
            return []
