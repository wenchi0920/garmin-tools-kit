"""
Purpose: 將簡約的 Workout DSL 與 Garmin Connect 原始 API 格式進行雙向轉換 (DTO 型別化)。
Author: Gemini CLI
"""
import re
from typing import Dict, Any, List, Union, Optional
from models import WorkoutModel, ExecutableStepDTO, RepeatGroupDTO

class WorkoutDSLParser:
    def __init__(self, dsl_data: Optional[Dict[str, Any]] = None):
        if dsl_data:
            self.settings = dsl_data.get("settings", {})
            self.definitions = dsl_data.get("definitions", {})
            self.workouts_dsl = dsl_data.get("workouts", {})
        else:
            self.settings = {}
            self.definitions = {}
            self.workouts_dsl = {}

    def _pace_to_mps(self, pace_str: str) -> float:
        """將 min:sec 轉換為 meters per second."""
        try:
            if ":" in pace_str:
                m, s = map(int, pace_str.split(":"))
                total_seconds_per_km = m * 60 + s
            else:
                total_seconds_per_km = float(pace_str) * 60
            return 1000.0 / total_seconds_per_km
        except:
            return 0.0

    def _mps_to_pace(self, mps: float) -> str:
        """將 meters per second 轉換為 min:sec."""
        if not mps or mps <= 0:
            return "0:00"
        seconds_per_km = 1000.0 / mps
        m, s = divmod(int(round(seconds_per_km)), 60)
        return f"{m}:{s:02d}"

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
            else:
                v = self._pace_to_mps(pace_val)
                return {
                    "targetType": {"workoutTargetTypeId": 6, "workoutTargetTypeKey": "pace.zone"},
                    "targetValueOne": v,
                    "targetValueTwo": v
                }
        
        return {
            "targetType": {"workoutTargetTypeId": 1, "workoutTargetTypeKey": "no.target"}
        }

    def _parse_condition(self, cond_str: str) -> Dict[str, Any]:
        """解析 15min, 2000m, 10reps 或 15x 這種結束條件."""
        cond_str = cond_str.strip().lower()
        
        # 1. 優先處理複合格式或長關鍵字
        if ":" in cond_str:
            try:
                m, s = map(int, cond_str.split(":"))
                val = m * 60 + s
                return {"endCondition": {"conditionTypeId": 2, "conditionTypeKey": "time"}, "endConditionValue": float(val)}
            except:
                pass

        if cond_str.endswith("min"):
            val = float(cond_str.replace("min", "")) * 60
            return {"endCondition": {"conditionTypeId": 2, "conditionTypeKey": "time"}, "endConditionValue": val}
        
        if cond_str.endswith("reps") or cond_str.endswith("rep"):
            val = float(cond_str.replace("reps", "").replace("rep", ""))
            return {"endCondition": {"conditionTypeId": 1, "conditionTypeKey": "lap.button"}, "endConditionValue": val}
            
        if cond_str.endswith("breaths") or cond_str.endswith("breath"):
            val = float(cond_str.replace("breaths", "").replace("breath", ""))
            return {"endCondition": {"conditionTypeId": 12, "conditionTypeKey": "breaths"}, "endConditionValue": val}

        if cond_str.endswith("km") or cond_str.endswith("k"):
            val = float(cond_str.replace("km", "").replace("k", "")) * 1000
            return {"endCondition": {"conditionTypeId": 3, "conditionTypeKey": "distance"}, "endConditionValue": val}

        # 2. 處理短關鍵字
        if cond_str.endswith("s") or cond_str.endswith("sec"):
            # 確保不是 reps 的殘餘
            val_str = cond_str.replace("sec", "").replace("s", "")
            try:
                val = float(val_str)
                return {"endCondition": {"conditionTypeId": 2, "conditionTypeKey": "time"}, "endConditionValue": val}
            except:
                pass
                
        if cond_str.endswith("m"):
            val = float(cond_str.replace("m", ""))
            return {"endCondition": {"conditionTypeId": 3, "conditionTypeKey": "distance"}, "endConditionValue": val}
            
        if cond_str.endswith("x"):
            val = float(cond_str.replace("x", ""))
            return {"endCondition": {"conditionTypeId": 1, "conditionTypeKey": "lap.button"}, "endConditionValue": val}
        
        return {"endCondition": {"conditionTypeId": 1, "conditionTypeKey": "lap.button"}, "endConditionValue": None}

    def _dsl_to_steps(self, dsl_steps: List[Any], current_order: int = 1, child_id: Optional[int] = None) -> tuple[List[Union[ExecutableStepDTO, RepeatGroupDTO]], Dict[str, Any]]:
        steps = []
        type_id_map = {"warmup": 1, "cooldown": 2, "run": 3, "interval": 3, "recovery": 4, "rest": 5, "repeat": 6}
        sport_info = None
        
        # Use a local counter for child IDs if not provided
        if child_id is None:
            self._child_id_counter = getattr(self, "_child_id_counter", 0) + 1
            local_child_id = self._child_id_counter
        else:
            local_child_id = child_id

        order = current_order
        for item in dsl_steps:
            if isinstance(item, dict):
                key = list(item.keys())[0]
                val = item[key]
                
                # Check for sport type definition inside steps list
                if key == "sport":
                    sport_map = {
                        "running": {"sportTypeId": 1, "sportTypeKey": "running"},
                        "cycling": {"sportTypeId": 2, "sportTypeKey": "cycling"},
                        "swimming": {"sportTypeId": 3, "sportTypeKey": "swimming"},
                        "strength": {"sportTypeId": 5, "sportTypeKey": "strength_training"},
                        "yoga": {"sportTypeId": 7, "sportTypeKey": "yoga"},
                        "mobility": {"sportTypeId": 11, "sportTypeKey": "mobility"}
                    }
                    sport_info = sport_map.get(str(val).lower())
                    continue

                repeat_match = re.match(r"repeat\((\d+)\)", key)
                if repeat_match:
                    count = int(repeat_match.group(1))
                    # Increment global child counter for this repeat group
                    self._child_id_counter = getattr(self, "_child_id_counter", 0) + 1
                    group_child_id = self._child_id_counter
                    
                    group_steps, _ = self._dsl_to_steps(val, order + 1, child_id=group_child_id)
                    steps.append(RepeatGroupDTO(
                        stepOrder=order,
                        stepType={"stepTypeId": 6, "stepTypeKey": "repeat", "displayOrder": 6},
                        childStepId=group_child_id,
                        numberOfIterations=count,
                        workoutSteps=group_steps,
                        endCondition={"conditionTypeId": 7, "conditionTypeKey": "iterations", "displayOrder": 7, "displayable": False},
                        endConditionValue=float(count)
                    ))
                    # Important: Update order based on internal steps
                    # Repeat group itself is 1 step, plus all nested steps
                    def count_nested(s_list):
                        total = 0
                        for s in s_list:
                            total += 1
                            if isinstance(s, RepeatGroupDTO):
                                total += count_nested(s.workoutSteps)
                        return total
                    
                    order += 1 + count_nested(group_steps)
                    continue

                step_type = key
                description = None
                val_str = str(val)
                
                # Parse @note(...)
                note_match = re.search(r"@note\((.+?)\)", val_str)
                if note_match:
                    description = note_match.group(1)
                    val_str = val_str.replace(note_match.group(0), "").strip()

                if "@" in val_str:
                    cond_part, target_part = val_str.split("@", 1)
                    target_part = "@" + target_part
                else:
                    cond_part = val_str
                    target_part = ""
                
                cond_data = self._parse_condition(cond_part)
                # Ensure endCondition has displayable and displayOrder
                cond_data["endCondition"]["displayable"] = True
                cond_data["endCondition"]["displayOrder"] = cond_data["endCondition"].get("conditionTypeId", 1)

                target_data = self._parse_target(target_part)
                # Ensure targetType has displayOrder
                target_data["targetType"]["displayOrder"] = target_data["targetType"].get("workoutTargetTypeId", 1)

                step_type_id = type_id_map.get(step_type, 3)
                step = ExecutableStepDTO(
                    stepOrder=order,
                    stepType={"stepTypeId": step_type_id, "stepTypeKey": step_type, "displayOrder": step_type_id},
                    childStepId=child_id, # Only set if inside a repeat group
                    description=description,
                    endCondition=cond_data["endCondition"],
                    endConditionValue=cond_data.get("endConditionValue"),
                    targetType=target_data["targetType"],
                    targetValueOne=target_data.get("targetValueOne"),
                    targetValueTwo=target_data.get("targetValueTwo"),
                    zoneNumber=target_data.get("zoneNumber"),
                    strokeType={"strokeTypeId": 0, "strokeTypeKey": None, "displayOrder": 0},
                    equipmentType={"equipmentTypeId": 0, "equipmentTypeKey": None, "displayOrder": 0}
                )
                steps.append(step)
                order += 1
        return steps, sport_info

    def parse_workout(self, name: str) -> Dict[str, Any]:
        """DSL -> DTO -> Garmin Dict."""
        self._child_id_counter = 0 # Reset counter for each workout
        dsl_steps = self.workouts_dsl.get(name)
        if not dsl_steps: return {}

        workout_steps, sport_info = self._dsl_to_steps(dsl_steps)
        if not sport_info:
            sport_info = {"sportTypeId": 1, "sportTypeKey": "running"}

        workout_dto = WorkoutModel(
            workoutName=name,
            sportType=sport_info,
            workoutSegments=[{
                "segmentOrder": 1,
                "sportType": sport_info,
                "workoutSteps": workout_steps
            }]
        )
        return workout_dto.model_dump(exclude_none=True, by_alias=True)

    def get_all_workouts(self) -> List[Dict[str, Any]]:
        return [self.parse_workout(name) for name in self.workouts_dsl.keys()]
