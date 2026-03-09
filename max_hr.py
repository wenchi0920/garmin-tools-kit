#!/usr/bin/env python3
"""
Purpose: Garmin Connect 最大心率與心率指標抓取工具。
Author: Gemini CLI
Changelog:
2026-03-08: 1.0.0 - 初始版本，支援每日最大心率、安靜心率、乳酸閾值及歷史活動最大心率獲取。
"""
import argparse
import getpass
import os
import sys
import json
from datetime import datetime, date, timedelta
from typing import Dict, Optional, Any, List, Union
from loguru import logger
from tqdm import tqdm

# Import MaxHrClient from client package
from client import MaxHrClient, VERSION

def setup_logging(verbosity: int) -> None:
    logger.remove()
    if verbosity == 0:
        level = "INFO"
    elif verbosity == 1:
        level = "DEBUG"
    else:
        level = "TRACE"
    logger.add(sys.stderr, level=level, format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{message}</cyan>")

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Garmin Connect 心率指標抓取工具")
    parser.add_argument("--version", action="version", version=f"%(prog)s {VERSION}")
    parser.add_argument("-v", "--verbosity", action="count", default=0, help="增加輸出詳細度")
    parser.add_argument("--username", help="Garmin Connect 使用者名稱")
    parser.add_argument("--password", help="Garmin Connect 密碼")
    parser.add_argument("--env-file", nargs="?", const=".env", help="使用 env file 取得帳密")
    
    # Selection args
    parser.add_argument("-d", "--date", help="指定日期 (YYYY-MM-DD)，預設為今天", default=date.today().isoformat())
    parser.add_argument("-l", "--limit", type=int, default=5, help="獲取最近幾筆活動的心率紀錄 (預設 5)")
    
    # Operation args
    parser.add_argument("-o", "--output", help="輸出 JSON 檔案路徑")
    parser.add_argument("-ss", "--session", default=".garth", help="SSO 認證目錄")
    parser.add_argument("--summary", action="store_true", help="顯示文字摘要")
    
    return parser.parse_args()

def load_env_file(file_path: str) -> Dict[str, str]:
    env_data: Dict[str, str] = {}
    if not os.path.exists(file_path): return env_data
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line: continue
                key, value = line.split("=", 1)
                env_data[key.strip()] = value.strip().strip("'").strip("\"")
    except Exception as e:
        logger.error(f"讀取 env-file 錯誤: {e}")
    return env_data

def print_hr_summary(results: Any) -> None:
    daily = results.get("daily_metrics")
    recent = results.get("recent_activities", [])
    
    print("-" * 60)
    if daily:
        print(f"日期: {daily.get('calendarDate')}")
        print(f"今日最大心率: {daily.get('observedMaxHr')} bpm")
        print(f"今日安靜心率: {daily.get('restingHr')} bpm")
        print(f"乳酸閾值心率: {daily.get('lactateThresholdHr')} bpm (設定值)")
    
    if recent:
        print("\n最近活動最大心率紀錄:")
        for act in recent:
            print(f"  {act.get('startTimeLocal')} | Max: {act.get('maxHr'):.0f} | Avg: {act.get('averageHr'):.0f} | {act.get('activityName')}")
    print("-" * 60)

def main() -> None:
    args = parse_args()
    setup_logging(args.verbosity)
    
    username, password = args.username, args.password
    env_file_path = args.env_file or (".env" if os.path.exists(".env") else None)
    if env_file_path:
        env_vars = load_env_file(env_file_path)
        username = username or env_vars.get("GARMIN_USERNAME") or env_vars.get("USERNAME")
        password = password or env_vars.get("GARMIN_PASSWORD") or env_vars.get("PASSWORD")
    
    if not username: username = input("Username: ")
    if not password: password = getpass.getpass("Password: ")
    
    try:
        client = MaxHrClient(email=username, password=password, session_dir=args.session)
        results = {}

        logger.info(f"正在獲取日期 {args.date} 的心率指標...")
        daily = client.get_daily_hr_metrics(args.date)
        if daily:
            results["daily_metrics"] = daily.model_dump(mode="json")
        
        logger.info(f"正在獲取最近 {args.limit} 筆活動的心率紀錄...")
        recent = client.get_recent_activity_max_hr(limit=args.limit)
        if recent:
            results["recent_activities"] = [a.model_dump(mode="json") for a in recent]

        if not results:
            logger.error("未獲取到任何資料。")
            return

        # Output logic
        if args.summary:
            print_hr_summary(results)
        
        output_str = json.dumps(results, indent=4, ensure_ascii=False)
        if args.output:
            with open(args.output, "w", encoding="utf-8") as f:
                f.write(output_str)
            logger.success(f"結果已儲存至: {args.output}")
        elif not args.summary:
            print(output_str)

    except Exception as e:
        logger.error(f"執行失敗: {e}")
        if args.verbosity > 0: logger.exception("Stack trace:")
        sys.exit(1)

if __name__ == "__main__":
    main()
