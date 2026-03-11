"""
Purpose: Garmin Race Events Client to fetch events list and details from calendar service.
Author: Gemini CLI
Changelog:
- 2026-03-09: Initial creation.
- 2026-03-09: Updated to use /calendar-service/events which is more reliable.
"""

from typing import List, Dict, Any, Optional
import garth
from .client import Client

class RaceEventClient(Client):
    """
    Client for Garmin Race Events via Calendar Service.
    """
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def list_events(self, start_date: Optional[str] = None, end_date: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        獲取帳號內的賽事清單。
        :param start_date: 開始日期 (YYYY-MM-DD)
        :param end_date: 結束日期 (YYYY-MM-DD)
        """
        # Calendar Service Events Endpoint
        url = "/calendar-service/events"
        params = {}
        if start_date:
            params["startDate"] = start_date
        if end_date:
            params["endDate"] = end_date
            
        # Use connectapi method for OAuth-based request
        data = garth.client.connectapi(url, params=params)
        self._random_delay()
        
        if isinstance(data, list):
            return data
        return []

    def get_event(self, event_id: int) -> Dict[str, Any]:
        """
        獲取特定賽事的詳細資訊。
        """
        # Note: /event-service/events might work for specific event details if the ID is known
        url = f"/event-service/events/{event_id}"
        data = garth.client.connectapi(url)
        return data if data else {}
