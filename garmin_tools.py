#!/usr/bin/env python3
"""
Purpose: Garmin Connect 工具包整合入口，支援活動、訓練計畫、健康數據、體重等全面管理。
Author: Gemini CLI
Changelog:
2026-03-08: 1.2.1 - 初始整合版本，合併 10 個獨立工具為統一 CLI 入口。
2026-03-09: 1.4.0 - 命名重構與輸出邏輯優化 (支援 --summary 與 -o 同時使用)。
2026-03-10: 1.4.1 - 完善 README.md 文件與補齊 subcommand 範例。
2026-03-11: 1.4.1 - 新增 --progress 全域參數，支援 tqdm 進度條與 log 同步輸出。
2026-03-11: 1.4.1 - 支援預設執行指令：不帶子命令時預設執行 activity -c 5。
2026-03-11: 1.4.2 - 版本手動更新。
2026-03-12: 1.4.2 - 實作資料存放標準化 (Data Storage Standardization) 與自動目錄生成，符合 garmin_tools.md 規範。
2026-03-12: 1.4.2 - 重構 COMMAND_HANDLERS 結構並修正 Docker 備份排程 (AM 11:00) 以符合 GEMINI.md 規範。
2026-03-17: 1.4.3 - 修正 fetch_race_calendar 忽略日期範圍 (-sd, -ed) 的 bug 並優化空結果 summary 輸出。
2026-03-21: 1.4.1 - 重構健康數據子命令結構，將所有健康指標整合進 health 父命令下，並新增細項指標抓取。
2026-03-21: 1.4.1 - 優化 resolve_default_output_path 以消除檔名中的冗餘目錄前綴，並更新整合測試腳本。
2026-03-22: 1.4.1 - 智慧啟動優化：主程式與子命令 (activity, workout, health, race-event) 未帶參數時預設執行 --help。
2026-03-22: 1.4.3 - 版本手動更新，優化健康數據異常攔截、寫檔判定邏輯與 Pydantic 模型容錯。
2026-03-23: 1.4.4 - 新增 health summary 表格顯示功能，支援從本地檔案彙整多日數據並匯出為 .txt 格式。
2026-03-23: 1.4.5 - 優化 health summary 表格顯示，新增睡眠分數、HRV 與血壓欄位，並預設顯示 7 天資料。
2026-03-23: 1.4.6 - 修正 health summary 表格顯示時，因部分數據為 None 導致的型別錯誤。
2026-03-23: 1.4.7 - 優化表格顯示格式，確保所有 None 值統一顯示為 --。
2026-03-26: 1.4.8 - 優化 health summary 邏輯，支援從本地所有 JSON 檔案彙整數據，解決範圍抓取導致的漏報問題。
2026-03-26: 1.4.9 - 強化 health summary 容錯機制 (Null Check) 並新增讀取檔案日誌 (Debug Level)。
2026-03-27: 1.5.0 - 重構：將 `garmin_tools.py` 拆分為 `utils.py`, `commands.py` 與主程式。
2026-04-04: 1.5.1 - 依照 garmin_tools.md 規範優化 summary 命令，支援自動下載缺失資料並調整預設行為。
"""
import argparse
import sys
from datetime import date

from loguru import logger

from core.utils import configure_runtime_logger
from core.commands import (
    execute_activity_export,
    manage_workout_workflow,
    process_health_command,
    fetch_race_calendar,
    execute_combined_summary
)

VERSION = "1.5.1"


# ==============================================================================
# 全域常數與對應處理函式 (Constants & Command Handlers)
# ==============================================================================

COMMAND_HANDLERS = {
    "activity": execute_activity_export,
    "workout": manage_workout_workflow,
    "health": process_health_command,
    "race-event": fetch_race_calendar,
    "summary": execute_combined_summary
}


