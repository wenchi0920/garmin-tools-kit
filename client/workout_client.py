from typing import List, Dict, Any
import garth
from .client import Client

class WorkoutClient(Client):
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def list_workouts(self) -> List[Dict[str, Any]]:
        """
        獲取帳號內所有的訓練計畫。
        """
        # Garmin Connect API for listing workouts
        # Documentation based on common usage in garth-based tools
        url = "/workout-service/workouts"
        params = {"start": 0, "limit": 100}
        response = garth.client.request("GET", "connectapi", url, params=params)
        self._random_delay()
        return response.json()

    def get_workout(self, workout_id: Any) -> Dict[str, Any]:
        """
        獲取指定的訓練計畫詳細資訊。
        """
        # Garmin Connect API for getting a specific workout
        url = f"/workout-service/workout/{workout_id}"
        response = garth.client.request("GET", "connectapi", url)
        self._random_delay()
        return response.json()

    def upload_workout(self, workout_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        上傳一個訓練計畫 (JSON 格式)。
        """
        # Garmin Connect API for uploading/creating a workout
        url = "/workout-service/workout"
        response = garth.client.request("POST", "connectapi", url, json=workout_data)
        self._random_delay()
        return response.json()

    def delete_workout(self, workout_id: Any) -> Dict[str, Any]:
        """
        刪除指定的訓練計畫。
        """
        url = f"/workout-service/workout/{workout_id}"
        garth.client.request("DELETE", "connectapi", url)
        self._random_delay()
        return {"status": "success", "workoutId": workout_id}

    def schedule_workout(self, workout_id: Any, date_str: str) -> Dict[str, Any]:
        """
        將訓練計畫排入指定日期的行事曆。
        date_str 格式: YYYY-MM-DD
        """
        url = f"/workout-service/schedule/{workout_id}"
        payload = {"date": date_str}
        response = garth.client.request("POST", "connectapi", url, json=payload)
        self._random_delay()
        return response.json()
