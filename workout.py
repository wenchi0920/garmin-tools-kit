#!/usr/bin/env python3
"""
Purpose: Garmin Connect 訓練 (Workout) 管理工具，支援 DSL 解析與批次上傳。
Author: Gemini CLI
Changelog:
2026-03-07: 1.0.0 - 初始版本。
2026-03-08: 1.1.0 - 實作 DSL 解析器，支援簡約 YAML 格式與批次上傳。
2026-03-08: 1.1.1 - 實作 deleteSameNameWorkout 功能，上傳前自動清理同名計畫。
"""
import argparse
import getpass
import os
import pprint
import sys
import yaml
from typing import Dict, Optional, Any, List
from loguru import logger

# Import Client and Parser from client package
from client import WorkoutClient, WorkoutDSLParser, VERSION

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
    parser = argparse.ArgumentParser(description="Garmin Connect 訓練 (Workout) 管理工具")
    parser.add_argument("--version", action="version", version=f"%(prog)s {VERSION}")
    parser.add_argument("-v", "--verbosity", action="count", default=0, help="增加輸出與日誌詳細度")
    parser.add_argument("--username", help="您的 Garmin Connect 使用者名稱或電子郵件地址")
    parser.add_argument("--password", help="您的 Garmin Connect 密碼")
    parser.add_argument("--env-file", nargs="?", const=".env", help="使用 env file 優先使用這個來取得 username, password (預設值: .env)")
    parser.add_argument("-ss", "--session", default=".garth", help="SSO 認證資訊儲存目錄 (預設值: .garth)")
    
    subparsers = parser.add_subparsers(dest="command", help="子指令", required=True)
    
    # List workouts
    subparsers.add_parser("list", help="列出帳號下所有的訓練計畫")
    
    # Get workout
    get_parser = subparsers.add_parser("get", help="下載指定的訓練計畫詳細資訊 (YAML 格式)")
    get_parser.add_argument("id", help="欲下載的訓練計畫 ID")
    get_parser.add_argument("-o", "--output", help="儲存檔名 (預設值: workout_ID.yaml)")

    # Upload workout
    upload_parser = subparsers.add_parser("upload", help="上傳訓練計畫 (支援 DSL 或原始 YAML)")
    upload_parser.add_argument("file", help="訓練計畫 YAML 檔案路徑")

    # Delete workout
    delete_parser = subparsers.add_parser("delete", help="刪除訓練計畫")
    delete_parser.add_argument("id", help="欲刪除的訓練計畫 ID")
    
    return parser.parse_args()

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

def display_workouts(workouts: List[Dict[str, Any]]) -> None:
    """
    格式化並顯示訓練計畫列表。
    """
    if not workouts:
        logger.warning("沒有可供顯示的訓練計畫。")
        return

    logger.info("-" * 100)
    logger.info(f"{'ID':<15} | {'名稱':<40} | {'類型':<15} | {'建立日期':<20}")
    logger.info("-" * 100)
    
    for w in workouts:
        wid = w.get("workoutId", "N/A")
        name = w.get("workoutName", "N/A")
        sport = w.get("sportType", {}).get("sportTypeKey", "N/A")
        created = w.get("createdDate", "N/A")
        if len(name) > 38:
            name = name[:35] + "..."
        logger.info(f"{wid:<15} | {name:<40} | {sport:<15} | {created:<20}")
    logger.info("-" * 100)

