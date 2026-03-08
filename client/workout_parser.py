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

    def _get_executable_step_template(self, step_order: int) -> Dict[str, Any]:
        """建立符合 Garmin 規格的空步驟範本。"""
        return {
            "type": "ExecutableStepDTO",
            "stepId": None,
            "stepOrder": step_order,
            "childStepId": None,
            "description": None,
            "endCondition": {
                "conditionTypeId": 1,
                "conditionTypeKey": "lap.button"
            },
            "endConditionValue": None,
            "targetType": {
                "workoutTargetTypeId": 1,
                "workoutTargetTypeKey": "no.target"
            },
            "targetValueOne": None,
            "targetValueTwo": None,
            "zoneNumber": None,
            "secondaryTargetType": None,
            "secondaryTargetValueOne": None,
            "secondaryTargetValueTwo": None,
            "secondaryZoneNumber": None,
            "strokeType": {"strokeTypeId": 0, "strokeTypeKey": None},
            "equipmentType": {"equipmentTypeId": 0, "equipmentTypeKey": None},
            "category": None,
            "exerciseName": None,
            "weightValue": None,
            "weightUnit": None
        }

    def _parse_target(self, target_str: str) -> Dict[str, Any]:
        """解析 @H(z2) 或 @P($GA) 這種目標."""
        target_str = target_str.strip()
        
        # 心率區間: @H(z2)
        hr_match = re.search(r"@H\(z(\d+)\)", target_str)
        if hr_match:
            zone = int(hr_match.group(1))
            return {
                "targetType": {"workoutTargetTypeId": 4, "workoutTargetTypeKey": "heart.rate.zone"},
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
                v_high = self._pace_to_mps(p_high)
                v_low = self._pace_to_mps(p_low)
                return {
                    "targetType": {"workoutTargetTypeId": 6, "workoutTargetTypeKey": "pace.zone"},
                    "targetValueOne": min(v_high, v_low),
                    "targetValueTwo": max(v_high, v_low)
                }
        
        return {
            "targetType": {"workoutTargetTypeId": 1, "workoutTargetTypeKey": "no.target"}
        }

    def _parse_condition(self, cond_str: str) -> Dict[str, Any]:
        """解析 15min 或 2000m 這種結束條件."""
        cond_str = cond_str.strip()
        if cond_str.endswith("min"):
            val = float(cond_str.replace("min", "")) * 60
            return {"endCondition": {"conditionTypeId": 2, "conditionTypeKey": "time"}, "endConditionValue": val}
        elif cond_str.endswith("s") or cond_str.endswith("sec"):
            val = float(cond_str.replace("sec", "").replace("s", ""))
            return {"endCondition": {"conditionTypeId": 2, "conditionTypeKey": "time"}, "endConditionValue": val}
        elif cond_str.endswith("m"):
            val = float(cond_str.replace("m", ""))
            return {"endCondition": {"conditionTypeId": 3, "conditionTypeKey": "distance"}, "endConditionValue": val}
        elif cond_str.endswith("k") or cond_str.endswith("km"):
            val = float(cond_str.replace("km", "").replace("k", "")) * 1000
            return {"endCondition": {"conditionTypeId": 3, "conditionTypeKey": "distance"}, "endConditionValue": val}
        
        return {"endCondition": {"conditionTypeId": 1, "conditionTypeKey": "lap.button"}, "endConditionValue": None}

    def _dsl_to_steps(self, dsl_steps: List[Any], current_order: int = 1) -> List[Dict[str, Any]]:
        steps = []
        # Mapping table for step types
        type_id_map = {
            "warmup": 1,
            "cooldown": 2,
            "run": 3,
            "interval": 3,
            "recovery": 4,
            "rest": 5,
            "repeat": 6
        }

        order = current_order
        for item in dsl_steps:
            if isinstance(item, dict):
                key = list(item.keys())[0]
                val = item[key]
                
                # 處理重複: repeat(8) -> RepeatGroupDTO
                repeat_match = re.match(r"repeat\((\d+)\)", key)
                if repeat_match:
                    count = int(repeat_match.group(1))
                    group_steps = self._dsl_to_steps(val, order + 1)
                    steps.append({
                        "type": "RepeatGroupDTO",
                        "stepId": None,
                        "stepOrder": order,
                        "stepType": {"stepTypeId": 6, "stepTypeKey": "repeat"},
                        "childStepId": 1,
                        "numberOfIterations": count,
                        "workoutSteps": group_steps,
                        "endCondition": {"conditionTypeId": 7, "conditionTypeKey": "iterations"},
                        "endConditionValue": float(count),
                        "smartRepeat": False
                    })
                    order += len(group_steps) + 1
                    continue

                # 處理基本步驟: warmup, run, recovery, cooldown
                step_type = key
                if "@" in val:
                    cond_part, target_part = val.split("@", 1)
                    target_part = "@" + target_part
                else:
                    cond_part = val
                    target_part = ""
                
                step = self._get_executable_step_template(order)
                step.update({
                    "stepType": {
                        "stepTypeId": type_id_map.get(step_type, 3),
                        "stepTypeKey": step_type
                    },
                    **self._parse_condition(cond_part),
                    **self._parse_target(target_part)
                })
                steps.append(step)
                order += 1
        return steps

    def parse_workout(self, name: str) -> Dict[str, Any]:
        """將特定名稱的 DSL 轉換為 Garmin 格式."""
        dsl_steps = self.workouts_dsl.get(name)
        if not dsl_steps:
            return {}

        return {
            "workoutName": name,
            "sportType": {"sportTypeId": 1, "sportTypeKey": "running"},
            "workoutSegments": [
                {
                    "segmentOrder": 1,
                    "sportType": {"sportTypeId": 1, "sportTypeKey": "running"},
                    "workoutSteps": self._dsl_to_steps(dsl_steps)
                }
            ]
        }

    def get_all_workouts(self) -> List[Dict[str, Any]]:
        return [self.parse_workout(name) for name in self.workouts_dsl.keys()]
