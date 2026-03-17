"""
Purpose: Garmin Tool Kit Docker Scheduler
Author: Senior Python Staff Engineer
Changelog:
2026-03-17: v1.0.0 - 初始版本，替代 Docker 中不穩定的 crontab
"""

import time
import datetime
import subprocess
import sys
import os
from loguru import logger

# 配置 Loguru 輸出到標準輸出，以便 Docker 捕獲
logger.remove()
logger.add(sys.stdout, format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{message}</cyan>", colorize=True)

def run_backup_job():
    """執行備份腳本"""
    logger.info("🕒 觸發定時備份任務 (AM 11:00)...")
    try:
        # 直接執行現有的 backup.sh
        script_path = "/app/backup.sh"
        if not os.path.exists(script_path):
            logger.error(f"找不到備份腳本: {script_path}")
            return
            
        result = subprocess.run(["bash", script_path], capture_output=True, text=True)
        
        # 輸出備份結果
        if result.stdout:
            for line in result.stdout.splitlines():
                logger.info(f"[Backup Out] {line}")
        
        if result.stderr:
            for line in result.stderr.splitlines():
                logger.warning(f"[Backup Err] {line}")
                
        if result.returncode == 0:
            logger.success("✅ 備份任務執行成功。")
        else:
            logger.error(f"❌ 備份任務失敗，Exit Code: {result.returncode}")
            
    except Exception as e:
        logger.exception(f"💥 執行備份時發生未預期的異常: {e}")

def main():
    # 設定多個備份時間點
    target_times = ["08:00", "11:00", "22:00"]
    logger.info("🚀 Garmin Tool Kit 守護排程器已啟動...")
    logger.info(f"📅 預定執行時間: 每天 {', '.join(target_times)}")
    
    while True:
        now = datetime.datetime.now()
        current_time = now.strftime("%H:%M")
        
        if current_time in target_times:
            run_backup_job()
            # 執行完後，休眠 61 秒，跳過這一分鐘
            time.sleep(61)
        
        # 每隔 30 秒檢查一次，減少 CPU 負擔
        time.sleep(30)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("👋 排程器已被使用者手動關閉。")
    except Exception as e:
        logger.critical(f"💀 排程器發生致命錯誤並停止: {e}")
        sys.exit(1)
