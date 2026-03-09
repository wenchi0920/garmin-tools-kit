#!/usr/bin/env python3
"""
Purpose: Garmin Connect 賽事 (Race Events) 抓取工具。
Author: Gemini CLI
Changelog:
2026-03-09: 1.0.0 - 初始版本，支援清單獲取與 JSON 匯出。
"""
import argparse
import getpass
import os
import sys
import json
from datetime import datetime
from typing import Dict, Optional, Any, List
from loguru import logger
from tqdm import tqdm

# Import Client from client package
from client.race_event_client import RaceEventClient
from models.raceEventModel import RaceEventModel, RaceEventListModel

VERSION = "1.0.0"

def setup_logging(verbosity: int) -> None:
    # Remove default handler
    logger.remove()
    
    # Set level based on verbosity
    if verbosity == 0:
        level = "INFO"
    elif verbosity == 1:
        level = "DEBUG"
    else:
        level = "TRACE"
        
    logger.add(sys.stderr, level=level, format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{message}</cyan>")

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Garmin Connect 賽事抓取工具")
    parser.add_argument("--version", action="version", version=f"%(prog)s {VERSION}")
    parser.add_argument("-v", "--verbosity", action="count", default=0, help="增加輸出與日誌詳細度")
    parser.add_argument("--username", help="您的 Garmin Connect 使用者名稱或電子郵件地址")
    parser.add_argument("--password", help="您的 Garmin Connect 密碼")
    parser.add_argument("--env-file", nargs="?", const=".env", help="使用 env file 優先使用這個來取得 username, password (預設值: .env)")
    
    # Selection args
    parser.add_argument("-d", "--date", help="指定單一日期 (YYYY-MM-DD)")
    parser.add_argument("-sd", "--start-date", help="開始抓取賽事的日期 (YYYY-MM-DD)")
    parser.add_argument("-ed", "--end_date", help="結束抓取賽事的日期 (YYYY-MM-DD)")
    
    # Operation args
    parser.add_argument("--summary", action="store_true", help="在終端機顯示美化的賽事摘要")
    parser.add_argument("-o", "--output", help="將原始 JSON 資料儲存至指定路徑")
    parser.add_argument("--directory", default="./data", help="匯出目錄路徑（預設值：'./data'）")
    parser.add_argument("-ss", "--session", default=".garth", help="SSO 認證資訊儲存目錄 (預設值: .garth)")
    
    return parser.parse_args()

def print_summary(events: List[RaceEventModel]) -> None:
    """
    印出美化的賽事摘要。
    """
    if not events:
        print("\n[!] 未找到任何賽事。")
        return

    print("\n" + "="*80)
    print(f"{'Garmin Race Events Summary':^80}")
    print("="*80)
    
    # Sort events by date
    sorted_events = sorted(events, key=lambda x: x.date)
    
    for event in sorted_events:
        target = "N/A"
        if event.completion_target:
            val = event.completion_target.value
            unit = event.completion_target.unit or ""
            target = f"{val} {unit}"
            
        time_str = "N/A"
        if event.event_time_local and event.event_time_local.startTimeHhMm:
            time_str = event.event_time_local.startTimeHhMm
            
        loc = event.location or "N/A"
        if len(loc) > 30:
            loc = loc[:27] + "..."

        print(f"📅 日期: {event.date} | 🕒 時間: {time_str}")
        print(f"🏆 名稱: {event.event_name}")
        print(f"🏃 類型: {event.event_type:<10} | 🎯 目標: {target}")
        print(f"📍 地點: {loc}")
        print("-" * 80)
    
    print(f"總計: {len(events)} 個賽事")
    print("="*80 + "\n")

def load_env_file(file_path: str) -> Dict[str, str]:
    """
    載入指定的 env file 並回傳內容字典。
    """
    env_data: Dict[str, str] = {}
    if not os.path.exists(file_path):
        if file_path != ".env":
            logger.warning(f"找不到指定的 env-file: {file_path}")
        return env_data

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if "=" in line:
                    key, value = line.split("=", 1)
                    env_data[key.strip()] = value.strip().strip("'").strip("\"")
    except Exception as e:
        logger.error(f"讀取 env-file 發生錯誤: {e}")
    
    return env_data

def main() -> None:
    args = parse_args()
    setup_logging(args.verbosity)
    
    username: Optional[str] = args.username
    password: Optional[str] = args.password

    # 若指定了 --env-file (或環境中存在預設的 .env)，則優先讀取
    env_file_path = args.env_file or (".env" if os.path.exists(".env") else None)
    if env_file_path:
        env_vars = load_env_file(env_file_path)
        username = username or env_vars.get("GARMIN_USERNAME") or env_vars.get("USERNAME")
        password = password or env_vars.get("GARMIN_PASSWORD") or env_vars.get("PASSWORD")
    
    # 若仍無帳密，則進行互動式輸入
    if not username:
        username = input("Garmin Connect 使用者名稱: ")
    if not password:
        password = getpass.getpass("Garmin Connect 密碼: ")

    try:
        # Initialize Client
        client = RaceEventClient(email=username, password=password, session_dir=args.session)
        
        # Determine date range
        start_date = args.start_date
        end_date = args.end_date
        
        if args.date:
            start_date = args.date
            end_date = args.date
            
        # Fetch Events
        logger.info(f"正在獲取賽事清單... (範圍: {start_date or '不限'} ~ {end_date or '不限'})")
        raw_events = client.list_events(start_date=start_date, end_date=end_date)
        
        if not raw_events:
            logger.info("未找到任何賽事。")
            return

        # Validate with DTO
        validated_events = []
        for event in raw_events:
            try:
                validated_events.append(RaceEventModel.model_validate(event))
            except Exception as e:
                logger.warning(f"賽事資料驗證失敗 (ID: {event.get('id')}): {e}")

        logger.info(f"成功獲取 {len(validated_events)} 個賽事。")

        if args.summary:
            print_summary(validated_events)

        # Create output directory
        if not os.path.exists(args.directory):
            os.makedirs(args.directory)
            logger.info(f"建立目錄: {args.directory}")

        # Save to JSON
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        filename = f"race_events_{timestamp}.json"
        filepath = args.output if args.output else os.path.join(args.directory, filename)
        
        output_data = [event.model_dump(by_alias=True) for event in validated_events]
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(output_data, f, ensure_ascii=False, indent=4)
            
        logger.info(f"原始資料已儲存至: {filepath}")
        
        if not args.summary:
            # Print legacy summary if not requested --summary
            print("\n--- 賽事清單摘要 ---")
            print(f"{'ID':<12} | {'日期':<12} | {'名稱'}")
            print("-" * 50)
            for event in validated_events:
                print(f"{event.id:<12} | {event.date:<12} | {event.event_name}")
            print("-" * 50)

    except Exception as e:
        logger.error(f"執行過程中發生錯誤: {e}")
        if args.verbosity > 0:
            logger.exception("Stack trace:")
        sys.exit(1)

if __name__ == "__main__":
    main()
