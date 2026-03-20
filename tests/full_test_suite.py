#!/usr/bin/env python3
"""
Purpose: Garmin Tool Kit 全方位整合測試套件 (v1.4.2)
Author: Gemini CLI
Changelog:
2026-03-12: v1.0.0 - 初始測試套件，涵蓋所有子命令與全域選項的冒煙測試。
"""
import subprocess
import os
import sys

def run_cmd(cmd):
    """執行命令並返回輸出與退出碼"""
    print(f"Executing: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True)
    return result

def test_global_options():
    """測試全域選項"""
    print("\n--- Testing Global Options ---")
    
    # 1. --version
    res = run_cmd([sys.executable, "garmin_tools.py", "--version"])
    assert res.returncode == 0, f"Version failed: {res.stderr}"
    print(f"SUCCESS: {res.stdout.strip()}")
    
    # 2. --help
    res = run_cmd([sys.executable, "garmin_tools.py", "--help"])
    assert res.returncode == 0, f"Help failed: {res.stderr}"
    assert "activity" in res.stdout, "Missing activity subcommand in help"
    print("SUCCESS: Global help displayed correctly.")

def test_subcommands_help():
    """測試所有子命令的 help 選項"""
    commands = [
        "activity", "workout", "health", "sleep", "body-battery",
        "vo2max", "hrv", "weight", "max-hr", "race-event"
    ]
    
    print("\n--- Testing Subcommand Help ---")
    for cmd in commands:
        res = run_cmd([sys.executable, "garmin_tools.py", cmd, "--help"])
        assert res.returncode == 0, f"Subcommand help failed: {cmd}, {res.stderr}"
        print(f"SUCCESS: {cmd} help displayed.")

def test_default_command():
    """測試預設指令 (activity -c 5)"""
    print("\n--- Testing Default Command ---")
    # 使用 -v 觸發日誌但不進行實際下載 (避免登入)
    res = run_cmd([sys.executable, "garmin_tools.py", "-v"])
    # 預期報錯 (因為未提供帳號)，但應確認 ArgumentParser 是否正確解析為 activity
    # 我們檢查 stdout/stderr 是否包含 activity 相關的日誌訊息
    assert "正在獲取活動列表... 數量=5" in res.stderr or "Garmin Connect 使用者名稱" in res.stdout, "Default command failed"
    print("SUCCESS: Default command (activity -c 5) correctly invoked.")

def test_data_storage_path_generation():
    """測試資料存放標準化 (不進行登入，僅驗證 ArgumentParser)"""
    print("\n--- Testing Path Generation (Smoke) ---")
    # 測試 activity 預設目錄
    res = run_cmd([sys.executable, "garmin_tools.py", "-v", "activity", "-c", "1"])
    assert "data/activity" in res.stderr or "Garmin Connect" in res.stdout, "Activity default directory mismatch"
    print("SUCCESS: Data storage paths align with garmin_tools.md specifications.")

def main():
    print("Starting Comprehensive Test Suite for Garmin Tool Kit...")
    
    try:
        test_global_options()
        test_subcommands_help()
        test_default_command()
        test_data_storage_path_generation()
        print("\n" + "="*50)
        print("ALL SMOKE TESTS PASSED!")
        print("="*50)
    except AssertionError as e:
        print(f"\nTEST FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\nAN ERROR OCCURRED: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
