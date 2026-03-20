"""
Purpose: Garmin Tool Kit Docker Scheduler with Real-time Logging
Author: Senior Python Staff Engineer
Changelog:
2026-03-17: v1.0.0 - 初始版本
2026-03-17: v1.1.0 - 支援多時段備份 (08, 11, 22)
2026-03-17: v1.2.0 - 實作即時日誌串流與持久化檔案日誌 (Persistent Logging)
"""

import time
import datetime
import subprocess
import sys
import os
from loguru import logger

# 確保掛載的 data 目錄存在 (用於存放持久化日誌)
LOG_DIR = "/app/data/logs"
os.makedirs(LOG_DIR, exist_ok=True)
# 檔名模板，Loguru 會自動代入日期
LOG_FILE_PATTERN = os.path.join(LOG_DIR, "backup_{time:YYYY-MM-DD}.log")

# 配置 Loguru
logger.remove()
# 1. 輸出到標準輸出 (Docker logs 捕獲)
logger.add(sys.stdout, format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{message}</cyan>", colorize=True)
# 2. 輸出到檔案 (按日期輪替，保留 30 天)
logger.add(
    LOG_FILE_PATTERN, 
    format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {message}", 
    rotation="00:00", 
    retention="30 days", 
    compression="zip"
)

def run_backup_job():
    """執行備份腳本並即時串流輸出"""
    logger.info("🕒 觸發定時備份任務...")
    try:
        script_path = "/app/backup.sh"
        if not os.path.exists(script_path):
            logger.error(f"找不到備份腳本: {script_path}")
            return
            
        # 使用 Popen 實現即時串流輸出
        process = subprocess.Popen(
            ["bash", script_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT, # 將 stderr 合併到 stdout
            text=True,
            bufsize=1, # 行緩衝
            universal_newlines=True
        )

        # 讀取輸出
        if process.stdout:
            for line in process.stdout:
                clean_line = line.strip()
                if clean_line:
                    logger.info(f"[Backup] {clean_line}")

        process.wait()
                
        if process.returncode == 0:
            logger.success("✅ 備份任務執行成功。")
        else:
            logger.error(f"❌ 備份任務失敗，Exit Code: {process.returncode}")
            
    except Exception as e:
        logger.exception(f"💥 執行備份時發生未預期的異常: {e}")

def update_heartbeat():
    """更新心跳檔案時間戳"""
    try:
        with open("/tmp/scheduler_heartbeat", "w") as f:
            f.write(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    except Exception:
        pass

def main():
    # 設定多個備份時間點 (08, 13, 18, 23)
    target_times = ["08:00", "13:00", "18:00", "23:00"]
    logger.info("🚀 Garmin Tool Kit 守護排程器已啟動...")
    logger.info(f"📅 預定執行時間: 每天 {', '.join(target_times)}")
    logger.info(f"💾 持久化日誌目錄: {LOG_DIR}")
    
    while True:
        # 更新心跳
        update_heartbeat()
        
        now = datetime.datetime.now()
        current_time = now.strftime("%H:%M")
        
        if current_time in target_times:
            run_backup_job()
            # 執行完後，休眠 61 秒，跳過這一分鐘
            time.sleep(61)
        
        # 每隔 30 秒檢查一次
        time.sleep(30)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("👋 排程器已被使用者手動關閉。")
    except Exception as e:
        logger.critical(f"💀 排程器發生致命錯誤並停止: {e}")
        sys.exit(1)
