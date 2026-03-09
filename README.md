# Garmin Tool Kit (v1.4.0) 🚀

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
- **Version**: v1.4.0
- **程式說明描述**: 
  這是一個用來與 Garmin Connect Web 溝通並抓取資料的命令列工具包。包含活動資料下載、訓練計畫 (Workout) 管理 (使用特製的 YAML DSL 格式定義與上傳)、每日健康摘要、心率變異度 (HRV)、睡眠紀錄、最大心率指標、VO2 Max 等各項生理與訓練數據的查詢。一切操作皆整合在 `garmin_tools.py` 中，適合進階運動員與想要批量處理資料的使用者。

## 2. 核心功能
- **整合入口**：一個 `garmin_tools.py` 搞定所有功能，支援子命令模式。
- **數據導出**：支援將活動導出為 `FIT`, `GPX`, `TCX`, `JSON` 格式，並支援描述命名，甚至可同步原始活動時間到檔案。
- **訓練自動化 (DSL)**：使用 YAML 定義訓練課表，支援複雜重複結構 (`repeat`)、自訂配速區間 (`@P`)、心率區間 (`@H`) 與全域變數設定 (`definitions`)。
- **週期排程與管理**：自動刪除 Garmin 上的同名計畫，一次性排入整週課表至行事曆，並支援備份現有課表。
- **全方位健康追蹤**：包含 HRV、睡眠分數、Body Battery (身體能量趨勢)、體重變化、VO2 Max (最大攝氧量) 及最大心率等生理指標查詢與美化輸出 (`--summary`)。

## 3. 跨平台獨立執行檔下載 (免安裝 Python)
若您不想安裝 Python 環境，可以直接從 [GitHub Releases](../../releases) 下載對應作業系統的編譯版本：
- **Windows**: 下載 `garmin-tools-windows.exe`。
- **Linux**: 下載 `garmin-tools-linux`。
- **macOS**: 下載 `garmin-tools-macos`。

下載後，只需在終端機 (或 CMD/PowerShell) 中將其更名為 `garmin-tools` 並加上執行權限 (Linux/Mac) 即可直接使用：
```bash
# Linux/Mac 範例
chmod +x garmin-tools-linux
./garmin-tools-linux activity -c 5
```

## 4. 環境設定與安裝

### 一般使用 (Linux/Mac/Windows)
- **需求**：Python 3.10 或更高版本。建議使用虛擬環境隔離套件。
```bash
# 1. 複製專案
git clone <repository_url>
cd garmin-tools-kit

# 2. 建立並啟動虛擬環境 (視作業系統而定)
python3 -m venv virtualenv
# Linux / Mac:
source virtualenv/bin/activate
# Windows (PowerShell):
.\virtualenv\Scripts\Activate.ps1

# 3. 安裝依賴套件
pip install -r requirements.txt
```

### Docker 安裝與執行
使用 Docker 可以免去本地環境配置的煩惱。
```bash
# 使用 Docker Compose (推薦)
# 請先修改 docker-compose.yml 內的環境變數
docker-compose run --rm garmin-tools activity -c 5

# 手動 Docker 執行
docker build -t garmin-tools .
docker run --rm -v $(pwd)/.garth:/app/.garth -v $(pwd)/data:/app/data --env-file .env garmin-tools activity -c 3
```

## 5. 認證機制
本工具使用 **Garth** 進行 SSO (Single Sign-On) 登入。這是一種安全且推薦的登入方式。
- 首次成功登入後，登入憑證與 Session 資訊會預設儲存於工作目錄下的 `.garth/` 目錄中。
- 後續執行指令時將直接讀取憑證，免去重複登入。

請建立並設定環境變數檔案 (預設為 `.env`) 於專案根目錄：
```env
GARMIN_USERNAME=your_email@example.com
GARMIN_PASSWORD=your_password
```

## 6. 使用方式
無論在哪個作業系統下，都透過執行 `garmin_tools.py` 搭配對應的子命令來使用。
- **Linux/Mac**: 開啟 Terminal，切換至專案目錄，並載入虛擬環境後執行：
  `python3 garmin_tools.py [subcommand] [options]`
- **Windows**: 開啟 Command Prompt 或 PowerShell，載入虛擬環境後執行：
  `python garmin_tools.py [subcommand] [options]`

## 7. CLI 參數與選項詳細說明

### 全域選項 (Global Options)
任何子命令都可以搭配以下全域選項使用：
- `-h, --help`: 顯示幫助訊息。
- `--version`: 顯示程式版本。
- `-v, --verbosity`: 設定日誌詳細度。可重複使用 (`-v` 為 INFO, `-vv` 為 DEBUG, `-vvv` 為 TRACE)。
- `--username USERNAME`: 覆寫 `.env` 中的 Garmin 帳號。
- `--password PASSWORD`: 覆寫 `.env` 中的 Garmin 密碼。
- `--env-file [ENV_FILE]`: 指定自訂的環境變數檔案路徑 (預設為 `.env`)。
- `-ss SESSION, --session SESSION`: 指定 SSO 憑證儲存目錄 (預設為 `.garth`)。

