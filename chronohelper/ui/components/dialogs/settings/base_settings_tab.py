# -*- coding: utf-8 -*-
"""
設定選項卡基類
"""

import tkinter as tk
from chronohelper.config.colors import COLORS

class BaseSettingsTab(tk.Frame):
    """所有設定選項卡的基類"""
    def __init__(self, notebook, settings):
        """初始化選項卡
        
        Args:
            notebook (ttk.Notebook): 選項卡所屬的Notebook控件
            settings (dict): 應用程式設定
        """
        super().__init__(notebook, bg=COLORS["card"], padx=15, pady=15)
        self.settings = settings
        self.create_widgets()
    
    def create_widgets(self):
        """創建UI元素 - 子類需要覆寫此方法"""
        pass
    
    def validate(self):
        """驗證輸入 - 子類需要覆寫此方法
        
        Returns:
            bool: 輸入是否有效
        """
        return True
    
    def get_settings(self):
        """獲取設定 - 子類需要覆寫此方法
        
        Returns:
            dict: 選項卡的設定
        """
        return {} 