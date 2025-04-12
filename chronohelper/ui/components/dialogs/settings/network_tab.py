# -*- coding: utf-8 -*-
"""
網絡設定選項卡
"""

import tkinter as tk
from tkinter import ttk
from chronohelper.config.colors import COLORS
from chronohelper.ui.components.dialogs.settings.base_settings_tab import BaseSettingsTab

class NetworkTab(BaseSettingsTab):
    """網絡設定選項卡"""
    def create_widgets(self):
        """創建UI元素"""
        # 第二躍點檢測設定
        tk.Label(self, text="校內網絡檢測設定", font=("Arial", 11, "bold"), 
                 bg=COLORS["card"], fg=COLORS["text"]).grid(row=0, column=0, columnspan=3, sticky=tk.W, pady=(0,15))
        
        # 啟用第二躍點檢測
        self.enable_second_hop_var = tk.BooleanVar(value=self.settings.get("enable_second_hop", False))
        ttk.Checkbutton(self, text="啟用第二躍點檢測", 
                      variable=self.enable_second_hop_var).grid(row=1, column=0, sticky=tk.W, padx=15)
        
        tk.Label(self, text="當本機IP非163.23開頭時，檢測路由第二躍點是否為校內網絡", 
                 bg=COLORS["card"], fg=COLORS["light_text"], wraplength=350, justify=tk.LEFT).grid(
                 row=2, column=0, columnspan=3, sticky=tk.W, padx=25, pady=(0, 10))
        
        # 第二躍點檢測超時設定
        timeout_frame = tk.Frame(self, bg=COLORS["card"])
        timeout_frame.grid(row=3, column=0, sticky=tk.W, padx=15, pady=5)
        
        tk.Label(timeout_frame, text="第二躍點檢測超時時間:", bg=COLORS["card"]).pack(side=tk.LEFT, padx=(0,5))
        self.hop_timeout_var = tk.IntVar(value=self.settings.get("hop_check_timeout", 10))
        ttk.Spinbox(timeout_frame, from_=1, to=10, increment=1, 
                   textvariable=self.hop_timeout_var, width=3).pack(side=tk.LEFT)
        tk.Label(timeout_frame, text="秒", bg=COLORS["card"]).pack(side=tk.LEFT, padx=5)
        
        # 檢測說明
        tk.Label(self, text="檢測方式說明:", font=("Arial", 10, "bold"), 
                 bg=COLORS["card"], fg=COLORS["text"]).grid(row=4, column=0, sticky=tk.W, padx=15, pady=(20, 5))
        
        detection_info = (
            "1. 首先檢查本機IP是否為163.23開頭\n"
            "2. 如果不是，檢查默認閘道器IP（快速檢測）\n"
            "3. 如果閘道器IP也不是校內網絡，使用tracert命令檢測第二躍點\n"
            "4. 如果檢測超時，將使用緩存的上次結果"
        )
        
        tk.Label(self, text=detection_info, 
                 bg=COLORS["card"], fg=COLORS["light_text"], wraplength=350, justify=tk.LEFT).grid(
                 row=5, column=0, columnspan=3, sticky=tk.W, padx=25, pady=(0, 10))
        
        # 超時機制說明
        tk.Label(self, text="超時與性能說明:", font=("Arial", 10, "bold"), 
                 bg=COLORS["card"], fg=COLORS["text"]).grid(row=6, column=0, sticky=tk.W, padx=15, pady=(10, 5))
        
        timeout_info = (
            "• 設定較短的超時時間可減少應用程式卡頓，但可能降低檢測準確性\n"
            "• 檢測會在背景線程中執行，不會阻塞主界面\n"
            "• 檢測結果會自動緩存60秒，以減少系統資源使用\n"
            "• 如果檢測中斷或超時，將使用前次有效結果"
        )
        
        tk.Label(self, text=timeout_info, 
                 bg=COLORS["card"], fg=COLORS["light_text"], wraplength=350, justify=tk.LEFT).grid(
                 row=7, column=0, columnspan=3, sticky=tk.W, padx=25, pady=(0, 10))
    
    def validate(self):
        """驗證輸入
        
        Returns:
            bool: 輸入是否有效
        """
        try:
            hop_timeout = int(self.hop_timeout_var.get())
            if not 1 <= hop_timeout <= 10:
                self.hop_timeout_var.set(10)  # 重置為默認值
            return True
        except ValueError:
            return False
    
    def get_settings(self):
        """獲取設定
        
        Returns:
            dict: 選項卡的設定
        """
        return {
            "enable_second_hop": self.enable_second_hop_var.get(),
            "hop_check_timeout": int(self.hop_timeout_var.get())
        } 