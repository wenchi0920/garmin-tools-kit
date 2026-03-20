#!/bin/bash
# Purpose: 分時自動備份 Garmin 資料 (活動與生理數據)
# Author: Senior Systems Engineer
# Changelog:
# 2026-03-10: v1.0.0 - 初始版本
# 2026-03-17: v1.2.0 - 升級為全量備份 (包含 HRV, Sleep, Body Battery, VO2Max, Weight, Race-Event, Max-HR)
# 2026-03-20: v1.3.0 - 實作分時備份 (FIT: 08,11,18,23; 其他: 08) 並下載當天與前天資料
# 2026-03-20: v1.3.1 - 修正備份時段 (FIT: 08,13,18,23; 其他: 08) 並維持雙日資料下載

set -euo pipefail

# 切換到腳本所在目錄
SCRIPT_DIR=$(cd "$(dirname "$0")"; pwd)
cd "${SCRIPT_DIR}"

# 定義日期與小時
YESTERDAY=$(date -d "yesterday" '+%Y-%m-%d')
TODAY=$(date '+%Y-%m-%d')
HOUR=$(date '+%H')

echo "[$(date '+%Y-%m-%d %H:%M:%S')] 🚀 執行備份任務 (Hour: ${HOUR})..."

# 確保基礎數據目錄存在
mkdir -p "${SCRIPT_DIR}/data"

# 1. 活動數據 (FIT): 於 08, 13, 18, 23 時執行，抓取當天與前天
if [[ "$HOUR" == "08" || "$HOUR" == "13" || "$HOUR" == "18" || "$HOUR" == "23" ]]; then
    echo "📦 [FIT] 備份活動數據 (自 ${YESTERDAY} 至 ${TODAY})..."
    python3 garmin_tools.py -v activity --start_date "${YESTERDAY}" --end_date "${TODAY}" --format original --originaltime
fi

# 2. 其餘生理數據: 僅於 08 時執行，抓取當天與前天
if [[ "$HOUR" == "08" ]]; then
    echo "❤️ [HEALTH] 備份生理健康數據 (${YESTERDAY} & ${TODAY})..."
    
    # 健康摘要
    python3 garmin_tools.py -v health --date "${YESTERDAY}"
    python3 garmin_tools.py -v health --date "${TODAY}"
    
    # 睡眠分析
    python3 garmin_tools.py -v sleep --date "${YESTERDAY}"
    python3 garmin_tools.py -v sleep --date "${TODAY}"
    
    # HRV (心率變異度)
    python3 garmin_tools.py -v hrv --date "${YESTERDAY}" --detailed
    python3 garmin_tools.py -v hrv --date "${TODAY}" --detailed
    
    # Body Battery (身體能量)
    python3 garmin_tools.py -v body-battery --date "${YESTERDAY}"
    python3 garmin_tools.py -v body-battery --date "${TODAY}"
    
    # VO2 Max & 訓練狀態
    python3 garmin_tools.py -v vo2max --date "${YESTERDAY}"
    python3 garmin_tools.py -v vo2max --date "${TODAY}"
    
    # 體重紀錄
    python3 garmin_tools.py -v weight --date "${YESTERDAY}"
    python3 garmin_tools.py -v weight --date "${TODAY}"
    
    # 其他數據 (賽事、最大心率)
    python3 garmin_tools.py -v race-event --date "${YESTERDAY}"
    python3 garmin_tools.py -v race-event --date "${TODAY}"
    python3 garmin_tools.py -v max-hr --limit 5
fi

echo "[$(date '+%Y-%m-%d %H:%M:%S')] ✅ 備份任務完成。"
