#!/bin/bash
# Garmin Tool Kit 測試套件執行腳本
# 符合 GEMINI.md 規範：每次異動都要 test, test 內容要 all sub command, all option。

set -euo pipefail

export PYTHONPATH=.

echo "🚀 開始執行 Garmin Tool Kit 完整測試套件..."

# 1. 執行單元測試 (Models, DSL Parser, CLI Logic)
echo "----------------------------------------------------------------"
echo "📦 執行單元測試 (Unit Tests)..."
./virtualenv/bin/pytest tests/test_models.py tests/test_dsl_parser.py tests/test_cli_logic.py -v

# 2. 執行 CLI 全功能與參數測試
echo "----------------------------------------------------------------"
echo "命令行 執行 CLI 全功能與參數測試 (CLI & Options Tests)..."
./virtualenv/bin/pytest tests/test_full_cli.py -v

# 3. 測試隨機延遲邏輯 (驗證安全性規範)
# 這裡我們重新跑一次之前建立過的邏輯測試 (若檔案還在)
if [ -f tests/test_random_delay.py ]; then
    echo "----------------------------------------------------------------"
    echo "🛡️ 執行隨機延遲安全性測試 (Security/Random Delay Tests)..."
    ./virtualenv/bin/pytest tests/test_random_delay.py -v
fi

echo "----------------------------------------------------------------"
echo "✅ 所有測試已成功完成！"
