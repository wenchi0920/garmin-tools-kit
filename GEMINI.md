# Garmin Tool Kit 

這是一個用來與 Garmin Connect Web 溝通並抓取資料的工具包，支援活動匯出與訓練計畫 (Workout) 的 DSL 管理。


## 1. 資料夾說明

- `client/`: 核心通訊層。包含基於 `garth` 的認證機制、API 請求封裝及 DSL 解析器。
- `models/`: **DTO (Data Transfer Object)** 資料模型定義。使用 `Pydantic v2` 規範 Activity 與 Workout 的資料結構。
- `tests/`: 單元測試與集成測試集。包含 DTO 驗證、DSL 雙向轉換、Client 模擬測試。
- `data/`: 預設的活動資料匯出目錄。
- `example/`: 提供 Workout DSL 的範例 YAML 檔案（如 Yasso 800, VO2 Max, Sprint）。
- `data/`: 所有下載的資料 都預設 存放在這裡 。

## 2. 檔案說明 (Python Scripts)

### 版本控制
- `client/__init__.py`: 裡面的 VERSION, 不自動 遞疊 版本號碼 由我 手動控制

### 功能說明

- python3 garmin_tools.py --help

#### 全域 options 需求

  -h, --help            show this help message and exit
  --version             show program's version number and exit
  -v, --verbosity       詳細度
  --username USERNAME   Garmin 帳號
  --password PASSWORD   Garmin 密碼
  --env-file [ENV_FILE]
                        使用 env file (預設: .env)
  -ss SESSION, --session SESSION
                        SSO 目錄
  --over-write          如果檔案存在則覆蓋，否則忽略已存在的檔案
  --progress            顯示目前進度，啟用表示 用 tqdm 顯示目前進度/也要顯示log


- python3 garmin_tools.py activity => 活動匯出
#### activity options 需求

usage: garmin_tools.py activity [-h] [-c COUNT] [-sd START_DATE] [-ed END_DATE] [-f {gpx,tcx,original,json}] [-d DIRECTORY] [-ot] [--desc [DESC]]

options:
  -h, --help            show this help message and exit
  -c COUNT, --count COUNT
  -sd START_DATE, --start_date START_DATE
  -ed END_DATE, --end_date END_DATE
  -f {gpx,tcx,original,json}, --format {gpx,tcx,original,json}
  -d DIRECTORY, --directory DIRECTORY
  -ot, --originaltime
  --desc [DESC]




- python3 garmin_tools.py workout  => 訓練計畫管理
#### workout options 需求

usage: garmin_tools.py workout [-h] {list,get,upload,delete} ...

positional arguments:
  {list,get,upload,delete}
    list                列出計畫
    get                 下載計畫
    upload              上傳計畫 (YAML/DSL)
    delete              刪除計畫

options:
  -h, --help            show this help message and exit








- python3 garmin_tools.py health summary => 完整摘要
- python3 garmin_tools.py health sleep  => Sleep 睡眠紀錄與分析，包含分數與階段時間
- python3 garmin_tools.py health body-battery => 身體能量指數 (Body Battery) 趨勢與壓力摘要
- python3 garmin_tools.py health vo2max => VO2 Max 趨勢與目前訓練狀態報告
- python3 garmin_tools.py health hrv => HRV (心率變異度) 數據與摘要
- python3 garmin_tools.py health weight => 體重數據，支援 BMI 與體脂趨勢分析
- python3 garmin_tools.py health max-hr => 最大心率與安靜心率統計看板
- python3 garmin_tools.py health stress
- python3 garmin_tools.py health heart-rate
- python3 garmin_tools.py health steps
- python3 garmin_tools.py health calories
- python3 garmin_tools.py health training-readiness
- python3 garmin_tools.py health training-status
- python3 garmin_tools.py health fitness-age
- python3 garmin_tools.py health lactate-threshold
- python3 garmin_tools.py health race-predictions
- python3 garmin_tools.py health endurance-score
- python3 garmin_tools.py health hill-score
- python3 garmin_tools.py health personal-records
- python3 garmin_tools.py health performance-summary
- python3 garmin_tools.py health spo2
- python3 garmin_tools.py health respiration
- python3 garmin_tools.py health intensity-minutes
- python3 garmin_tools.py health blood-pressure
- python3 garmin_tools.py health hydration
- python3 garmin_tools.py health insights

#### health options 需求
usage: garmin_tools.py health [-h] [-d DATE] [-sd START_DATE] [-ed END_DATE] [--summary] [-o OUTPUT]

options:
  -h, --help            show this help message and exit
  -d DATE, --date DATE
  -sd START_DATE, --start_date START_DATE
  -ed END_DATE, --end_date END_DATE
  --summary
  -o OUTPUT, --output OUTPUT














### README

@README.md
必須要以下資料, 並依照 「最小異動原則，版本紀錄嚴禁刪除只能新增」 修改


1. VERSION , 程式說明描述
2. 核心功能
3. 跨平台獨立執行檔下載
4. 環境設定與安裝  一般使用/docker安裝
5. 認證機制
6. 使用方式  linux/mac/windows
7. cli 參數 詳細說明 / cli 子命令 詳細說明/ cli option 詳細說明
8. 使用範例 完整使用範例， 包含 all子命令 , all option 

9. 完整的 workout example 範例 (乳酸/LSD/金字塔間歇訓練/衝刺/VO2 Max/亞索 800)
10. Workout DSL 完整指南
11. 開發與測試
12. 更新紀錄 (Changelog)(版本紀錄嚴禁刪除只能新增, 並保留最新 20 的版本)
13. 免責聲明：本工具使用 Garmin Connect 的非官方 API。請遵守 Garmin 的服務條款，避免高頻率的惡意請求。
為了符合此規範，程式在每次下載活動與抓取活動列表後會隨機延遲 0.5s - 1.5s。


## 3. 測試與品質保證
專案包含完整的 `pytest` 測試集，確保核心邏輯的穩定性：
- `tests/test_activity_script.py`: 測試活動 CLI 腳本邏輯。
- `tests/test_workout_script.py`: 測試訓練計畫 CLI 腳本邏輯。
- `models/`: DTO 模型本身內建 Pydantic 驗證。

## 4. 程式碼結構模板 (Template)
每個腳本必須具備以下結構：
1. **Module Docstring**: 包含 Purpose, Author 及版本紀錄（嚴禁刪除舊紀錄）。
2. **Imports**: 標準庫 > 第三方庫 > 本地模組。
3. **Constants**: 全域常量，大寫蛇形命名。
4. **Main Logic**: 封裝在 `main()` 函式。
5. **Entry Point**: `if __name__ == "__main__":`。

## 5. 技術棧
- **環境**：Python 3.10+。
- **認證**：Garth (Garmin Connect SSO)。
- **工具**：Loguru (日誌), Pydantic v2 (DTO), Pytest (測試), tqdm (進度), PyYAML (DSL)。


## 6. test
- **測試file **：use @test_suite.sh。
- **測試**：每次異動都要 test , test 內容 要 all sub command, all option 。
- **test case **：每次異動都要 test case , test 內容 要 all sub command, all option 。
- **測試準則**：最嚴格嚴厲測試, 單元測試 (Unit Test)/整合測試 (Integration Test)/端對端測試 (E2E Test)

## 7. 禁止修改檔案
以下檔案 除非 我說要修改 或 允許修改 ， 否則 列出 異動的地方 
garmin_tools.md  
GEMINI.md  
README.md

## 8. docker compose 
1. docker 中 加入每天 AM11:00 自動執行備份
2. docker compose , dockerfile 禁止 mount .env file


