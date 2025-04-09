# -*- coding: utf-8 -*-
"""
任務卡片UI元件
"""

import os
import tkinter as tk
from tkinter import ttk
import datetime

from chronohelper.config.colors import COLORS
from chronohelper.ui.base import ModernButton

class TaskCard(tk.Frame):
    """任務卡片元件，顯示單個任務信息"""
    def __init__(self, master, task, on_edit=None, on_delete=None, on_sign_in=None, on_sign_out=None, on_update_status=None, main_canvas=None):
        super().__init__(master, bg=COLORS["card"], padx=15, pady=15)
        self.task = task
        self.on_edit = on_edit
        self.on_delete = on_delete
        self.on_sign_in = on_sign_in
        self.on_sign_out = on_sign_out
        self.on_update_status = on_update_status
        self.main_canvas = main_canvas  # 保存主Canvas的引用，用於滾動
        
        self.config(highlightbackground=COLORS["border"], highlightthickness=1)
        
        self.create_widgets()
        
        # 只綁定右鍵事件，其他事件不阻斷
        self.bind("<Button-3>", self.show_context_menu)
        
        # 綁定滾輪事件
        self.bind_wheel_events()
    
    def bind_wheel_events(self):
        """綁定滾輪事件到所有子元素"""
        # 在Windows上綁定MouseWheel事件
        if os.name == 'nt':
            self.bind("<MouseWheel>", self._on_mousewheel)
            for child in self.winfo_children():
                self._bind_wheel_to_children(child, "<MouseWheel>", self._on_mousewheel)
        # 在Linux/MacOS上綁定Button-4和Button-5事件
        else:
            self.bind("<Button-4>", self._on_mousewheel_up)
            self.bind("<Button-5>", self._on_mousewheel_down)
            for child in self.winfo_children():
                self._bind_wheel_to_children(child, "<Button-4>", self._on_mousewheel_up)
                self._bind_wheel_to_children(child, "<Button-5>", self._on_mousewheel_down)
    
    def _bind_wheel_to_children(self, widget, event, callback):
        """遞迴綁定滾輪事件到所有子元素"""
        widget.bind(event, callback)
        for child in widget.winfo_children():
            self._bind_wheel_to_children(child, event, callback)
    
    def _on_mousewheel(self, event):
        """Windows滾輪事件處理"""
        if self.main_canvas:
            # 將滾輪事件傳遞給Canvas
            self.main_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
    
    def _on_mousewheel_up(self, event):
        """Linux/MacOS向上滾動事件處理"""
        if self.main_canvas:
            self.main_canvas.yview_scroll(-1, "units")
    
    def _on_mousewheel_down(self, event):
        """Linux/MacOS向下滾動事件處理"""
        if self.main_canvas:
            self.main_canvas.yview_scroll(1, "units")
    
    def bind_right_click_to_children(self, widget):
        """只綁定右鍵選單，不綁定其他事件"""
        widget.bind("<Button-3>", self.show_context_menu)
        for child in widget.winfo_children():
            self.bind_right_click_to_children(child)
    
    def show_context_menu(self, event):
        """顯示右鍵選單，只阻止右鍵事件的傳播"""
        context_menu = tk.Menu(self, tearoff=0)
        
        # 狀態管理子選單
        status_menu = tk.Menu(context_menu, tearoff=0)
        
        # 簽到狀態選項
        status_menu.add_command(
            label="✓ 標記為已簽到" if not self.task.sign_in_done else "❌ 標記為未簽到",
            command=lambda: self.update_task_status("sign_in", not self.task.sign_in_done)
        )
        
        # 簽退狀態選項
        status_menu.add_command(
            label="✓ 標記為已簽退" if not self.task.sign_out_done else "❌ 標記為未簽退",
            command=lambda: self.update_task_status("sign_out", not self.task.sign_out_done)
        )
        
        # 重置狀態選項
        status_menu.add_separator()
        status_menu.add_command(
            label="重置所有狀態",
            command=self.reset_status
        )
        
        # 快速設置選項
        status_menu.add_separator()
        status_menu.add_command(
            label="一鍵設為完成",
            command=self.set_all_complete
        )
        
        # 將狀態選單添加到主選單
        context_menu.add_cascade(label="任務狀態管理", menu=status_menu)
        
        # 如果環境受限，添加重置選項
        if hasattr(self.task, 'campus_restricted') and self.task.campus_restricted:
            context_menu.add_command(label="重置環境限制", command=self.reset_restriction)
        
        context_menu.add_separator()
        context_menu.add_command(label="編輯任務", command=self.edit)
        context_menu.add_command(label="刪除任務", command=self.delete)
        
        # 顯示選單
        context_menu.tk_popup(event.x_root, event.y_root)
        
        # 只阻止右鍵事件繼續傳播
        return "break"
    
    def create_widgets(self):
        # 任務標題
        title_frame = tk.Frame(self, bg=COLORS["card"])
        title_frame.pack(fill=tk.X, pady=(0, 10))
        
        title_label = tk.Label(title_frame, text=self.task.name, font=("Arial", 12, "bold"),
                             bg=COLORS["card"], fg=COLORS["text"])
        title_label.pack(side=tk.LEFT)
        
        status_text, status_color = self.get_status_info()
        self.status_label = tk.Label(title_frame, text=status_text, font=("Arial", 10),
                                bg=status_color, fg="white", padx=8, pady=2)
        self.status_label.pack(side=tk.RIGHT)
        
        # 日期和時間信息
        info_frame = tk.Frame(self, bg=COLORS["card"])
        info_frame.pack(fill=tk.X, pady=5)
        
        date_label = tk.Label(info_frame, text=f"日期: {self.task.date}", font=("Arial", 10),
                             bg=COLORS["card"], fg=COLORS["text"])
        date_label.pack(side=tk.LEFT)
        
        time_label = tk.Label(info_frame, text=f"時間: {self.task.sign_in_time} - {self.task.sign_out_time}", 
                             font=("Arial", 10), bg=COLORS["card"], fg=COLORS["text"])
        time_label.pack(side=tk.RIGHT)
        
        # 進度管理器 - 顯示任務的完成狀態
        status_frame = tk.Frame(self, bg=COLORS["card"])
        status_frame.pack(fill=tk.X, pady=(5, 10))
        
        # 添加簽到狀態切換
        self.sign_in_status_var = tk.IntVar(value=1 if self.task.sign_in_done else 0)
        sign_in_cb = ttk.Checkbutton(status_frame, text="已完成簽到", 
                                   variable=self.sign_in_status_var,
                                   command=lambda: self.update_task_status("sign_in", self.sign_in_status_var.get()))
        sign_in_cb.pack(side=tk.LEFT, padx=(0, 10))
        
        # 添加簽退狀態切換
        self.sign_out_status_var = tk.IntVar(value=1 if self.task.sign_out_done else 0)
        sign_out_cb = ttk.Checkbutton(status_frame, text="已完成簽退", 
                                    variable=self.sign_out_status_var,
                                    command=lambda: self.update_task_status("sign_out", self.sign_out_status_var.get()))
        sign_out_cb.pack(side=tk.LEFT)
        
        # 任務受限警告
        if hasattr(self.task, 'campus_restricted') and self.task.campus_restricted:
            restricted_label = tk.Label(status_frame, text="⚠️ 環境受限", 
                                      font=("Arial", 9), bg=COLORS["card"], fg="#e74c3c")
            restricted_label.pack(side=tk.RIGHT)
        
        # 按鈕區域
        button_frame = tk.Frame(self, bg=COLORS["card"])
        button_frame.pack(fill=tk.X, pady=(5, 0))
        
        sign_in_button = ModernButton(button_frame, text="簽到", command=self.sign_in,
                                   bg=COLORS["secondary"], activebackground="#27ae60")
        sign_in_button.pack(side=tk.LEFT, padx=(0, 5))
        
        sign_out_button = ModernButton(button_frame, text="簽退", command=self.sign_out,
                                     bg=COLORS["secondary"], activebackground="#27ae60")
        sign_out_button.pack(side=tk.LEFT, padx=5)
        
        edit_button = ModernButton(button_frame, text="編輯", command=self.edit)
        edit_button.pack(side=tk.RIGHT, padx=(5, 0))
        
        # 刪除按鈕保持紅色
        delete_button = ModernButton(button_frame, text="刪除", command=self.delete,
                                   bg=COLORS["warning"], activebackground=COLORS["warning_dark"],
                                   keep_color=True)
        delete_button.pack(side=tk.RIGHT, padx=5)
        
        # 將右鍵菜單綁定到所有子元素
        self.bind_right_click_to_children(self)
    
    def update_task_status(self, status_type, value):
        """更新任務狀態
        
        Args:
            status_type: 狀態類型 ("sign_in" 或 "sign_out")
            value: 狀態值 (0 或 1)
        """
        if status_type == "sign_in":
            self.task.sign_in_done = bool(value)
            self.sign_in_status_var.set(1 if self.task.sign_in_done else 0)
        elif status_type == "sign_out":
            self.task.sign_out_done = bool(value)
            self.sign_out_status_var.set(1 if self.task.sign_out_done else 0)
        
        # 如果手動更新狀態，清除環境限制標記
        if hasattr(self.task, 'campus_restricted') and self.task.campus_restricted:
            self.task.campus_restricted = False
            self.task.last_attempt_time = None
        
        # 更新狀態標籤
        status_text, status_color = self.get_status_info()
        self.status_label.config(text=status_text, bg=status_color)
        
        # 更新UI以反映最新狀態
        self.update_idletasks()
        
        # 調用回調函數更新任務
        if self.on_update_status:
            self.on_update_status(self.task)
    
    def reset_status(self):
        """重置任務狀態"""
        self.task.sign_in_done = False
        self.task.sign_out_done = False
        self.sign_in_status_var.set(0)
        self.sign_out_status_var.set(0)
        
        # 清除環境限制標記
        if hasattr(self.task, 'campus_restricted'):
            self.task.campus_restricted = False
            self.task.last_attempt_time = None
        
        # 更新狀態標籤
        status_text, status_color = self.get_status_info()
        self.status_label.config(text=status_text, bg=status_color)
        
        # 調用回調函數更新任務
        if self.on_update_status:
            self.on_update_status(self.task)
    
    def set_all_complete(self):
        """將任務設為全部完成"""
        self.task.sign_in_done = True
        self.task.sign_out_done = True
        self.sign_in_status_var.set(1)
        self.sign_out_status_var.set(1)
        
        # 清除環境限制標記
        if hasattr(self.task, 'campus_restricted'):
            self.task.campus_restricted = False
            self.task.last_attempt_time = None
        
        # 更新狀態標籤
        status_text, status_color = self.get_status_info()
        self.status_label.config(text=status_text, bg=status_color)
        
        # 調用回調函數更新任務
        if self.on_update_status:
            self.on_update_status(self.task)
    
    def reset_restriction(self):
        """重置環境限制狀態"""
        if hasattr(self.task, 'campus_restricted'):
            self.task.campus_restricted = False
            self.task.last_attempt_time = None
            
            # 更新狀態標籤
            status_text, status_color = self.get_status_info()
            self.status_label.config(text=status_text, bg=status_color)
            
            # 調用回調函數更新任務
            if self.on_update_status:
                self.on_update_status(self.task)
    
    def get_status_info(self):
        today = datetime.date.today().strftime("%Y-%m-%d")
        task_date = self.task.date
        
        # 檢查環境受限狀態
        if hasattr(self.task, 'campus_restricted') and self.task.campus_restricted:
            return "環境受限", "#FF9800"  # 橙色表示環境受限
        
        # 手動設置的狀態優先顯示
        if task_date == today:
            if self.task.sign_in_done and self.task.sign_out_done:
                return "已完成", "#2ecc71"  # 綠色
            elif self.task.sign_in_done:
                now = datetime.datetime.now().strftime("%H:%M")
                if now >= self.task.sign_out_time:
                    return "待簽退", "#f39c12"  # 橙色
                else:
                    return "已簽到", "#3498db"  # 藍色
        
        # 日期狀態判斷
        if task_date < today:
            if self.task.sign_in_done and self.task.sign_out_done:
                return "已完成", "#2ecc71"
            else:
                return "已過期", "#95a5a6"  # 灰色
        elif task_date > today:
            return "等待中", "#3498db"  # 藍色
        else:  # 今天的任務
            now = datetime.datetime.now().strftime("%H:%M")
            if not self.task.sign_in_done and not self.task.sign_out_done:
                if now < self.task.sign_in_time:
                    return "今日待執行", "#3498db"  # 藍色
                else:
                    return "待處理", "#e74c3c"  # 紅色
            elif self.task.sign_in_done and not self.task.sign_out_done:
                return "已簽到", "#f39c12"  # 橙色
            else:
                return "已完成", "#2ecc71"  # 綠色
    
    def edit(self):
        if self.on_edit:
            self.on_edit(self.task)
    
    def delete(self):
        if self.on_delete:
            self.on_delete(self.task)
    
    def sign_in(self):
        if self.on_sign_in:
            self.on_sign_in(self.task)
    
    def sign_out(self):
        if self.on_sign_out:
            self.on_sign_out(self.task)
