# -*- coding: utf-8 -*-
"""
UI輔助工具類 - 提供通用UI組件和工具函數
"""

import tkinter as tk
from chronohelper.config.colors import COLORS

class SettingTooltip:
    """
    設定項工具提示類 - 為UI元素添加懸停提示
    
    這個類可以為任何 tkinter 小部件添加懸停提示，當鼠標移動到元素上時顯示提示文本。
    可以選擇性地顯示一個問號圖標來指示這個元素有提示信息。
    
    用法:
        # 基本用法 - 僅添加懸停提示
        tooltip = SettingTooltip(mybutton, "這是一個按鈕")
        
        # 高級用法 - 添加問號圖標
        tooltip = SettingTooltip(mylabel, "這是標籤說明")
        tooltip.place_hint(row=1, column=2)  # 在網格布局中添加問號圖標
    """
    def __init__(self, widget, text):
        """
        初始化工具提示
        
        Args:
            widget: 要添加提示的tkinter部件
            text: 提示文本內容
        """
        self.widget = widget
        self.text = text
        self.tip_window = None
        self.widget.bind("<Enter>", self.show_tip)
        self.widget.bind("<Leave>", self.hide_tip)
        
        # 初始化問號圖標，但不立即顯示
        self.hint_label = None
    
    def place_hint(self, row, column):
        """
        放置問號提示圖標（用於網格布局）
        
        Args:
            row: 網格布局中的行
            column: 網格布局中的列
        """
        if not self.hint_label:
            self.hint_label = tk.Label(self.widget.master, text="ⓘ", fg=COLORS["primary"], 
                                     bg=COLORS["card"], cursor="hand2")
            self.hint_label.bind("<Enter>", self.show_tip)
            self.hint_label.bind("<Leave>", self.hide_tip)
        
        self.hint_label.grid(row=row, column=column, padx=(2, 0))
    
    def show_tip(self, event=None):
        """
        顯示提示窗口
        
        Args:
            event: 觸發事件對象
        """
        if self.tip_window or not self.text:
            return
        
        x = y = 0
        if event:
            # 根據事件的小部件獲取位置
            try:
                x, y, _, _ = event.widget.bbox("insert") if hasattr(event.widget, "bbox") else (0, 0, 0, 0)
                x += event.widget.winfo_rootx() + 25
                y += event.widget.winfo_rooty() + 25
            except:
                # 如果無法獲取插入點位置，使用小部件左上角
                x = event.widget.winfo_rootx() + 20
                y = event.widget.winfo_rooty() + 20
        else:
            # 如果沒有事件，使用小部件的位置
            x = self.widget.winfo_rootx() + self.widget.winfo_width()
            y = self.widget.winfo_rooty() + 10
        
        # 創建工具提示窗口
        self.tip_window = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)  # 無邊框窗口
        tw.wm_geometry(f"+{x}+{y}")
        tw.attributes("-topmost", True)  # 確保提示顯示在頂層
        
        # 使用現代化風格
        frame = tk.Frame(tw, bg=COLORS["card"], bd=1, relief=tk.SOLID)
        frame.pack(fill=tk.BOTH, expand=True)
        
        label = tk.Label(frame, text=self.text, justify=tk.LEFT,
                      background=COLORS["card"], fg=COLORS["text"],
                      wraplength=250, padx=10, pady=10,
                      font=("Arial", "9", "normal"))
        label.pack()
    
    def hide_tip(self, event=None):
        """
        隱藏提示窗口
        
        Args:
            event: 觸發事件對象
        """
        tw = self.tip_window
        self.tip_window = None
        if tw:
            tw.destroy()

def add_tooltip(widget, text, row=None, column=None):
    """
    為控件添加工具提示
    
    這是一個便捷函數，用於快速為小部件添加工具提示，
    並可選擇性地添加問號圖標。
    
    Args:
        widget: 要添加提示的tkinter部件
        text: 提示文本內容
        row: 問號圖標的行位置（如果需要顯示）
        column: 問號圖標的列位置（如果需要顯示）
        
    Returns:
        SettingTooltip: 創建的工具提示實例
    
    Examples:
        # 僅添加懸停提示
        add_tooltip(my_button, "點擊提交表單")
        
        # 添加懸停提示和問號圖標
        add_tooltip(my_label, "這是一個重要設定", row=1, column=2)
    """
    tooltip = SettingTooltip(widget, text)
    if row is not None and column is not None:
        tooltip.place_hint(row, column)
    return tooltip 