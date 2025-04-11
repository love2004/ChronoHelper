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
    def __init__(self, widget, text, delay=500, button_safe=True):
        """
        初始化工具提示
        
        Args:
            widget: 要添加提示的tkinter部件
            text: 提示文本內容
            delay: 顯示提示前的延遲（毫秒）
            button_safe: 是否針對按鈕進行特殊處理，避免干擾按鈕點擊
        """
        self.widget = widget
        self.text = text
        self.delay = delay
        self.tip_window = None
        self.tip_timer = None
        
        # 確保不干擾按鈕的點擊事件
        self.button_safe = button_safe
        
        # 適配不同類型的部件
        if isinstance(widget, tk.Button) or "Button" in widget.__class__.__name__:
            # 按鈕需要特殊處理，避免干擾點擊
            self.button_safe = True
        
        # 使用add="+"參數添加事件而不是替換
        self.widget.bind("<Enter>", self._schedule_show, add="+")
        self.widget.bind("<Leave>", self._on_leave, add="+")
        self.widget.bind("<ButtonPress>", self._on_button_press, add="+")  # 任何滑鼠按下都隱藏提示
        
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
            self.hint_label.bind("<Enter>", self._schedule_show, add="+")  # 使用add="+"參數
            self.hint_label.bind("<Leave>", self._on_leave, add="+")
        
        self.hint_label.grid(row=row, column=column, padx=(2, 0))
    
    def _schedule_show(self, event=None):
        """安排延遲顯示提示窗口
        
        Args:
            event: 觸發事件對象
        """
        # 取消任何現有的定時器
        if self.tip_timer:
            self.widget.after_cancel(self.tip_timer)
            self.tip_timer = None
            
        # 如果是右鍵事件，不顯示提示
        if event and hasattr(event, 'num') and event.num == 3:
            return None
            
        # 安排延遲顯示
        self.tip_timer = self.widget.after(self.delay, lambda: self.show_tip(event))
        return None
    
    def _on_leave(self, event=None):
        """處理鼠標離開事件
        
        Args:
            event: 觸發事件對象
        """
        # 取消定時器
        if self.tip_timer:
            self.widget.after_cancel(self.tip_timer)
            self.tip_timer = None
        
        # 隱藏提示
        self.hide_tip(event)
        return None
    
    def _on_button_press(self, event=None):
        """處理按鈕按下事件
        
        Args:
            event: 觸發事件對象
        """
        # 取消定時器並隱藏提示
        if self.tip_timer:
            self.widget.after_cancel(self.tip_timer)
            self.tip_timer = None
        
        # 隱藏提示
        self.hide_tip(event)
        
        # 不干擾原始事件
        return None
    
    def show_tip(self, event=None):
        """
        顯示提示窗口
        
        Args:
            event: 觸發事件對象
        
        Returns:
            None: 不阻止事件繼續傳播
        """
        # 如果是右鍵事件，不顯示提示
        if event and hasattr(event, 'num') and event.num == 3:  # 3 表示右鍵
            return None
            
        # 如果提示已經顯示或沒有文本，則退出
        if self.tip_window or not self.text:
            return None
        
        # 對於按鈕，避免在點擊時顯示提示
        if self.button_safe and event and hasattr(event, 'type') and event.type.startswith('Button'):
            return None
            
        # 計算提示窗口顯示位置
        x = y = 0
        if event and hasattr(event, 'widget'):
            # 根據事件的小部件獲取位置
            try:
                event_widget = event.widget
                # 嘗試獲取精確位置
                if hasattr(event_widget, "bbox") and hasattr(event_widget, "index"):
                    try:
                        x, y, _, _ = event_widget.bbox("insert")
                        x += event_widget.winfo_rootx() + 25
                        y += event_widget.winfo_rooty() + 25
                    except:
                        # 如果無法獲取插入點，使用小部件位置
                        x = event_widget.winfo_rootx() + event_widget.winfo_width() + 5
                        y = event_widget.winfo_rooty() + 5
                else:
                    # 對於無法獲取精確位置的元件，使用簡單定位
                    x = event_widget.winfo_rootx() + 20
                    y = event_widget.winfo_rooty() + 20
            except Exception:
                # 故障安全模式：使用小部件的左上角
                try:
                    x = event.widget.winfo_rootx() + 15
                    y = event.widget.winfo_rooty() + 10
                except:
                    # 如果所有方法都失敗，使用默認位置
                    x = 100
                    y = 100
        else:
            # 如果沒有事件，使用小部件的位置
            try:
                x = self.widget.winfo_rootx() + self.widget.winfo_width()
                y = self.widget.winfo_rooty() + 10
            except:
                # 如果獲取位置失敗，使用默認位置
                x = 100
                y = 100
        
        # 創建工具提示窗口
        try:
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
            
            # 增加關閉提示的事件綁定
            tw.bind("<ButtonPress>", lambda e: self.hide_tip())
        except Exception:
            # 如果創建提示窗口失敗，確保不會留下殘留狀態
            self.tip_window = None
        
        # 不阻止事件繼續傳播
        return None
    
    def hide_tip(self, event=None):
        """
        隱藏提示窗口
        
        Args:
            event: 觸發事件對象
            
        Returns:
            None: 不阻止事件繼續傳播
        """
        # 如果是右鍵事件，允許事件繼續傳播
        if event and hasattr(event, 'num') and event.num == 3:  # 3 表示右鍵
            return None
        
        # 取消任何存在的計時器
        if self.tip_timer:
            try:
                self.widget.after_cancel(self.tip_timer)
            except Exception:
                pass  # 忽略可能的錯誤
            self.tip_timer = None
            
        # 銷毀提示窗口
        try:
            tw = self.tip_window
            self.tip_window = None
            if tw and tw.winfo_exists():
                tw.destroy()
        except Exception:
            # 如果銷毀過程中出現錯誤，強制清除引用
            self.tip_window = None
            
        # 不阻止事件繼續傳播
        return None

def add_tooltip(widget, text, row=None, column=None, delay=500, button_safe=True):
    """
    為控件添加工具提示
    
    這是一個便捷函數，用於快速為小部件添加工具提示，
    並可選擇性地添加問號圖標。
    
    Args:
        widget: 要添加提示的tkinter部件
        text: 提示文本內容
        row: 問號圖標的行位置（如果需要顯示）
        column: 問號圖標的列位置（如果需要顯示）
        delay: 顯示提示前的延遲時間（毫秒）
        button_safe: 針對按鈕是否進行特殊處理，避免干擾點擊
        
    Returns:
        SettingTooltip: 創建的工具提示實例
    
    Examples:
        # 僅添加懸停提示
        add_tooltip(my_button, "點擊提交表單")
        
        # 添加懸停提示和問號圖標
        add_tooltip(my_label, "這是一個重要設定", row=1, column=2)
        
        # 自定義延遲時間的提示
        add_tooltip(my_entry, "請輸入用戶名", delay=200)
    """
    # 創建並返回工具提示實例，傳遞所有參數
    tooltip = SettingTooltip(widget, text, delay=delay, button_safe=button_safe)
    
    # 如果提供了行和列參數，放置問號圖標
    if row is not None and column is not None:
        tooltip.place_hint(row, column)
        
    return tooltip 