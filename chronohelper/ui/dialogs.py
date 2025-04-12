# -*- coding: utf-8 -*-
"""
對話框UI元件
"""

import tkinter as tk
import datetime
import re
import requests
import subprocess
import webbrowser
import os

from requests.exceptions import RequestException
from bs4 import BeautifulSoup
from tkinter import ttk, messagebox
from chronohelper.config.colors import COLORS
from chronohelper.ui.base import ModernButton
from chronohelper.ui.helpers import add_tooltip

class ModernTaskDialog:
    """現代風格的任務編輯對話框"""
    def __init__(self, parent, title, name="", date="", sign_in="", sign_out="", notify=True):
        self.result = None
        
        # 如果日期為空，設置為今天
        if not date:
            date = datetime.date.today().strftime("%Y-%m-%d")
        
        self.dialog = tk.Toplevel(parent)
        self.dialog.title(title)
        self.dialog.geometry("450x450")  # 增加初始高度
        self.dialog.configure(bg=COLORS["card"])
        self.dialog.transient(parent)
        self.dialog.grab_set()
        self.dialog.resizable(True, True)  # 確保窗口可調整大小
        
        # 創建主框架以確保正確排列
        main_frame = tk.Frame(self.dialog, bg=COLORS["card"])
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 對話框標題
        header = tk.Frame(main_frame, bg=COLORS["primary"], padx=15, pady=10)
        header.pack(fill=tk.X)
        
        tk.Label(header, text=title, font=("Arial", 14, "bold"), 
                 bg=COLORS["primary"], fg="white").pack(anchor=tk.W)
        
        # 表單內容
        form_frame = tk.Frame(main_frame, bg=COLORS["card"], padx=20, pady=20)
        form_frame.pack(fill=tk.BOTH, expand=True)
        
        # 任務名稱
        tk.Label(form_frame, text="任務名稱:", bg=COLORS["card"], fg=COLORS["text"]).pack(anchor=tk.W, pady=(0, 5))
        self.name_var = tk.StringVar(value=name)
        name_entry = ttk.Entry(form_frame, textvariable=self.name_var, width=30)
        name_entry.pack(fill=tk.X, pady=(0, 15))
        
        # 日期
        tk.Label(form_frame, text="日期:", bg=COLORS["card"], fg=COLORS["text"]).pack(anchor=tk.W, pady=(0, 5))
        
        date_frame = tk.Frame(form_frame, bg=COLORS["card"])
        date_frame.pack(fill=tk.X, pady=(0, 15))
        
        self.year_var = tk.StringVar(value=date.split("-")[0] if date else "")
        self.month_var = tk.StringVar(value=date.split("-")[1] if date else "")
        self.day_var = tk.StringVar(value=date.split("-")[2] if date else "")
        
        years = [str(datetime.date.today().year + i) for i in range(-1, 3)]
        months = [f"{m:02d}" for m in range(1, 13)]
        days = [f"{d:02d}" for d in range(1, 32)]
        
        ttk.Combobox(date_frame, textvariable=self.year_var, values=years, width=5).pack(side=tk.LEFT)
        tk.Label(date_frame, text="-", bg=COLORS["card"]).pack(side=tk.LEFT)
        ttk.Combobox(date_frame, textvariable=self.month_var, values=months, width=3).pack(side=tk.LEFT)
        tk.Label(date_frame, text="-", bg=COLORS["card"]).pack(side=tk.LEFT)
        ttk.Combobox(date_frame, textvariable=self.day_var, values=days, width=3).pack(side=tk.LEFT)
        
        # 簽到時間
        tk.Label(form_frame, text="簽到時間:", bg=COLORS["card"], fg=COLORS["text"]).pack(anchor=tk.W, pady=(0, 5))
        
        sign_in_frame = tk.Frame(form_frame, bg=COLORS["card"])
        sign_in_frame.pack(fill=tk.X, pady=(0, 15))
        
        self.sign_in_hour = tk.StringVar(value=sign_in.split(":")[0] if sign_in else "")
        self.sign_in_minute = tk.StringVar(value=sign_in.split(":")[1] if sign_in else "")
        
        hours = [f"{h:02d}" for h in range(24)]
        minutes = [f"{m:02d}" for m in range(60)]
        
        ttk.Combobox(sign_in_frame, textvariable=self.sign_in_hour, values=hours, width=3).pack(side=tk.LEFT)
        tk.Label(sign_in_frame, text=":", bg=COLORS["card"]).pack(side=tk.LEFT)
        ttk.Combobox(sign_in_frame, textvariable=self.sign_in_minute, values=minutes, width=3).pack(side=tk.LEFT)
        
        # 簽退時間
        tk.Label(form_frame, text="簽退時間:", bg=COLORS["card"], fg=COLORS["text"]).pack(anchor=tk.W, pady=(0, 5))
        
        sign_out_frame = tk.Frame(form_frame, bg=COLORS["card"])
        sign_out_frame.pack(fill=tk.X, pady=(0, 15))
        
        self.sign_out_hour = tk.StringVar(value=sign_out.split(":")[0] if sign_out else "")
        self.sign_out_minute = tk.StringVar(value=sign_out.split(":")[1] if sign_out else "")
        
        ttk.Combobox(sign_out_frame, textvariable=self.sign_out_hour, values=hours, width=3).pack(side=tk.LEFT)
        tk.Label(sign_out_frame, text=":", bg=COLORS["card"]).pack(side=tk.LEFT)
        ttk.Combobox(sign_out_frame, textvariable=self.sign_out_minute, values=minutes, width=3).pack(side=tk.LEFT)
        
        # 通知選項
        self.notify_var = tk.BooleanVar(value=notify)
        ttk.Checkbutton(form_frame, text="啟用通知", variable=self.notify_var).pack(anchor=tk.W, pady=(0, 15))
        
        # 底部按鈕 - 使用獨立框架並固定在底部
        button_frame = tk.Frame(self.dialog, bg=COLORS["card"], padx=20, pady=20)
        button_frame.pack(side=tk.BOTTOM, fill=tk.X)  # 固定在底部
        
        cancel_btn = tk.Button(button_frame, text="取消", bg="#f1f2f6", fg=COLORS["text"],
                             relief=tk.FLAT, padx=15, pady=8, bd=0,
                             command=self.on_cancel)
        cancel_btn.pack(side=tk.RIGHT, padx=5)
        
        save_btn = ModernButton(button_frame, text="儲存", 
                              command=self.on_save)
        save_btn.pack(side=tk.RIGHT)
        
        # 設置最小窗口大小
        self.dialog.update_idletasks()
        self.dialog.minsize(450, 350)
        
        # 設置焦點
        name_entry.focus_set()
        
        self.dialog.protocol("WM_DELETE_WINDOW", self.on_cancel)
        self.dialog.wait_visibility()
        self.dialog.focus_set()
        self.dialog.wait_window()
    
    def on_save(self):
        # 獲取並驗證輸入值
        name = self.name_var.get().strip()
        if not name:
            messagebox.showwarning("輸入錯誤", "請輸入任務名稱", parent=self.dialog)
            return
        
        try:
            # 檢查日期格式
            year = self.year_var.get().strip()
            month = self.month_var.get().strip()
            day = self.day_var.get().strip()
            
            # 確保年月日都有填寫
            if not (year and month and day):
                messagebox.showwarning("輸入錯誤", "請輸入完整日期", parent=self.dialog)
                return
                
            # 驗證日期有效性
            date_str = f"{year}-{month}-{day}"
            datetime.datetime.strptime(date_str, "%Y-%m-%d")
            
            # 檢查時間格式
            sign_in_hour = self.sign_in_hour.get().strip()
            sign_in_minute = self.sign_in_minute.get().strip()
            sign_out_hour = self.sign_out_hour.get().strip()
            sign_out_minute = self.sign_out_minute.get().strip()
            
            # 確保時間都有填寫
            if not (sign_in_hour and sign_in_minute and sign_out_hour and sign_out_minute):
                messagebox.showwarning("輸入錯誤", "請輸入完整的簽到簽退時間", parent=self.dialog)
                return
            
            # 格式化時間
            sign_in_time = f"{sign_in_hour}:{sign_in_minute}"
            sign_out_time = f"{sign_out_hour}:{sign_out_minute}"
            
            # 驗證時間格式
            datetime.datetime.strptime(sign_in_time, "%H:%M")
            datetime.datetime.strptime(sign_out_time, "%H:%M")
            
            # 確保簽退時間晚於簽到時間
            if sign_in_time >= sign_out_time:
                messagebox.showwarning("輸入錯誤", "簽退時間必須晚於簽到時間", parent=self.dialog)
                return
            
            # 所有驗證通過，設置結果
            self.result = (name, date_str, sign_in_time, sign_out_time, self.notify_var.get())
            self.dialog.destroy()
            
        except ValueError as e:
            messagebox.showwarning("輸入錯誤", f"日期或時間格式無效: {str(e)}", parent=self.dialog)
    
    def on_cancel(self):
        self.dialog.destroy()
