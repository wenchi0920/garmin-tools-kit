
import argparse
import json
import os
from datetime import datetime, date, timedelta
from typing import Dict, Any, List

import yaml
from loguru import logger
from tqdm import tqdm

from client import (
    ActivityClient, BodyBatteryClient, HealthClient, HrvClient,
    MaxHrClient, SleepClient, Vo2MaxClient, WeightClient,
    WorkoutClient, WorkoutDSLParser, RaceEventClient
)
from models.raceEventModel import RaceEventModel
from .utils import resolve_user_auth, resolve_default_output_path, format_seconds, pad_text


def execute_activity_export(args: argparse.Namespace):
    username, password = resolve_user_auth(args)
    client = ActivityClient(email=username, password=password, session_dir=args.session)

    # 處理單日查詢或日期範圍
    start_date = args.start_date or args.date
    end_date = args.end_date or args.date

    logger.info(f"正在獲取活動列表... 數量={args.count}, 範圍={start_date or '不限'} ~ {end_date or '不限'}")
    activities = client.list_activities(count=args.count, start_date=start_date, end_date=end_date)

    if not activities:
        logger.warning("找不到符合條件的活動。")
        return

    if not os.path.exists(args.directory):
        os.makedirs(args.directory, exist_ok=True)

    iterable = tqdm(activities, desc="下載活動進度", unit="個") if args.progress else activities
    for activity in iterable:
        client.download_activity(
            activity, format=args.format, directory=args.directory,
            original_time=args.originaltime, desc=args.desc,
            overwrite=args.over_write
        )
    logger.success(f"任務完成。所有活動已匯出至: {os.path.abspath(args.directory)}")


def manage_workout_workflow(args: argparse.Namespace):
    username, password = resolve_user_auth(args)
    client = WorkoutClient(email=username, password=password, session_dir=args.session)

    if args.workout_command == "list":
        workouts = client.list_workouts()
        logger.info("-" * 100)
        logger.info(f"{'ID':<15} | {'名稱':<40} | {'類型':<15} | {'建立日期':<20}")
        logger.info("-" * 100)
        for w in workouts:
            name = (w.get("workoutName")[:35] + "...") if len(w.get("workoutName", "")) > 38 else w.get("workoutName",
                                                                                                        "N/A")
            logger.info(
                f"{w.get('workoutId'):<15} | {name:<40} | {w.get('sportType', {}).get('sportTypeKey'):<15} | {w.get('createdDate'):<20}")
        logger.success(f"成功獲取 {len(workouts)} 個訓練計畫。")

    elif args.workout_command == "get":
        workout_data = client.get_workout(args.id)
        target_dir = "data/workout"
        if not os.path.exists(target_dir):
            os.makedirs(target_dir, exist_ok=True)

        filename = f"workout_{args.id}.yaml"
        output_file = args.output or os.path.join(target_dir, filename)

        if not args.over_write and os.path.exists(output_file):
            logger.info(f"檔案已存在，跳過儲存: {output_file}")
        else:
            with open(output_file, "w", encoding="utf-8") as f:
                yaml.dump(workout_data, f, sort_keys=False, allow_unicode=True, indent=4)
            logger.success(f"訓練計畫下載成功! 檔名: {output_file}")

    elif args.workout_command == "upload":
        with open(args.file, "r", encoding="utf-8") as f:
            yaml_content = yaml.safe_load(f)

        if isinstance(yaml_content, dict) and "workouts" in yaml_content:
            parser = WorkoutDSLParser(yaml_content)
            workouts_to_upload = parser.get_all_workouts()
            uploaded_id_map = {}

            if yaml_content.get("settings", {}).get("deleteSameNameWorkout", False):
                existing_workouts = client.list_workouts()
                existing_map = {w["workoutName"]: w["workoutId"] for w in existing_workouts}
                for w in workouts_to_upload:
                    if w["workoutName"] in existing_map:
                        client.delete_workout(existing_map[w["workoutName"]])

            iterable = tqdm(workouts_to_upload, desc="上傳計畫進度", unit="個") if args.progress else workouts_to_upload
            for w in iterable:
                result = client.upload_workout(w)
                uploaded_id_map[w["workoutName"]] = result.get("workoutId")
                logger.success(f"計畫 '{w['workoutName']}' 上傳成功! ID: {result.get('workoutId')}")

            schedule_plan = yaml_content.get("schedulePlan")
            if schedule_plan and schedule_plan.get("start_from"):
                start_date = datetime.strptime(str(schedule_plan.get("start_from")), "%Y-%m-%d")
                for i, name in enumerate(schedule_plan.get("workouts", [])):
                    curr_date = (start_date + timedelta(days=i)).strftime("%Y-%m-%d")
                    if name.lower() != "rest" and name in uploaded_id_map:
                        client.schedule_workout(uploaded_id_map[name], curr_date)
        else:
            result = client.upload_workout(yaml_content)
            logger.success(f"上傳成功! ID: {result.get('workoutId')}")

    elif args.workout_command == "delete":
        client.delete_workout(args.id)
        logger.success(f"計畫已刪除! ID: {args.id}")


