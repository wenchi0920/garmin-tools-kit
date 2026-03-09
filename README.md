# Garmin Tool Kit (v1.3.0) 🚀

這是一個功能強大的 Garmin Connect 自動化工具包，旨在幫助運動愛好者與數據分析師透過 Python 腳本輕鬆管理 Garmin Connect 上的數據。本工具包的核心優勢在於 **Workout DSL** ( 領域特定語言)，讓您能用人類可讀的 YAML 格式定義複雜的訓練計畫，並一鍵同步至雲端與行事曆。

---

## 📋 目錄
1. [核心功能](#-核心功能)
2. [環境設定與安裝](#-環境設定與安裝)
3. [認證機制](#-認證機制)
4. [活動數據匯出 (activity.py)](#-活動數據匯出-activitypy)
5. [比賽賽事抓取 (race_event.py)](#-比賽賽事抓取-race_eventpy)
6. [訓練計畫管理 (workout.py)](#-訓練計畫管理-workoutpy)
7. [健康數據系列 (Health Suite)](#-健康數據系列-health-suite)
8. [Workout DSL 完整指南](#-workout-dsl-完整指南)
9. [開發與測試](#-開發與測試)
10. [🔄 更新紀錄 (Changelog)](#-更新紀錄-changelog)

---

## 🚀 核心功能

- **數據導出**：支援將活動導出為 `FIT`, `GPX`, `TCX`, `JSON` 格式，並支援檔案時間戳記同步。
- **賽事管理**：抓取 Garmin 行事曆中的比賽賽事 (Race Events) 清單。
- **訓練自動化**：使用 YAML 定義訓練課表，支援複雜的重複結構、區間目標（心率、配速、功率）。
- **週期排程**：一次性排入整週或整個月的訓練計畫至 Garmin 行事曆。
- **全方位健康追蹤**：抓取 HRV (心率變異度)、睡眠分數、每日健康摘要、身體能量指數、體重趨勢、VO2 Max 及最大心率。
- **精確指標**：獲取 API 隱藏的精確數據（如 VO2 Max 小數點、ACWR 負荷比值）。

---

## 🛠 環境設定與安裝

### 需求
- Python 3.10+
- 建議使用虛擬環境 (virtualenv)

### 安裝步驟
```bash
# 複製專案
git clone <repository_url>
cd garmin-tools-kit

# 建立並啟動虛擬環境
python3 -m venv virtualenv
source virtualenv/bin/activate  # Linux/macOS
# virtualenv\Scripts\activate  # Windows

# 安裝依賴套件
pip install -r requirements.txt
```

---

## 🔐 認證機制

本工具使用 **Garth** 進行 SSO (單一登入)。登入成功後，憑證會安全地儲存在 `.garth/` 目錄中，有效期長達一年。

### 設定環境變數
在專案根目錄建立 `.env` 檔案，可自動讀取帳密：
```env
GARMIN_USERNAME=your_email@example.com
GARMIN_PASSWORD=your_password
```

---

## 🏃 活動數據匯出 (`activity.py`)

負責從 Garmin Connect Web 抓取活動資料，支援多種匯出格式與自動化命名。

### 詳細 CLI 參數教學
| 參數 | 說明 | 範例 |
| :--- | :--- | :--- |
| `-c, --count` | 下載最近活動數量 (預設 1, 輸入 `all` 抓取全部) | `-c 10` |
| `-sd, --start_date` | 開始日期 (YYYY-MM-DD) | `-sd 2026-01-01` |
| `-ed, --end_date` | 結束日期 (YYYY-MM-DD) | `-ed 2026-03-08` |
| `-f, --format` | 格式: `original` (下載 .zip 並解壓為 .fit), `gpx`, `tcx`, `json` | `-f gpx` |
| `-d, --directory` | 儲存目錄 (預設 `./data`) | `-d ./my_runs` |
| `-ot, --originaltime`| 將檔案修改時間設為活動開始時間 | `-ot` |
| `--desc [LEN]` | 在檔名中加入活動描述，可限制字數長度 | `--desc 20` |
| `-v, -vv` | 增加輸出詳細度 (DEBUG/TRACE) | `-vv` |

### 檔名規範
匯出的檔案將統一命名為：`activity_YYYY-mm-dd_HH-ii-ss+時區.格式`
- 使用活動發生地的當地時間。
- 末尾標記時區偏移量（例如 `+0800`）。

### 教學範例
1. **下載最近 5 筆活動並儲存為 GPX**:
   ```bash
   python activity.py -c 5 -f gpx --env-file
   ```
2. **下載 2026 年初的所有原始資料並同步檔案時間**:
   ```bash
   python activity.py -sd 2026-01-01 -ed 2026-03-01 -f original -ot
   ```

---

## 🏁 比賽賽事抓取 (`race_event.py`)

負責從 Garmin Connect 行事曆中抓取使用者已建立或訂閱的**比賽賽事 (Race Events)**，並匯出為 JSON 格式供分析。

### 詳細 CLI 參數教學
| 參數 | 說明 | 範例 |
| :--- | :--- | :--- |
| `-sd, --start_date` | 開始日期 (YYYY-MM-DD) | `-sd 2024-01-01` |
| `-ed, --end_date` | 結束日期 (YYYY-MM-DD) | `-ed 2024-12-31` |
| `-d, --directory` | 儲存目錄 (預設 `./data`) | `-d ./my_races` |
| `-ss, --session` | SSO 認證儲存目錄 | `-ss .garth` |

### 教學範例
1. **抓取 2024 年全年的賽事**:
   ```bash
   python race_event.py -sd 2024-01-01 -ed 2024-12-31
   ```
2. **抓取未來已排定的賽事**:
   ```bash
   python race_event.py
   ```

---

## 🏋️ 訓練計畫管理 (`workout.py`)

支援透過 DSL (YAML) 管理 Garmin 訓練計畫，實現「代碼即課表」。

### 子指令說明
- **`list`**：列出帳號下所有訓練計畫 (顯示 ID, 名稱, 類型, 日期)。
- **`get <id>`**：將雲端計畫下載並轉換為可編輯的 YAML DSL 格式。
- **`upload <file>`**：上傳一個或多個課表 DSL 檔案至雲端。
- **`delete <id>`**：刪除雲端指定的訓練計畫。

### 教學範例
1. **列出所有計畫**: `python workout.py list --env-file`
2. **下載指定計畫為 YAML**: `python workout.py get 12345678 -o my_workout.yaml`
3. **上傳新課表**: `python workout.py upload example/marathon_lsd.yaml`

---

## 🏥 健康數據系列 (Health Suite)

這是一組專門抓取生理指標的工具，均支援 `--summary` 模式提供直觀輸出。

### 通用操作參數
- `-d, --date`: 指定單一日期 (YYYY-MM-DD)，預設為今天。
- `-sd, --start_date`: 開始日期，用於獲取歷史趨勢資料。
- `-ed, --end_date`: 結束日期 (預設為今天)。
- `--summary`: 在終端機顯示人性化的排版摘要（推薦使用）。
- `-o, --output`: 將原始 JSON 資料儲存至指定路徑。

### 1. HRV 狀態 (`hrv.py`)
- **功能**：獲取心率變異度摘要與睡眠期間的 5 分鐘採樣點。
- **範例**：`python hrv.py --summary`

### 2. 睡眠分析 (`sleep.py`)
- **功能**：獲取睡眠分數、評語及各階段（深層、REM、淺層）時長。
- **範例**：`python sleep.py --summary`

### 3. 健康摘要 (`health.py`)
- **功能**：獲取步數、活動卡路里、壓力、呼吸頻率與靜止心率。
- **範例**：`python health.py --summary`

### 4. 身體能量 (`body_battery.py`)
- **功能**：獲取 Body Battery 的充電/消耗狀況與關鍵影響事件。
- **範例**：`python body_battery.py --summary`

### 5. 體重管理 (`weight.py`)
- **功能**：獲取體重歷史趨勢或**上傳**最新測量值。
- **上傳範例**：`python weight.py --upload 72.5`

### 6. 體能指標 (`vo2max.py`)
- **功能**：獲取 VO2 Max 趨勢（精確至小數點）與訓練狀態 (Load, ACWR, 狀態評語)。
- **範例**：`python vo2max.py --summary`

### 7. 心率指標 (`max_hr.py`)
- **功能**：獲取今日最大心率、安靜心率、乳酸閾值及歷史活動心率。
- **範例**：`python max_hr.py --summary`

---

## 📝 Workout DSL 完整指南

### 1. 單位與語法
- **時間**：`10min`, `90s`, `1:30` (分:秒)
- **距離**：`1km`, `800m`, `5k`, `10mile`
- **目標 (@)**：
    - **心率**：`@H(z1)` (區間 1), `@H(140-150)` (自定義 bpm)
    - **配速**：`@P(5:00-5:30)` (min/km), `@P($Easy)` (變數引用)
    - **功率**：`@W(200-220)` (Watts)

### 2. 完整訓練範例：亞索 800 (`yasso800_dsl.yaml`)
亞索 800 (Yasso 800) 是預測全馬成績的經典訓練。邏輯為跑 800m，恢復時間與 800m 跑步時間相同。
```yaml
settings:
  deleteSameNameWorkout: true  # 上傳時自動刪除雲端同名計畫

definitions:
  # 目標全馬 3 小時 30 分，則 800m 跑 3 分 30 秒 (約 4:22 min/km)
  Yasso_Pace: 4:20-4:30
  Recovery_HR: z1

workouts:
  "亞索 800 (10 趟)":
    - warmup: 15min @H(z2)
    - repeat(10):
      - interval: 800m @P($Yasso_Pace)
      - recovery: 210s @H($Recovery_HR)  # 210s = 3:30 慢跑恢復
    - cooldown: 10min @H(z1)

schedulePlan:
  start_from: 2026-03-09
  workouts:
    - "亞索 800 (10 趟)"
    - "rest"
    - "rest"
```

---

## 🧪 開發與測試

```bash
# 執行所有單元測試
python3 -m pytest tests/ -v
```

---

## 🔄 更新紀錄 (Changelog)

- **2026-03-09 (v1.3.0)**:
  - 新增 `race_event.py` 比賽賽事抓取工具，支援 `--summary` 美化輸出。
  - 實作 `RaceEventClient` 與 `RaceEventModel` DTO。
  - 完善單元測試與 `race_event.md` 指南。
- **2026-03-09 (v1.2.2)**:
  - 整合 `activity.md` 與 `workout.md` 詳細教學至主 README。
  - 新增亞索 800 (Yasso 800) 完整 DSL 範例。
  - 擴充 Health Suite 所有工具的詳細參數說明與教學範例。
- **2026-03-08 (v1.2.1)**:
  - 1.2.1 版本發佈。
  - 支援全系列健康數據抓取 (HRV, Sleep, Body Battery, etc.)。
  - 強化 Workout DSL 支援與 Pydantic v2 模型校驗。

---
**免責聲明**：本工具使用 Garmin Connect 的非官方 API。請遵守 Garmin 的服務條款，避免高頻率的惡意請求。

*Generated by Gemini CLI - 2026-03-08*
*Updated by Gemini CLI - 2026-03-09*
