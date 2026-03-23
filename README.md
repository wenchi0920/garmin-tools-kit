# Garmin Tool Kit (v1.4.6) 🚀

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
- **Version**: v1.4.6
- **程式說明描述**: 
  這是一個用來與 Garmin Connect Web 溝通並抓取資料的命令列工具包。包含活動資料下載、訓練計畫 (Workout) 管理、健康數據匯出 (HRV, Sleep, Stress, VO2 Max, Training Readiness 等) 以及賽事行事曆管理。一切操作皆整合在 `garmin_tools.py` 中，適合進階運動員與想要批量處理數據的使用者。

## 2. 核心功能
- **整合入口**：一個 `garmin_tools.py` 搞定所有功能，支援子命令模式。
- **數據導出**：支援將活動導出為 `FIT`, `GPX`, `TCX`, `JSON` 格式，並還原檔案時間。
- **訓練自動化 (DSL)**：使用 YAML 定義訓練課表，支援複雜重複結構與配速/心率區間。
- **健康數據中心**：整合所有生理指標至 `health` 父命令下，支援超過 20 種健康指標抓取與文字摘要 (`--summary`)。
- **賽事行事曆**：透過 `race-event` 管理您的比賽目標。
- **自動化備份 (Docker)**：容器內建 `cron` 排程，每天 AM 11:00 自動執行備份。
- **智慧啟動**：主程式與各子命令未帶參數時會自動顯示幫助訊息 (`--help`)。

## 3. 跨平台獨立執行檔下載 (免安裝 Python)
若您不想安裝 Python 環境，可以直接從 [GitHub Releases](../../releases) 下載對應作業系統的編譯版本：
- **Windows**: 下載 `garmin-tools-windows.exe`。
- **Linux**: 下載 `garmin-tools-linux`。
- **macOS**: 下載 `garmin-tools-macos`。

下載後，只需在終端機 (或 CMD/PowerShell) 中將其更名為 `garmin-tools` 並加上執行權限 (Linux/Mac) 即可直接使用。

## 4. 環境設定與安裝

### 一般使用 (Linux/Mac/Windows)
- **需求**：Python 3.10 或更高版本。
```bash
# 1. 複製專案
git clone <repository_url>
cd garmin-tools-kit

# 2. 建立並啟動虛擬環境
python3 -m venv virtualenv
source virtualenv/bin/activate # Windows 用 .\virtualenv\Scripts\Activate.ps1

# 3. 安裝依賴套件
pip install -r requirements.txt
```

### Docker 安裝與執行
使用 Docker 可以免去本地環境配置。
```bash
# 設定環境變數後執行 (避免將密碼存入 .env)
export GARMIN_USERNAME=your_email@example.com
export GARMIN_PASSWORD=your_password
docker-compose run --rm garmin-tools activity -c 5
```

## 5. 認證機制
本工具使用 **Garth** 進行 SSO (Single Sign-On) 登入。
- 首次登入成功後，憑證會儲存於 `.garth/` 目錄中。
- 請於根目錄建立 `.env` 檔案或設定環境變數：
```env
GARMIN_USERNAME=your_email@example.com
GARMIN_PASSWORD=your_password
```

## 6. 使用方式
- **Linux/Mac**: `python3 garmin_tools.py [subcommand] [options]`
- **Windows**: `python garmin_tools.py [subcommand] [options]`
- **智慧預設**: 直接執行 `python garmin_tools.py` 會顯示幫助資訊。

## 7. CLI 參數與選項詳細說明

### 全域選項 (Global Options)
- `--version`: 顯示程式版本。
- `-v, --verbosity`: 設定日誌詳細度 (`-v`, `-vv`, `-vvv`)。
- `--username USERNAME`: 覆寫 Garmin 帳號。
- `--password PASSWORD`: 覆寫 Garmin 密碼。
- `--env-file [FILE]`: 指定自訂環境變數檔案。
- `--progress`: 啟用進度條顯示。
- `--over-write`: 檔案存在時覆蓋。
- `--gui`: 啟動圖形化介面。

### 子命令 (Subcommands)
1. **`activity`**: 活動匯出。
   - `-c COUNT`: 下載 N 筆或 `all`。
   - `-f FORMAT`: 格式 (`gpx`, `tcx`, `original`, `json`)。
   - `-ot`: 還原活動真實時間。
   - `--desc [N]`: 檔名加入描述 (最長 N)。
2. **`workout`**: 訓練計畫管理。
   - `list`: 列出計畫。
   - `get <ID>`: 下載為 YAML。
   - `upload <FILE>`: 上傳 YAML/DSL 課表。
   - `delete <ID>`: 刪除計畫。
3. **`health`**: 整合健康數據。
   - **子命令**: `summary`, `sleep`, `hrv`, `body-battery`, `vo2max`, `weight`, `max-hr`, `stress`, `steps`, `training-readiness`, `training-status`, `fitness-age`, `lactate-threshold`, `race-predictions` 等。
   - `--summary`: 美化輸出摘要。
   - `--detailed`: (僅 hrv) 包含採樣點。
   - `--upload <KG>`: (僅 weight) 上傳體重。
4. **`race-event`**: 賽事行事曆。
   - `-sd`, `-ed`: 日期範圍篩選。
   - `--summary`: 列表顯示。
5. **`summary`**: 綜合日報。
   - `-d DATE`: 彙整指定日期所有本地/雲端數據。

## 8. 使用範例 (完整)

**活動管理：**
```bash
# 下載最新 5 筆 GPX 活動並還原時間戳
python garmin_tools.py activity -c 5 -f gpx -ot --progress
```