def display_health_table(items: List[Dict[str, Any]], output_file: str = None) -> None:
    """以表格格式顯示健康數據摘要"""
    if not items:
        logger.warning("沒有資料可以顯示表格。")
        return

    # 表頭
    headers = ["日期", "步數/目標", "距離", "卡路里(活動/總計)", "心率(安靜/最大)", "壓力", "能量(高/低)", "睡眠分數", "hrv", "完備度", "血壓"]
    col_widths = [12, 12, 10, 18, 16, 6, 10, 8, 8, 8, 10]

    table_lines = []
    header_line = " | ".join(f"{h:<{w}}" for h, w in zip(headers, col_widths))
    table_lines.append("-" * len(header_line))
    table_lines.append(header_line)
    table_lines.append("-" * len(header_line))

    for entry in items:
        if not isinstance(entry, dict): continue
        date_str = str(entry.get("calendarDate", "N/A"))
        steps = f"{(entry.get('totalSteps') or 0)}/{(entry.get('dailyStepGoal') or 0)}"
        dist = f"{(entry.get('totalDistanceMeters') or 0) / 1000:.2f}km"
        cals = f"{int(entry.get('activeKilocalories') or 0)}/{int(entry.get('totalKilocalories') or 0)}"
        hr = f"{(entry.get('restingHeartRate') or '--')}/{(entry.get('maxHeartRate') or '--')}"
        stress = f"{(entry.get('averageStressLevel') or '--')}"
        bb = f"{(entry.get('bodyBatteryHighestValue') or '--')}/{(entry.get('bodyBatteryLowestValue') or '--')}"

        # 額外欄位 (從彙整中獲取)
        sleep_score = str(entry.get("sleep_score", "--"))
        hrv = str(entry.get("hrv_avg", "--"))
        readiness = str(entry.get("readiness_score", "--"))
        bp = entry.get("blood_pressure", "--")

        row = [date_str, steps, dist, cals, hr, stress, bb, sleep_score, hrv, readiness, bp]
        row_line = " | ".join(f"{str(v):<{w}}" for v, w in zip(row, col_widths))
        table_lines.append(row_line)

    table_lines.append("-" * len(header_line))

    # 輸出至控制台
    table_content = "\n".join(table_lines)
    print(table_content)

    # 若有指定輸出檔案，則儲存 (通常是 .txt)
    if output_file:
        try:
            # 確保目錄存在
            os.makedirs(os.path.dirname(os.path.abspath(output_file)), exist_ok=True)
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(table_content)
            logger.success(f"表格已儲存至: {output_file}")
        except Exception as e:
            logger.error(f"儲存表格失敗: {e}")


