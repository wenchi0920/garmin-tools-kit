#!/bin/bash
# Purpose: 使用 tobix/pywine:3.10 編譯 Windows GUI
# Author: Gemini CLI
# Version: 1.4.2

set -e

APP_NAME="garmin-tools-gui-windows"
MAIN_SCRIPT="garmin_gui.py"
OUTPUT_NAME="garmin-tools-gui-windows.exe"

echo "=========================================================="
echo "🚀 準備編譯 Windows 版 Garmin GUI 執行檔 (使用 pywine:3.10)..."
echo "=========================================================="

# 1. 檢查 Docker
if ! command -v docker &> /dev/null; then
    echo "❌ 錯誤: 找不到 docker 指令。請先安裝 Docker。"
    exit 1
fi

# 2. 清理舊檔案
echo "🧹 清理舊的編譯目錄 (build/dist)..."
rm -rf build dist

# 3. 執行編譯
echo "📦 啟動 Docker 編譯容器 (tobix/pywine:3.10)..."

docker run --rm \
    -v "$(pwd):/src" \
    -w "/src" \
    tobix/pywine:3.10 \
    sh -c "python -m pip install --upgrade pip && \
           python -m pip install pyinstaller -r requirements.txt && \
           wine python -m PyInstaller --onefile --noconsole \
           --collect-all tkcalendar \
           --collect-all babel \
           --name ${APP_NAME} ${MAIN_SCRIPT}"

# 4. 驗證產出
if [ -f "dist/${APP_NAME}.exe" ]; then
    echo "=========================================================="
    echo "✅ 編譯成功！"
    echo "📍 檔案路徑: dist/${APP_NAME}.exe"
    echo "=========================================================="
else
    echo "❌ 編譯失敗，請檢查上方日誌。"
    exit 1
fi