**訓練計畫：**
```bash
# 上傳自定義間歇課表
python garmin_tools.py workout upload example/yasso800_dsl.yaml
```

**健康數據 (整合 health 命令)：**
```bash
# 查看今日睡眠分數與分析
python garmin_tools.py health sleep --summary

# 以表格形式查看最近 7 天的健康摘要 (優先使用本地快取)
python garmin_tools.py health summary -d 7

# 將健康摘要表格儲存為文字檔
python garmin_tools.py health summary -d 10 -o data/health/report.txt

# 查看最近一週的 HRV 趨勢
python garmin_tools.py health hrv --summary -sd 2026-03-15

# 上傳今日體重 (70.5kg)
python garmin_tools.py health weight --upload 70.5

# 查看訓練完備度與 VO2 Max
python garmin_tools.py health training-readiness --summary
python garmin_tools.py health vo2max --summary
```

**賽事與綜合摘要：**
```bash
# 查看 2026 年賽事
python garmin_tools.py race-event -sd 2026-01-01 -ed 2026-12-31 --summary

# 一鍵生成今日健康全覽
python garmin_tools.py summary
```

## 9. 完整的 Workout Example 範例

### 1. 乳酸門檻 (Lactate Threshold)
```yaml
workouts:
  "門檻巡航間歇 (3x3km)":
    - warmup: 15min @H(z2)
    - repeat(3):
      - run: 3000m @P(4:30-4:45)
      - recovery: 2min @H(z1)
    - cooldown: 10min @H(z1)
```

### 2. 馬拉松 LSD (Long Slow Distance)
```yaml
workouts:
  "週日長跑 (LSD) 120min":
    - warmup: 10min @H(z1)
    - run: 100min @H(z2)
    - cooldown: 10min @H(z1)
```

### 3. 金字塔間歇訓練 (Pyramid Intervals)
```yaml
workouts:
  "速度金字塔 (4-8-12-8-4)":
    - warmup: 15min @H(z2)
    - interval: 400m @P(3:45-4:00)
    - recovery: 90s @H(z1)
    - interval: 800m @P(4:00-4:15)
    - recovery: 2min @H(z1)
    - interval: 1200m @P(4:00-4:15)
    - recovery: 3min @H(z1)
    - interval: 800m @P(4:00-4:15)
    - recovery: 2min @H(z1)
    - interval: 400m @P(3:45-4:00)
    - cooldown: 10min @H(z1)
```

### 4. 短距離衝刺 (Sprint Repeats)
```yaml
workouts:
  "斜坡/平地衝刺 (10x30s)":
    - warmup: 20min @H(z2)
    - repeat(10):
      - interval: 30s @P(3:00-3:30)
      - rest: 90s @H(z1)
    - cooldown: 15min @H(z1)
```

### 5. VO2 Max 間歇 (VO2 Max Intervals)
```yaml
workouts:
  "VO2 Max 間歇 (5x1k)":
    - warmup: 15min @H(z2)
    - repeat(5):
      - interval: 1000m @P(3:55-4:10)
      - recovery: 3min @H(z1)
    - cooldown: 10min @H(z1)
```

### 6. 亞索 800 (Yasso 800)
```yaml
workouts:
  "亞索 800 (10 趟)":
    - warmup: 15min @H(z2)
    - repeat(10):
      - interval: 800m @P(4:20-4:30)
      - recovery: 210s @H(z1)
    - cooldown: 10min @H(z1)
```

## 10. Workout DSL 完整指南

本工具支援 DSL 將 YAML 轉換為 Garmin API 結構。
- **目標設定**:
  - `@P(配速)`: 如 `@P(4:30-4:45)`。
  - `@H(心率)`: 如 `@H(z2)` 或 `@H(140-150)`。
- **重複區塊**: `repeat(N):` 後接縮排步驟。
- **動作**: `warmup`, `run`, `interval`, `recovery`, `rest`, `cooldown`。

## 11. 開發與測試
- **嚴謹模式**: 必須 100% 覆蓋 Type Hints。
- **測試命令**: 執行 `pytest` 進行全量驗證 (Unit, Integration, E2E)。
- **日誌**: 使用 `loguru` 進行分層紀錄。

## 12. 更新紀錄 (Changelog)

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
    - 根據 GEMINI.md 規範重構 README.md。
    - 優化健康數據異常處理與 Pydantic 模型容錯。
    - 更新主程式智慧啟動邏輯（未帶參數自動執行 --help）。
- **2026-03-21**: **v1.4.1** - 🚀 **重大重構：健康數據子命令整合。**
    - 將所有生理指標整合至 `health` 父命令下（如 `health sleep`, `health hrv`）。
    - 統一數據儲存路徑規範（DSS 標準）。
- **2026-03-17**: v1.4.3 - 修正 `race-event` 忽略日期範圍篩選的 Bug。
- **2026-03-12**: v1.4.2 - 實作資料存放標準化 (Data Storage Standardization)。
- **2026-03-11**: v1.4.1 - 新增 `--progress` 全域參數支援。
- **2026-03-09**: v1.4.0 - 重大更新：10 合 1 整合為單一入口。
- **2026-03-07**: v1.0.0 - 初始發布。

## 13. 免責聲明
本工具使用 Garmin Connect 的非官方 API。請遵守 Garmin 服務條款，避免高頻惡意請求。
為符合規範，程式在每次下載或抓取列表後會隨機延遲 **0.5s - 1.5s**。

---
*Generated by Gemini CLI - 2026-03-23*
