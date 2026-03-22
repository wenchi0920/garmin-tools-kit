#!/usr/bin/env python3
"""
Purpose: Garmin Connect 工具包整合入口，支援活動、訓練計畫、健康數據、體重等全面管理。
Author: Gemini CLI
Changelog:
2026-03-08: 1.2.1 - 初始整合版本，合併 10 個獨立工具為統一 CLI 入口。
2026-03-09: 1.4.0 - 命名重構與輸出邏輯優化 (支援 --summary 與 -o 同時使用)。
2026-03-10: 1.4.1 - 完善 README.md 文件與補齊 subcommand 範例。
2026-03-11: 1.4.1 - 新增 --progress 全域參數，支援 tqdm 進度條與 log 同步輸出。
2026-03-11: 1.4.1 - 支援預設執行指令：不帶子命令時預設執行 activity -c 5。
2026-03-11: 1.4.2 - 版本手動更新。
2026-03-12: 1.4.2 - 實作資料存放標準化 (Data Storage Standardization) 與自動目錄生成，符合 garmin_tools.md 規範。
2026-03-12: 1.4.2 - 重構 COMMAND_HANDLERS 結構並修正 Docker 備份排程 (AM 11:00) 以符合 GEMINI.md 規範。
2026-03-17: 1.4.3 - 修正 fetch_race_calendar 忽略日期範圍 (-sd, -ed) 的 bug 並優化空結果 summary 輸出。
2026-03-21: 1.4.1 - 重構健康數據子命令結構，將所有健康指標整合進 health 父命令下，並新增細項指標抓取。
2026-03-21: 1.4.1 - 優化 resolve_default_output_path 以消除檔名中的冗餘目錄前綴，並更新整合測試腳本。
2026-03-22: 1.4.1 - 智慧啟動優化：主程式與子命令 (activity, workout, health, race-event) 未帶參數時預設執行 --help。
2026-03-22: 1.4.3 - 版本手動更新，優化健康數據異常攔截、寫檔判定邏輯與 Pydantic 模型容錯。
"""
import argparse
import getpass
import json
import os
import sys
from datetime import datetime, date, timedelta
from typing import Dict, Any, List

import yaml
from loguru import logger
from tqdm import tqdm

# Import Clients and Models
from client import (
    ActivityClient, BodyBatteryClient, HealthClient, HrvClient,
    MaxHrClient, SleepClient, Vo2MaxClient, WeightClient,
    WorkoutClient, WorkoutDSLParser, RaceEventClient
)
from models.raceEventModel import RaceEventModel

VERSION = "1.4.3"


# ==============================================================================
# 共通工具函式 (Utility Functions)
# ==============================================================================

def configure_runtime_logger(verbosity: int, use_progress: bool = False) -> None:
    """設定 Loguru 日誌層級與格式"""
    logger.remove()
    if verbosity == 0:
        level = "INFO"
    elif verbosity == 1:
        level = "DEBUG"
    else:
        level = "TRACE"
    
    log_format = "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{message}</cyan>"
    
    if use_progress:
        # 當啟用 progress 時，使用 tqdm.write 來避免破壞進度條
        logger.add(
            lambda msg: tqdm.write(msg, end=""),
            level=level,
            format=log_format,
            colorize=True
        )
    else:
        logger.add(
            sys.stderr,
            level=level,
            format=log_format
        )


def load_env_file(file_path: str) -> Dict[str, str]:
    """載入 .env 檔案"""
    env_data: Dict[str, str] = {}
    if not os.path.exists(file_path):
        return env_data
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, value = line.split("=", 1)
                env_data[key.strip()] = value.strip().strip("'").strip("\"")
    except Exception as e:
        logger.error(f"讀取 env-file 錯誤: {e}")
    return env_data


