"""
Purpose: 將簡約的 Workout DSL 轉換為 Garmin Connect 原始 API 格式。
Author: Gemini CLI
"""
import re
from typing import Dict, Any, List, Union

class WorkoutDSLParser:
    def __init__(self, dsl_data: Dict[str, Any]):
        self.settings = dsl_data.get("settings", {})
        self.definitions = dsl_data.get("definitions", {})
        self.workouts_dsl = dsl_data.get("workouts", {})

    def _pace_to_mps(self, pace_str: str) -> float:
        """將 min:sec 轉換為 meters per second."""
        try:
            m, s = map(int, pace_str.split(":"))
            total_seconds_per_km = m * 60 + s
            return 1000.0 / total_seconds_per_km
        except:
            return 0.0

    def _parse_target(self, target_str: str) -> Dict[str, Any]:
        """解析 @H(z2) 或 @P($GA) 這種目標."""
        target_str = target_str.strip()
        
        # 心率區間: @H(z2)
        hr_match = re.search(r"@H\(z(\d+)\)", target_str)
        if hr_match:
            zone = int(hr_match.group(1))
            return {
                "targetType": {"workoutTargetTypeKey": "heart.rate.zone"},
                "zoneNumber": zone
            }
        
        # 配速: @P($GA) 或 @P(6:00-6:30)
        pace_match = re.search(r"@P\((.+)\)", target_str)
        if pace_match:
            pace_val = pace_match.group(1)
            if pace_val.startswith("$"):
                pace_val = self.definitions.get(pace_val[1:], pace_val)
            
            if "-" in pace_val:
                p_high, p_low = pace_val.split("-")
                # Garmin API 配速: targetValueOne 是較慢的(低速), targetValueTwo 是較快的(高速)
                return {
                    "targetType": {"workoutTargetTypeKey": "pace.zone"},
                    "targetValueOne": self._pace_to_mps(p_high),
                    "targetValueTwo": self._pace_to_mps(p_low)
                }
        
        return {"targetType": {"workoutTargetTypeKey": "no.target"}}

    def _parse_condition(self, cond_str: str) -> Dict[str, Any]:
        """解析 15min 或 2000m 這種結束條件."""
        cond_str = cond_str.strip()
        if cond_str.endswith("min"):
            val = float(cond_str.replace("min", "")) * 60
            return {"endCondition": {"conditionTypeKey": "time"}, "endConditionValue": val}
        elif cond_str.endswith("s") or cond_str.endswith("sec"):
            val = float(cond_str.replace("sec", "").replace("s", ""))
            return {"endCondition": {"conditionTypeKey": "time"}, "endConditionValue": val}
        elif cond_str.endswith("m"):
            val = float(cond_str.replace("m", ""))
            return {"endCondition": {"conditionTypeKey": "distance"}, "endConditionValue": val}
        elif cond_str.endswith("k") or cond_str.endswith("km"):
            val = float(cond_str.replace("km", "").replace("k", "")) * 1000
            return {"endCondition": {"conditionTypeKey": "distance"}, "endConditionValue": val}
        
        return {"endCondition": {"conditionTypeKey": "lap.button"}, "endConditionValue": None}

    def _dsl_to_steps(self, dsl_steps: List[Any]) -> List[Dict[str, Any]]:
        steps = []
        for i, item in enumerate(dsl_steps):
            if isinstance(item, dict):
                key = list(item.keys())[0]
                val = item[key]
                
                # 處理重複: repeat(8)
                repeat_match = re.match(r"repeat\((\d+)\)", key)
                if repeat_match:
                    count = int(repeat_match.group(1))
                    steps.append({
                        "type": "RepeatedStepDTO",
                        "stepOrder": i + 1,
                        "repeatIterations": count,
                        "workoutSteps": self._dsl_to_steps(val)
                    })
                    continue

                # 處理基本步驟: warmup, run, recovery, cooldown
                step_type = key
                if "@" in val:
                    cond_part, target_part = val.split("@", 1)
                    target_part = "@" + target_part
                else:
                    cond_part = val
                    target_part = ""
                
                step = {
                    "type": "ExecutableStepDTO",
                    "stepOrder": i + 1,
                    "stepType": {"stepTypeKey": step_type},
                    **self._parse_condition(cond_part),
                    **self._parse_target(target_part)
                }
                steps.append(step)
        return steps

    def parse_workout(self, name: str) -> Dict[str, Any]:
        """將特定名稱的 DSL 轉換為 Garmin 格式."""
        dsl_steps = self.workouts_dsl.get(name)
        if not dsl_steps:
            return {}

        return {
            "workoutName": name,
            "sportType": {"sportTypeKey": "running"},
            "workoutSegments": [
                {
                    "segmentOrder": 1,
                    "sportType": {"sportTypeKey": "running"},
                    "workoutSteps": self._dsl_to_steps(dsl_steps)
                }
            ]
        }

    def get_all_workouts(self) -> List[Dict[str, Any]]:
        return [self.parse_workout(name) for name in self.workouts_dsl.keys()]
