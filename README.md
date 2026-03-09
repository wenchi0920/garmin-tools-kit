# Garmin Tool Kit (v1.4.0) 🚀

這是一個功能強大的 Garmin Connect 自動化工具包，旨在幫助運動愛好者與數據分析師透過 Python 腳本輕鬆管理 Garmin Connect 上的數據。本工具包現在已全面整合為單一入口 `garmin_tools.py`。

---

## 📋 目錄
1. [核心功能](#-核心功能)
2. [環境設定與安裝](#-環境設定與安裝)
3. [認證機制](#-認證機制)
4. [CLI 完整教學 (garmin_tools.py)](#-cli-完整教學-garmin-toolspy)
5. [子命令詳細說明](#-子命令詳細說明)
6. [Docker 安裝與執行](#-docker-安裝與執行)
7. [Workout DSL 完整指南與範例](#-workout-dsl-完整指南與範例)
8. [🔄 更新紀錄 (Changelog)](#-更新紀錄-changelog)

---

## 🚀 核心功能

- **整合入口**：一個 `garmin_tools.py` 搞定所有功能，支援子命令模式。
- **數據導出**：支援將活動導出為 `FIT`, `GPX`, `TCX`, `JSON` 格式，並支援描述命名。
- **訓練自動化 (DSL)**：使用 YAML 定義訓練課表，支援複雜重複結構、區間目標。
- **週期排程**：自動刪除同名計畫並一次性排入整週課表至行事曆。
- **全方位健康追蹤**：HRV、睡眠分數、Body Battery、體重、VO2 Max 及最大心率。

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
source virtualenv/bin/activate

# 安裝依賴套件
pip install -r requirements.txt
```

---

## 🔐 認證機制

本工具使用 **Garth** 進行 SSO 登入。憑證會儲存在 `.garth/` 目錄中。

### 設定環境變數 (.env)
```env
GARMIN_USERNAME=your_email@example.com
GARMIN_PASSWORD=your_password
```

---

## 📖 CLI 完整教學 (`garmin_tools.py`)

所有功能現在都透過 `garmin_tools.py` 調用。

### 通用參數 (Global Options)
| 參數 | 說明 |
| :--- | :--- |
| `-v, -vv` | 增加日誌詳細度 (INFO -> DEBUG -> TRACE) |
| `--env-file` | 指定環境變數檔案 (預設為 `.env`) |
| `-ss, --session` | SSO 認證目錄 (預設為 `.garth`) |

### 子命令一覽 (Commands)
1. `activity`: 活動數據匯出
2. `workout`: 訓練計畫管理 (DSL/上傳/下載/排程)
3. `health`: 每日健康摘要
4. `sleep`: 睡眠分析與分數
5. `body-battery`: 身體能量趨勢
6. `vo2max`: VO2 Max 歷史與訓練狀態
7. `race-event`: 賽事清單抓取
8. `hrv`: HRV 狀態與詳細採樣點
9. `weight`: 體重趨勢與**體重上傳**
10. `max-hr`: 最大心率指標與活動心率紀錄

---

## 🔍 子命令詳細說明

### 🏃 活動數據匯出 (`activity`)
支援按數量或日期範圍抓取。
- **範例**: `python garmin_tools.py activity -c 5 -f gpx --desc 20`
- **參數**:
    - `-c, --count`: 數量或 `all`
    - `-sd, -ed`: 開始/結束日期
    - `-f`: 格式 (`original`, `gpx`, `tcx`, `json`)
    - `-ot`: 同步檔案時間戳記

### 🏋️ 訓練計畫管理 (`workout`)
- **範例 (列出)**: `python garmin_tools.py workout list`
- **範例 (上傳)**: `python garmin_tools.py workout upload example/yasso800_dsl.yaml`
- **範例 (下載)**: `python garmin_tools.py workout get <ID> -o my.yaml`

### 🏥 健康數據與生理指標
所有健康類指令均支援 `--summary` 顯示美化摘要。
- **HRV**: `python garmin_tools.py hrv --summary --detailed` (含 5 分鐘採樣)
- **睡眠**: `python garmin_tools.py sleep --summary -d 2026-03-08`
- **體重上傳**: `python garmin_tools.py weight --upload 70.5`
- **VO2 Max**: `python garmin_tools.py vo2max --summary -sd 2026-01-01`

---

## 🐳 Docker 安裝與執行

### 使用 Docker Compose (推薦)
1. 修改 `docker-compose.yml` 中的環境變數。
2. 執行：
```bash
docker-compose run --rm garmin-tools activity -c 5
```

### 手動 Docker 執行
```bash
docker build -t garmin-tools .
docker run --rm -v $(pwd)/.garth:/app/.garth -v $(pwd)/data:/app/data --env-file .env garmin-tools activity -c 3
```

---

## 📝 Workout DSL 完整指南與範例

### 1. 亞索 800 (Yasso 800) - `yasso800_dsl.yaml`
```yaml
workouts:
  "亞索 800 (10趟)":
    - warmup: 15min @H(z2)
    - repeat(10):
      - interval: 800m @P(4:20-4:30)
      - recovery: 3:30 @H(z1)
    - cooldown: 10min
```

### 2. 乳酸閾值/門檻跑 (Lactate Threshold)
```yaml
workouts:
  "門檻巡航間歇 (3x3km)":
    - warmup: 2km @H(z2)
    - repeat(3):
      - interval: 3km @P(4:45-4:55)
      - recovery: 2min @H(z1)
    - cooldown: 2km
```

### 3. 馬拉松 LSD (Long Slow Distance)
```yaml
workouts:
  "Marathon LSD 25km":
    - interval: 25km @H(z2)
```

### 4. 速度金字塔 (Pyramid Intervals)
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

---

## 🔄 更新紀錄 (Changelog)

- **2026-03-07**: v1.0.0 - 初始發布 (Activity/Workout)。
- **2026-03-08**: v1.2.1 - 完善 DTO 支援與環境變數優先級。
- **2026-03-09**: **v1.4.0** - 🚀 **重大更新：10 合 1 整合為 `garmin_tools.py` 單一入口。**
    - 新增 `hrv`, `sleep`, `health`, `body-battery`, `vo2max`, `max-hr`, `weight`, `race-event` 整合命令。
    - 統一認證處理流程與錯誤處理。
    - 支援美化摘要 (`--summary`) 模式。

---
*Last Updated: 2026-03-09*