def resolve_user_auth(args: argparse.Namespace) -> tuple[str, str]:
    """獲取使用者名稱與密碼"""
    username = args.username
    password = args.password

    env_file_path = args.env_file or (".env" if os.path.exists(".env") else None)
    if env_file_path:
        env_vars = load_env_file(env_file_path)
        username = username or env_vars.get("GARMIN_USERNAME") or env_vars.get("USERNAME")
        password = password or env_vars.get("GARMIN_PASSWORD") or env_vars.get("PASSWORD")

    # 檢查環境變數
    username = username or os.environ.get("GARMIN_USERNAME") or os.environ.get("USERNAME")
    password = password or os.environ.get("GARMIN_PASSWORD") or os.environ.get("PASSWORD")

    if not username:
        username = input("Garmin Connect 使用者名稱: ")
    if not password:
        password = getpass.getpass("Garmin Connect 密碼: ")

    return username, password


def format_seconds(seconds: Any) -> str:
    """格式化秒數為 時:分"""
    try:
        # 處理可能的 MagicMock 或 None
        sec = int(seconds) if seconds is not None else 0
    except (ValueError, TypeError):
        sec = 0
    hours, remainder = divmod(sec, 3600)
    minutes, _ = divmod(remainder, 60)
    return f"{hours}時{minutes}分"


def resolve_default_output_path(command: str, args: argparse.Namespace) -> str:
    """根據子命令與參數產生預設儲存路徑 (符合 garmin_tools.md 規範)"""
    base_dir = "data"
    sub_dir = command
    file_prefix = command
    
    # 支援 health 相關細項目錄
    if hasattr(args, "health_command") and args.health_command:
        # 特殊處理: summary 統一存在 data/health/
        if args.health_command == "summary":
            sub_dir = "health"
            file_prefix = "health"
        else:
            sub_dir = args.health_command
            file_prefix = args.health_command
            
        # 特殊處理: body-battery 包含年份資料夾
        if args.health_command == "body-battery":
            target_date = getattr(args, "date", None) or getattr(args, "start_date", None) or datetime.now().strftime("%Y-%m-%d")
            year = target_date[:4]
            sub_dir = f"body-battery_{year}"
    
    target_dir = os.path.join(base_dir, sub_dir)
    if not os.path.exists(target_dir):
        os.makedirs(target_dir, exist_ok=True)
        
    start_date = getattr(args, "start_date", None)
    end_date = getattr(args, "end_date", None)
    date_val = getattr(args, "date", None)

    if start_date and end_date:
        filename = f"{file_prefix}_{start_date}_{end_date}.json"
    elif start_date:
        filename = f"{file_prefix}_{start_date}_latest.json"
    else:
        filename = f"{file_prefix}_{date_val}.json"
        
    return os.path.join(target_dir, filename)


# ==============================================================================
# 子命令處理邏輯 (Command Handlers)
# ==============================================================================

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


