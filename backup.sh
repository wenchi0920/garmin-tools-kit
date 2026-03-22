#!/bin/bash
# Purpose: 分時自動備份 Garmin 資料 (活動與生理數據)
# Author: Senior Systems Engineer
# Changelog:
# 2026-03-10: v1.0.0 - 初始版本
# 2026-03-17: v1.2.0 - 升級為全量備份 (包含 HRV, Sleep, Body Battery, VO2Max, Weight, Race-Event, Max-HR)
# 2026-03-20: v1.3.0 - 實作分時備份 (FIT: 08,11,18,23; 其他: 08) 並下載當天與前天資料
# 2026-03-20: v1.3.1 - 修正備份時段 (FIT: 08,13,18,23; 其他: 08) 並維持雙日資料下載
# 2026-03-22: v1.4.0 - 依照 garmin_tools.md 補齊所有健康指標 (23項)，確保每日抓取雙日資料

set -euo pipefail

# 切換到腳本所在目錄
SCRIPT_DIR=$(cd "$(dirname "$0")"; pwd)
cd "${SCRIPT_DIR}"

# 定義日期與小時
YESTERDAY=$(date -d "yesterday" '+%Y-%m-%d')
TODAY=$(date '+%Y-%m-%d')
HOUR=$(date '+%H')

echo "[$(date '+%Y-%m-%d %H:%M:%S')] 🚀 執行全量備份任務 (Hour: ${HOUR})..."

# 確保基礎數據目錄存在
mkdir -p "${SCRIPT_DIR}/data"

# 1. 活動數據 (FIT): 於 08, 13, 18, 23 時執行，抓取當天與前天
if [[ "$HOUR" == "08" || "$HOUR" == "13" || "$HOUR" == "18" || "$HOUR" == "23" ]]; then
    echo "📦 [FIT] 備份活動數據 (自 ${YESTERDAY} 至 ${TODAY})..."
    python3 garmin_tools.py -v activity --start_date "${YESTERDAY}" --end_date "${TODAY}" --format original --originaltime
fi

# 2. 其餘生理數據: 僅於 08 時執行全量備份，抓取當天與前天
if [[ "$HOUR" == "08" ]]; then
    echo "❤️ [HEALTH] 執行全量生理健康數據備份 (${YESTERDAY} & ${TODAY})..."
    
    # 定義需要抓取雙日資料的指標 (Daily Metrics)
    METRICS=(
        "summary" "sleep" "body-battery" "hrv" "weight" "vo2max" 
        "training-status" "stress" "heart-rate" "steps" "calories" 
        "training-readiness" "spo2" "respiration" "hydration"
    )

    for metric in "${METRICS[@]}"; do
        echo "   -> 正在備份: ${metric}..."
        # HRV 需額外帶 --detailed
        EXTRA_ARGS=""
        if [[ "$metric" == "hrv" ]]; then EXTRA_ARGS="--detailed"; fi
        
        python3 garmin_tools.py -v health "${metric}" --date "${YESTERDAY}" ${EXTRA_ARGS}
        python3 garmin_tools.py -v health "${metric}" --date "${TODAY}" ${EXTRA_ARGS}
    done

    # 定義範圍或單次執行的指標 (Range or Periodic Metrics)
    echo "   -> 正在更新週期性指標..."
    python3 garmin_tools.py -v health fitness-age
    python3 garmin_tools.py -v health lactate-threshold
    python3 garmin_tools.py -v health race-predictions
    python3 garmin_tools.py -v health personal-records
    python3 garmin_tools.py -v health insights
    python3 garmin_tools.py -v health max-hr --limit 5
    
    # 範圍指標
    python3 garmin_tools.py -v health intensity-minutes --start_date "${YESTERDAY}" --end_date "${TODAY}"
    python3 garmin_tools.py -v health blood-pressure --start_date "${YESTERDAY}" --end_date "${TODAY}"
    
    # 賽事數據
    echo "   -> 正在更新賽事行事曆..."
    python3 garmin_tools.py -v race-event --start_date "${YESTERDAY}" --end_date "${TODAY}"
fi

echo "[$(date '+%Y-%m-%d %H:%M:%S')] ✅ 備份任務完成。"
