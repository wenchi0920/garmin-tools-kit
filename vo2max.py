#!/usr/bin/env python3
"""
Purpose: Garmin Connect VO2 Max 趨勢與訓練狀態抓取工具。
Author: Gemini CLI
Changelog:
2026-03-08: 1.0.0 - 初始版本，支援 VO2 Max 歷史趨勢與訓練狀態獲取。
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

# Import Vo2MaxClient from client package
from client import Vo2MaxClient, VERSION

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
    parser = argparse.ArgumentParser(description="Garmin Connect VO2 Max 趨勢抓取工具")
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

def print_vo2max_entry(entry: Any) -> None:
    if not entry: return
    generic = entry.get("generic", {})
    if not generic: return
    
    cdate = generic.get("calendarDate")
    val = generic.get("vo2MaxValue")
    precise = generic.get("vo2MaxPreciseValue")
    age = generic.get("fitnessAge", "N/A")
    
    print(f"日期: {cdate} | VO2 Max: {val} (精確: {precise}) | 體能年齡: {age}")

def print_training_status(status: Any) -> None:
    if not status: return
    
    # mostRecentTrainingStatus is a dict from model_dump
    latest = status.get("latest_status")
    if not latest:
        # Try to find it in the raw dict structure if latest_status property wasn't dumped
        data = status.get("mostRecentTrainingStatus", {}).get("latestTrainingStatusData", {})
        for k, v in data.items():
            if v.get("primaryTrainingDevice"):
                latest = v
                break
        if not latest and data:
            latest = list(data.values())[0]

    if latest:
        print(f"訓練狀態: {latest.get('trainingStatusFeedbackPhrase', 'N/A')}")
        load = latest.get("acuteTrainingLoadDTO", {})
        if load:
            print(f"負荷指標: 短期 {load.get('dailyTrainingLoadAcute')} | 長期 {load.get('dailyTrainingLoadChronic')} | 比值 {load.get('dailyAcuteChronicWorkloadRatio')}")

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
        client = Vo2MaxClient(email=username, password=password, session_dir=args.session)
        results = {}

        # 1. Fetch history if range provided
        if args.start_date:
            end_date = args.end_date or date.today().isoformat()
            logger.info(f"正在抓取 VO2 Max 歷史: {args.start_date} 至 {end_date}")
            history = client.get_vo2max_history(args.start_date, end_date)
            results["history"] = [h.model_dump(mode="json") for h in history]
            logger.info(f"成功抓取 {len(history)} 筆歷史資料。")
        
        # 2. Fetch training status (latest)
        logger.info(f"正在獲取訓練狀態與最近 VO2 Max...")
        status = client.get_training_status(args.date)
        if status:
            results["status"] = status.model_dump(mode="json")
            # Inject latest_status property for easy access in summary
            results["status"]["latest_status"] = status.latest_status.model_dump(mode="json") if status.latest_status else None
        
        if not results:
            logger.error("未獲取到任何資料。")
            return

        # Output logic
        if args.summary:
            print("-" * 60)
            if "status" in results:
                print_training_status(results["status"])
                recent_v = results["status"].get("mostRecentVO2Max")
                if recent_v:
                    print("最近 VO2 Max 詳情:")
                    print_vo2max_entry(recent_v)
            
            if "history" in results:
                print("\nVO2 Max 歷史趨勢:")
                for entry in results["history"]:
                    print_vo2max_entry(entry)
            print("-" * 60)
        
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