def process_health_command(args: argparse.Namespace):
    """整合處理所有健康指標相關邏輯"""
    username, password = resolve_user_auth(args)
    cmd = args.health_command
    metric_collection = {}

    # 初始化必要的 Clients
    health_client = HealthClient(email=username, password=password, session_dir=args.session)
    
    # 根據子命令分流處理
    try:
        if cmd in ["summary", "stress", "heart-rate", "steps", "calories", "spo2", "respiration"]:
            if args.start_date:
                data_list = health_client.get_daily_summaries(args.start_date, args.end_date or date.today().isoformat(), show_progress=args.progress)
                if data_list: metric_collection = {"data": [h.model_dump(mode="json") for h in data_list]}
            else:
                data = health_client.get_daily_summary(args.date)
                if data: metric_collection = {"data": data.model_dump(mode="json")}
            
            if args.summary and metric_collection.get("data"):
                items = metric_collection["data"] if isinstance(metric_collection["data"], list) else [metric_collection["data"]]
                for entry in items:
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
            client = SleepClient(email=username, password=password, session_dir=args.session)
            if args.start_date:
                data_list = client.get_sleep_data_range(args.start_date, args.end_date or date.today().isoformat(), show_progress=args.progress)
                if data_list: metric_collection = {"data": [s.model_dump(mode="json") for s in data_list]}
            else:
                data = client.get_sleep_data(args.date)
                if data: metric_collection = {"data": data.model_dump(mode="json")}
            if args.summary and metric_collection.get("data"):
                items = metric_collection["data"] if isinstance(metric_collection["data"], list) else [metric_collection["data"]]
                for s in items:
                    dto = s.get("dailySleepDTO", {})
                    score = dto.get("sleepScores", {}).get("overall", {}).get("value", "N/A")
                    print(f"😴 {dto.get('calendarDate')} | 分數: {score} | 總計: {format_seconds(dto.get('sleepTimeSeconds', 0))} | 深層: {format_seconds(dto.get('deepSleepSeconds', 0))}")

        elif cmd == "body-battery":
            client = BodyBatteryClient(email=username, password=password, session_dir=args.session)
            if args.start_date:
                data_list = client.get_body_battery_reports(args.start_date, args.end_date or date.today().isoformat())
                if data_list: metric_collection = {"data": [h.model_dump(mode="json") for h in data_list]}
            else:
                data = client.get_body_battery_report(args.date)
                if data: metric_collection = {"data": data.model_dump(mode="json")}
            if args.summary and metric_collection.get("data"):
                items = metric_collection["data"] if isinstance(metric_collection["data"], list) else [metric_collection["data"]]
                for b in items:
                    feedback = b.get('bodyBatteryDynamicFeedbackEvent', {}) or {}
                    print(f"🔋 {b.get('calendarDate')} | 充電: {b.get('charged')} | 消耗: {b.get('drained')} | 評分: {feedback.get('feedbackShortType', 'N/A')}")

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
            if args.summary and metric_collection.get("data"):
                data = metric_collection["data"]
                entries = data["dateWeightList"] if "dateWeightList" in data else [data]
                for w in entries:
                    ts = w.get("timestamp") or w.get("date")
                    dt = datetime.fromtimestamp(ts / 1000).strftime("%Y-%m-%d")
                    print(f"⚖️ {dt} | 體重: {w.get('weight', 0) / 1000.0:.2f} kg | BMI: {w.get('bmi', 'N/A')} | 體脂: {w.get('bodyFat', 'N/A')}%")

        elif cmd == "vo2max" or cmd == "training-status":
            client = Vo2MaxClient(email=username, password=password, session_dir=args.session)
            if args.start_date:
                history = client.get_vo2max_history(args.start_date, args.end_date or date.today().isoformat())
                if history: metric_collection["history"] = [h.model_dump(mode="json") for h in history]
            status = client.get_training_status(args.date)
            if status:
                metric_collection["status"] = status.model_dump(mode="json")
                metric_collection["status"]["latest_status"] = status.latest_status.model_dump(mode="json") if status.latest_status else None
            if args.summary:
                if "status" in metric_collection:
                    latest = metric_collection["status"].get("latest_status", {})
                    print(f"🏆 訓練狀態: {latest.get('trainingStatusFeedbackPhrase', 'N/A')}")
                if "history" in metric_collection:
                    for h in metric_collection["history"]:
                        g = h.get("generic", {})
                        print(f"📈 {g.get('calendarDate')} | VO2 Max: {g.get('vo2MaxValue')} | 體能年齡: {g.get('fitnessAge')}")

        elif cmd == "max-hr":
            client = MaxHrClient(email=username, password=password, session_dir=args.session)
            if getattr(args, "from_file", False): logger.info("正在檢查本地快取數據...")
            daily = client.get_daily_hr_metrics(args.date)
            if daily: metric_collection["daily_metrics"] = daily.model_dump(mode="json")
            limit_val = getattr(args, "limit", 5)
            recent = client.get_recent_activity_max_hr(limit=limit_val)
            if recent: metric_collection["recent_activities"] = [a.model_dump(mode="json") for a in recent]
            if args.summary:
                d = metric_collection.get("daily_metrics", {})
                if d: print(f"💓 {d.get('calendarDate')} | 最大: {d.get('observedMaxHr')} | 安靜: {d.get('restingHr')}")
                for a in metric_collection.get("recent_activities", []):
                    print(f"🏃 {a.get('startTimeLocal')} | Max: {a.get('maxHr', 0):.0f} | {a.get('activityName')}")

        elif cmd == "training-readiness":
            data = health_client.get_training_readiness(args.date)
            if data: metric_collection = {"data": data}
            if args.summary and metric_collection.get("data"):
                d = metric_collection["data"]
                print(f"🚦 訓練完備度: {d.get('score')} ({d.get('status')}) | 建議: {d.get('feedback')}")

        elif cmd == "fitness-age":
            data = health_client.get_fitness_age()
            if data: metric_collection = {"data": data}
            if args.summary and metric_collection.get("data"):
                d = metric_collection["data"]
                print(f"👶 體能年齡: {d.get('fitnessAge')} | 實際年齡: {d.get('actualAge')}")

        elif cmd == "lactate-threshold":
            data = health_client.get_lactate_threshold()
            if data: metric_collection = {"data": data}

        elif cmd == "race-predictions":
            data = health_client.get_race_predictions()
            if data: metric_collection = {"data": data}

        elif cmd == "intensity-minutes":
            data = health_client.get_intensity_minutes(args.start_date or args.date, args.end_date or args.date)
            if data: metric_collection = {"data": data}

        elif cmd == "hydration":
            data = health_client.get_hydration(args.date)
            if data: metric_collection = {"data": data}

        elif cmd == "personal-records":
            data = health_client.get_personal_records()
            if data: metric_collection = {"data": data}

        elif cmd == "insights":
            data = health_client.get_insights()
            if data: metric_collection = {"data": data}

        elif cmd == "spo2":
            data = health_client.get_daily_summary(args.date)
            if data: metric_collection = {"data": data.model_dump(mode="json")}
            if args.summary and metric_collection.get("data"):
                 print(f"🩸 SpO2: {metric_collection['data'].get('averageSpo2', 'N/A')}%")

        elif cmd == "respiration":
            data = health_client.get_daily_summary(args.date)
            if data: metric_collection = {"data": data.model_dump(mode="json")}
            if args.summary and metric_collection.get("data"):
                 print(f"🫁 呼吸: {metric_collection['data'].get('avgWakingRespirationValue', 'N/A')} brpm")

        elif cmd == "blood-pressure":
            data = health_client.get_blood_pressure(args.start_date or args.date, args.end_date or date.today().isoformat())
            if data: metric_collection = {"data": data}
    except Exception as e:
        logger.error(f"執行健康數據子命令 '{cmd}' 失敗: {e}")
        return

    # 處理輸出
    output_path = args.output
    if not output_path and not args.summary:
        output_path = resolve_default_output_path("health", args)

    if output_path:
        # 僅在有獲取到實際數據時才儲存，避免覆蓋有效舊檔
        if not metric_collection or (isinstance(metric_collection.get("data"), list) and not metric_collection["data"]):
            logger.warning(f"跳過儲存: 無有效數據可供儲存 ({cmd})")
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

    if args.start_date:
        start_date = args.start_date
        end_date = args.end_date or date.today().isoformat()
    else:
        start_date = args.date
        end_date = args.date

    raw_events = client.list_events(start_date=start_date, end_date=end_date)

    validated = []
    for e in raw_events:
        try:
            validated.append(RaceEventModel.model_validate(e))
        except:
            continue

    if args.summary:
        print("\n" + "=" * 60)
        if not validated:
            print(f"📅 {start_date} ~ {end_date} 期間無賽事紀錄")
        else:
            for e in sorted(validated, key=lambda x: x.event_date):
                print(f"📅 {e.event_date} | 🏆 {e.event_name} | 🏃 {e.event_type}")
        print("=" * 60)

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


