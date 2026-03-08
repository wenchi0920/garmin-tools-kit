#!/usr/bin/env python3
"""
Purpose: Garmin Connect 活動匯出工具，負責抓取並下載活動資料。
Author: Gemini CLI
Changelog:
2026-03-07: 1.0.0 - 初始版本。
2026-03-07: 1.0.1 - 實作 --env-file 功能，更新預設匯出目錄為 ./data 並優化檔名格式符合規範。
2026-03-08: 1.0.2 - 更新預設匯出格式為 'original'，優化環境變數讀取優先級與時間解析容錯。
"""
import argparse
import getpass
import os
import sys
from datetime import datetime
from typing import Dict, Optional, Any, List
from loguru import logger
from tqdm import tqdm

# Import Client from client package
from client import ActivityClient, VERSION

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
    parser = argparse.ArgumentParser(description="Garmin Connect 活動匯出工具")
    parser.add_argument("--version", action="version", version=f"%(prog)s {VERSION}")
    parser.add_argument("-v", "--verbosity", action="count", default=0, help="增加輸出與日誌詳細度")
    parser.add_argument("--username", help="您的 Garmin Connect 使用者名稱或電子郵件地址（若未提供，系統將會提示輸入）")
    parser.add_argument("--password", help="您的 Garmin Connect 密碼（若未提供，系統將會提示輸入）")
    parser.add_argument("--env-file", nargs="?", const=".env", help="使用 env file 優先使用這個來取得 username, password (預設值: .env)")
    parser.add_argument("-c", "--count", default="1", help="要下載的最近活動數量，或輸入 'all'（預設值：1）")
    parser.add_argument("-sd", "--start_date", help="開始抓取活動的日期 (YYYY-MM-DD)")
    parser.add_argument("-ed", "--end_date", help="結束抓取活動的日期 (YYYY-MM-DD)")
    parser.add_argument("-f", "--format", choices=["gpx", "tcx", "original", "json"], default="original", help="匯出格式 (預設值: 'original')")
    parser.add_argument("-d", "--directory", default="./data", help="匯出目錄路徑（預設值：'./data'）")
    parser.add_argument("-ot", "--originaltime", action="store_true", help="將檔案時間設定為活動開始時間")
    parser.add_argument("--desc", nargs="?", const=True, help="將活動描述附加至檔案名稱；若提供數字則限制長度")
    parser.add_argument("-ss", "--session", default=".garth", help="SSO 認證資訊儲存目錄 (預設值: .garth)")
    
    return parser.parse_args()

def load_env_file(file_path: str) -> Dict[str, str]:
    """
    載入指定的 env file 並回傳內容字典。
    """
    env_data: Dict[str, str] = {}
    if not os.path.exists(file_path):
        # 僅在使用者主動指定非預設路徑時才發出警告
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
                    # 移除可能的引號
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
        client = ActivityClient(email=username, password=password, session_dir=args.session)
        
        logger.info(f"正在獲取活動列表... 數量={args.count}, 開始日期={args.start_date or '不限'}, 結束日期={args.end_date or '不限'}")
            
        activities: List[Dict[str, Any]] = client.list_activities(
            count=args.count, 
            start_date=args.start_date, 
            end_date=args.end_date
        )
        
        if not activities:
            logger.warning("找不到任何符合條件的活動。")
            return

        logger.info(f"找到 {len(activities)} 個活動。")
        
        if not os.path.exists(args.directory):
            logger.debug(f"建立目錄: {args.directory}")
            os.makedirs(args.directory, exist_ok=True)
            
        # 下載流程
        for activity in tqdm(activities, desc="下載活動進度", unit="個"):
            activity_id = activity["activityId"]
            activity_name = activity["activityName"]
            start_time = activity["startTimeLocal"]
            
            logger.debug(f"處理中: {activity_id} | {activity_name} ({start_time})")
                
            client.download_activity(
                activity, 
                format=args.format, 
                directory=args.directory, 
                original_time=args.originaltime, 
                desc=args.desc
            )
        
        logger.success(f"任務完成。所有活動已匯出至: {os.path.abspath(args.directory)}")
    except Exception as e:
        logger.error(f"程式執行發生嚴重錯誤: {e}")
        if args.verbosity > 0:
            logger.exception("詳細錯誤堆疊：")
        sys.exit(1)

if __name__ == "__main__":
    main()