def main():
    """程式入口點 (Entry Point)"""
    parser = argparse.ArgumentParser(description="Garmin Connect 整合工具包 (v" + VERSION + ")")
    parser.add_argument("--version", action="version", version=f"%(prog)s {VERSION}")
    parser.add_argument("-v", "--verbosity", action="count", default=0, help="詳細度")
    parser.add_argument("--username", help="Garmin 帳號")
    parser.add_argument("--password", help="Garmin 密碼")
    parser.add_argument("--env-file", nargs="?", const=".env", help="使用 env file (預設: .env)")
    parser.add_argument("-ss", "--session", default=".garth", help="SSO 目錄")
    parser.add_argument("--over-write", action="store_true", help="如果檔案存在則覆蓋，否則忽略已存在的檔案")
    parser.add_argument("--progress", action="store_true", help="顯示目前進度，啟用表示 用 tqdm 顯示目前進度/也要顯示log")
    parser.add_argument("--gui", action="store_true", help="啟動圖形化使用者介面 (GUI)")

    subparsers = parser.add_subparsers(dest="command", help="子命令 (未指定則顯示 --help)")

    # Activity
    activity_parser = subparsers.add_parser("activity", help="活動匯出")
    activity_parser.add_argument("-c", "--count", default="10", help="支援整數或 all, 預設 10")
    activity_parser.add_argument("-d", "--date", help="指定單一日期 (YYYY-MM-DD)")
    activity_parser.add_argument("-sd", "--start-date", "--start_date")
    activity_parser.add_argument("-ed", "--end-date", "--end_date")
    activity_parser.add_argument("-f", "--format", choices=["gpx", "tcx", "original", "json"], default="original")
    activity_parser.add_argument("--directory", default="data/activity")
    activity_parser.add_argument("-ot", "--originaltime", action="store_true", help="修正檔案時間 (預設啟用)")
    activity_parser.add_argument("--no-ot", action="store_false", dest="originaltime", help="停用修正檔案時間")
    activity_parser.set_defaults(originaltime=True)
    activity_parser.add_argument("--desc", nargs="?", const=True, help="檔名加入活動描述，可指定長度 [N]")

    # Workout
    workout_parser = subparsers.add_parser("workout", help="訓練計畫管理")
    workout_subparsers = workout_parser.add_subparsers(dest="workout_command", required=True)
    workout_subparsers.add_parser("list", help="列出計畫")
    p_wget = workout_subparsers.add_parser("get", help="下載計畫")
    p_wget.add_argument("id")
    p_wget.add_argument("-o", "--output")
    p_wup = workout_subparsers.add_parser("upload", help="上傳計畫 (YAML/DSL)")
    p_wup.add_argument("file")
    p_wdel = workout_subparsers.add_parser("delete", help="刪除計畫")
    p_wdel.add_argument("id")

    # Race Event
    race_parser = subparsers.add_parser("race-event", help="賽事清單與行事曆看板")
    race_parser.add_argument("-d", "--date", default=date.today().isoformat())
    race_parser.add_argument("-sd", "--start-date", "--start_date")
    race_parser.add_argument("-ed", "--end-date", "--end_date")
    race_parser.add_argument("--summary", action="store_true")
    race_parser.add_argument("-o", "--output")

    # Summary (Standalone) - 重新定義為全域綜合摘要
    summary_parser = subparsers.add_parser("summary", help="綜合文字摘要 (優先讀取本地資料，無資料則從 API 下載)")
    summary_parser.add_argument("-d", "--days", type=int, default=1, help="顯示從今天往前推算的天數 (預設 1 天, 即今天)")
    summary_parser.add_argument("-o", "--output", help="將摘要存儲至指定檔案 (.txt)")
    summary_parser.add_argument("--date", help="指定特定日期 (YYYY-MM-DD)，若提供則忽略 -d")

    # Health Subparsers
    health_parser = subparsers.add_parser("health", help="每日健康數據管理，包含步數、心率、能量、壓力、訓練指標等")
    health_subparsers = health_parser.add_subparsers(dest="health_command", required=True)

    # Health Subcommands
    def add_health_sub(sub_parser, name, help_text, has_detailed=False, has_upload=False, has_limit=False, has_from_file=False):
        p = sub_parser.add_parser(name, help=help_text)
        p.add_argument("-d", "--date", default=date.today().isoformat())
        p.add_argument("-sd", "--start-date", "--start_date")
        p.add_argument("-ed", "--end-date", "--end_date")
        p.add_argument("--summary", action="store_true", help="顯示文字摘要")
        p.add_argument("-o", "--output", help="儲存至指定 JSON 檔案")
        if has_detailed:
            p.add_argument("--detailed", action="store_true", help="包含詳細採樣點資料")
        if has_upload:
            p.add_argument("--upload", type=float, metavar="KG", help="上傳一筆新的體重紀錄 (kg)")
        if has_limit:
            p.add_argument("-l", "--limit", type=int, default=5, metavar="LIMIT", help="查詢最近活動的最大心率筆數")
        if has_from_file:
            p.add_argument("--from-file", action="store_true", help="優先從本地已下載的檔案讀取數據")
        return p

    add_health_sub(health_subparsers, "health", "基礎健康摘要 (步數、心率等)")
    add_health_sub(health_subparsers, "sleep", "睡眠數據")
    add_health_sub(health_subparsers, "body-battery", "身體能量指數")
    add_health_sub(health_subparsers, "hrv", "心率變異度 (HRV)", has_detailed=True)
    add_health_sub(health_subparsers, "weight", "體重管理", has_upload=True)
    add_health_sub(health_subparsers, "vo2max", "VO2 Max 與訓練狀態")
    add_health_sub(health_subparsers, "max-hr", "最大心率統計", has_limit=True, has_from_file=True)
    add_health_sub(health_subparsers, "stress", "壓力水準")
    add_health_sub(health_subparsers, "heart-rate", "每日心率")
    add_health_sub(health_subparsers, "steps", "步數統計")
    add_health_sub(health_subparsers, "calories", "卡路里消耗")
    add_health_sub(health_subparsers, "training-readiness", "訓練完備度")
    add_health_sub(health_subparsers, "training-status", "目前訓練狀態與負荷分析")
    add_health_sub(health_subparsers, "fitness-age", "體能年齡")
    add_health_sub(health_subparsers, "lactate-threshold", "乳酸閾值")
    add_health_sub(health_subparsers, "race-predictions", "賽事預測")
    add_health_sub(health_subparsers, "intensity-minutes", "熱血時間")
    add_health_sub(health_subparsers, "hydration", "補水紀錄")
    add_health_sub(health_subparsers, "personal-records", "個人紀錄")
    add_health_sub(health_subparsers, "insights", "Garmin Insights")
    add_health_sub(health_subparsers, "spo2", "脈搏血氧 (SpO2)")
    add_health_sub(health_subparsers, "respiration", "呼吸頻率")
    add_health_sub(health_subparsers, "blood-pressure", "血壓紀錄")

    # 若執行時未帶任何參數，或子命令後面未帶參數，則自動加上 --help 以符合 GEMINI.md 規範
    # 注意：根據 garmin_tools.md 3.5 節，summary 應支援預設當天日期直接執行
    if len(sys.argv) == 1:
        sys.argv.append("--help")
    elif len(sys.argv) > 1 and sys.argv[-1] in COMMAND_HANDLERS and sys.argv[-1] != "summary":
        sys.argv.append("--help")

    args = parser.parse_args()

    if args.gui:
        try:
            import garmin_gui
            garmin_gui.main()
            return
        except ImportError:
            print("錯誤: 找不到 garmin_gui.py 或其依賴項。請確保已安裝 tkinter。")
            return

    # 若無 command (例如只帶了全域參數但沒子命令)，則預設顯示 help
    if not args.command:
        parser.print_help()
        sys.exit(0)

    configure_runtime_logger(args.verbosity, args.progress)

    try:
        COMMAND_HANDLERS[args.command](args)
    except Exception as e:
        logger.error(f"程式執行失敗: {e}")
        if args.verbosity > 0: logger.exception("詳細錯誤：")
        sys.exit(1)


if __name__ == "__main__":
    main()
