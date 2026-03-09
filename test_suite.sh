#!/bin/bash
# Garmin Tools Strictest Test Suite (v1.4.0)
# 涵蓋：Unit Test, Integration Test, E2E Test
# 準則：全子命令、全選項、全路徑覆蓋

LOG_FILE="test_results.log"
TEST_DIR="./test_suite_workspace"
rm -rf $TEST_DIR && mkdir -p $TEST_DIR

echo "================================================================"
echo "🛡️  STRICTEST TEST SUITE ACTIVATED"
echo "================================================================" | tee $LOG_FILE

# 成功檢查函數
check_status() {
    if [ $1 -eq 0 ]; then
        echo -e "✅ [SUCCESS] $2" | tee -a $LOG_FILE
    else
        echo -e "❌ [FAILURE] $2" | tee -a $LOG_FILE
        exit 1
    fi
}

# 檔案存在檢查
check_file() {
    if [ -f "$1" ]; then
        echo -e "📄 [FILE OK] $1 exists" | tee -a $LOG_FILE
    else
        echo -e "🚫 [FILE MISSING] $1 is missing" | tee -a $LOG_FILE
        exit 1
    fi
}

# --- 階段 0: 環境準備 ---
echo "--- PHASE 0: Environment Preparation ---" | tee -a $LOG_FILE
pip install pytest pytest-mock --quiet >> $LOG_FILE 2>&1

# --- 階段 1: 單元測試與整合測試 (Unit & Integration) ---
echo "--- PHASE 1: Unit & Integration Tests (pytest) ---" | tee -a $LOG_FILE
python3 -m pytest tests/ >> $LOG_FILE 2>&1
check_status $? "Pytest Suite (Models, Parsers, Client Logic)"

# --- 階段 2: 端對端測試 (E2E - garmin_tools.py) ---
echo "--- PHASE 2: End-to-End Tests (Full Command Coverage) ---" | tee -a $LOG_FILE

# 1. ACTIVITY: 全格式與全選項
echo "[E2E] Testing Activity (Formats: original, gpx, tcx, json)..." | tee -a $LOG_FILE
for fmt in original gpx tcx json; do
    python3 garmin_tools.py activity -c 1 -f $fmt -d $TEST_DIR/activity_$fmt --desc 10 --originaltime >> $LOG_FILE 2>&1
    check_status $? "Activity Export: $fmt with desc/ot"
done

# 2. WORKOUT: CRUD 完整生命週期
echo "[E2E] Testing Workout (DSL -> Upload -> Get -> Delete)..." | tee -a $LOG_FILE
UPLOAD_OUT=$(python3 garmin_tools.py workout upload example/yasso800_dsl.yaml 2>&1)
echo "$UPLOAD_OUT" >> $LOG_FILE
W_ID=$(echo "$UPLOAD_OUT" | grep -oE "ID: [0-9]+" | awk '{print $2}')
check_status $? "Workout: Upload DSL"
if [ -z "$W_ID" ]; then check_status 1 "Workout: Extract ID"; fi

python3 garmin_tools.py workout get $W_ID -o $TEST_DIR/downloaded.yaml >> $LOG_FILE 2>&1
check_status $? "Workout: Get YAML"
check_file "$TEST_DIR/downloaded.yaml"

python3 garmin_tools.py workout delete $W_ID >> $LOG_FILE 2>&1
check_status $? "Workout: Delete ID $W_ID"

# 3. HEALTH SUITE (Health, Sleep, Body Battery, HRV, VO2Max, Max-HR, Weight, Race)
echo "[E2E] Testing Health & Performance Suite..." | tee -a $LOG_FILE
commands=("health" "sleep" "body-battery" "vo2max" "race-event" "hrv" "weight" "max-hr")
for cmd in "${commands[@]}"; do
    args=""
    if [ "$cmd" == "hrv" ]; then args="--detailed"; fi
    if [ "$cmd" == "weight" ]; then 
        python3 garmin_tools.py weight --upload 70.0 -d $(date +%Y-%m-%d) >> $LOG_FILE 2>&1
        check_status $? "Weight: Upload"
    fi
    
    if [ "$cmd" == "max-hr" ]; then
        python3 garmin_tools.py max-hr -l 5 --summary >> $LOG_FILE 2>&1
        check_status $? "max-hr: Limit/Summary"
        continue
    fi
    
    python3 garmin_tools.py $cmd -sd 2026-03-01 --summary -o $TEST_DIR/$cmd.json >> $LOG_FILE 2>&1
    check_status $? "$cmd: Range/Summary/Output"
    check_file "$TEST_DIR/$cmd.json"
done

# 4. 全域與邊界檢查
echo "[E2E] Testing Global Flags & Auth Resolution..." | tee -a $LOG_FILE
python3 garmin_tools.py --version >> $LOG_FILE 2>&1
check_status $? "Global: Version"

python3 garmin_tools.py --env-file .env health -d 2026-03-08 >> $LOG_FILE 2>&1
check_status $? "Global: Env-file logic"

echo "================================================================"
echo "🛡️  ALL STAGES PASSED: STrictest Validation Complete"
echo "================================================================"
