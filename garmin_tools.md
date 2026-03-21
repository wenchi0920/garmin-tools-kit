# 🛠 Garmin Tool Kit (v1.4.1) 技術參考手冊

本手冊詳述 `garmin_tools.py` 的功能實作、參數配置與運作邏輯，幫助開發者與使用者深度掌握工具包。

---

## 1. 核心設計規範

### 1.1 智慧預設行為 (Smart Default)
若直接執行 `python garmin_tools.py` , `python garmin_tools.py activity` , `python garmin_tools.py workout` , `python garmin_tools.py health`, `python garmin_tools.py race-event` 而不帶任何子命令，系統將自動啟動預設任務：
*   **執行指令**: `--help`

### 1.2 認證獲取優先級 (Auth Hierarchy)
系統會依序檢查以下來源，直到獲取認證資訊：
1.  **CLI 參數**: `--username` 與 `--password`。
2.  **環境變數檔案**: `--env-file` (預設 `.env`) 中的 `GARMIN_USERNAME`。
3.  **系統環境變數**: 直接讀取 OS 的環境變數。
4.  **互動式輸入**: 若以上皆無，則在終端機提示輸入。

---

## 2. 全域通用選項 (Global Options)

| 選項 | 類型 | 功能描述 |
| :--- | :--- | :--- |
| `-v, -vv, -vvv` | 旗標 | 設定日誌層級 (INFO, DEBUG, TRACE)。 |
| `--progress` | 旗標 | 啟用進度條。整合 `tqdm` 與 `loguru`，確保日誌輸出不閃爍。 |
| `--over-write` | 旗標 | 開啟後，若目標檔案已存在則強制覆蓋。預設為「跳過」。 |
| `-ss, --session` | 路徑 | SSO 憑證目錄 (預設 `.garth`)。 |
| `--gui` | 旗標 | 啟動 Tkinter 圖形化使用者介面 (需安裝依賴)。 |

---

## 3. 子命令實作詳解

### 3.1 活動管理 (`activity`)
負責備份歷史運動記錄。
*   **檔案命名詳細規則 (Naming Convention)**:
    系統會根據活動的開始時間（當地時間）與時區偏移自動生成檔名，格式如下：
    `activity_YYYY-MM-DD_HH-MM-SS±HHMM[_描述].{格式}`
    *   **時間戳**: `YYYY-MM-DD_HH-MM-SS` (例如 `2026-03-21_08-30-00`)。
    *   **時區偏移**: `±HHMM` (例如 `+0800` 代表台北/北京時區)。
    *   **描述欄位**: 若帶有 `--desc` 參數且該活動有描述文字，系統會過濾非法字元並截取指定長度附加於後方。
    *   **範例**: `activity_2026-03-21_08-30-00+0800_MorningRun.fit`
*   `-c, --count`: 支援整數或 `all`。
*   `-f, --format`: 支援 `original` (FIT), `gpx`, `tcx`, `json`。
*   `-ot, --originaltime`: 修正檔案的系統「建立/修改時間」，使其與運動時間同步（使用 GMT 時間戳）。
*   `--desc [N]`: 檔名加入活動描述，截取前 `N` 個字元。


### 3.2 訓練計畫管理 (`workout`)
支援強大的 DSL 解析與自動排程。
*   `list`: 表格化輸出所有計畫的 ID、名稱、類型與建立日期。
*   `get <ID>`: 下載為 DSL 格式 (YAML)。
*   `upload <FILE>`: 
    *   **自動清理**: 若 YAML 設定 `deleteSameNameWorkout: true`，上傳前會自動刪除舊的同名課表。
    *   **自動排程**: 若 YAML 包含 `schedulePlan` (如 `start_from: 2026-03-01`)，系統會自動按順序將課表排入 Garmin 行事曆。
*   `delete <ID>`: 徹底刪除指定計畫。

### 3.3 健康數據中心 (`health`)
整合 22 項生理與訓練指標。

**通用參數**: `-d` (單日), `-sd`/`-ed` (範圍), `--summary` (文字摘要), `-o` (輸出路徑)。

| 類別 | 子命令 (Sub-commands) | 特殊功能 / 說明 |
| :--- | :--- | :--- |
| **基礎監測** | `summary`, `heart-rate`, `steps`, `calories`, `spo2`, `respiration`, `stress` | 支援範圍抓取與文字看板輸出。 |
| **品質分析** | `sleep`, `hrv`, `body-battery` | `hrv` 可選 `--detailed` 抓取 5 分鐘級別採樣。 |
| **進度指標** | `vo2max`, `training-status`, `training-readiness`, `fitness-age` | 包含訓練反饋語句與趨勢分析。 |
| **專項記錄** | `weight`, `hydration`, `blood-pressure` | `weight` 支援 `--upload KG` 快速紀錄。 |
| **長期統計** | `lactate-threshold`, `race-predictions`, `personal-records`, `insights` | 抓取個人最佳紀錄與系統建議。 |

### 3.4 賽事管理 (`race-event`)
**通用參數**: `-d` (單日), `-sd`/`-ed` (範圍), `--summary` (文字摘要), `-o` (輸出路徑)。
*   支援查看特定日期或範圍內的賽事紀錄。
*   `--summary` 會以時間軸形式美化輸出賽事清單。

---

## 4. 資料儲存與檔名規範 (DSS)

系統遵循「資料存放標準化」規範，所有輸出預設存放於 `data/` 目錄：

| 功能類別 | 預設子目錄 | 檔名規則範例 |
| :--- | :--- | :--- |
| **活動匯出** | `data/activity/` | `activity_2026-03-21_08-30-00+0800.fit` |
| **訓練計畫** | `data/workout/` | `workout_123456789.yaml` |
| **健康摘要** | `data/health/` | `health_2026-03-21.json` |
| **生理指標** | `data/{cmd}/` | `hrv_2026-03-21.json` |
| **身體能量** | `data/body-battery_{YYYY}/` | `body-battery_2026-03-21.json` |
| **範圍數據** | `data/{cmd}/` | `sleep_2026-03-01_2026-03-07.json` |

---

## 5. 開發者備註

*   **API 限頻**: 每步操作皆內建 `_random_delay()` (0.5s - 1.5s)，嚴禁惡意加速以防帳號被鎖。
*   **錯誤診斷**: 執行失敗時，使用 `-vv` 參數可查看完整的 Traceback 與 API 響應細節。

---
*Last Updated: 2026-03-21 | Garmin Tool Kit Engineering Team*
