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


### 核心執行腳本
- `activity.py`: 活動匯出工具 (CLI)。支援按數量、日期範圍抓取活動，並下載為各種格式。
- `workout.py`: 訓練計畫管理工具 (CLI)。支援 DSL 解析、批次上傳、自動刪除同名計畫與行事曆排程。

### Client 模組 (`client/`)
- `client.py`: 基礎客戶端類別。負責處理 Garmin Garth 的登入與 Session 管理。
- `activity_client.py`: 實作活動列表獲取與檔案下載解壓。**全面採用 ActivityModel DTO**。
- `workout_client.py`: 實作 Workout 的 CRUD 與排程。
- `workout_parser.py`: **Workout DSL 解析器與匯出器**。支援 `YAML ↔ DTO ↔ Garmin JSON` 的雙向轉換。

### 資料模型 (`models/`)
- `activityModel.py`: 活動 DTO，包含時區偏移與微秒補全的日期解析邏輯。
- `workoutModel.py`: 訓練計畫 DTO，嚴格定義 Garmin API 的層級結構與 alias。

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


