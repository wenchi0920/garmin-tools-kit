"""
Purpose: Garmin Tool Kit Docker Scheduler with Integrated Backup Engine
Author: Senior Python Staff Engineer
Changelog:
2026-03-17: v1.0.0 - 初始版本
2026-03-17: v1.2.0 - 實作即時日誌串流與持久化檔案日誌
2026-03-25: v1.3.0 - 整合 backup.sh 功能，實作自動化備份引擎，移除 Shell 依賴
"""

import os
from dotenv import load_dotenv

# --- 配置 (Configurations) ---
# 取得程式實體路徑，確保無論從何處啟動都能找到 .env
APP_ROOT = os.path.dirname(os.path.abspath(__file__))
# 優先載入 .env 檔案 (本地開發環境)，並允許覆寫環境變數 (override=True)
load_dotenv(os.path.join(APP_ROOT, ".env"), override=True)

# 如果環境變數中有指定 APP_ROOT，則以此為準 (允許外部覆寫)
APP_ROOT = os.getenv("APP_ROOT", APP_ROOT)

import time
import datetime
import subprocess
import sys
import argparse
from loguru import logger

DATA_DIR = os.getenv("DATA_DIR", os.path.join(APP_ROOT, "data"))
LOG_DIR = os.path.join(DATA_DIR, "logs")
GARMIN_TOOLS_PATH = os.path.join(APP_ROOT, "garmin_tools.py")

os.makedirs(LOG_DIR, exist_ok=True)

# 配置 Loguru
LOG_FILE_PATTERN = os.path.join(LOG_DIR, "backup_{time:YYYY-MM-DD}.log")
logger.remove()
logger.add(sys.stdout, format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{message}</cyan>", colorize=True)
logger.add(LOG_FILE_PATTERN, format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {message}", rotation="00:00", retention="30 days", compression="zip")

def execute_cmd(args):
    """執行命令並即時記錄輸出"""
    cmd_str = " ".join(args)
    logger.info(f"[CMD] {cmd_str}")
    
    try:
        process = subprocess.Popen(
            args,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            universal_newlines=True,
            cwd=APP_ROOT
        )

        if process.stdout:
            for line in process.stdout:
                clean_line = line.strip()
                if clean_line:
                    logger.info(f"  {clean_line}")

        process.wait()
        if process.returncode != 0:
            logger.error(f"❌ 命令執行失敗 (Exit Code: {process.returncode})")
            return False
        return True
    except Exception as e:
        logger.error(f"💥 執行命令時發生異常: {e}")
        return False

def run_backup_job(force_all=False):
    """備份任務核心引擎"""
    now = datetime.datetime.now()
    hour = now.hour
    today = now.strftime("%Y-%m-%d")
    yesterday = (now - datetime.timedelta(days=1)).strftime("%Y-%m-%d")
    
    logger.info("================================================================================")
    logger.info(f"🚀 啟動備份引擎 (Hour: {hour:02d}, Force: {force_all})")
    logger.info("================================================================================")

    python_bin = sys.executable

    # 1. [FIT & Summary] 於 08, 13, 18, 23 時執行，或強制執行
    if force_all or hour in [8, 13, 18, 23]:
        logger.info("📦 [FIT] 備份活動數據 (雙日)...")
        execute_cmd([python_bin, GARMIN_TOOLS_PATH, "-v", "activity", "--start_date", yesterday, "--end_date", today, "--format", "original", "--originaltime"])

        logger.info("📊 [SUMMARY] 備份綜合摘要 (7天)...")
        execute_cmd([python_bin, GARMIN_TOOLS_PATH, "health", "summary", "-d", "7", "-o", "data/health/report.txt"])

    # 2. [HEALTH] 於 08, 23 時執行全量生理數據備份，或強制執行
    if force_all or hour in [8, 23]:
        logger.info("❤️ [HEALTH] 執行全量生理健康數據備份...")
        
        # 雙日指標 (Daily Metrics)
        metrics = ["sleep", "body-battery", "hrv", "weight", "vo2max", "training-status", "stress", "heart-rate", "steps", "calories", "training-readiness", "spo2", "respiration", "hydration"]
        for metric in metrics:
            logger.info(f"   -> 指標備份: {metric}...")
            base_args = [python_bin, GARMIN_TOOLS_PATH, "-v", "--over-write", "health", metric]
            
            for date in [yesterday, today]:
                current_args = base_args + ["--date", date]
                if metric == "hrv":
                    current_args.append("--detailed")
                execute_cmd(current_args)

        # 週期性指標 (Periodic)
        logger.info("   -> 更新週期性指標...")
        periodic_tasks = [
            ["fitness-age"], ["lactate-threshold"], ["race-predictions"], 
            ["personal-records"], ["insights"], ["max-hr", "--limit", "5"]
        ]
        for task in periodic_tasks:
            execute_cmd([python_bin, GARMIN_TOOLS_PATH, "-v", "--over-write", "health"] + task)
        
        # 範圍型指標 (Range)
        logger.info("   -> 更新範圍與賽事數據...")
        range_tasks = [
            ["health", "intensity-minutes", "--start_date", yesterday, "--end_date", today],
            ["health", "blood-pressure", "--start_date", yesterday, "--end_date", today],
            ["race-event", "--start_date", yesterday, "--end_date", today]
        ]
        for task in range_tasks:
            execute_cmd([python_bin, GARMIN_TOOLS_PATH, "-v", "--over-write"] + task)

    logger.success(f"✅ 備份引擎執行完畢。")
    logger.info("================================================================================")

def update_heartbeat():
    try:
        with open("/tmp/scheduler_heartbeat", "w") as f:
            f.write(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    except Exception: pass

def main():
    parser = argparse.ArgumentParser(description="Garmin Tool Kit Scheduler")
    parser.add_argument("-d", "--force-all", action="store_true", help="強制執行全量備份")
    parser.add_argument("--now", action="store_true", help="立即執行一次後結束")
    args = parser.parse_args()

    if args.now:
        run_backup_job(force_all=args.force_all)
        return

    target_times = ["08:00", "13:00", "18:00", "23:00"]
    logger.info("🚀 Garmin Tool Kit 守護排程器已啟動...")
    logger.info(f"📅 預定執行時間: 每天 {', '.join(target_times)}")
    
    while True:
        update_heartbeat()
        now = datetime.datetime.now()
        current_time = now.strftime("%H:%M")
        
        if current_time in target_times:
            run_backup_job(force_all=args.force_all)
            time.sleep(61)
        
        time.sleep(30)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("👋 排程器手動關閉。")
    except Exception as e:
        logger.critical(f"💀 致命錯誤: {e}")
        sys.exit(1)
