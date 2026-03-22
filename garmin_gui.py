#!/usr/bin/env python3
"""
Purpose: Garmin Tool Kit GUI 批次下載介面 (終極整合版)
Author: Gemini CLI
Changelog:
2026-03-11: 1.4.2 - 整合取消按鈕、.env 自動填入、中英雙語、tkcalendar、20行長日誌與實體偵錯檔。
"""

import os
import platform
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from datetime import datetime, timedelta
import subprocess
import sys
import re
import logging

from client import VERSION

# 嘗試加載 tkcalendar
HAS_CALENDAR = False
try:
    from tkcalendar import DateEntry
    HAS_CALENDAR = True
except ImportError:
    pass

# 7. 偵錯日誌檔配置 (@garmin_gui_debug.log)
DEBUG_LOG_FILE = "garmin_gui_debug.log"
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler(DEBUG_LOG_FILE, encoding='utf-8'),
        logging.StreamHandler()
    ]
)

def get_default_download_path():
    if platform.system() == "Windows":
        return r"C:\Garmin"
    else:
        return os.path.join(os.path.expanduser("~"), "Garmin")

class GarminGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Garmin Connect 批次工具 v" + VERSION)
        self.root.geometry("850x950")
        
        # 狀態控制
        self.is_running = False
        self.current_process = None
        
        # 1. 變數定義
        self.username_var = tk.StringVar()
        self.password_var = tk.StringVar()
        self.download_path_var = tk.StringVar(value=get_default_download_path())
        self.start_date_var = tk.StringVar(value=(datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d"))
        self.end_date_var = tk.StringVar(value=datetime.now().strftime("%Y-%m-%d"))
        
        # 2. 功能清單
        self.cmd_defs = [
            ("activity", "Activity", "活動匯出", True),
            ("health", "Health", "每日摘要", False),
            ("sleep", "Sleep", "睡眠紀錄", False),
            ("hrv", "HRV", "心率變異", False),
            ("body-battery", "Body Battery", "身體能量", False),
            ("vo2max", "VO2 Max", "最大攝氧", False),
            ("weight", "Weight", "體重紀錄", False),
            ("max-hr", "Max HR", "心率指標", False),
            ("race-event", "Race Event", "賽事清單", False)
        ]
        self.cmd_vars = {name: tk.BooleanVar(value=default) for name, en, cn, default in self.cmd_defs}

        self.setup_ui()
        self.load_env_to_inputs()
        self.log(f"系統啟動。偵錯日誌：{os.path.abspath(DEBUG_LOG_FILE)}")
        self.log(f"日曆元件狀態：{'已啟用 (tkcalendar)' if HAS_CALENDAR else '未啟用 (手動輸入)'}")

    def setup_ui(self):
        style = ttk.Style()
        style.configure("Header.TLabelframe.Label", font=("Microsoft JhengHei", 11, "bold"), foreground="#005A9E")
        
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # 區塊 1: 帳號
        login_lf = ttk.LabelFrame(main_frame, text=" 1. 登入資訊 (Login) ", style="Header.TLabelframe", padding=10)
        login_lf.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(login_lf, text="帳號 (Email):").grid(row=0, column=0, sticky=tk.E, padx=5, pady=5)
        ttk.Entry(login_lf, textvariable=self.username_var, width=50).grid(row=0, column=1, sticky=tk.W, padx=5)
        
        ttk.Label(login_lf, text="密碼 (Password):").grid(row=1, column=0, sticky=tk.E, padx=5, pady=5)
        ttk.Entry(login_lf, textvariable=self.password_var, show="*", width=50).grid(row=1, column=1, sticky=tk.W, padx=5)

        # 區塊 2: 功能 (中英)
        cmd_lf = ttk.LabelFrame(main_frame, text=" 2. 下載內容 (Commands) ", style="Header.TLabelframe", padding=10)
        cmd_lf.pack(fill=tk.X, pady=10)
        
        for i, (name, en, cn, _) in enumerate(self.cmd_defs):
            ttk.Checkbutton(cmd_lf, text=f"{en} ({cn})", variable=self.cmd_vars[name]).grid(row=i//3, column=i%3, sticky=tk.W, padx=20, pady=8)

        # 區塊 3: 設定
        opt_frame = ttk.Frame(main_frame)
        opt_frame.pack(fill=tk.X, pady=10)

        # 3. 日期範圍
        date_lf = ttk.LabelFrame(opt_frame, text=" 3. 日期範圍 (Date) ", style="Header.TLabelframe", padding=10)
        date_lf.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
        
        if HAS_CALENDAR:
            ttk.Label(date_lf, text="開始:").grid(row=0, column=0, padx=5, pady=5)
            DateEntry(date_lf, textvariable=self.start_date_var, date_pattern='y-mm-dd', width=12).grid(row=0, column=1, padx=5)
            ttk.Label(date_lf, text="結束:").grid(row=1, column=0, padx=5, pady=5)
            DateEntry(date_lf, textvariable=self.end_date_var, date_pattern='y-mm-dd', width=12).grid(row=1, column=1, padx=5)
        else:
            ttk.Label(date_lf, text="開始日期:").grid(row=0, column=0, padx=5, pady=5)
            ttk.Entry(date_lf, textvariable=self.start_date_var, width=15).grid(row=0, column=1, padx=5)
            ttk.Label(date_lf, text="結束日期:").grid(row=1, column=0, padx=5, pady=5)
            ttk.Entry(date_lf, textvariable=self.end_date_var, width=15).grid(row=1, column=1, padx=5)

        # 4. 路徑
        path_lf = ttk.LabelFrame(opt_frame, text=" 4. 下載路徑 (Path) ", style="Header.TLabelframe", padding=10)
        path_lf.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        ttk.Entry(path_lf, textvariable=self.download_path_var, width=35).pack(pady=5, fill=tk.X)
        ttk.Button(path_lf, text="瀏覽 (Browse...)", command=self.browse_folder).pack(pady=2)

        # 5. 按鈕區 (下載/取消)
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill=tk.X, pady=15)
        
        self.btn_run = tk.Button(
            btn_frame, text=" 🚀 下載 (Download) ", command=self.start_task,
            bg="#28a745", fg="white", font=("Microsoft JhengHei", 10, "bold"),
            width=20, height=1, relief=tk.RAISED
        )
        self.btn_run.pack(side=tk.LEFT, padx=(150, 10))

        self.btn_cancel = tk.Button(
            btn_frame, text=" 🛑 取消 (Cancel) ", command=self.stop_task,
            bg="#dc3545", fg="white", font=("Microsoft JhengHei", 10, "bold"),
            width=20, height=1, relief=tk.RAISED, state=tk.DISABLED
        )
        self.btn_cancel.pack(side=tk.LEFT)

        # 6. 執行日誌 (20行)
        log_lf = ttk.LabelFrame(main_frame, text=" 6. 執行日誌 (Logs) ", style="Header.TLabelframe", padding=5)
        log_lf.pack(fill=tk.BOTH, expand=True, pady=(0, 5))
        
        self.log_txt = tk.Text(
            log_lf, height=20, bg="#121212", fg="#00FF00", 
            font=("Consolas", 10), wrap=tk.WORD
        )
        self.log_txt.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        sb = ttk.Scrollbar(log_lf, command=self.log_txt.yview)
        sb.pack(side=tk.RIGHT, fill=tk.Y)
        self.log_txt.config(yscrollcommand=sb.set)

    def load_env_to_inputs(self):
        if os.path.exists(".env"):
            try:
                with open(".env", "r", encoding="utf-8") as f:
                    content = f.read()
                    u = re.search(r"GARMIN_USERNAME=(.+)", content)
                    p = re.search(r"GARMIN_PASSWORD=(.+)", content)
                    if u: self.username_var.set(u.group(1).strip().strip("'").strip('"'))
                    if p: self.password_var.set(p.group(1).strip().strip("'").strip('"'))
                self.log("系統：已從 .env 自動載入預設帳號密碼。")
            except Exception as e:
                logging.error(f"載入 .env 失敗: {e}")

    def browse_folder(self):
        d = filedialog.askdirectory()
        if d: self.download_path_var.set(d)

    def log(self, msg):
        t = datetime.now().strftime("%H:%M:%S")
        formatted = f"[{t}] {msg}"
        logging.info(msg)
        self.root.after(0, self._log_ui, formatted)

    def _log_ui(self, formatted):
        self.log_txt.config(state=tk.NORMAL)
        self.log_txt.insert(tk.END, formatted + "\n")
        self.log_txt.see(tk.END)
        self.log_txt.config(state=tk.DISABLED)
        self.root.update_idletasks()

    def start_task(self):
        if not self.username_var.get() or not self.password_var.get():
            messagebox.showwarning("提示", "請輸入帳號與密碼")
            return
        self.is_running = True
        self.btn_run.config(state=tk.DISABLED, bg="#6c757d")
        self.btn_cancel.config(state=tk.NORMAL)
        threading.Thread(target=self.execute_worker, daemon=True).start()

    def stop_task(self):
        if self.is_running:
            self.is_running = False
            self.log("🛑 正在終止任務...")
            if self.current_process:
                self.current_process.terminate()

    def execute_worker(self):
        user, pw = self.username_var.get(), self.password_var.get()
        sd, ed = self.start_date_var.get(), self.end_date_var.get()
        path = self.download_path_var.get()
        
        try:
            with open(".env", "w", encoding="utf-8") as f:
                f.write(f"GARMIN_USERNAME={user}\nGARMIN_PASSWORD={pw}\n")
        except: pass

        selected = [k for k, v in self.cmd_vars.items() if v.get()]
        if not selected:
            self.log("❌ 警告：未選取下載項目")
            self.root.after(0, self.reset_ui)
            return

        os.makedirs(path, exist_ok=True)
        self.log(f"--- 啟動批次任務 (共 {len(selected)} 項) ---")
        
        for cmd in selected:
            if not self.is_running: break
            self.log(f"🚀 處理中: {cmd}")
            
            cli_cmd = [sys.executable, "garmin_tools.py", "--username", user, "--password", pw]
            
            # 健康數據子命令映射
            health_sub_map = {
                "health": "summary",
                "sleep": "sleep",
                "hrv": "hrv",
                "body-battery": "body-battery",
                "vo2max": "vo2max",
                "weight": "weight",
                "max-hr": "max-hr"
            }
            
            if cmd in health_sub_map:
                sub = health_sub_map[cmd]
                cli_cmd.extend(["health", sub, "--start_date", sd, "--end_date", ed, "--summary"])
                if sub == "hrv":
                    cli_cmd.append("--detailed")
                cli_cmd.extend(["--output", os.path.join(path, f"{sub}_{sd}_{ed}.json")])
            elif cmd == "activity":
                cli_cmd.extend(["activity", "--start_date", sd, "--end_date", ed, "--directory", path, "--count", "all", "-ot"])
            elif cmd == "race-event":
                cli_cmd.extend(["race-event", "--start_date", sd, "--end_date", ed, "--summary"])
                cli_cmd.extend(["--output", os.path.join(path, f"{cmd}_{sd}_{ed}.json")])

            try:
                self.current_process = subprocess.Popen(cli_cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding="utf-8", errors="replace")
                for line in self.current_process.stdout:
                    msg = line.strip()
                    if msg:
                        msg = re.sub(r'\x1b\[[0-9;]*m', '', msg)
                        self.log(f"  > {msg}")
                self.current_process.wait()
                if self.current_process.returncode == 0: self.log(f"✅ {cmd} 下載成功")
                else: self.log(f"❌ {cmd} 失敗 (Code: {self.current_process.returncode})")
            except Exception as e:
                self.log(f"💥 發生錯誤: {e}")

        self.log("🏁 任務已結束")
        self.root.after(0, self.reset_ui)
        if self.is_running: messagebox.showinfo("完成", "批次下載任務已結束！\n詳情請見 garmin_gui_debug.log")

    def reset_ui(self):
        self.is_running = False
        self.current_process = None
        self.btn_run.config(state=tk.NORMAL, bg="#28a745")
        self.btn_cancel.config(state=tk.DISABLED)

def main():
    if platform.system() == "Windows":
        try:
            from ctypes import windll
            windll.shcore.SetProcessDpiAwareness(1)
        except: pass
    root = tk.Tk()
    app = GarminGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()
