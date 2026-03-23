# 🚀 Garmin Tool Kit: 開發者手冊與工程規範 (Master Engineering Guide)

本文件定義了專案的核心架構、開發標準與自動化行為準則。所有開發異動必須嚴格遵循本規範，確保系統達到「生產級別 (Production-Ready)」的穩定性。

---

## 1. 核心開發哲學 (Engineering Philosophy)
*   **偏執於正確性**：除了產出代碼，必須主動預判邊界條件、錯誤情境與相依關係。
*   **功能保全 (Functional Integrity)**：嚴禁改動邏輯運算。重構範圍僅限於「標識符更名 (Identifier Refactoring)」，確保輸出行為與原始版本 100% 一致。
*   **手動版本控制 (VERSION Rule)**：
    *   `client/__init__.py` 中的 `VERSION` 為最高權威。
    *   **嚴禁 AI 自動遞增版本號**。版本號更新必須由人類操作或獲取明確授權。
*   **最小異動原則 (LSP)**：每次修改必須經過多次思考，僅執行達成目標所需的最小變更。

---

## 2. 專案架構導覽 (Project Structure)

### 📂 目錄職責描述
*   `client/`: **核心通訊層**。封裝 Garmin API 請求、認證機制 (Garth) 與 DSL 解析邏輯。
*   `models/`: **DTO 資料模型**。使用 `Pydantic v2` 定義嚴謹的資料結構，負責資料驗證與 JSON 序列化。
*   `data/`: **預設存檔目錄**。遵循「資料存放標準化 (DSS)」規範，自動按子命令與日期分類儲存。
*   `example/`: **DSL 範本庫**。提供各種訓練計畫 (Workout) 的 YAML 範例。
*   `tests/`: **品質保證中心**。包含單元測試、整合測試與 CLI 模擬測試。

---

## 3. CLI 指令集與預設行為

### 核心子命令 (Subcommands)
1.  **`activity`**: 活動數據匯出（支援 GPX, TCX, FIT, JSON）。
2.  **`workout`**: 訓練計畫管理（list, get, upload, delete）。
3.  **`health`**: 健康數據中心（整合 sleep, hrv, vo2max, stress 等 20+ 項指標）。
4.  **`race-event`**: 賽事行事曆與看板管理。

### 預設行為與全域選項
*   **智慧啟動**：若執行 `garmin_tools.py` 未帶子命令，預設執行 --help。
*   **全域參數**：
    *   `--progress`: 同時啟用 `tqdm` 進度條與 `loguru` 日誌。
    *   `--over-write`: 檔案衝突處理預設為「跳過」，需帶此參數方可覆蓋。

---

## 4. 生產環境開發規範 (Production Standards)

### A. 代碼品質約束 (Code Quality)
*   **Python 嚴謹模式**：
    *   必須 100% 覆蓋 **Type Hints**。
    *   變數命名應體現「意圖」而非「資料類型」（例如 `is_active` 而非 `act_bool`）。
    *   函數名稱必須是強而有力的動詞。
*   **日誌系統**：實作 `trace` 到 `critical` 的分層日誌，處理大量資料時需輸出進度比例。
*   **安全防禦**：執行刪除或覆蓋動作前，必須記錄目標的**絕對路徑**。

### B. 環境與容器限制 (Docker & Env)
*   **Docker 排程**：內建自定義排程器 (`scheduler.py`)，於每天 **08, 13, 18, 23** 時自動執行 `backup.sh`。
*   **安全隔離**：`Dockerfile` 與 `docker-compose.yml` **嚴禁 Mount `.env` 檔案**，必須使用環境變數注入。

---

## 5. 測試與品質保證 (QA Protocol)

### 核心測試準則 (The Golden Rule)
> **「任何異動皆不完整，除非經過驗證。」**

*   **全量驗證**：每次異動必須執行 `pytest`，測試範圍必須涵蓋 **All Subcommands** 與 **All Options**。
*   **三層測試架構**：
    1.  **單元測試 (Unit Test)**: 驗證 DTO 模型與工具函式。
    2.  **整合測試 (Integration Test)**: 模擬 API 響應，驗證 CLI 路由與分發邏輯。
    3.  **端對端測試 (E2E Test)**: 驗證完整的下載、轉換與儲存工作流。
