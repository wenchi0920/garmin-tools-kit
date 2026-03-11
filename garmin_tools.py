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
"""
import argparse
import getpass
import json
import os
import sys
from datetime import datetime, date, timedelta
from typing import Dict

import yaml
from loguru import logger
from tqdm import tqdm

# Import Clients and Models
from client import (
    ActivityClient, BodyBatteryClient, HealthClient, HrvClient,
    MaxHrClient, SleepClient, Vo2MaxClient, WeightClient,
    WorkoutClient, WorkoutDSLParser, VERSION
)
from client.race_event_client import RaceEventClient
from models.raceEventModel import RaceEventModel


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


def format_seconds(seconds: int) -> str:
    """格式化秒數為 時:分"""
    hours, remainder = divmod(seconds, 3600)
    minutes, _ = divmod(remainder, 60)
    return f"{hours}時{minutes}分"


# ==============================================================================
# 子命令處理邏輯 (Command Handlers)
# ==============================================================================

def execute_activity_export(args: argparse.Namespace):
    username, password = resolve_user_auth(args)
    client = ActivityClient(email=username, password=password, session_dir=args.session)

    logger.info(f"正在獲取活動列表... 數量={args.count}, 範圍={args.start_date or '不限'} ~ {args.end_date or '不限'}")
    activities = client.list_activities(count=args.count, start_date=args.start_date, end_date=args.end_date)

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
        output_file = args.output or f"workout_{args.id}.yaml"
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


def fetch_daily_health_metrics(args: argparse.Namespace):
    username, password = resolve_user_auth(args)
    client = HealthClient(email=username, password=password, session_dir=args.session)

    if args.start_date:
        data_list = client.get_daily_summaries(args.start_date, args.end_date or date.today().isoformat(), show_progress=args.progress)
        metric_collection = {"data": [h.model_dump(mode="json") for h in data_list]}
    else:
        data = client.get_daily_summary(args.date)
        metric_collection = {"data": data.model_dump(mode="json")} if data else {}

    if args.summary and metric_collection.get("data"):
        items = metric_collection["data"] if isinstance(metric_collection["data"], list) else [metric_collection["data"]]
        for summary_entry in items:
            print("-" * 50)
            print(f"日期: {summary_entry.get('calendarDate')}")
            print(
                f"活動: 步數 {summary_entry.get('totalSteps')}/{summary_entry.get('dailyStepGoal')} | 距離 {summary_entry.get('totalDistanceMeters', 0) / 1000:.2f}km")
            print(
                f"心率: 靜止 {summary_entry.get('restingHeartRate')} | 最低 {summary_entry.get('minHeartRate')} | 最高 {summary_entry.get('maxHeartRate')}")
            print(f"能量: 身體能量當前 {summary_entry.get('bodyBatteryMostRecentValue')} | 壓力平均 {summary_entry.get('averageStressLevel')}")

    if args.output:
        if not args.over_write and os.path.exists(args.output):
            logger.info(f"檔案已存在，跳過儲存: {args.output}")
        else:
            with open(args.output, "w", encoding="utf-8") as f:
                json.dump(metric_collection, f, indent=4, ensure_ascii=False)
            logger.success(f"資料已儲存至: {args.output}")
    elif not args.summary:
        print(json.dumps(metric_collection, indent=4, ensure_ascii=False))


def fetch_sleep_analytics(args: argparse.Namespace):
    username, password = resolve_user_auth(args)
    client = SleepClient(email=username, password=password, session_dir=args.session)

    if args.start_date:
        data_list = client.get_sleep_data_range(args.start_date, args.end_date or date.today().isoformat(), show_progress=args.progress)
        metric_collection = {"data": [s.model_dump(mode="json") for s in data_list]}
    else:
        data = client.get_sleep_data(args.date)
        metric_collection = {"data": data.model_dump(mode="json")} if data else {}

    if args.summary and metric_collection.get("data"):
        items = metric_collection["data"] if isinstance(metric_collection["data"], list) else [metric_collection["data"]]
        for summary_entry in items:
            dto = summary_entry.get("dailySleepDTO", {})
            score = dto.get("sleepScores", {}).get("overall", {}).get("value", "N/A")
            print("-" * 40)
            print(f"日期: {dto.get('calendarDate')} | 分數: {score}")
            print(
                f"時間: 總計 {format_seconds(dto.get('sleepTimeSeconds', 0))} | 深層 {format_seconds(dto.get('deepSleepSeconds', 0))}")

    if args.output:
        if not args.over_write and os.path.exists(args.output):
            logger.info(f"檔案已存在，跳過儲存: {args.output}")
        else:
            with open(args.output, "w", encoding="utf-8") as f:
                json.dump(metric_collection, f, indent=4, ensure_ascii=False)
            logger.success(f"資料已儲存至: {args.output}")
    elif not args.summary:
        print(json.dumps(metric_collection, indent=4, ensure_ascii=False))


def process_weight_tracking(args: argparse.Namespace):
    username, password = resolve_user_auth(args)
    client = WeightClient(email=username, password=password, session_dir=args.session)

    if args.upload:
        if client.upload_weight(args.upload, args.date):
            logger.success(f"已上傳 {args.upload} kg 至 {args.date}")
        return

    if args.start_date:
        history = client.get_weight_history(args.start_date, args.end_date or date.today().isoformat())
        metric_collection = {"data": history.model_dump(mode="json")} if history else {}
    else:
        entry = client.get_latest_weight(args.date)
        metric_collection = {"data": entry.model_dump(mode="json")} if entry else {}

    if args.summary and metric_collection.get("data"):
        data = metric_collection["data"]
        entries = data["dateWeightList"] if "dateWeightList" in data else [data]
        for summary_entry in entries:
            ts = summary_entry.get("timestamp") or summary_entry.get("date")
            dt = datetime.fromtimestamp(ts / 1000).strftime("%Y-%m-%d")
            print(
                f"日期: {dt} | 體重: {summary_entry.get('weight', 0) / 1000.0:.2f} kg | BMI: {summary_entry.get('bmi', 'N/A')} | 體脂: {summary_entry.get('bodyFat', 'N/A')}%")

    if args.output:
        if not args.over_write and os.path.exists(args.output):
            logger.info(f"檔案已存在，跳過儲存: {args.output}")
        else:
            with open(args.output, "w", encoding="utf-8") as f:
                json.dump(metric_collection, f, indent=4, ensure_ascii=False)
            logger.success(f"資料已儲存至: {args.output}")
    elif not args.summary:
        print(json.dumps(metric_collection, indent=4, ensure_ascii=False))


def retrieve_hrv_readings(args: argparse.Namespace):
    username, password = resolve_user_auth(args)
    client = HrvClient(email=username, password=password, session_dir=args.session)

    if args.start_date:
        data_list = client.get_hrv_data_range(args.start_date, args.end_date or date.today().isoformat(), show_progress=args.progress)
        metric_collection = {"data": [h.model_dump(mode="json") for h in data_list]}
    else:
        data = client.get_hrv_data(args.date)
        metric_collection = {"data": data.model_dump(mode="json")} if data else {}

    # 移除細節 (若未指定 --detailed)
    if not args.detailed and metric_collection.get("data"):
        items = metric_collection["data"] if isinstance(metric_collection["data"], list) else [metric_collection["data"]]
        for item in items:
            if "hrvReadings" in item: del item["hrvReadings"]

    if args.output:
        if not args.over_write and os.path.exists(args.output):
            logger.info(f"檔案已存在，跳過儲存: {args.output}")
        else:
            with open(args.output, "w", encoding="utf-8") as f:
                json.dump(metric_collection, f, indent=4, ensure_ascii=False)
            logger.success(f"資料已儲存至: {args.output}")
    elif not args.summary:
        print(json.dumps(metric_collection, indent=4, ensure_ascii=False))


def analyze_body_battery(args: argparse.Namespace):
    username, password = resolve_user_auth(args)
    client = BodyBatteryClient(email=username, password=password, session_dir=args.session)

    if args.start_date:
        data_list = client.get_body_battery_reports(args.start_date, args.end_date or date.today().isoformat())
        metric_collection = {"data": [h.model_dump(mode="json") for h in data_list]}
    else:
        data = client.get_body_battery_report(args.date)
        metric_collection = {"data": data.model_dump(mode="json")} if data else {}

    if args.summary and metric_collection.get("data"):
        items = metric_collection["data"] if isinstance(metric_collection["data"], list) else [metric_collection["data"]]
        for summary_entry in items:
            print(
                f"日期: {summary_entry.get('calendarDate')} | 充電: {summary_entry.get('charged')} | 消耗: {summary_entry.get('drained')} | 評分: {summary_entry.get('bodyBatteryDynamicFeedbackEvent', {}).get('feedbackShortType')}")

    if args.output:
        if not args.over_write and os.path.exists(args.output):
            logger.info(f"檔案已存在，跳過儲存: {args.output}")
        else:
            with open(args.output, "w", encoding="utf-8") as f:
                json.dump(metric_collection, f, indent=4, ensure_ascii=False)
            logger.success(f"資料已儲存至: {args.output}")
    elif not args.summary:
        print(json.dumps(metric_collection, indent=4, ensure_ascii=False))


def evaluate_vo2max_trends(args: argparse.Namespace):
    username, password = resolve_user_auth(args)
    client = Vo2MaxClient(email=username, password=password, session_dir=args.session)
    metric_collection = {}

    if args.start_date:
        history = client.get_vo2max_history(args.start_date, args.end_date or date.today().isoformat())
        metric_collection["history"] = [h.model_dump(mode="json") for h in history]

    status = client.get_training_status(args.date)
    if status:
        metric_collection["status"] = status.model_dump(mode="json")
        metric_collection["status"]["latest_status"] = status.latest_status.model_dump(
            mode="json") if status.latest_status else None

    if args.summary:
        if "status" in metric_collection:
            latest = metric_collection["status"].get("latest_status", {})
            print(f"訓練狀態: {latest.get('trainingStatusFeedbackPhrase', 'N/A')}")
        if "history" in metric_collection:
            for h in metric_collection["history"]:
                g = h.get("generic", {})
                print(
                    f"日期: {g.get('calendarDate')} | VO2 Max: {g.get('vo2MaxValue')} | 體能年齡: {g.get('fitnessAge')}")

    if args.output:
        if not args.over_write and os.path.exists(args.output):
            logger.info(f"檔案已存在，跳過儲存: {args.output}")
        else:
            with open(args.output, "w", encoding="utf-8") as f:
                json.dump(metric_collection, f, indent=4, ensure_ascii=False)
            logger.success(f"資料已儲存至: {args.output}")
    elif not args.summary:
        print(json.dumps(metric_collection, indent=4, ensure_ascii=False))


def report_heart_rate_indicators(args: argparse.Namespace):
    username, password = resolve_user_auth(args)
    client = MaxHrClient(email=username, password=password, session_dir=args.session)
    metric_collection = {}

    daily = client.get_daily_hr_metrics(args.date)
    if daily: metric_collection["daily_metrics"] = daily.model_dump(mode="json")
    recent = client.get_recent_activity_max_hr(limit=args.limit)
    if recent: metric_collection["recent_activities"] = [a.model_dump(mode="json") for a in recent]

    if args.summary:
        d = metric_collection.get("daily_metrics", {})
        if d:
            print(f"日期: {d.get('calendarDate')} | 最大: {d.get('observedMaxHr')} | 安靜: {d.get('restingHr')}")
        for a in metric_collection.get("recent_activities", []):
            print(f"活動: {a.get('startTimeLocal')} | Max: {a.get('maxHr'):.0f} | {a.get('activityName')}")

    if not args.summary:
        print(json.dumps(metric_collection, indent=4, ensure_ascii=False))


def fetch_race_calendar(args: argparse.Namespace):
    username, password = resolve_user_auth(args)
    client = RaceEventClient(email=username, password=password, session_dir=args.session)

    start_date = args.date if args.date else args.start_date
    end_date = args.date if args.date else args.end_date
    raw_events = client.list_events(start_date=start_date, end_date=end_date)

    validated = []
    for e in raw_events:
        try:
            validated.append(RaceEventModel.model_validate(e))
        except:
            continue

    if args.summary:
        print("\n" + "=" * 60)
        for e in sorted(validated, key=lambda x: x.event_date):
            print(f"📅 {e.event_date} | 🏆 {e.event_name} | 🏃 {e.event_type}")
        print("=" * 60)

    if args.output:
        if not args.over_write and os.path.exists(args.output):
            logger.info(f"檔案已存在，跳過儲存: {args.output}")
        else:
            output_data = [e.model_dump(by_alias=True) for e in validated]
            with open(args.output, "w", encoding="utf-8") as f:
                json.dump(output_data, f, indent=4, ensure_ascii=False)
            logger.success(f"資料已儲存至: {args.output}")
    elif not args.summary:
        print(json.dumps([e.model_dump(by_alias=True) for e in validated], indent=4, ensure_ascii=False))


# ==============================================================================
# CLI 入口 (Entry Point)
# ==============================================================================

def main():
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

    subparsers = parser.add_subparsers(dest="command", help="子命令 (預設: activity -c 5)")

    # Activity
    activity_parser = subparsers.add_parser("activity", help="活動匯出")
    activity_parser.add_argument("-c", "--count", default="1")
    activity_parser.add_argument("-sd", "--start_date")
    activity_parser.add_argument("-ed", "--end_date")
    activity_parser.add_argument("-f", "--format", choices=["gpx", "tcx", "original", "json"], default="original")
    activity_parser.add_argument("-d", "--directory", default="./data")
    activity_parser.add_argument("-ot", "--originaltime", action="store_true")
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

    # Health Data Shared Args
    def add_date_range_args(p):
        p.add_argument("-d", "--date", default=date.today().isoformat())
        p.add_argument("-sd", "--start_date")
        p.add_argument("-ed", "--end_date")
        p.add_argument("--summary", action="store_true")
        p.add_argument("-o", "--output")

    # Others
    add_date_range_args(subparsers.add_parser("health", help="每日健康摘要"))
    add_date_range_args(subparsers.add_parser("sleep", help="睡眠紀錄"))
    add_date_range_args(subparsers.add_parser("body-battery", help="身體能量指數"))
    add_date_range_args(subparsers.add_parser("vo2max", help="VO2 Max 與訓練狀態"))
    add_date_range_args(subparsers.add_parser("race-event", help="賽事清單"))

    p_hrv = subparsers.add_parser("hrv", help="HRV 數據")
    add_date_range_args(p_hrv)
    p_hrv.add_argument("--detailed", action="store_true")

    p_weight = subparsers.add_parser("weight", help="體重數據")
    add_date_range_args(p_weight)
    p_weight.add_argument("--upload", type=float, help="上傳體重 (kg)")

    p_hr = subparsers.add_parser("max-hr", help="心率指標")
    p_hr.add_argument("-d", "--date", default=date.today().isoformat())
    p_hr.add_argument("-l", "--limit", type=int, default=5)
    p_hr.add_argument("--summary", action="store_true")

    args = parser.parse_args()
    
    if args.gui:
        try:
            import garmin_gui
            garmin_gui.main()
            return
        except ImportError:
            print("錯誤: 找不到 garmin_gui.py 或其依賴項。請確保已安裝 tkinter。")
            return

    # 預設執行指令: 若無 command 則預設執行 activity -c 5
    if not args.command:
        args.command = "activity"
        setattr(args, "count", "5")
        setattr(args, "start_date", None)
        setattr(args, "end_date", None)
        setattr(args, "format", "original")
        setattr(args, "directory", "./data")
        setattr(args, "originaltime", False)
        setattr(args, "desc", None)

    configure_runtime_logger(args.verbosity, args.progress)

    handlers = {
        "activity": execute_activity_export,
        "workout": manage_workout_workflow,
        "health": fetch_daily_health_metrics,
        "sleep": fetch_sleep_analytics,
        "weight": process_weight_tracking,
        "hrv": retrieve_hrv_readings,
        "body-battery": analyze_body_battery,
        "vo2max": evaluate_vo2max_trends,
        "max-hr": report_heart_rate_indicators,
        "race-event": fetch_race_calendar
    }

    try:
        handlers[args.command](args)
    except Exception as e:
        logger.error(f"程式執行失敗: {e}")
        if args.verbosity > 0: logger.exception("詳細錯誤：")
        sys.exit(1)


if __name__ == "__main__":
    main()
