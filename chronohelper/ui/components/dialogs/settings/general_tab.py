 # -*- coding: utf-8 -*-
"""
基本設定選項卡
"""

import tkinter as tk
from tkinter import ttk
from chronohelper.config.colors import COLORS
from chronohelper.ui.helpers import add_tooltip
from chronohelper.ui.components.dialogs.settings.base_settings_tab import BaseSettingsTab

class GeneralTab(BaseSettingsTab):
    """基本設定選項卡"""
    def create_widgets(self):
        """創建UI元素"""
        # 通知設定
        self.notify_var = tk.BooleanVar(value=self.settings.get("global_notify", True))
        tk.Label(self, text="通知設定", font=("Arial", 11, "bold"), 
                 bg=COLORS["card"], fg=COLORS["text"]).grid(row=0, column=0, sticky=tk.W, pady=(0,10))
        ttk.Checkbutton(self, text="啟用全局通知（影響所有任務）", 
                       variable=self.notify_var).grid(row=1, column=0, sticky=tk.W, padx=15)
        
        self.autostart_var = tk.BooleanVar(value=self.settings.get("auto_start", True))
        ttk.Checkbutton(self, text="啟動程式時自動開始檢查任務", 
                       variable=self.autostart_var).grid(row=2, column=0, sticky=tk.W, padx=15, pady=10)
        
        tk.Label(self, text="任務檢查間隔", font=("Arial", 11, "bold"), 
                 bg=COLORS["card"], fg=COLORS["text"]).grid(row=3, column=0, sticky=tk.W, pady=(10,5))
        
        interval_frame = tk.Frame(self, bg=COLORS["card"])
        interval_frame.grid(row=4, column=0, sticky=tk.W, padx=15)
        
        self.interval_var = tk.IntVar(value=self.settings.get("check_interval", 30))
        ttk.Spinbox(interval_frame, from_=10, to=300, increment=10, 
                   textvariable=self.interval_var, width=5).pack(side=tk.LEFT)
        tk.Label(interval_frame, text="秒", bg=COLORS["card"]).pack(side=tk.LEFT, padx=5)
        
        # 會話維持設定
        tk.Label(self, text="會話維持設定", font=("Arial", 11, "bold"), 
                 bg=COLORS["card"], fg=COLORS["text"]).grid(row=5, column=0, sticky=tk.W, pady=(20,5))
        # 會話刷新間隔
        session_frame = tk.Frame(self, bg=COLORS["card"])
        session_frame.grid(row=6, column=0, sticky=tk.W, padx=15)
        tk.Label(session_frame, text="會話刷新間隔:", bg=COLORS["card"]).pack(side=tk.LEFT, padx=(0,5))
        self.session_refresh_var = tk.IntVar(value=self.settings.get("session_refresh_interval", 240))
        ttk.Spinbox(session_frame, from_=60, to=600, increment=30, 
                   textvariable=self.session_refresh_var, width=5).pack(side=tk.LEFT)
        tk.Label(session_frame, text="秒 (建議240秒)", bg=COLORS["card"], fg=COLORS["light_text"]).pack(side=tk.LEFT, padx=5)
        # 會話有效時間
        valid_frame = tk.Frame(self, bg=COLORS["card"])
        valid_frame.grid(row=7, column=0, sticky=tk.W, padx=15, pady=(5,0))
        tk.Label(valid_frame, text="會話有效時間:", bg=COLORS["card"]).pack(side=tk.LEFT, padx=(0,5))
        self.session_valid_var = tk.IntVar(value=self.settings.get("session_valid_time", 270))
        ttk.Spinbox(valid_frame, from_=120, to=600, increment=30, 
                   textvariable=self.session_valid_var, width=5).pack(side=tk.LEFT)
        tk.Label(valid_frame, text="秒 (建議270秒)", bg=COLORS["card"], fg=COLORS["light_text"]).pack(side=tk.LEFT, padx=5)
        # 會話設定說明
        session_info = tk.Label(self, 
            text="注意: 會話刷新間隔應小於會話有效時間，建議差值約30秒",
            bg=COLORS["card"], fg=COLORS["light_text"], wraplength=350, justify=tk.LEFT)
        session_info.grid(row=8, column=0, sticky=tk.W, padx=15, pady=(5, 0))
        
        # 為會話設定添加詳細工具提示
        session_tooltip_text = (
            "會話維持設定說明：\n\n"
            "會話刷新間隔：系統會每隔此設定的時間自動訪問一次系統以保持會話活躍。\n"
            "會話有效時間：系統假設會話在此時間內有效，超過此時間將重新登入。\n\n"
            "建議設定：\n"
            "- 會話刷新間隔：240秒（4分鐘）\n"
            "- 會話有效時間：270秒（4.5分鐘）\n\n"
            "這樣可以確保系統在會話過期前進行刷新，避免需要重新登入。"
        )
        add_tooltip(session_info, session_tooltip_text)
        
        # 通知設定
        notification_frame = tk.Frame(self, bg=COLORS["card"])
        notification_frame.grid(row=9, column=0, sticky=tk.W, padx=15, pady=(20,5))
        
        tk.Label(notification_frame, text="通知顯示時間:", bg=COLORS["card"]).pack(side=tk.LEFT)
        
        self.notification_duration_var = tk.IntVar(value=self.settings.get("notification_duration", 5))
        duration_spinbox = ttk.Spinbox(notification_frame, from_=1, to=10, increment=1, 
                   textvariable=self.notification_duration_var, width=3)
        duration_spinbox.pack(side=tk.LEFT, padx=5)
        
        tk.Label(notification_frame, text="秒", bg=COLORS["card"]).pack(side=tk.LEFT)
        
        # 為通知設定添加工具提示
        notify_tooltip_text = (
            "通知設定說明：\n\n"
            "通知顯示時間：控制桌面通知在螢幕上顯示的時間長度。\n"
            "較長的顯示時間使您有更多時間閱讀通知內容，\n"
            "但可能會占用螢幕空間更久。\n\n"
            "建議時間：3-5秒"
        )
        add_tooltip(duration_spinbox, notify_tooltip_text)
    
    def validate(self):
        """驗證輸入
        
        Returns:
            bool: 輸入是否有效
        """
        try:
            check_interval = int(self.interval_var.get())
            session_refresh = int(self.session_refresh_var.get())
            session_valid = int(self.session_valid_var.get())
            notification_duration = int(self.notification_duration_var.get())
            
            # 驗證會話維持時間邏輯
            if session_refresh >= session_valid:
                # 自動調整，刷新間隔設為有效時間的90%
                session_refresh = int(session_valid * 0.9)
                self.session_refresh_var.set(session_refresh)
            
            return True
        except ValueError:
            return False
    
    def get_settings(self):
        """獲取設定
        
        Returns:
            dict: 選項卡的設定
        """
        return {
            "global_notify": self.notify_var.get(),
            "auto_start": self.autostart_var.get(),
            "check_interval": int(self.interval_var.get()),
            "session_refresh_interval": int(self.session_refresh_var.get()),
            "session_valid_time": int(self.session_valid_var.get()),
            "notification_duration": int(self.notification_duration_var.get())
        }