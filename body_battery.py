#!/usr/bin/env python3
"""
Purpose: Garmin Connect 身體能量指數 (Body Battery) 抓取工具。
Author: Gemini CLI
Changelog:
2026-03-08: 1.0.0 - 初始版本，支援獲取每日 Body Battery 充電、消耗、關鍵事件與詳細數值。
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

# Import BodyBatteryClient from client package
from client import BodyBatteryClient, VERSION

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
    parser = argparse.ArgumentParser(description="Garmin Connect 身體能量指數抓取工具")
    parser.add_argument("--version", action="version", version=f"%(prog)s {VERSION}")
    parser.add_argument("-v", "--verbosity", action="count", default=0, help="增加輸出詳細度")
    parser.add_argument("--username", help="Garmin Connect 使用者名稱")
    parser.add_argument("--password", help="Garmin Connect 密碼")
    parser.add_argument("--env-file", nargs="?", const=".env", help="使用 env file 取得帳密")
    
    # Selection args
    parser.add_argument("-d", "--date", help="指定日期 (YYYY-MM-DD)，預設為今天", default=date.today().isoformat())
    parser.add_argument("-sd", "--start_date", help="開始日期 (YYYY-MM-DD)")
    parser.add_argument("-ed", "--end_date", help="結束日期 (YYYY-MM-DD)")
    
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

def format_duration(ms: int) -> str:
    seconds = ms // 1000
    hours, remainder = divmod(seconds, 3600)
    minutes, _ = divmod(remainder, 60)
    return f"{hours}時{minutes}分"

def print_bb_summary(data: Any) -> None:
    if not data: return
    
    calendar_date = data.get("calendarDate")
    charged = data.get("charged", "N/A")
    drained = data.get("drained", "N/A")
    feedback = data.get("bodyBatteryDynamicFeedbackEvent", {}).get("feedbackShortType", "N/A")
    
    events = data.get("bodyBatteryActivityEvent", [])
    
    print("-" * 60)
    print(f"日期: {calendar_date}")
    print(f"今日統計: 充電 {charged} | 消耗 {drained}")
    print(f"系統評分: {feedback}")
    
    if events:
        print("\n關鍵事件:")
        for event in events:
            etype = event.get("eventType", "Unknown")
            impact = event.get("bodyBatteryImpact", 0)
            dur = format_duration(event.get("durationInMilliseconds", 0))
            fb = event.get("shortFeedback", "")
            print(f"  [{etype}] 影響 {impact: >+3} | 持續 {dur: <7} | {fb}")
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
        client = BodyBatteryClient(email=username, password=password, session_dir=args.session)
        results = {}

        if args.start_date:
            end_date = args.end_date or date.today().isoformat()
            logger.info(f"正在抓取 Body Battery 列表: {args.start_date} 至 {end_date}")
            bb_list = client.get_body_battery_reports(args.start_date, end_date)
            results["data"] = [h.model_dump(mode="json") for h in bb_list]
            logger.info(f"成功抓取 {len(bb_list)} 筆資料。")
        else:
            target_date = args.date
            logger.info(f"正在抓取日期 {target_date} 的 Body Battery 資料...")
            bb_data = client.get_body_battery_report(target_date)
            if bb_data:
                results["data"] = bb_data.model_dump(mode="json")
            else:
                logger.warning(f"找不到 {target_date} 的數據。")

        if not results or not results.get("data"):
            logger.error("未獲取到任何資料。")
            return

        # Output logic
        if args.summary:
            if isinstance(results["data"], list):
                for d in results["data"]: print_bb_summary(d)
            else:
                print_bb_summary(results["data"])
        
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
