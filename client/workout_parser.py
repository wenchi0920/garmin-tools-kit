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
            m, s = map(int, pace_str.split(":"))
            total_seconds_per_km = m * 60 + s
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

    def _dsl_to_steps(self, dsl_steps: List[Any], current_order: int = 1) -> List[Union[ExecutableStepDTO, RepeatGroupDTO]]:
        steps = []
        type_id_map = {"warmup": 1, "cooldown": 2, "run": 3, "interval": 3, "recovery": 4, "rest": 5, "repeat": 6}

        order = current_order
        for item in dsl_steps:
            if isinstance(item, dict):
                key = list(item.keys())[0]
                val = item[key]
                
                repeat_match = re.match(r"repeat\((\d+)\)", key)
                if repeat_match:
                    count = int(repeat_match.group(1))
                    group_steps = self._dsl_to_steps(val, order + 1)
                    steps.append(RepeatGroupDTO(
                        stepOrder=order,
                        stepType={"stepTypeId": 6, "stepTypeKey": "repeat"},
                        numberOfIterations=count,
                        workoutSteps=group_steps,
                        endCondition={"conditionTypeId": 7, "conditionTypeKey": "iterations"},
                        endConditionValue=float(count)
                    ))
                    order += len(group_steps) + 1
                    continue

                step_type = key
                if "@" in val:
                    cond_part, target_part = val.split("@", 1)
                    target_part = "@" + target_part
                else:
                    cond_part = val
                    target_part = ""
                
                cond_data = self._parse_condition(cond_part)
                target_data = self._parse_target(target_part)
                
                step = ExecutableStepDTO(
                    stepOrder=order,
                    stepType={"stepTypeId": type_id_map.get(step_type, 3), "stepTypeKey": step_type},
                    endCondition=cond_data["endCondition"],
                    endConditionValue=cond_data.get("endConditionValue"),
                    targetType=target_data["targetType"],
                    targetValueOne=target_data.get("targetValueOne"),
                    targetValueTwo=target_data.get("targetValueTwo"),
                    zoneNumber=target_data.get("zoneNumber")
                )
                steps.append(step)
                order += 1
        return steps

    def parse_workout(self, name: str) -> Dict[str, Any]:
        """DSL -> DTO -> Garmin Dict."""
        dsl_steps = self.workouts_dsl.get(name)
        if not dsl_steps: return {}

        workout_dto = WorkoutModel(
            workoutName=name,
            sportType={"sportTypeId": 1, "sportTypeKey": "running"},
            workoutSegments=[{
                "segmentOrder": 1,
                "sportType": {"sportTypeId": 1, "sportTypeKey": "running"},
                "workoutSteps": self._dsl_to_steps(dsl_steps)
            }]
        )
        return workout_dto.model_dump(exclude_none=True, by_alias=True)

    def get_all_workouts(self) -> List[Dict[str, Any]]:
        return [self.parse_workout(name) for name in self.workouts_dsl.keys()]

    def _step_to_dsl(self, step: Union[ExecutableStepDTO, RepeatGroupDTO]) -> Dict[str, Any]:
        if isinstance(step, RepeatGroupDTO):
            key = f"repeat({step.numberOfIterations})"
            return {key: [self._step_to_dsl(s) for s in step.workoutSteps]}
        
        # ExecutableStepDTO
        step_type = step.stepType.get("stepTypeKey", "run")
        
        # End condition
        cond_key = step.endCondition.get("conditionTypeKey")
        val = step.endConditionValue
        if cond_key == "time":
            cond_str = f"{int(val/60)}min" if val % 60 == 0 else f"{int(val)}s"
        elif cond_key == "distance":
            cond_str = f"{int(val/1000)}k" if val % 1000 == 0 else f"{int(val)}m"
        else:
            cond_str = "lap"
            
        # Target
        target_key = step.targetType.get("workoutTargetTypeKey")
        target_str = ""
        if target_key == "heart.rate.zone":
            target_str = f"@H(z{step.zoneNumber})"
        elif target_key == "pace.zone":
            p1 = self._mps_to_pace(step.targetValueOne)
            p2 = self._mps_to_pace(step.targetValueTwo)
            target_str = f"@P({p1}-{p2})"
            
        return {step_type: f"{cond_str}{target_str}"}

    def workout_to_dsl(self, workout_json: Dict[str, Any]) -> Dict[str, Any]:
        """Garmin Dict -> DTO -> DSL List."""
        workout_dto = WorkoutModel.model_validate(workout_json)
        dsl_list = []
        for segment in workout_dto.workoutSegments:
            for step in segment.workoutSteps:
                dsl_list.append(self._step_to_dsl(step))
        return {workout_dto.workoutName: dsl_list}
