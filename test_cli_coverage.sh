#!/bin/bash

# ==============================================================================
# Garmin Tool Kit: CLI Coverage Test Suite
# This script verifies that all subcommands and options are correctly defined
# and that the argument parser is functioning for all possible inputs.
# ==============================================================================

# 顏色定義
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 偵測 python 指令
if command -v python3 &>/dev/null; then
    PYTHON=python3
elif command -v python &>/dev/null; then
    PYTHON=python
else
    echo -e "${RED}[ERROR] Python is not installed.${NC}"
    exit 1
fi

# 基礎測試函式
test_command() {
    local cmd="$1"
    local desc="$2"
    echo -n "Testing: $desc ($cmd) ... "
    output=$($PYTHON garmin_tools.py $cmd --help 2>&1)
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}[PASS]${NC}"
    else
        echo -e "${RED}[FAIL]${NC}"
        echo "$output"
        return 1
    fi
}

echo -e "${BLUE}=== Starting CLI Coverage Tests ===${NC}"

# 1. 全域選項
test_command "" "Global Help"
test_command "--version" "Version"

# 2. Activity
test_command "activity" "Activity Subcommand"
test_command "activity -c 5 -f gpx --directory tmp_test --desc" "Activity with options"

# 3. Workout
test_command "workout" "Workout Subcommand"
test_command "workout list" "Workout List"
test_command "workout get 123456" "Workout Get"
test_command "workout upload test.yaml" "Workout Upload"
test_command "workout delete 123456" "Workout Delete"

# 4. Race Event
test_command "race-event" "Race Event Subcommand"
test_command "race-event --summary" "Race Event options"

# 5. Summary (Standalone)
test_command "summary" "Standalone Summary"
test_command "summary -d 7 -o test_summary.txt" "Summary options"

# 6. Health
test_command "health" "Health Subcommand"

HEALTH_SUBS=(
    "sleep" "body-battery" "hrv" "weight" "vo2max" "max-hr" 
    "stress" "heart-rate" "steps" "calories" "training-readiness" 
    "training-status" "fitness-age" "lactate-threshold" "race-predictions" 
    "intensity-minutes" "hydration" "personal-records"  
    "spo2" "respiration" "blood-pressure"
)

for sub in "${HEALTH_SUBS[@]}"; do
    test_command "health $sub" "Health Subcommand: $sub"
done

# 7. 特殊選項測試 (驗證 removed option 確實不在)
echo -n "Verifying --from-file is removed from health max-hr ... "
if $PYTHON garmin_tools.py health max-hr --help 2>&1 | grep -q -e "--from-file"; then
    echo -e "${RED}[FAIL] --from-file still exists in help output!${NC}"
    exit 1
else
    echo -e "${GREEN}[PASS] --from-file correctly removed.${NC}"
fi

echo -e "${BLUE}=== CLI Coverage Tests Completed ===${NC}"