# ==============================================================================
# 全域常數與對應處理函式 (Constants & Command Handlers)
# ==============================================================================

COMMAND_HANDLERS = {
    "activity": execute_activity_export,
    "workout": manage_workout_workflow,
    "health": process_health_command,
    "race-event": fetch_race_calendar
}


def main():
    """程式入口點 (Entry Point)"""
    parser = argparse.ArgumentParser(description="Garmin Connect 整合工具包 (v" + VERSION + ")")
    parser.add_argument("--version", action="version", version=f"%(prog)s {VERSION}")
    parser.add_argument("-v", "--verbosity", action="count", default=0, help="詳細度")
    parser.add_argument("--username", help="Garmin 帳號")
    parser.add_argument("--password", help="Garmin 密碼")
    parser.add_argument("--env-file", nargs="?", const=".env", help="使用 env file (預設: .env)")
    parser.add_argument("-ss", "--session", default=".garth", help="SSO 目錄")
    parser.add_argument("--over-write", action="store_true", help="如果檔案存在則覆蓋，否則忽略已存在的檔案")
    parser.add_argument("--progress", action="store_true", help="顯示目前進度，啟用表示 用 tqdm 顯示目前進度/也要顯示log")
    parser.add_argument("--gui", action="store_true", help="啟動圖形化使用者介面 (GUI)")

    subparsers = parser.add_subparsers(dest="command", help="子命令 (未指定則顯示 --help)")

    # Activity
    activity_parser = subparsers.add_parser("activity", help="活動匯出")
    activity_parser.add_argument("-c", "--count", default="10", help="支援整數或 all, 預設 10")
    activity_parser.add_argument("-d", "--date", help="指定單一日期 (YYYY-MM-DD)")
    activity_parser.add_argument("-sd", "--start-date", "--start_date")
    activity_parser.add_argument("-ed", "--end-date", "--end_date")
    activity_parser.add_argument("-f", "--format", choices=["gpx", "tcx", "original", "json"], default="original")
    activity_parser.add_argument("--directory", default="data/activity")
    activity_parser.add_argument("-ot", "--originaltime", action="store_true", default=True, help="修正檔案時間 (預設啟用)")
    activity_parser.add_argument("--desc", nargs="?", const=True)

    # Workout
    workout_parser = subparsers.add_parser("workout", help="訓練計畫管理")
    workout_subparsers = workout_parser.add_subparsers(dest="workout_command", required=True)
    workout_subparsers.add_parser("list", help="列出計畫")
    p_wget = workout_subparsers.add_parser("get", help="下載計畫")
    p_wget.add_argument("id")
    p_wget.add_argument("-o", "--output")
    p_wup = workout_subparsers.add_parser("upload", help="上傳計畫 (YAML/DSL)")
    p_wup.add_argument("file")
    p_wdel = workout_subparsers.add_parser("delete", help="刪除計畫")
    p_wdel.add_argument("id")

    # Race Event
    race_parser = subparsers.add_parser("race-event", help="賽事清單與行事曆看板")
    race_parser.add_argument("-d", "--date", default=date.today().isoformat())
    race_parser.add_argument("-sd", "--start-date", "--start_date")
    race_parser.add_argument("-ed", "--end-date", "--end_date")
    race_parser.add_argument("--summary", action="store_true")
    race_parser.add_argument("-o", "--output")

    # Health Subparsers
    health_parser = subparsers.add_parser("health", help="每日健康數據管理，包含步數、心率、能量、壓力、訓練指標等")
    health_subparsers = health_parser.add_subparsers(dest="health_command", required=True)

    # Health Subcommands
    def add_health_sub(sub_parser, name, help_text, has_detailed=False, has_upload=False, has_limit=False, has_from_file=False):
        p = sub_parser.add_parser(name, help=help_text)
        p.add_argument("-d", "--date", default=date.today().isoformat())
        p.add_argument("-sd", "--start-date", "--start_date")
        p.add_argument("-ed", "--end-date", "--end_date")
        p.add_argument("--summary", action="store_true", help="顯示文字摘要")
        p.add_argument("-o", "--output", help="儲存至指定 JSON 檔案")
        if has_detailed:
            p.add_argument("--detailed", action="store_true", help="包含詳細採樣點資料")
        if has_upload:
            p.add_argument("--upload", type=float, metavar="KG", help="上傳一筆新的體重紀錄 (kg)")
        if has_limit:
            p.add_argument("-l", "--limit", type=int, default=5, metavar="LIMIT", help="查詢最近活動的最大心率筆數")
        if has_from_file:
            p.add_argument("--from-file", action="store_true", help="優先從本地已下載的檔案讀取數據")
        return p

    add_health_sub(health_subparsers, "summary", "綜合健康摘要")
    add_health_sub(health_subparsers, "sleep", "睡眠數據")
    add_health_sub(health_subparsers, "body-battery", "身體能量指數")
    add_health_sub(health_subparsers, "hrv", "心率變異度 (HRV)", has_detailed=True)
    add_health_sub(health_subparsers, "weight", "體重管理", has_upload=True)
    add_health_sub(health_subparsers, "vo2max", "VO2 Max 與訓練狀態")
    add_health_sub(health_subparsers, "max-hr", "最大心率統計", has_limit=True, has_from_file=True)
    add_health_sub(health_subparsers, "stress", "壓力水準")
    add_health_sub(health_subparsers, "heart-rate", "每日心率")
    add_health_sub(health_subparsers, "steps", "步數統計")
    add_health_sub(health_subparsers, "calories", "卡路里消耗")
    add_health_sub(health_subparsers, "training-readiness", "訓練完備度")
    add_health_sub(health_subparsers, "training-status", "目前訓練狀態與負荷分析")
    add_health_sub(health_subparsers, "fitness-age", "體能年齡")
    add_health_sub(health_subparsers, "lactate-threshold", "乳酸閾值")
    add_health_sub(health_subparsers, "race-predictions", "賽事預測")
    add_health_sub(health_subparsers, "intensity-minutes", "熱血時間")
    add_health_sub(health_subparsers, "hydration", "補水紀錄")
    add_health_sub(health_subparsers, "personal-records", "個人紀錄")
    add_health_sub(health_subparsers, "insights", "Garmin Insights")
    add_health_sub(health_subparsers, "spo2", "脈搏血氧 (SpO2)")
    add_health_sub(health_subparsers, "respiration", "呼吸頻率")
    add_health_sub(health_subparsers, "blood-pressure", "血壓紀錄")

    # 若執行時未帶任何參數，或子命令後面未帶參數，則自動加上 --help 以符合 GEMINI.md 規範
    if len(sys.argv) == 1:
        sys.argv.append("--help")
    elif len(sys.argv) > 1 and sys.argv[-1] in COMMAND_HANDLERS:
        sys.argv.append("--help")

    args = parser.parse_args()
    
    if args.gui:
        try:
            import garmin_gui
            garmin_gui.main()
            return
        except ImportError:
            print("錯誤: 找不到 garmin_gui.py 或其依賴項。請確保已安裝 tkinter。")
            return

    # 若無 command (例如只帶了全域參數但沒子命令)，則預設顯示 help
    if not args.command:
        parser.print_help()
        sys.exit(0)

    configure_runtime_logger(args.verbosity, args.progress)

    try:
        COMMAND_HANDLERS[args.command](args)
    except Exception as e:
        logger.error(f"程式執行失敗: {e}")
        if args.verbosity > 0: logger.exception("詳細錯誤：")
        sys.exit(1)


if __name__ == "__main__":
    main()