### 子命令 (Subcommands)
1. **`activity`**: 活動匯出。
   - `-c COUNT, --count COUNT`: 下載最新的 N 筆活動，或使用 `all` 下載全部。
   - `-sd START_DATE, --start_date START_DATE`: 篩選起始日期 (YYYY-MM-DD)。
   - `-ed END_DATE, --end_date END_DATE`: 篩選結束日期 (YYYY-MM-DD)。
   - `-f {gpx,tcx,original,json}, --format`: 指定下載格式 (預設通常為 original)。
   - `-d DIRECTORY, --directory DIRECTORY`: 指定儲存目錄 (預設為 `data/`)。
   - `-ot, --originaltime`: 將下載檔案的系統建立/修改時間修改為活動發生的真實時間。
   - `--desc [DESC]`: 在檔名中加入活動描述 (預設最多 20 字元)。
2. **`workout`**: 訓練計畫管理 (支援 `list`, `get`, `upload`, `delete` 四個動作)。
   - `list`: 列出雲端上的計畫。
   - `get <ID> -o <FILE>`: 下載指定 ID 的計畫為 YAML。
   - `upload <FILE>`: 將 YAML 定義上傳為 Garmin 課表。
   - `delete <ID>`: 刪除指定的課表 ID。
3. **`health`**: 每日健康摘要。
   - `-d, -sd, -ed`: 指定單日或日期範圍。
   - `--summary`: 美化並總結輸出結果。
   - `-o OUTPUT`: 匯出至檔案。
4. **`sleep`**: 睡眠紀錄與分析。
   - `-d, -sd, -ed, --summary, -o OUTPUT`: 同上。
5. **`body-battery`**: 身體能量指數。
   - `-d, -sd, -ed, --summary, -o OUTPUT`: 同上。
6. **`vo2max`**: VO2 Max 與訓練狀態。
   - `-d, -sd, -ed, --summary, -o OUTPUT`: 同上。
7. **`race-event`**: 賽事清單。
   - `-d, -sd, -ed, --summary, -o OUTPUT`: 同上。
8. **`hrv`**: HRV 數據。
   - `-d, -sd, -ed, --summary, -o OUTPUT`: 同上。
   - `--detailed`: 包含 5 分鐘級別的詳細採樣點資料。
9. **`weight`**: 體重數據。
   - `-d, -sd, -ed, --summary, -o OUTPUT`: 同上。
   - `--upload UPLOAD`: 上傳一筆新的體重紀錄 (單位為 kg)。
10. **`max-hr`**: 心率指標。
    - `-d DATE`: 查詢特定日期。
    - `-l LIMIT, --limit LIMIT`: 限制查詢筆數。
    - `--summary`: 美化輸出。

## 8. 使用範例 (完整)

**通用參數示範：**
```bash
python garmin_tools.py -vv --env-file .prod.env activity -c 5
```

**Activity (活動匯出):**
```bash
# 下載最新 10 筆 GPX 活動，使用活動描述為檔名，並還原檔案時間戳
python garmin_tools.py activity -c 10 -f gpx --desc 20 -ot

# 下載 2026-01-01 到 2026-01-31 的 FIT 原始檔
python garmin_tools.py activity -sd 2026-01-01 -ed 2026-01-31 -f original
```

**Workout (訓練計畫):**
```bash
# 上傳課表
python garmin_tools.py workout upload example/yasso800_dsl.yaml

# 列出現有課表
python garmin_tools.py workout list

# 下載單一課表並儲存為 YAML
python garmin_tools.py workout get 123456789 -o my_workout.yaml
```

**Health / 生理指標:**
```bash
# 美化輸出當日 HRV，並附帶詳細數據
python garmin_tools.py hrv --summary --detailed

# 查詢指定日期的睡眠分數
python garmin_tools.py sleep --summary -d 2026-03-08

# 查看一段時間內的 Body Battery
python garmin_tools.py body-battery --summary -sd 2026-03-01 -ed 2026-03-07

# 上傳體重紀錄 (例如: 70.5kg)
python garmin_tools.py weight --upload 70.5

# 查看最高心率歷史
python garmin_tools.py max-hr --limit 5 --summary
```

## 9. 完整的 Workout Example 範例

此工具支援使用 YAML 高度自訂各種類型的跑步與訓練計畫。

### 1. 乳酸閾值/門檻跑 (Lactate Threshold)
```yaml
workouts:
  "門檻巡航間歇 (3x3km)":
    - warmup: 2km @H(z2)
    - repeat(3):
      - interval: 3km @P(4:45-4:55)
      - recovery: 2min @H(z1)
    - cooldown: 2km
```

### 2. 馬拉松 LSD (Long Slow Distance)
```yaml
workouts:
  "Marathon LSD 25km":
    - interval: 25km @H(z2)
```

