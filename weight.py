#!/usr/bin/env python3
"""
Purpose: Garmin Connect 體重與身體組成抓取工具。
Author: Gemini CLI
Changelog:
2026-03-08: 1.0.0 - 初始版本，支援最新體重與體重歷史抓取。
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

# Import WeightClient from client package
from client import WeightClient, VERSION

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
    parser = argparse.ArgumentParser(description="Garmin Connect 體重數據抓取工具")
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
    parser.add_argument("--upload", type=float, help="上傳體重 (單位: kg)")
    
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

def print_weight_entry(entry: Any) -> None:
    if not entry: return
    
    # entry might be a dict (from dumped model)
    w_gram = entry.get("weight", 0)
    w_kg = w_gram / 1000.0
    bmi = entry.get("bmi", "N/A")
    fat = entry.get("bodyFat", "N/A")
    ts = entry.get("timestamp") or entry.get("date")
    dt_str = datetime.fromtimestamp(ts / 1000).strftime("%Y-%m-%d %H:%M")
    
    print(f"時間: {dt_str} | 體重: {w_kg:.2f} kg | BMI: {bmi} | 體脂: {fat}%")

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
        client = WeightClient(email=username, password=password, session_dir=args.session)
        results = {}

        if args.upload:
            success = client.upload_weight(args.upload, args.date)
            if success:
                logger.success(f"已完成 {args.upload} kg 的上傳任務。")
            else:
                sys.exit(1)
            return

        if args.start_date:
            end_date = args.end_date or date.today().isoformat()
            logger.info(f"正在抓取體重歷史列表: {args.start_date} 至 {end_date}")
            history = client.get_weight_history(args.start_date, end_date)
            if history:
                results["data"] = history.model_dump(mode="json")
                logger.info(f"成功抓取 {len(history.dateWeightList)} 筆資料。")
            else:
                logger.warning("未獲取到體重歷史。")
        else:
            target_date = args.date
            logger.info(f"正在獲取截至 {target_date} 的最新體重...")
            entry = client.get_latest_weight(target_date)
            if entry:
                results["data"] = entry.model_dump(mode="json")
            else:
                logger.warning(f"找不到截至 {target_date} 的體重數據。")

        if not results or not results.get("data"):
            logger.error("未獲取到任何資料。")
            return

        # Output logic
        if args.summary:
            print("-" * 60)
            data = results["data"]
            if "dateWeightList" in data:
                for entry in data["dateWeightList"]:
                    print_weight_entry(entry)
            else:
                print_weight_entry(data)
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
