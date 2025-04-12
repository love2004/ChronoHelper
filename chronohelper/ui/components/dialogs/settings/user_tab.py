# -*- coding: utf-8 -*-
"""
用戶資訊選項卡
"""

import tkinter as tk
from tkinter import ttk
from chronohelper.config.colors import COLORS
from chronohelper.ui.components.dialogs.settings.base_settings_tab import BaseSettingsTab

class UserTab(BaseSettingsTab):
    """用戶資訊選項卡"""
    def create_widgets(self):
        """創建UI元素"""
        tk.Label(self, text="個人資料", font=("Arial", 11, "bold"), 
                 bg=COLORS["card"], fg=COLORS["text"]).grid(row=0, column=0, columnspan=3, sticky=tk.W, pady=(0,15))
        
        tk.Label(self, text="姓名:", bg=COLORS["card"]).grid(row=1, column=0, sticky=tk.W, padx=(15,5), pady=5)
        self.name_var = tk.StringVar(value=self.settings.get("name", ""))
        ttk.Entry(self, textvariable=self.name_var, width=15).grid(row=1, column=1, sticky=tk.W, pady=5)
        
        tk.Label(self, text="(用於確認登入狀態)", bg=COLORS["card"], fg=COLORS["light_text"]).grid(
            row=1, column=2, sticky=tk.W, padx=5, pady=5)
    
    def validate(self):
        """驗證輸入
        
        Returns:
            bool: 輸入是否有效
        """
        return True
    
    def get_settings(self):
        """獲取設定
        
        Returns:
            dict: 選項卡的設定
        """
        return {
            "name": self.name_var.get().strip()
        } 