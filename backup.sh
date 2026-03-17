#!/bin/bash
# Purpose: 自動備份 Garmin 資料 (活動與健康數據)
# Author: Gemini CLI
# Changelog:
# 2026-03-10: v1.0.0 - 初始版本
# 2026-03-17: v1.0.1 - 修改排程為每天 08:00, 11:00, 12:00, 22:00

set -euo pipefail

echo "[$(date '+%Y-%m-%d %H:%M:%S')] 開始執行自動備份任務..."

# 切換到工作目錄
cd /app

# 確保備份目錄存在
echo "正在檢查備份目錄..."
mkdir -p /app/data/activities
mkdir -p /app/data/health

# 1. 備份最新活動 (預設下載最新 10 筆，避免遺漏)
echo "正在備份活動數據..."
python3 garmin_tools.py activity --count 10 --format original --directory /app/data/activities --originaltime

# 2. 備份昨日健康摘要 (因為 11:00 執行，備份昨天最完整)
YESTERDAY=$(date -d "yesterday" '+%Y-%m-%d')
echo "正在備份健康摘要 (${YESTERDAY})..."
python3 garmin_tools.py health --date "${YESTERDAY}" --output "/app/data/health/health_${YESTERDAY}.json"

# 3. 備份昨日睡眠數據
echo "正在備份睡眠數據 (${YESTERDAY})..."
python3 garmin_tools.py sleep --date "${YESTERDAY}" --output "/app/data/health/sleep_${YESTERDAY}.json"

# 4. 備份昨日 HRV 數據
echo "正在備份 HRV 數據 (${YESTERDAY})..."
python3 garmin_tools.py hrv --date "${YESTERDAY}" --output "/app/data/health/hrv_${YESTERDAY}.json"

echo "[$(date '+%Y-%m-%d %H:%M:%S')] 備份任務完成。"