def display_health_summary(cmd: str, metric_collection: Dict[str, Any], args: argparse.Namespace = None):
    """格式化顯示健康數據摘要 (Helper for console output)"""
    if not metric_collection or (not metric_collection.get("data") and not metric_collection.get("status") and not metric_collection.get("daily_metrics") and not metric_collection.get("history")):
        return

    items = metric_collection.get("data", [])
    if not isinstance(items, list):
        items = [items]

    if cmd in ["stress", "heart-rate", "steps", "calories", "spo2", "respiration"]:
        for entry in items:
            if not isinstance(entry, dict): continue
            print("-" * 60)
            print(f"📅 日期: {entry.get('calendarDate')}")
            if cmd in ["summary", "steps"]:
                print(f"🏃 步數: {entry.get('totalSteps', 0)}/{entry.get('dailyStepGoal', 0)} | 距離: {entry.get('totalDistanceMeters', 0) / 1000:.2f}km")
            if cmd in ["summary", "calories"]:
                print(f"🔥 卡路里: 總計 {entry.get('totalKilocalories')} | 基礎 {entry.get('bmrKilocalories')} | 活動 {entry.get('activeKilocalories')}")
            if cmd in ["summary", "heart-rate"]:
                print(f"💓 心率: 靜止 {entry.get('restingHeartRate')} | 最低 {entry.get('minHeartRate')} | 最高 {entry.get('maxHeartRate')}")
            if cmd in ["summary", "stress"]:
                print(f"😫 壓力: 平均 {entry.get('averageStressLevel')} | 最高 {entry.get('maxStressLevel')}")
            if cmd in ["summary", "spo2", "respiration"]:
                print(f"🩸 SpO2: {entry.get('averageSpo2', 'N/A')}% | 🫁 呼吸: {entry.get('avgWakingRespirationValue', 'N/A')} brpm")

    elif cmd == "sleep":
        for s in items:
            if not isinstance(s, dict): continue
            dto = s.get("dailySleepDTO", {})
            score = dto.get("sleepScores", {}).get("overall", {}).get("value", "N/A")
            print(f"😴 {dto.get('calendarDate')} | 分數: {score} | 總計: {format_seconds(dto.get('sleepTimeSeconds', 0))} | 深層: {format_seconds(dto.get('deepSleepSeconds', 0))}")

    elif cmd == "body-battery":
        for b in items:
            if not isinstance(b, dict): continue
            feedback = b.get('bodyBatteryDynamicFeedbackEvent', {}) or {}
            print(f"🔋 {b.get('calendarDate')} | 充電: {b.get('charged')} | 消耗: {b.get('drained')} | 評分: {feedback.get('feedbackShortType', 'N/A')}")

    elif cmd == "hrv":
        for item in items:
            if not isinstance(item, dict): continue
            status = item.get("dailyHrvFeedback", "N/A")
            print(f"💓 {item.get('calendarDate')} | HRV 狀態: {status} | 7日平均: {item.get('lastNightAvg', 'N/A')} ms")

    elif cmd == "weight":
        data = metric_collection.get("data", {})
        entries = data.get("dateWeightList", []) if isinstance(data, dict) and "dateWeightList" in data else items
        for w in entries:
            if not isinstance(w, dict): continue
            ts = w.get("timestamp") or w.get("date")
            if not ts: continue
            dt = datetime.fromtimestamp(ts / 1000).strftime("%Y-%m-%d")
            print(f"⚖️ {dt} | 體重: {w.get('weight', 0) / 1000.0:.2f} kg | BMI: {w.get('bmi', 'N/A')} | 體脂: {w.get('bodyFat', 'N/A')}%")

    elif cmd == "vo2max" or cmd == "training-status":
        if "status" in metric_collection:
            latest = metric_collection["status"].get("latest_status", {})
            if latest: print(f"🏆 訓練狀態: {latest.get('trainingStatusFeedbackPhrase', 'N/A')}")
        if "history" in metric_collection:
            for h in metric_collection["history"]:
                if not isinstance(h, dict): continue
                g = h.get("generic", {})
                print(f"📈 {g.get('calendarDate')} | VO2 Max: {g.get('vo2MaxValue')} | 體能年齡: {g.get('fitnessAge')}")

    elif cmd == "max-hr":
        d = metric_collection.get("daily_metrics", {})
        if d: print(f"💓 {d.get('calendarDate')} | 最大: {d.get('observedMaxHr')} | 安靜: {d.get('restingHr')}")
        for a in metric_collection.get("recent_activities", []):
            if not isinstance(a, dict): continue
            print(f"🏃 {a.get('startTimeLocal')} | Max: {a.get('maxHr', 0):.0f} | {a.get('activityName')}")

    elif cmd == "training-readiness":
        for d in items:
            if not isinstance(d, dict): continue
            calendar_date = d.get('calendarDate', '--')
            score = d.get('score', '--')
            # Handle possible variations in field names
            level = d.get('level') or d.get('trainingReadinessStatus') or d.get('status') or '--'
            feedback = d.get('feedbackShort') or d.get('trainingReadinessFeedback') or d.get('feedback') or '--'
            print(f"🚦 {calendar_date} | 訓練完備度: {score} ({level}) | 建議: {feedback}")

    elif cmd == "fitness-age":
        for d in items:
            if not isinstance(d, dict): continue
            print(f"👶 體能年齡: {d.get('fitnessAge')} | 可達成目標: {d.get('achievableFitnessAge', '--')} | 實際年齡: {d.get('actualAge')}")

    elif cmd == "lactate-threshold":
        for d in items:
            if not isinstance(d, dict): continue
            # Try multiple known key patterns
            hr = d.get('heartRate') or d.get('lactateThresholdHeartRate') or '--'
            speed = d.get('speed') or d.get('lactateThresholdSpeed')
            
            if speed:
                # speed is in m/s, convert to min/km
                total_seconds = 1000 / speed
                minutes = int(total_seconds // 60)
                seconds = int(total_seconds % 60)
                pace = f"{minutes}:{seconds:02d} min/km"
            else:
                pace = "--"
            print(f"🏃 乳酸閾值: 心率 {hr} bpm | 配速 {pace}")

    elif cmd == "race-predictions":
        def fmt_sec(s):
            if not s: return "--"
            try:
                return str(timedelta(seconds=int(float(s))))
            except:
                return "--"
        
        for d in items:
            if not isinstance(d, dict): continue
            
            # Handle List of objects format (v2)
            preds = d.get("racePredictions")
            if isinstance(preds, list):
                p_map = {p.get("distance"): p.get("predictedTime") for p in preds if isinstance(p, dict)}
                print(f"🏁 賽事預測: 5k {fmt_sec(p_map.get(5000))} | 10k {fmt_sec(p_map.get(10000))} | 半馬 {fmt_sec(p_map.get(21097.5) or p_map.get(21100))} | 全馬 {fmt_sec(p_map.get(42195))}")
            else:
                # Handle Flat dict format (v1)
                p = d.get("racePredictions") or d
                print(f"🏁 賽事預測: 5k {fmt_sec(p.get('fiveK'))} | 10k {fmt_sec(p.get('tenK'))} | 半馬 {fmt_sec(p.get('halfMarathon'))} | 全馬 {fmt_sec(p.get('marathon'))}")

    elif cmd == "intensity-minutes":
        for d in items:
            if not isinstance(d, dict): continue
            moderate = d.get('moderateIntensityMinutes') or d.get('moderateValue') or 0
            vigorous = d.get('vigorousIntensityMinutes') or d.get('vigorousValue') or 0
            total = d.get('totalIntensityMinutes') or (moderate + 2 * vigorous)
            print(f"🔥 熱血時間 ({d.get('calendarDate')}): 總計 {total} (中 {moderate} / 高 {vigorous}) | 目標: {d.get('intensityMinutesGoal') or d.get('weeklyGoal') or '--'}")

    elif cmd == "hydration":
        for d in items:
            if not isinstance(d, dict): continue
            print(f"💧 補水 ({d.get('calendarDate')}): 已攝取 {d.get('value')} ml / 目標 {d.get('goal')} ml")

    elif cmd == "personal-records":
        for d in items:
            if not isinstance(d, dict): continue
            print(f"🏆 {d.get('type')}: {d.get('value')} ({d.get('date')})")

    elif cmd == "blood-pressure":
        data = metric_collection.get("data", {})
        summaries = data.get("measurementSummaries", []) if isinstance(data, dict) else []
        for s in summaries:
            print(f"🩸 血壓 ({s.get('calendarDate')}): {s.get('systolic')}/{s.get('diastolic')} | 心率 {s.get('heartRate')}")


def process_health_command(args: argparse.Namespace):
    """整合處理所有健康指標相關邏輯"""
    username, password = resolve_user_auth(args)
    cmd = args.health_command
    metric_collection = {}

    # 初始化必要的 Clients
    health_client = HealthClient(email=username, password=password, session_dir=args.session)

    # 根據子命令分流處理
    try:
        if cmd == "health" or cmd in ["stress", "heart-rate", "steps", "calories", "spo2", "respiration"]:
            if args.start_date:
                data_list = health_client.get_daily_summaries(args.start_date, args.end_date or date.today().isoformat(), show_progress=args.progress)
                if data_list: metric_collection = {"data": [h.model_dump(mode="json") for h in data_list]}
            else:
                data = health_client.get_daily_summary(args.date)
                if data: metric_collection = {"data": data.model_dump(mode="json")}

        elif cmd == "sleep":
            client = SleepClient(email=username, password=password, session_dir=args.session)
            if args.start_date:
                data_list = client.get_sleep_data_range(args.start_date, args.end_date or date.today().isoformat(), show_progress=args.progress)
                if data_list: metric_collection = {"data": [s.model_dump(mode="json") for s in data_list]}
            else:
                data = client.get_sleep_data(args.date)
                if data: metric_collection = {"data": data.model_dump(mode="json")}

        elif cmd == "body-battery":
            client = BodyBatteryClient(email=username, password=password, session_dir=args.session)
            if args.start_date:
                data_list = client.get_body_battery_reports(args.start_date, args.end_date or date.today().isoformat())
                if data_list: metric_collection = {"data": [h.model_dump(mode="json") for h in data_list]}
            else:
                data = client.get_body_battery_report(args.date)
                if data: metric_collection = {"data": data.model_dump(mode="json")}

        elif cmd == "hrv":
            client = HrvClient(email=username, password=password, session_dir=args.session)
            if args.start_date:
                data_list = client.get_hrv_data_range(args.start_date, args.end_date or date.today().isoformat(), show_progress=args.progress)
                if data_list: metric_collection = {"data": [h.model_dump(mode="json") for h in data_list]}
            else:
                data = client.get_hrv_data(args.date)
                if data: metric_collection = {"data": data.model_dump(mode="json")}
            if not getattr(args, "detailed", False) and metric_collection.get("data"):
                items = metric_collection["data"] if isinstance(metric_collection["data"], list) else [metric_collection["data"]]
                for item in items:
                    if "hrvReadings" in item: del item["hrvReadings"]

        elif cmd == "weight":
            client = WeightClient(email=username, password=password, session_dir=args.session)
            upload_val = getattr(args, "upload", None)
            if upload_val:
                if client.upload_weight(upload_val, args.date):
                    logger.success(f"已上傳 {upload_val} kg 至 {args.date}")
                return
            if args.start_date:
                history = client.get_weight_history(args.start_date, args.end_date or date.today().isoformat())
                if history: metric_collection = {"data": history.model_dump(mode="json")}
            else:
                entry = client.get_latest_weight(args.date)
                if entry: metric_collection = {"data": entry.model_dump(mode="json")}

        elif cmd == "vo2max" or cmd == "training-status":
            client = Vo2MaxClient(email=username, password=password, session_dir=args.session)
            if args.start_date:
                history = client.get_vo2max_history(args.start_date, args.end_date or date.today().isoformat())
                if history: metric_collection["history"] = [h.model_dump(mode="json") for h in history]
            status = client.get_training_status(args.date)
            if status:
                metric_collection["status"] = status.model_dump(mode="json")
                if status.latest_status:
                    metric_collection["status"]["latest_status"] = status.latest_status.model_dump(mode="json")

        elif cmd == "max-hr":
            client = MaxHrClient(email=username, password=password, session_dir=args.session)
            daily = client.get_daily_hr_metrics(args.date)
            if daily: metric_collection["daily_metrics"] = daily.model_dump(mode="json")
            limit_val = getattr(args, "limit", 5)
            recent = client.get_recent_activity_max_hr(limit=limit_val)
            if recent: metric_collection["recent_activities"] = [a.model_dump(mode="json") for a in recent]
        elif cmd == "training-readiness":
            if args.start_date:
                data_list = health_client.get_training_readiness_range(args.start_date, args.end_date or date.today().isoformat(), show_progress=args.progress)
                if data_list: metric_collection = {"data": data_list}
            else:
                data = health_client.get_training_readiness(args.date)
                if data: metric_collection = {"data": data}

        elif cmd == "fitness-age":
            data = health_client.get_fitness_age(args.date)
            if data: metric_collection = {"data": data}

        elif cmd == "lactate-threshold":
            data = health_client.get_lactate_threshold()
            if data: metric_collection = {"data": data}

        elif cmd == "race-predictions":
            data = health_client.get_race_predictions()
            if data: metric_collection = {"data": data}

        elif cmd == "intensity-minutes":
            if args.start_date:
                data = health_client.get_intensity_minutes(args.start_date, args.end_date or date.today().isoformat(), show_progress=args.progress)
            else:
                data = health_client.get_intensity_minutes(args.date, args.date)
            if data: metric_collection = {"data": data}

        elif cmd == "hydration":
            data = health_client.get_hydration(args.date)
            if data: metric_collection = {"data": data}

        elif cmd == "personal-records":
            data = health_client.get_personal_records()
            if data: metric_collection = {"data": data}

        elif cmd == "spo2":
            data = health_client.get_daily_summary(args.date)
            if data: metric_collection = {"data": data.model_dump(mode="json")}

        elif cmd == "respiration":
            data = health_client.get_daily_summary(args.date)
            if data: metric_collection = {"data": data.model_dump(mode="json")}

        elif cmd == "blood-pressure":
            data = health_client.get_blood_pressure(args.start_date or args.date, args.end_date or date.today().isoformat())
            if data: metric_collection = {"data": data}

        # 顯示摘要 (重用顯示邏輯)
        if args.summary:
            display_health_summary(cmd, metric_collection, args)

    except Exception as e:
        logger.error(f"執行健康數據子命令 '{cmd}' 失敗: {e}")
        return

    # 處理輸出
    output_path = args.output
    if not output_path and not args.summary:
        output_path = resolve_default_output_path("health", args)

    if output_path:
        # 如果是 .txt，則跳過 JSON 儲存 (因為 display_health_summary 已經儲存過表格了)
        if output_path.endswith(".txt"):
            return

        # 僅在有獲取到實際數據時才儲存，避免覆蓋有效舊檔
        if not metric_collection or (not metric_collection.get("data") and not metric_collection.get("status") and not metric_collection.get("daily_metrics")):
            logger.warning(f"跳過儲存: 無有效數據 ({cmd})")
            return

        if not args.over_write and os.path.exists(output_path):
            logger.info(f"檔案已存在，跳過儲存: {output_path}")
        else:
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(metric_collection, f, indent=4, ensure_ascii=False)
            logger.success(f"資料已儲存至: {output_path}")
    elif not args.summary:
        print(json.dumps(metric_collection, indent=4, ensure_ascii=False))


def fetch_race_calendar(args: argparse.Namespace):
    username, password = resolve_user_auth(args)
    client = RaceEventClient(email=username, password=password, session_dir=args.session)

    # 獲取完整賽事清單 (抓取一個極廣的範圍以符合「所有賽事」需求)
    start_date = "2020-01-01"
    end_date = "2099-12-31"

    raw_events = client.list_events(start_date=start_date, end_date=end_date)

    validated = []
    for e in raw_events:
        try:
            validated.append(RaceEventModel.model_validate(e))
        except:
            continue

    if args.summary:
        today = date.today()
        upcoming = [e for e in validated if e.event_date >= today]
        past = [e for e in validated if e.event_date < today]

        def get_dist_str(e: RaceEventModel) -> str:
            if not e.completion_target or not e.completion_target.value:
                return "--"
            val = e.completion_target.value
            unit = (e.completion_target.unit or "").lower()
            if "meter" in unit:
                return f"{val / 1000:.2f} km"
            elif "kilometer" in unit:
                return f"{val:.2f} km"
            return f"{val} {unit}"

        # 欄位寬度定義
        W_DATE, W_CAT, W_NAME, W_DIST, W_TYPE = 12, 12, 35, 12, 15
        
        header = (
            f"{pad_text('時間', W_DATE)} | "
            f"{pad_text('分類', W_CAT)} | "
            f"{pad_text('賽事名稱', W_NAME)} | "
            f"{pad_text('距離', W_DIST)} | "
            f"{pad_text('類型', W_TYPE)}"
        )
        
        print("\n" + "=" * len(header))
        print(header)
        print("-" * len(header))
        
        print(f"🏆 我的賽事 (Upcoming)")
        if not upcoming:
            print("  無即將到來的賽事")
        else:
            for e in sorted(upcoming, key=lambda x: x.event_date):
                dist = get_dist_str(e)
                print(
                    f"{pad_text(str(e.event_date), W_DATE)} | "
                    f"{pad_text('我的賽事', W_CAT)} | "
                    f"{pad_text(e.event_name, W_NAME)} | "
                    f"{pad_text(dist, W_DIST)} | "
                    f"{pad_text(e.event_type or '--', W_TYPE)}"
                )
        
        print("\n" + "-" * len(header))
        print(f"🕒 過去賽事 (Past)")
        if not past:
            print("  無過去賽事紀錄")
        else:
            # 過去賽事由近到遠排序
            for e in sorted(past, key=lambda x: x.event_date, reverse=True):
                dist = get_dist_str(e)
                print(
                    f"{pad_text(str(e.event_date), W_DATE)} | "
                    f"{pad_text('過去賽事', W_CAT)} | "
                    f"{pad_text(e.event_name, W_NAME)} | "
                    f"{pad_text(dist, W_DIST)} | "
                    f"{pad_text(e.event_type or '--', W_TYPE)}"
                )
        print("=" * len(header))

    output_path = args.output
    if not output_path and not args.summary:
        output_path = resolve_default_output_path("race-event", args)

    if output_path:
        if not args.over_write and os.path.exists(output_path):
            logger.info(f"檔案已存在，跳過儲存: {output_path}")
        else:
            output_data = [e.model_dump(mode="json", by_alias=True) for e in validated]
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(output_data, f, indent=4, ensure_ascii=False)
            logger.success(f"資料已儲存至: {output_path}")
    elif not args.summary:
        print(json.dumps([e.model_dump(mode="json", by_alias=True) for e in validated], indent=4, ensure_ascii=False))


def execute_combined_summary(args: argparse.Namespace):
    """處理頂層 summary 命令：優先從本地快取彙整資料，若無資料則從 API 下載 (符合 garmin_tools.md 規範)"""
    target_dates = []

    if getattr(args, "date", None):
        target_dates = [args.date]
    else:
        # 計算過去 N 天 (含今天)
        days = getattr(args, "days", 7) # 預設改為 7 天
        end_date = date.today()
        start_date = end_date - timedelta(days=days-1)
        delta = (end_date - start_date).days + 1
        target_dates = [(start_date + timedelta(days=i)).isoformat() for i in range(delta)]

    # 建立日期索引的資料字典，避免多次讀取檔案
    data_map = {d: {"calendarDate": d} for d in target_dates}
    # 追蹤每個日期缺失的指標
    missing_data = {d: {"health", "sleep", "hrv", "bp", "readiness"} for d in target_dates}

    def scan_and_index(directory: str, metric_type: str, index_logic):
        if not os.path.exists(directory):
            return
        files = [f for f in os.listdir(directory) if f.endswith(".json")]
        for filename in sorted(files):
            file_path = os.path.join(directory, filename)
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = json.load(f)
                    if content:
                        found_dates = index_logic(content)
                        for d in (found_dates or []):
                            if d in missing_data:
                                missing_data[d].discard(metric_type)
            except Exception as e:
                logger.debug(f"⚠️ 讀取檔案 {file_path} 失敗: {e}")

    # 1. 核心健康數據 (health)
    def index_health(content):
        found = []
        data_list = content.get("data", [])
        if not isinstance(data_list, list): data_list = [data_list]
        for h in data_list:
            if not h: continue
            d = h.get("calendarDate")
            if d in target_dates:
                data_map[d].update(h)
                found.append(d)
        return found

    # 2. 睡眠分數 (sleep)
    def index_sleep(content):
        found = []
        data_list = content.get("data", [])
        if not isinstance(data_list, list): data_list = [data_list]
        for s in data_list:
            if not s: continue
            dto = s.get("dailySleepDTO", {})
            if not dto: continue
            d = dto.get("calendarDate")
            if d in target_dates:
                scores = dto.get("sleepScores") or {}
                score = scores.get("overall", {}).get("value", "--")
                data_map[d]["sleep_score"] = score
                found.append(d)
        return found

    # 3. HRV 趨勢 (hrv)
    def index_hrv(content):
        found = []
        data = content.get("data") or {}
        if isinstance(data, dict):
            data_list = [data.get("hrvSummary") or data]
        else:
            data_list = data
        if not isinstance(data_list, list): data_list = [data_list]
        for h in data_list:
            if not h or not isinstance(h, dict): continue
            d = h.get("calendarDate")
            if d in target_dates:
                data_map[d]["hrv_avg"] = h.get("lastNightAvg", "--")
                found.append(d)
        return found

    # 4. 血壓 (blood-pressure)
    def index_bp(content):
        found = []
        summaries = (content.get("data") or {}).get("measurementSummaries", [])
        for s in summaries:
            if not s: continue
            d = s.get("calendarDate")
            if d in target_dates:
                data_map[d]["blood_pressure"] = f"{s.get('systolic')}/{s.get('diastolic')}"
                found.append(d)
        return found

    # 5. 訓練完備度 (readiness)
    def index_readiness(content):
        found = []
        data_list = content.get("data", [])
        if not isinstance(data_list, list): data_list = [data_list]
        for d_item in data_list:
            if not d_item: continue
            d = d_item.get("calendarDate")
            if d in target_dates:
                data_map[d]["readiness_score"] = d_item.get("score", "--")
                found.append(d)
        return found

    # 首次掃描
    scan_and_index("data/health", "health", index_health)
    scan_and_index("data/sleep", "sleep", index_sleep)
    scan_and_index("data/hrv", "hrv", index_hrv)
    scan_and_index("data/blood-pressure", "bp", index_bp)
    scan_and_index("data/training-readiness", "readiness", index_readiness)

    # 檢查是否有缺失資料，有的話才下載
    all_missing_metrics = set().union(*(missing_data[d] for d in target_dates))
    if any(missing_data[d] for d in target_dates):
        logger.info(f"正在彙整 {len(target_dates)} 天的健康資料，偵測到部分日期缺失，準備從 API 下載...")
        username, password = resolve_user_auth(args)
        
        for metric in all_missing_metrics:
            dates_to_download = [d for d in target_dates if metric in missing_data[d]]
            if not dates_to_download: continue
            
            try:
                if metric == "health":
                    client = HealthClient(email=username, password=password, session_dir=args.session)
                    for d in dates_to_download:
                        data = client.get_daily_summary(d)
                        if data:
                            save_path = resolve_default_output_path("health", argparse.Namespace(health_command="health", date=d))
                            with open(save_path, "w", encoding="utf-8") as f:
                                json.dump({"data": data.model_dump(mode="json")}, f, indent=4, ensure_ascii=False)
                            index_health({"data": data.model_dump(mode="json")})
                elif metric == "sleep":
                    client = SleepClient(email=username, password=password, session_dir=args.session)
                    for d in dates_to_download:
                        data = client.get_sleep_data(d)
                        if data:
                            save_path = resolve_default_output_path("health", argparse.Namespace(health_command="sleep", date=d))
                            with open(save_path, "w", encoding="utf-8") as f:
                                json.dump({"data": data.model_dump(mode="json")}, f, indent=4, ensure_ascii=False)
                            index_sleep({"data": data.model_dump(mode="json")})
                elif metric == "hrv":
                    client = HrvClient(email=username, password=password, session_dir=args.session)
                    for d in dates_to_download:
                        data = client.get_hrv_data(d)
                        if data:
                            save_path = resolve_default_output_path("health", argparse.Namespace(health_command="hrv", date=d))
                            with open(save_path, "w", encoding="utf-8") as f:
                                json.dump({"data": data.model_dump(mode="json")}, f, indent=4, ensure_ascii=False)
                            index_hrv({"data": data.model_dump(mode="json")})
                elif metric == "bp":
                    client = HealthClient(email=username, password=password, session_dir=args.session)
                    # 抓取缺失日期範圍
                    sd, ed = min(dates_to_download), max(dates_to_download)
                    data = client.get_blood_pressure(sd, ed)
                    if data:
                        save_path = resolve_default_output_path("health", argparse.Namespace(health_command="blood-pressure", start_date=sd, end_date=ed))
                        with open(save_path, "w", encoding="utf-8") as f:
                            json.dump({"data": data}, f, indent=4, ensure_ascii=False)
                        index_bp({"data": data})
                elif metric == "readiness":
                    client = HealthClient(email=username, password=password, session_dir=args.session)
                    for d in dates_to_download:
                        data = client.get_training_readiness(d)
                        if data:
                            save_path = resolve_default_output_path("health", argparse.Namespace(health_command="training-readiness", date=d))
                            with open(save_path, "w", encoding="utf-8") as f:
                                json.dump({"data": data}, f, indent=4, ensure_ascii=False)
                            index_readiness({"data": data})
            except Exception as e:
                logger.error(f"下載 {metric} 資料失敗: {e}")
    else:
        logger.info(f"所有目標日期 ({len(target_dates)} 天) 的本地資料已齊備。")

    local_items = []
    for d in target_dates:
        item = data_map[d]
        relevant_keys = ["totalSteps", "restingHeartRate", "sleep_score", "hrv_avg", "blood_pressure"]
        if any(k in item for k in relevant_keys):
            local_items.append(item)

    if not local_items:
        logger.warning("未找到任何健康數據 (本地或 API)。")
        return

    # 顯示表格並存檔
    display_health_table(local_items, output_file=getattr(args, "output", None))
