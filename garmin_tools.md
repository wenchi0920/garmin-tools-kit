# 🛠 Garmin Tool Kit (v1.4.1) 技術參考手冊

本手冊詳述 `garmin_tools.py` 的功能實作、參數配置與運作邏輯，幫助開發者與使用者深度掌握工具包。

---

## 1. 核心設計規範

### 1.1 智慧預設行為 (Smart Default)
若直接執行 `python garmin_tools.py` , `python garmin_tools.py activity` , `python garmin_tools.py workout` , `python garmin_tools.py health`, `python garmin_tools.py race-event` 而不帶任何子命令，系統將自動啟動預設任務：

python garmin_tools.py => python garmin_tools.py --help
python garmin_tools.py activity => python garmin_tools.py activity --help
python garmin_tools.py workout => python garmin_tools.py workout --help
python garmin_tools.py health => python garmin_tools.py health --help
python garmin_tools.py race-event => python garmin_tools.py race-event --help

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

python3 garmin_tools.py activity
python3 garmin_tools.py workout
python3 garmin_tools.py health
python3 garmin_tools.py race-event

python3 garmin_tools.py summary
python3 garmin_tools.py summary  預設當天日期 , 要提供所有 的健康數據, 然後不存檔, 使用檔案 

### 3.1 活動管理 (`activity`)
負責備份歷史運動記錄。
*   **檔案命名詳細規則 (Naming Convention)**:
    系統會根據活動的開始時間（當地時間）與時區偏移自動生成檔名，格式如下：
    `activity_YYYY-MM-DD_HH-MM-SS±HHMM[_描述].{格式}`
    *   **時間戳**: `YYYY-MM-DD_HH-MM-SS` (例如 `2026-03-21_08-30-00`)。
    *   **時區偏移**: `±HHMM` (例如 `+0800` 代表台北/北京時區)。
    *   **描述欄位**: 若帶有 `--desc` 參數且該活動有描述文字，系統會過濾非法字元並截取指定長度附加於後方。
    *   **範例**: `activity_2026-03-21_08-30-00+0800_MorningRun.fit`
*   `-c, --count`: 支援整數或 `all`, 預設 10 。
*   `-d, --date`: 指定單一日期 (YYYY-MM-DD)。
*   `-sd, --start-date`: 篩選起始日期 (YYYY-MM-DD)。
*   `-ed, --end-date`: 篩選結束日期 (YYYY-MM-DD)。
*   `-f, --format`: 支援 `original` (FIT), `gpx`, `tcx`, `json`, 預設 original。
*   `-ot, --originaltime`: 修正檔案的系統「建立/修改時間」，使其與運動時間同步（使用 GMT 時間戳）, 預設使用。
*   `--directory`: 指定儲存目錄 (預設 `data/activity`)。
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
整合 23 項生理與訓練指標。所有指令皆支援 `-d, --date`, `-sd, --start-date`, `-ed, --end-date`, `--summary`, `-o` 通用參數。

| 子命令 | 名稱 (名稱規則) | 檔案命名規則 (預設) | 功能描述與詳細說明 |
| :--- | :--- | :--- | :--- |
| `sleep` | 睡眠數據 | `sleep_{日期}.json` | **睡眠品質分析**。提供各階段時間(深層/淺層/REM)、睡眠分數及品質反饋。 |
| `body-battery` | 身體能量指數 | `body-battery_{日期}.json` | **能量趨勢監控**。紀錄充電與消耗值，反映當日身體疲勞與恢復狀況。 |
| `hrv` | 心率變異度 | `hrv_{日期}.json` | **心率變異度趨勢**。支援 `--detailed` 參數以獲取睡眠期間的高頻採樣。 |
| `weight` | 體重管理 | `weight_{日期}.json` | **體重與體組成**。支援 `--upload KG` 快速同步體重數據至雲端。 |
| `vo2max` | VO2 Max | `vo2max_{日期}.json` | **最大攝氧量評估**。追蹤體能發展，包含跑力值與體能年齡估算。 |
| `training-status` | 訓練狀態 | `training-status_{日期}.json` | **目前訓練負荷分析**。分析訓練量是否足以提升體能(生產、維持、過度訓練等)。 |
| `max-hr` | 最大心率統計 | `max-hr_{日期}.json` | **心率指標報表**。分析近期活動的最大心率，支援 `--from-file` 優先讀取快取。 |
| `stress` | 壓力水準 | `stress_{日期}.json` | **全日壓力監控**。紀錄平均壓力與最高壓力值，分析身心放鬆狀況。 |
| `heart-rate` | 每日心率 | `heart-rate_{日期}.json` | **安靜心率與心率區間**。紀錄靜止心率、最低心率與最高心率分佈。 |
| `steps` | 步數統計 | `steps_{日期}.json` | **活動量追蹤**。紀錄當日步數、目標達成率與步行距離。 |
| `calories` | 卡路里消耗 | `calories_{日期}.json` | **能量代謝紀錄**。區分基礎代謝 (BMR) 與活動卡路里消耗。 |
| `training-readiness` | 訓練完備度 | `training-readiness_{日期}.json` | **運動建議指南**。根據睡眠、恢復時間與壓力給予今日運動強度的建議。 |
| `fitness-age` | 體能年齡 | `fitness-age_{日期}.json` | **生理年齡分析**。根據 BMI、靜止心率與高強度活動量估算體能年齡。 |
| `lactate-threshold` | 乳酸閾值 | `lactate-threshold_{日期}.json` | **耐力指標追蹤**。紀錄乳酸閾值心率與配速，用於調整訓練區間。 |
| `race-predictions` | 賽事預測 | `race-predictions_{日期}.json` | **完賽時間預估**。根據體能估算 5k, 10k, 半馬與全馬的預期完賽時間。 |
| `intensity-minutes` | 熱血時間 | `intensity-minutes_{日期}.json` | **週活動量統計**。追蹤中高強度活動的分鐘數，符合健康建議。 |
| `hydration` | 補水紀錄 | `hydration_{日期}.json` | **水分攝取追蹤**。紀錄當日飲水量與預設目標之對比。 |
| `personal-records` | 個人紀錄 | `personal-records_{日期}.json` | **最佳紀錄存檔**。抓取所有運動項目的個人最佳成績。 |
| `insights` | Garmin Insights | `insights_{日期}.json` | **同儕數據對比**。提供與同性別/年齡組群的活動數據對比分析。 |
| `spo2` | 脈搏血氧 | `spo2_{日期}.json` | **血氧飽和度**。監控睡眠或高海拔期間的平均血氧水準。 |
| `respiration` | 呼吸頻率 | `respiration_{日期}.json` | **每分鐘呼吸次數**。紀錄睡眠與清醒時的平均呼吸頻率 (brpm)。 |
| `blood-pressure` | 血壓紀錄 | `blood-pressure_{日期}.json` | **血壓健康管理**。紀錄手動輸入或相容設備同步的收縮壓與舒張壓。 |

### 3.4 賽事管理 (`race-event`)
**通用參數**: `-d, --date` (單日), `-sd, --start-date` (範圍起始), `-ed, --end-date` (範圍結束), `--summary` (文字摘要), `-o` (輸出路徑)。
*   支援查看特定日期或範圍內的賽事紀錄。
*   `--summary` 會以時間軸形式美化輸出賽事清單。



### 3.5 文字摘要 (`summary`)
彙整  指定日期 文字摘要 預設當天日期， 優先使用檔案資料，如果沒有資料在下載
**通用參數**: `-d` 表示 今天往前顯示 幾天
**通用參數**: `-o` save to file  (單日)

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