*   **延遲與限頻**：為了符合 Garmin API 規範，測試中應驗證隨機延遲 (0.5s - 1.5s) 邏輯。

---

## 6. 禁止與約束 (Strict Constraints)

1.  **檔案鎖定**：除非獲得明確指令，否則禁止修改 `garmin_tools.md`, `GEMINI.md`, `README.md`。
2.  **歷史透明**：版本紀錄 (Changelog) **嚴禁刪除舊紀錄**，僅能新增。
3.  **免責聲明**：本工具使用非官方 API，開發者必須遵守 Garmin 服務條款，嚴禁高頻率惡意請求。


## 6. README

<!-- Imported from: README.md -->
# Garmin Tool Kit (v1.4.7) 🚀

這是一個功能強大的 Garmin Connect 自動化工具包，旨在幫助運動愛好者與數據分析師透過 Python 腳本輕鬆管理 Garmin Connect 上的數據。本工具包現在已全面整合為單一入口 `garmin_tools.py`。

## 📋 目錄
1. [VERSION, 程式說明描述](#1-version-程式說明描述)
2. [核心功能](#2-核心功能)
3. [跨平台獨立執行檔下載](#3-跨平台獨立執行檔下載-免安裝-python)
4. [環境設定與安裝](#4-環境設定與安裝)
5. [認證機制](#5-認證機制)
6. [使用方式](#6-使用方式)
7. [CLI 參數與選項詳細說明](#7-cli-參數與選項詳細說明)
8. [使用範例 (完整)](#8-使用範例-完整)
9. [完整的 Workout Example 範例](#9-完整的-workout-example-範例)
10. [Workout DSL 完整指南](#10-workout-dsl-完整指南)
11. [開發與測試](#11-開發與測試)
12. [更新紀錄 (Changelog)](#12-更新紀錄-changelog)
13. [免責聲明](#13-免責聲明)

---

## 1. VERSION, 程式說明描述
- **Version**: v1.4.7
- **程式說明描述**: 
  這是一個用來與 Garmin Connect Web 溝通並抓取資料的命令列工具包。包含活動資料下載、訓練計畫 (Workout) 管理、健康數據匯出 (HRV, Sleep, Stress, VO2 Max, Training Readiness 等) 以及賽事行事曆管理。一切操作皆整合在 `garmin_tools.py` 中，適合進階運動員與想要批量處理數據的使用者。

## 2. 核心功能
- **整合入口**：一個 `garmin_tools.py` 搞定所有功能，支援子命令模式。
...
- **測試命令**: 執行 `pytest` 進行全量驗證 (Unit, Integration, E2E)。
- **日誌**: 使用 `loguru` 進行分層紀錄。

## 12. 更新紀錄 (Changelog)

- **2026-03-23**: **v1.4.7** - 🚀 **優化表格顯示格式。**
    - 確保 `None` 值統一顯示為 `--`，提升表格易讀性。
- **2026-03-23**: **v1.4.6** - 🚀 **Bug Fix: 修正 Summary 顯示錯誤。**
    - 解決當 `totalDistanceMeters` 為 `None` 時導致的計算錯誤。
- **2026-03-23**: **v1.4.5** - 🚀 **優化 Health Summary 表格顯示。**
    - 新增睡眠分數、HRV 與血壓欄位。
    - `health summary` 預設顯示過去 7 天資料。
    - 強化多檔案 (health, sleep, hrv, bp) 數據彙整邏輯。
- **2026-03-23**: **v1.4.4** - 🚀 **新增 Health Summary 表格顯示與多日彙整。**
    - 實作 `health summary` 表格輸出，支援 `-d N` 參數抓取過去 N 天資料。
    - 優化數據讀取邏輯，優先從本地 `data/health/` 目錄彙整資料。
    - 支援將表格直接匯出為 `.txt` 格式檔案。
- **2026-03-22**: **v1.4.3** - 🚀 **版本穩定性更新與 README 重構。**
...
1. VERSION , 程式說明描述
2. 核心功能
3. 跨平台獨立執行檔下載
4. 環境設定與安裝  一般使用/docker安裝
5. 認證機制
...