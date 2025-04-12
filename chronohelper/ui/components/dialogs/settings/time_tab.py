# -*- coding: utf-8 -*-
"""
預設時間選項卡
"""

import tkinter as tk
from tkinter import ttk, messagebox
from chronohelper.config.colors import COLORS
from chronohelper.ui.components.dialogs.settings.base_settings_tab import BaseSettingsTab

class TimeTab(BaseSettingsTab):
    """預設時間選項卡"""
    def create_widgets(self):
        """創建UI元素"""
        tk.Label(self, text="預設簽到簽退時間", font=("Arial", 11, "bold"), 
                 bg=COLORS["card"], fg=COLORS["text"]).grid(row=0, column=0, columnspan=2, sticky=tk.W, pady=(0,15))
        
        tk.Label(self, text="預設簽到時間:", bg=COLORS["card"]).grid(row=1, column=0, sticky=tk.W, padx=(15,5), pady=5)
        
        # 簽到時間選擇器
        sign_in_frame = tk.Frame(self, bg=COLORS["card"])
        sign_in_frame.grid(row=1, column=1, sticky=tk.W, pady=5)
        
        self.default_sign_in_hour = tk.StringVar(value=self.settings.get("default_sign_in", "09:00").split(":")[0])
        self.default_sign_in_minute = tk.StringVar(value=self.settings.get("default_sign_in", "09:00").split(":")[1])
        
        hours = [f"{h:02d}" for h in range(24)]
        minutes = [f"{m:02d}" for m in range(60)]
        
        ttk.Combobox(sign_in_frame, textvariable=self.default_sign_in_hour, 
                    values=hours, width=3).pack(side=tk.LEFT)
        tk.Label(sign_in_frame, text=":", bg=COLORS["card"]).pack(side=tk.LEFT)
        ttk.Combobox(sign_in_frame, textvariable=self.default_sign_in_minute, 
                    values=minutes, width=3).pack(side=tk.LEFT)
        
        # 簽退時間選擇器
        tk.Label(self, text="預設簽退時間:", bg=COLORS["card"]).grid(row=2, column=0, sticky=tk.W, padx=(15,5), pady=5)
        
        sign_out_frame = tk.Frame(self, bg=COLORS["card"])
        sign_out_frame.grid(row=2, column=1, sticky=tk.W, pady=5)
        
        self.default_sign_out_hour = tk.StringVar(value=self.settings.get("default_sign_out", "18:00").split(":")[0])
        self.default_sign_out_minute = tk.StringVar(value=self.settings.get("default_sign_out", "18:00").split(":")[1])
        
        ttk.Combobox(sign_out_frame, textvariable=self.default_sign_out_hour, 
                    values=hours, width=3).pack(side=tk.LEFT)
        tk.Label(sign_out_frame, text=":", bg=COLORS["card"]).pack(side=tk.LEFT)
        ttk.Combobox(sign_out_frame, textvariable=self.default_sign_out_minute, 
                    values=minutes, width=3).pack(side=tk.LEFT)
    
    def validate(self):
        """驗證輸入
        
        Returns:
            bool: 輸入是否有效
        """
        try:
            # 格式化為HH:MM格式
            sign_in_hour = int(self.default_sign_in_hour.get())
            sign_in_minute = int(self.default_sign_in_minute.get())
            sign_out_hour = int(self.default_sign_out_hour.get())
            sign_out_minute = int(self.default_sign_out_minute.get())
            
            # 驗證時間格式
            if not (0 <= sign_in_hour <= 23 and 0 <= sign_in_minute <= 59 and
                    0 <= sign_out_hour <= 23 and 0 <= sign_out_minute <= 59):
                messagebox.showerror("時間格式錯誤", "請確保時間格式為有效的小時(0-23)和分鐘(0-59)", parent=self.winfo_toplevel())
                return False
            
            # 驗證簽到時間小於簽退時間
            sign_in_time = f"{sign_in_hour:02d}:{sign_in_minute:02d}"
            sign_out_time = f"{sign_out_hour:02d}:{sign_out_minute:02d}"
            
            if sign_in_time >= sign_out_time:
                messagebox.showwarning("時間設定警告", "簽到時間應早於簽退時間", parent=self.winfo_toplevel())
                return False
            
            return True
        except ValueError:
            messagebox.showerror("時間格式錯誤", "請確保時間格式為有效的小時和分鐘", parent=self.winfo_toplevel())
            return False
    
    def get_settings(self):
        """獲取設定
        
        Returns:
            dict: 選項卡的設定
        """
        sign_in_hour = int(self.default_sign_in_hour.get())
        sign_in_minute = int(self.default_sign_in_minute.get())
        sign_out_hour = int(self.default_sign_out_hour.get())
        sign_out_minute = int(self.default_sign_out_minute.get())
        
        return {
            "default_sign_in": f"{sign_in_hour:02d}:{sign_in_minute:02d}",
            "default_sign_out": f"{sign_out_hour:02d}:{sign_out_minute:02d}"
        } 