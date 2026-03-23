#!/bin/bash
# Purpose: 分時自動備份 Garmin 資料 (活動與生理數據)
# Author: Senior Systems Engineer
# Changelog:
# 2026-03-10: v1.0.0 - 初始版本
# 2026-03-17: v1.2.0 - 升級為全量備份 (包含 HRV, Sleep, Body Battery, VO2Max, Weight, Race-Event, Max-HR)
# 2026-03-20: v1.3.0 - 實作分時備份 (FIT: 08,11,18,23; 其他: 08) 並下載當天與前天資料
# 2026-03-20: v1.3.1 - 修正備份時段 (FIT: 08,13,18,23; 其他: 08) 並維持雙日資料下載
# 2026-03-22: 依照 garmin_tools.md 補齊所有健康指標 (23項)，確保每日抓取雙日資料
# 2026-03-22: 增加 -d 參數支援強制全量備份任務，優化 METRICS 循環邏輯
# 2026-03-22: 實作 Daily Logging 功能，日誌按日存放於 logs/ 目錄
# 2026-03-22: 實作 Command Logging 功能，完整記錄每一步執行的指令
# 2026-03-23: v1.3.2 - 將 health summary 備份時段調整為 (08, 13, 18, 23) 與 FIT 同步

set -euo pipefail

# 切換到腳本所在目錄
SCRIPT_DIR=$(cd "$(dirname "$0")"; pwd)
cd "${SCRIPT_DIR}"

# 定義日期與小時
YESTERDAY=$(date -d "yesterday" '+%Y-%m-%d')
TODAY=$(date '+%Y-%m-%d')
HOUR=$(date '+%H')

# --- 日誌配置 (Logging) ---
LOG_DIR="${SCRIPT_DIR}/logs"
LOG_FILE="${LOG_DIR}/backup_${TODAY}.log"
mkdir -p "${LOG_DIR}"

# 將所有輸出重新導向至日誌檔案與終端機 (tee)
exec > >(tee -a "${LOG_FILE}") 2>&1

# --- 輔助函式: 紀錄並執行指令 ---
run_cmd() {
    echo "[CMD] $*"
    "$@"
}

# 解析參數
FORCE_ALL=false
while getopts "d" opt; do
  case $opt in
    d) FORCE_ALL=true ;;
    *) echo "用法: $0 [-d (強制全量備份)]"; exit 1 ;;
  esac
done

echo "================================================================================"
if [ "$FORCE_ALL" = true ]; then
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] ⚠️ 偵測到強制執行參數 (-d)，將忽略小時檢查並執行全量備份..."
fi

echo "[$(date '+%Y-%m-%d %H:%M:%S')] 🚀 啟動備份任務 (Hour: ${HOUR}, Log: ${LOG_FILE})"
echo "================================================================================"

# 確保基礎數據目錄存在
mkdir -p "${SCRIPT_DIR}/data"

# 1. 活動數據 (FIT) 與 綜合摘要 (Summary): 於 08, 13, 18, 23 時執行，或強制執行時觸發
if [[ "$FORCE_ALL" == "true" || "$HOUR" == "08" || "$HOUR" == "13" || "$HOUR" == "18" || "$HOUR" == "23" ]]; then
    echo "📦 [FIT] 備份活動數據 (自 ${YESTERDAY} 至 ${TODAY})..."
    run_cmd python3 garmin_tools.py -v activity --start_date "${YESTERDAY}" --end_date "${TODAY}" --format original --originaltime

    echo "📊 [SUMMARY] 備份綜合摘要 (${YESTERDAY} & ${TODAY})..."
    run_cmd python3 garmin_tools.py -v --over-write health summary --date "${YESTERDAY}" --summary
    run_cmd python3 garmin_tools.py -v --over-write health summary --date "${TODAY}" --summary
fi

# 2. 其餘生理數據: 僅於 08 時執行全量備份，或強制執行時觸發
if [[ "$FORCE_ALL" == "true" || "$HOUR" == "08" ]]; then
    echo "❤️ [HEALTH] 執行全量生理健康數據備份 (${YESTERDAY} & ${TODAY})..."
    
    # 定義需要抓取雙日資料的指標 (Daily Metrics)
    METRICS=(
        "sleep" "body-battery" "hrv" "weight" "vo2max" 
        "training-status" "stress" "heart-rate" "steps" "calories" 
        "training-readiness" "spo2" "respiration" "hydration"
    )

    for metric in "${METRICS[@]}"; do
        echo "   -> 正在備份: ${metric}..."
        # HRV 需額外帶 --detailed
        if [[ "$metric" == "hrv" ]]; then
            run_cmd python3 garmin_tools.py -v --over-write health "${metric}" --date "${YESTERDAY}" --detailed
            run_cmd python3 garmin_tools.py -v --over-write health "${metric}" --date "${TODAY}" --detailed
        else
            run_cmd python3 garmin_tools.py -v --over-write health "${metric}" --date "${YESTERDAY}"
            run_cmd python3 garmin_tools.py -v --over-write health "${metric}" --date "${TODAY}"
        fi
    done

    # 定義範圍或單次執行的指標 (Range or Periodic Metrics)
    echo "   -> 正在更新週期性指標..."
    run_cmd python3 garmin_tools.py -v --over-write health fitness-age
    run_cmd python3 garmin_tools.py -v --over-write health lactate-threshold
    run_cmd python3 garmin_tools.py -v --over-write health race-predictions
    run_cmd python3 garmin_tools.py -v --over-write health personal-records
    run_cmd python3 garmin_tools.py -v --over-write health insights
    run_cmd python3 garmin_tools.py -v --over-write health max-hr --limit 5
    
    # 範圍指標
    run_cmd python3 garmin_tools.py -v --over-write health intensity-minutes --start_date "${YESTERDAY}" --end_date "${TODAY}"
    run_cmd python3 garmin_tools.py -v --over-write health blood-pressure --start_date "${YESTERDAY}" --end_date "${TODAY}"
    
    # 賽事數據
    echo "   -> 正在更新賽事行事曆..."
    run_cmd python3 garmin_tools.py -v --over-write race-event --start_date "${YESTERDAY}" --end_date "${TODAY}"
fi

echo -e "\n[$(date '+%Y-%m-%d %H:%M:%S')] ✅ 備份任務完成。"
echo "================================================================================"
