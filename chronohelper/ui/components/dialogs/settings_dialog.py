# -*- coding: utf-8 -*-
"""
設定對話框UI元件
"""

import tkinter as tk
from tkinter import ttk, messagebox
from chronohelper.config.colors import COLORS
from chronohelper.ui.base import ModernButton
from chronohelper.ui.components.dialogs.settings import (
    GeneralTab, APITab, NetworkTab, UserTab, TimeTab, VPNTab
)

class SettingsDialog:
    """設定對話框"""
    def __init__(self, parent, settings):
        self.result = None
        self.settings = settings.copy()
        
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("ChronoHelper - 設定")
        self.dialog.geometry("500x580") 
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
        
        tk.Label(header, text="應用程式設定", font=("Arial", 14, "bold"), 
                 bg=COLORS["primary"], fg="white").pack(anchor=tk.W)
        
        # 底部按鈕 - 使用獨立框架並固定在底部
        button_frame = tk.Frame(self.dialog, bg=COLORS["card"], padx=15, pady=15)
        button_frame.pack(side=tk.BOTTOM, fill=tk.X)  # 固定在底部
        
        cancel_btn = tk.Button(button_frame, text="取消", bg="#f1f2f6", fg=COLORS["text"],
                             relief=tk.FLAT, padx=15, pady=8, bd=0,
                             command=self.on_cancel)
        cancel_btn.pack(side=tk.RIGHT, padx=5)
        
        save_btn = ModernButton(button_frame, text="儲存設定", 
                              command=self.on_save)
        save_btn.pack(side=tk.RIGHT)
        
        # 設定內容（使用Notebook選項卡）
        notebook_frame = tk.Frame(main_frame, bg=COLORS["card"], padx=15, pady=15)
        notebook_frame.pack(fill=tk.BOTH, expand=True)
        
        self.notebook = ttk.Notebook(notebook_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        
        # 創建並添加所有選項卡
        self.general_tab = GeneralTab(self.notebook, self.settings)
        self.notebook.add(self.general_tab, text="基本設定")
        
        self.api_tab = APITab(self.notebook, self.settings)
        self.notebook.add(self.api_tab, text="API設定")
        
        self.network_tab = NetworkTab(self.notebook, self.settings)
        self.notebook.add(self.network_tab, text="網絡設定")
        
        self.user_tab = UserTab(self.notebook, self.settings)
        self.notebook.add(self.user_tab, text="用戶資訊")
        
        self.time_tab = TimeTab(self.notebook, self.settings)
        self.notebook.add(self.time_tab, text="預設時間")
        
        self.vpn_tab = VPNTab(self.notebook, self.settings)
        self.notebook.add(self.vpn_tab, text="VPN")
        
        # 設置最小窗口大小，確保按鈕始終可見
        self.dialog.update_idletasks()
        self.dialog.minsize(500, 450)  # 增加最小高度
        
        # 設置窗口協議處理
        self.dialog.protocol("WM_DELETE_WINDOW", self.on_cancel)
        self.dialog.wait_visibility()
        self.dialog.focus_set()
    
    def on_cancel(self):
        """取消設定"""
        self.dialog.destroy()
    
    def on_save(self):
        """儲存設定"""
        # 驗證所有選項卡的設定
        if not self._validate_all_tabs():
            return
        
        # 獲取所有選項卡的設定
        self.result = {}
        
        # 合併所有選項卡的設定
        self.result.update(self.general_tab.get_settings())
        self.result.update(self.api_tab.get_settings())
        self.result.update(self.network_tab.get_settings())
        self.result.update(self.user_tab.get_settings())
        self.result.update(self.time_tab.get_settings())
        self.result.update(self.vpn_tab.get_settings())
        
        # 關閉對話框
        self.dialog.destroy()
    
    def _validate_all_tabs(self):
        """驗證所有選項卡的設定
        
        Returns:
            bool: 所有選項卡的設定是否有效
        """
        # 驗證所有選項卡
        if not self.general_tab.validate():
            self.notebook.select(0)  # 切換到基本設定選項卡
            return False
        
        if not self.api_tab.validate():
            self.notebook.select(1)  # 切換到API設定選項卡
            return False
        
        if not self.network_tab.validate():
            self.notebook.select(2)  # 切換到網絡設定選項卡
            return False
        
        if not self.user_tab.validate():
            self.notebook.select(3)  # 切換到用戶資訊選項卡
            return False
        
        if not self.time_tab.validate():
            self.notebook.select(4)  # 切換到預設時間選項卡
            return False
        
        if not self.vpn_tab.validate():
            self.notebook.select(5)  # 切換到VPN選項卡
            return False
        
        return True
    
    def show(self):
        """顯示設定對話框並等待結果
        
        Returns:
            dict: 更新後的設定，如果用戶取消則返回None
        """
        # 等待對話框關閉
        self.dialog.wait_window()
        return self.result 