### 3. 金字塔間歇訓練 (Pyramid Intervals)
```yaml
workouts:
  "速度金字塔 (4-8-12-8-4)":
    - repeat(1):
      - interval: 400m @P(4:00)
      - recovery: 200m
      - interval: 800m @P(4:10)
      - recovery: 400m
      - interval: 1200m @P(4:20)
      - recovery: 600m
      - interval: 800m @P(4:10)
      - recovery: 400m
      - interval: 400m @P(4:00)
```

### 4. 短距離衝刺 (Sprint Repeats)
```yaml
settings:
  deleteSameNameWorkout: true
definitions:
  Sprint_Pace: 3:00-3:30
workouts:
  "斜坡/平地衝刺 (10x30s)":
    - warmup: 20min @H(z2)
    - repeat(10):
      - interval: 30s @P($Sprint_Pace)
      - rest: 90s @H(z1)
    - cooldown: 15min @H(z1)
```

### 5. VO2 Max 間歇 (VO2 Max Intervals)
```yaml
workouts:
  "VO2 Max 間歇 (5x1k)":
    - warmup: 15min
    - repeat(5):
      - interval: 1000m @P(4:00-4:10)
      - recovery: 3min @H(z1)
    - cooldown: 10min
```

### 6. 亞索 800 (Yasso 800)
```yaml
workouts:
  "亞索 800 (10趟)":
    - warmup: 15min @H(z2)
    - repeat(10):
      - interval: 800m @P(4:20-4:30)
      - recovery: 3:30 @H(z1)
    - cooldown: 10min
```

## 10. Workout DSL 完整指南

此專案使用獨創的 DSL (Domain Specific Language) 結合 YAML 檔案，可將自然語言風格的課表轉換為 Garmin API 支援的結構。

### 結構說明
- `settings`: (可選) 例如 `deleteSameNameWorkout: true` 可以在上傳時自動覆蓋舊的同名課表。
- `definitions`: (可選) 全域變數，方便統一管理配速或心率區間，例如 `My_Pace: 4:30-5:00`，後續可透過 `$My_Pace` 呼叫。
- `workouts`: 課表主體，使用 `Map` 定義，鍵為課表名稱，值為步驟列表。

### 步驟與距離/時間定義
- **動作類型**: `warmup` (暖身), `interval` (訓練), `recovery` (恢復), `rest` (休息), `cooldown` (緩和)。
- **長度單位**:
  - 距離: `km`, `m` (例如: `3km`, `400m`)
  - 時間: `min`, `s` (例如: `15min`, `30s`)
- **重複區塊**: 
  - `repeat(N):` 代表接下來的子步驟將執行 `N` 次。必須縮排定義子步驟。

### 目標區間定義 (Targets)
- **配速 `@P(...)`**: 可以給定範圍 `4:00-4:10`，或單一數值 `4:00` (系統會視為精確目標或稍做寬容計算)。
- **心率 `@H(...)`**:
  - `z1` ~ `z5`: 內建的 Garmin 心率區間 (Zone 1 到 Zone 5)。
  - 也可以直接給定數值 `140-150` 表示目標心率介於 140~150 bpm。

### DSL 語法範例解析
`- interval: 800m @P(4:20-4:30)`
- 動作: `interval` (間歇)
- 條件: 達到 `800m`
- 目標: 配速介於 `4:20/km` 到 `4:30/km` 之間。

## 11. 開發與測試

為確保此專案在生產環境下穩健運作，所有開發行為必須符合《生產級工程開發規範彙整》(參考 `GEMINI.md`)。

### 測試與品質保證
專案包含完整的 `pytest` 測試集，確保核心邏輯的穩定性。每次異動都必須執行完整測試，包含：單元測試 (Unit Test) / 整合測試 (Integration Test) / 端對端測試 (E2E Test)。
- **測試命令**: 執行所有測試需涵蓋全部子命令與選項。
- **測試目錄**:
  - `tests/`: 包含 `test_activity_script.py`, `test_workout_script.py` 等 CLI 測試。
  - `models/`: 透過 `Pydantic v2` 自帶嚴謹的結構驗證，保護 DTO 轉換的正確性。

每次修改後請確保所有測試皆綠燈，並落實「最小異動原則」。

## 12. 更新紀錄 (Changelog)

- **2026-03-07**: v1.0.0 - 初始發布 (Activity/Workout)。
- **2026-03-08**: v1.2.1 - 完善 DTO 支援與環境變數優先級。
- **2026-03-09**: **v1.4.0** - 🚀 **重大更新：10 合 1 整合為 `garmin_tools.py` 單一入口。**
    - 新增 `hrv`, `sleep`, `health`, `body-battery`, `vo2max`, `max-hr`, `weight`, `race-event` 整合命令。
    - 統一認證處理流程與錯誤處理。
    - 支援美化摘要 (`--summary`) 模式。
    - 更新 `README.md` 包含完整使用範例、全功能選項詳解與開發測試規範。

## 13. 免責聲明

免責聲明：本工具使用 Garmin Connect 的非官方 API。請遵守 Garmin 的服務條款，避免高頻率的惡意請求。使用者若因濫用高頻請求導致帳號遭受限制，請自行負責。

---
*Generated by Gemini CLI - 2026-03-09*
