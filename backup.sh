#!/bin/bash
# Purpose: 全量自動備份 Garmin 資料 (活動與所有生理數據)
# Author: Senior Systems Engineer
# Changelog:
# 2026-03-10: v1.0.0 - 初始版本
# 2026-03-17: v1.2.0 - 升級為全量備份 (包含 HRV, Sleep, Body Battery, VO2Max, Weight, Race-Event, Max-HR)

set -euo pipefail

echo "[$(date '+%Y-%m-%d %H:%M:%S')] 🚀 開始執行全量自動備份任務..."

# 切換到工作目錄
cd /app

# 定義日期 (備份昨天與今天，確保數據完整)
YESTERDAY=$(date -d "yesterday" '+%Y-%m-%d')
TODAY=$(date '+%Y-%m-%d')

# 確保基礎目錄存在 (程式會自動建立子目錄，但我們預先建立以求保險)
mkdir -p /app/data

# 1. 活動數據 (備份最新 20 筆，避免遺漏同步較慢的活動)
echo "📦 [1/8] 備份活動數據 (最新 20 筆)..."
python3 garmin_tools.py activity --count 20 --format original --originaltime --progress

# 2. 健康摘要 (步數、心率等)
echo "❤️ [2/8] 備份健康摘要 (${YESTERDAY})..."
python3 garmin_tools.py health --date "${YESTERDAY}" --progress

# 3. 睡眠分析
echo "😴 [3/8] 備份睡眠數據 (${YESTERDAY})..."
python3 garmin_tools.py sleep --date "${YESTERDAY}" --progress

# 4. HRV (心率變異度)
echo "📊 [4/8] 備份 HRV 數據 (${YESTERDAY})..."
python3 garmin_tools.py hrv --date "${YESTERDAY}" --detailed --progress

# 5. Body Battery (身體能量)
echo "⚡ [5/8] 備份 Body Battery (${YESTERDAY})..."
python3 garmin_tools.py body-battery --date "${YESTERDAY}" --progress

# 6. VO2 Max & 訓練狀態
echo "🏃 [6/8] 備份 VO2 Max 趨勢..."
python3 garmin_tools.py vo2max --date "${TODAY}" --progress

# 7. 體重紀錄
echo "⚖️ [7/8] 備份體重歷史..."
python3 garmin_tools.py weight --date "${TODAY}" --progress

# 8. 其他數據 (賽事、最大心率)
echo "🏁 [8/8] 備份賽事與最大心率指標..."
python3 garmin_tools.py race-event --date "${TODAY}" --progress
python3 garmin_tools.py max-hr --limit 5 --progress

echo "[$(date '+%Y-%m-%d %H:%M:%S')] ✅ 全量備份任務完成。"