def main() -> None:
    args = parse_args()
    setup_logging(args.verbosity)
    
    username: Optional[str] = args.username
    password: Optional[str] = args.password

    env_file_path = args.env_file or (".env" if os.path.exists(".env") else None)
    if env_file_path:
        env_vars = load_env_file(env_file_path)
        username = username or env_vars.get("GARMIN_USERNAME") or env_vars.get("USERNAME")
        password = password or env_vars.get("GARMIN_PASSWORD") or env_vars.get("PASSWORD")
    
    username = username or os.environ.get("GARMIN_USERNAME") or os.environ.get("USERNAME")
    password = password or os.environ.get("GARMIN_PASSWORD") or os.environ.get("PASSWORD")

    if not username:
        username = input("Garmin Connect 使用者名稱: ")
    if not password:
        password = getpass.getpass("Garmin Connect 密碼: ")
    
    try:
        client = WorkoutClient(email=username, password=password, session_dir=args.session)
        
        if args.command == "list":
            logger.info("正在獲取訓練計畫列表...")
            workouts = client.list_workouts()
            display_workouts(workouts)
            logger.success(f"成功獲取 {len(workouts)} 個訓練計畫。")
            
        elif args.command == "get":
            logger.info(f"正在獲取訓練計畫詳細資訊: {args.id}")
            workout_data = client.get_workout(args.id)
            
            output_file = args.output or f"workout_{args.id}.yaml"
            logger.info(f"正在將訓練計畫內容儲存至: {output_file}")
            try:
                with open(output_file, "w", encoding="utf-8") as f:
                    yaml.dump(workout_data, f, sort_keys=False, allow_unicode=True, indent=4)
                logger.success(f"訓練計畫下載成功! 檔名: {output_file}")
            except Exception as e:
                logger.error(f"儲存 YAML 發生錯誤: {e}")
                sys.exit(1)

        elif args.command == "upload":
            if not os.path.exists(args.file):
                logger.error(f"找不到檔案: {args.file}")
                sys.exit(1)
            
            logger.info(f"讀取訓練計畫檔案: {args.file}")
            try:
                with open(args.file, "r", encoding="utf-8") as f:
                    yaml_content = yaml.safe_load(f)
            except yaml.YAMLError as e:
                logger.error(f"YAML 格式解析錯誤: {e}")
                sys.exit(1)

            # 判斷是否為 DSL 格式 (含有 workouts 鍵值)
            if isinstance(yaml_content, dict) and "workouts" in yaml_content:
                logger.info("檢測到 DSL 格式，開始解析...")
                parser = WorkoutDSLParser(yaml_content)
                workouts_to_upload = parser.get_all_workouts()
                
                # 紀錄上傳後的 Name -> ID 對照表，供排程使用
                uploaded_id_map: Dict[str, Any] = {}
                
                # 處理 deleteSameNameWorkout
                delete_existing = yaml_content.get("settings", {}).get("deleteSameNameWorkout", False)
                if delete_existing:
                    logger.info("檢查是否有同名訓練計畫需先行刪除...")
                    existing_workouts = client.list_workouts()
                    existing_map = {w["workoutName"]: w["workoutId"] for w in existing_workouts}
                    
                    for w in workouts_to_upload:
                        name = w["workoutName"]
                        if name in existing_map:
                            wid = existing_map[name]
                            logger.info(f"發現同名計畫: {name} (ID: {wid})，正在刪除...")
                            client.delete_workout(wid)

                for w in workouts_to_upload:
                    name = w["workoutName"]
                    if not w: continue
                    logger.info(f"正在上傳訓練計畫: {name}...")


                    pprint.pprint(w)

                    result = client.upload_workout(w)
                    new_id = result.get("workoutId")
                    uploaded_id_map[name] = new_id
                    logger.success(f"訓練計畫 '{name}' 上傳成功! ID: {new_id}")

                # 處理 schedulePlan
                schedule_plan = yaml_content.get("schedulePlan")
                if schedule_plan:
                    from datetime import timedelta
                    start_date_str = schedule_plan.get("start_from")
                    if not start_date_str:
                        logger.warning("schedulePlan 缺少 'start_from' 日期，跳過排程。")
                    else:
                        start_date = datetime.strptime(start_date_str, "%Y-%m-%d")
                        logger.info(f"檢測到排程計畫，起始日期: {start_date_str}")
                        
                        workouts_in_plan = schedule_plan.get("workouts", [])
                        for i, name in enumerate(workouts_in_plan):
                            current_date = (start_date + timedelta(days=i)).strftime("%Y-%m-%d")
                            if name.lower() == "rest":
                                logger.info(f"日期 {current_date}: 休息日")
                                continue
                            
                            wid = uploaded_id_map.get(name)
                            if wid:
                                logger.info(f"正在將 '{name}' (ID: {wid}) 排程至: {current_date}")
                                client.schedule_workout(wid, current_date)
                            else:
                                logger.warning(f"計畫中的名稱 '{name}' 在 workouts 定義中找不到，跳過排程。")
                        logger.success("排程計畫執行完成。")
            else:
                # 原始 Garmin 格式
                logger.info("偵測為原始 Garmin 格式...")
                result = client.upload_workout(yaml_content)
                new_id = result.get("workoutId")
                new_name = result.get("workoutName")
                logger.success(f"訓練計畫上傳成功! ID: {new_id}, 名稱: {new_name}")
            
        elif args.command == "delete":
            logger.info(f"正在刪除訓練計畫: {args.id}")
            client.delete_workout(args.id)
            logger.success(f"訓練計畫刪除成功! ID: {args.id}")
            
    except Exception as e:
        logger.error(f"發生錯誤: {e}")
        if args.verbosity > 0:
            logger.exception("詳細錯誤堆疊資訊：")
        sys.exit(1)

if __name__ == "__main__":
    main()
