# Garmin Tool Kit CLI Reference (v1.5.0)

本文件整合了 `garmin_tools.py` 的指令結構說明與實際執行範例。

---

## 1. 全域選項 (Global Options)

### 結構說明
`python3 garmin_tools.py [-h] [--version] [-v] [--username USERNAME] [--password PASSWORD] [--env-file [ENV_FILE]] [-ss SESSION] [--over-write] [--progress] [--gui]`

### 執行範例
```bash
# 顯示幫助資訊與版本
python3 garmin_tools.py --help
python3 garmin_tools.py --version
```

---

## 2. 子命令: activity (活動匯出)

### 結構說明
`python3 garmin_tools.py activity [-h] [-c COUNT] [-d DATE] [-sd START_DATE] [-ed END_DATE] [-f {gpx,tcx,original,json}] [--directory DIRECTORY] [-ot] [--no-ot] [--desc [DESC]]`

### 執行範例
```bash
# 匯出最近 10 筆活動為 GPX 格式並顯示進度
python3 garmin_tools.py activity --count 10 --format gpx --progress

# 匯出特定日期活動為 JSON
python3 garmin_tools.py activity --date 2026-04-03 --format json

# 匯出指定日期範圍內的活動為 TCX
python3 garmin_tools.py activity --start-date 2026-03-01 --end-date 2026-03-31 --format tcx

# 匯出所有活動至指定目錄，並在檔名加入 20 字元的描述
python3 garmin_tools.py activity --count all --directory ./my_activities --desc 20
```

---

## 3. 子命令: workout (訓練計畫管理)

### 結構說明
- **列出計畫**: `python3 garmin_tools.py workout list [-h]`
- **下載計畫**: `python3 garmin_tools.py workout get [-h] [-o OUTPUT] id`
- **上傳計畫**: `python3 garmin_tools.py workout upload [-h] file`
- **刪除計畫**: `python3 garmin_tools.py workout delete [-h] id`

### 執行範例
```bash
# 列出所有訓練計畫
python3 garmin_tools.py workout list

# 下載指定 ID 的計畫並儲存為 YAML
python3 garmin_tools.py workout get 12345678 -o my_workout.yaml

# 從 YAML/DSL 檔案上傳計畫
python3 garmin_tools.py workout upload example/sprint_repeats.yaml

# 刪除指定 ID 的計畫
python3 garmin_tools.py workout delete 12345678
```

---

## 4. 子命令: race-event (賽事管理)

### 結構說明
`python3 garmin_tools.py race-event [-h] [-d DATE] [-sd START_DATE] [-ed END_DATE] [--summary] [-o OUTPUT]`

### 執行範例
```bash
# 顯示賽事摘要
python3 garmin_tools.py race-event --summary

# 匯出 2026 全年度賽事到 JSON 檔案
python3 garmin_tools.py race-event --start-date 2026-01-01 --end-date 2026-12-31 -o races.json
```

---

## 5. 子命令: summary (本地數據摘要)

### 結構說明
`python3 garmin_tools.py summary [-h] [-d DAYS] [-o OUTPUT] [--date DATE]`

### 執行範例
```bash
# 顯示過去 7 天的本地數據摘要
python3 garmin_tools.py summary --days 7

# 顯示特定日期的摘要並存成文字檔
python3 garmin_tools.py summary --date 2026-04-03 -o daily_report.txt
```

---

## 6. 子命令: health (健康數據管理)

### 結構說明
**基礎語法**: `python3 garmin_tools.py health {subcommand} [options]`

**健康子命令通用選項**:
`[-h] [-d DATE] [-sd START_DATE] [-ed END_DATE] [--summary] [-o OUTPUT]`

### 子命令清單與範例

| 子命令 | 功能描述 | 執行範例 (部分) |
| :--- | :--- | :--- |
| **health** | 基礎健康摘要 (步數、心率等) | `python3 garmin_tools.py health health --summary` |
| **sleep** | 睡眠數據 | `python3 garmin_tools.py health sleep --days 7 --summary` |
| **body-battery** | 身體能量指數 | `python3 garmin_tools.py health body-battery -d 2026-04-03` |
| **hrv** | 心率變異度 (HRV) | `python3 garmin_tools.py health hrv --summary` |
| **weight** | 體重管理 | `python3 garmin_tools.py health weight --summary` |
| **(weight upload)** | 上傳體重 | `python3 garmin_tools.py health weight --upload 70.5` |
| **vo2max** | VO2 Max 與訓練狀態 | `python3 garmin_tools.py health vo2max --summary` |
| **max-hr** | 最大心率統計 | `python3 garmin_tools.py health max-hr --summary` |
| **stress** | 壓力水準 | `python3 garmin_tools.py health stress --summary` |
| **heart-rate** | 每日心率 | `python3 garmin_tools.py health heart-rate -d 2026-04-03` |
| **steps** | 步數統計 | `python3 garmin_tools.py health steps -sd 2026-03-01 -ed 2026-03-07` |
| **calories** | 卡路里消耗 | `python3 garmin_tools.py health calories --summary` |
| **training-readiness** | 訓練完備度 | `python3 garmin_tools.py health training-readiness --summary` |
| **training-status** | 訓練狀態與負荷分析 | `python3 garmin_tools.py health training-status --summary` |
| **fitness-age** | 體能年齡 | `python3 garmin_tools.py health fitness-age` |
| **lactate-threshold** | 乳酸閾值 | `python3 garmin_tools.py health lactate-threshold` |
| **race-predictions** | 賽事預測 | `python3 garmin_tools.py health race-predictions` |
| **intensity-minutes** | 熱血時間 | `python3 garmin_tools.py health intensity-minutes` |
| **hydration** | 補水紀錄 | `python3 garmin_tools.py health hydration --summary` |
| **personal-records** | 個人紀錄 | `python3 garmin_tools.py health personal-records` |
| **insights** | Garmin Insights | `python3 garmin_tools.py health insights` |
| **spo2** | 脈搏血氧 (SpO2) | `python3 garmin_tools.py health spo2 --summary` |
| **respiration** | 呼吸頻率 | `python3 garmin_tools.py health respiration --summary` |
| **blood-pressure** | 血壓紀錄 | `python3 garmin_tools.py health blood-pressure --summary` |
