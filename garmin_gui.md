# Garmin Connect 批次下載工具 GUI 介面說明

這是一個基於 `tkinter` 開發的圖形化使用者介面 (GUI)，旨在提供更直觀的方式來批次下載 Garmin Connect 上的各項生理數據與活動紀錄。

對應檔案 `garmin_gui.py`

## 📋 介面功能摘要

1.  **自動化帳號登入**：啟動時自動讀取 `.env` 檔案，並將 `GARMIN_USERNAME` 與 `GARMIN_PASSWORD` 帶入輸入框。執行任務後也會自動更新 `.env`。
2.  **多功能批次勾選**：支援中英文對照的功能選單，可同時選取多項任務：
    *   `Activity` (活動匯出)
    *   `Health` (每日摘要)
    *   `Sleep` (睡眠紀錄)
    *   `HRV` (心率變異)
    *   `Body Battery` (身體能量)
    *   `VO2 Max` (最大攝氧)
    *   `Weight` (體重紀錄)
    *   `Max HR` (心率指標)
    *   `Race Event` (賽事清單)
3.  **智慧日期選擇器**：整合 `tkcalendar` (DateEntry) 彈出式日曆；若環境未安裝則自動切換為手動輸入框。預設範圍為最近 7 天。
4.  **跨平台路徑管理**：自動判別作業系統預設路徑（Windows: `C:\Garmin`, Linux/Mac: `~/Garmin`），並支援資料夾瀏覽修改。
5.  **任務控制**：具備「下載」與「取消」按鈕，支援在中途停止正在執行的背景任務。
6.  **即時日誌監控**：提供 20 行高度的深色模式日誌視窗，完整顯示背景 CLI 的每一條執行訊息。
7.  **偵錯日誌輸出**：同步產出實體檔案 `garmin_gui_debug.log` 供開發者排查問題。

---

## 🚀 啟動方式

確保您已安裝所有必要依賴項：
```bash
pip install -r requirements.txt
# 建議安裝日曆組件
pip install tkcalendar
```

使用以下任一指令啟動介面：
```bash
python3 garmin_gui.py
# 或
python3 garmin_tools.py --gui
```

---

## 🛠️ 技術細節

*   **版本**：v1.4.2
*   **執行緒安全**：採用 `root.after()` 進行 UI 非同步更新，解決 Linux 環境下背景執行緒操作 GUI 導致的 `Segmentation fault` 問題。
*   **子進程管理**：透過 `subprocess.Popen` 呼叫核心 `garmin_tools.py`，並即時補捉 stdout 輸出至日誌視窗。
*   **DPI 支援**：內建 Windows 高 DPI 縮放修正，確保在 4K 螢幕下介面不模糊。

---

## 📜 更新紀錄 (Changelog)

- **2026-03-11 (v1.4.2)**：整合取消按鈕、.env 自動填入、中英雙語勾選、tkcalendar 深度整合、20行長型日誌視窗與實體偵錯檔輸出。
