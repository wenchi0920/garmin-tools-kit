
import argparse
import getpass
import os
import sys
from datetime import datetime
from typing import Dict, Any

from loguru import logger
from tqdm import tqdm


def configure_runtime_logger(verbosity: int, use_progress: bool = False) -> None:
    """設定 Loguru 日誌層級與格式"""
    logger.remove()
    if verbosity == 0:
        level = "INFO"
    elif verbosity == 1:
        level = "DEBUG"
    else:
        level = "TRACE"

    log_format = "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{message}</cyan>"

    if use_progress:
        # 當啟用 progress 時，使用 tqdm.write 來避免破壞進度條
        logger.add(
            lambda msg: tqdm.write(msg, end=""),
            level=level,
            format=log_format,
            colorize=True
        )
    else:
        logger.add(
            sys.stderr,
            level=level,
            format=log_format
        )


def load_env_file(file_path: str) -> Dict[str, str]:
    """載入 .env 檔案"""
    env_data: Dict[str, str] = {}
    if not os.path.exists(file_path):
        return env_data
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, value = line.split("=", 1)
                env_data[key.strip()] = value.strip().strip("'").strip('"')
    except Exception as e:
        logger.error(f"讀取 env-file 錯誤: {e}")
    return env_data


def resolve_user_auth(args: argparse.Namespace) -> tuple[str, str]:
    """獲取使用者名稱與密碼"""
    username = args.username
    password = args.password

    env_file_path = args.env_file or (".env" if os.path.exists(".env") else None)
    if env_file_path:
        env_vars = load_env_file(env_file_path)
        username = username or env_vars.get("GARMIN_USERNAME") or env_vars.get("USERNAME")
        password = password or env_vars.get("GARMIN_PASSWORD") or env_vars.get("PASSWORD")

    # 檢查環境變數
    username = username or os.environ.get("GARMIN_USERNAME") or os.environ.get("USERNAME")
    password = password or os.environ.get("GARMIN_PASSWORD") or os.environ.get("PASSWORD")

    if not username:
        username = input("Garmin Connect 使用者名稱: ")
    if not password:
        password = getpass.getpass("Garmin Connect 密碼: ")

    return username, password


def format_seconds(seconds: Any) -> str:
    """格式化秒數為 時:分"""
    try:
        # 處理可能的 MagicMock 或 None
        sec = int(seconds) if seconds is not None else 0
    except (ValueError, TypeError):
        sec = 0
    hours, remainder = divmod(sec, 3600)
    minutes, _ = divmod(remainder, 60)
    return f"{hours}時{minutes}分"


import unicodedata

def pad_text(text: str, length: int, align: str = "<") -> str:
    """處理中英文混排的填充對齊"""
    if text is None:
        text = "--"
    
    # 計算顯示寬度
    display_width = 0
    for char in text:
        if unicodedata.east_asian_width(char) in ('F', 'W', 'A'):
            display_width += 2
        else:
            display_width += 1
            
    padding = max(0, length - display_width)
    if align == "<":
        return text + " " * padding
    elif align == ">":
        return " " * padding + text
    return text + " " * padding

def resolve_default_output_path(command: str, args: argparse.Namespace) -> str:
    """根據子命令與參數產生預設儲存路徑 (符合 garmin_tools.md 規範)"""
    base_dir = "data"
    sub_dir = command
    file_prefix = command

    # 支援 health 相關細項目錄
    if hasattr(args, "health_command") and args.health_command:
        # 特殊處理: summary 統一存在 data/health/
        if args.health_command == "summary":
            sub_dir = "health"
            file_prefix = "health"
        else:
            sub_dir = args.health_command
            file_prefix = args.health_command

        # 特殊處理: body-battery 包含年份資料夾
        if args.health_command == "body-battery":
            target_date = getattr(args, "date", None) or getattr(args, "start_date", None) or datetime.now().strftime("%Y-%m-%d")
            year = target_date[:4]
            sub_dir = f"body-battery_{year}"

    target_dir = os.path.join(base_dir, sub_dir)
    if not os.path.exists(target_dir):
        os.makedirs(target_dir, exist_ok=True)

    start_date = getattr(args, "start_date", None)
    end_date = getattr(args, "end_date", None)
    date_val = getattr(args, "date", None)

    if start_date and end_date:
        filename = f"{file_prefix}_{start_date}_{end_date}.json"
    elif start_date:
        filename = f"{file_prefix}_{start_date}_latest.json"
    else:
        # 如果都沒有，預設使用今天日期 (防止出現 _None.json)
        val = date_val or datetime.now().strftime("%Y-%m-%d")
        filename = f"{file_prefix}_{val}.json"

    return os.path.join(target_dir, filename)
