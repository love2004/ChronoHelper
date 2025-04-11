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
        
        # 改進邊框樣式和陰影效果
        self.config(highlightbackground=COLORS["border"], highlightthickness=1, relief=tk.FLAT)
        
        # 創建UI元件
        self.create_widgets()
        
        # 只綁定右鍵事件，其他事件不阻斷
        self.bind("<Button-3>", self.show_context_menu)
        
        # 綁定滾輪事件
        self.bind_wheel_events()
        
        # 綁定任務卡片懸停效果
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)
    
    def _on_enter(self, event):
        """鼠標進入卡片時的效果"""
        self.config(highlightbackground=COLORS["primary"], bg=COLORS["card_hover"])
        for child in self.winfo_children():
            if isinstance(child, tk.Frame):
                child.config(bg=COLORS["card_hover"])
                for subchild in child.winfo_children():
                    if isinstance(subchild, tk.Label) and subchild != self.status_label:
                        subchild.config(bg=COLORS["card_hover"])
                    elif isinstance(subchild, tk.Frame):
                        subchild.config(bg=COLORS["card_hover"])
                        for s in subchild.winfo_children():
                            if isinstance(s, tk.Label):
                                s.config(bg=COLORS["card_hover"])
    
    def _on_leave(self, event):
        """鼠標離開卡片時的效果"""
        self.config(highlightbackground=COLORS["border"], bg=COLORS["card"])
        for child in self.winfo_children():
            if isinstance(child, tk.Frame):
                child.config(bg=COLORS["card"])
                for subchild in child.winfo_children():
                    if isinstance(subchild, tk.Label) and subchild != self.status_label:
                        subchild.config(bg=COLORS["card"])
                    elif isinstance(subchild, tk.Frame):
                        subchild.config(bg=COLORS["card"])
                        for s in subchild.winfo_children():
                            if isinstance(s, tk.Label):
                                s.config(bg=COLORS["card"])
    
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
        # 任務標題和狀態區域
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
        
        # 添加進度條
        progress_frame = tk.Frame(self, bg=COLORS["card"])
        progress_frame.pack(fill=tk.X, pady=(10, 5))
        
        # 計算進度百分比
        progress_value = self._calculate_progress()
        
        # 提示文字
        progress_text = tk.Label(progress_frame, text=f"任務進度: {int(progress_value*100)}%", 
                               font=("Arial", 9), bg=COLORS["card"], fg=COLORS["text"])
        progress_text.pack(side=tk.LEFT)
        
        # 創建進度條框架
        progress_bar_frame = tk.Frame(self, height=6, bg=COLORS["card"])
        progress_bar_frame.pack(fill=tk.X, pady=(0, 10))
        
        # 創建進度條底色
        self.progress_bg = tk.Canvas(progress_bar_frame, height=6, bg=COLORS["progress_bg"], 
                                   highlightthickness=0)
        self.progress_bg.pack(fill=tk.X)
        
        # 根據進度創建進度條填充
        progress_color = self._get_progress_color(progress_value)
        self.progress_fill = self.progress_bg.create_rectangle(
            0, 0, progress_value * self.progress_bg.winfo_reqwidth(), 6, 
            fill=progress_color, outline=""
        )
        
        # 進度條重繪綁定
        self.progress_bg.bind("<Configure>", self._redraw_progress)
        
        # 任務狀態管理區域
        status_frame = tk.Frame(self, bg=COLORS["card"])
        status_frame.pack(fill=tk.X, pady=5)
        
        # 狀態指示區域（使用圖形化指示）
        indicator_frame = tk.Frame(status_frame, bg=COLORS["card"])
        indicator_frame.pack(side=tk.LEFT)
        
        # 簽到狀態指示
        sign_in_frame = tk.Frame(indicator_frame, bg=COLORS["card"])
        sign_in_frame.pack(side=tk.LEFT, padx=(0, 10))
        
        sign_in_color = "#2ecc71" if self.task.sign_in_done else "#e0e0e0"
        sign_in_indicator = tk.Canvas(sign_in_frame, width=15, height=15, bg=COLORS["card"], 
                                    highlightthickness=0)
        sign_in_indicator.create_oval(2, 2, 13, 13, fill=sign_in_color, outline="")
        sign_in_indicator.pack(side=tk.LEFT, padx=(0, 5))
        
        sign_in_label = tk.Label(sign_in_frame, text="簽到", font=("Arial", 9), 
                               bg=COLORS["card"], fg=COLORS["text"])
        sign_in_label.pack(side=tk.LEFT)
        
        # 簽退狀態指示
        sign_out_frame = tk.Frame(indicator_frame, bg=COLORS["card"])
        sign_out_frame.pack(side=tk.LEFT)
        
        sign_out_color = "#2ecc71" if self.task.sign_out_done else "#e0e0e0"
        sign_out_indicator = tk.Canvas(sign_out_frame, width=15, height=15, bg=COLORS["card"], 
                                     highlightthickness=0)
        sign_out_indicator.create_oval(2, 2, 13, 13, fill=sign_out_color, outline="")
        sign_out_indicator.pack(side=tk.LEFT, padx=(0, 5))
        
        sign_out_label = tk.Label(sign_out_frame, text="簽退", font=("Arial", 9), 
                                bg=COLORS["card"], fg=COLORS["text"])
        sign_out_label.pack(side=tk.LEFT)
        
        # 任務狀態切換
        status_toggle_frame = tk.Frame(status_frame, bg=COLORS["card"])
        status_toggle_frame.pack(side=tk.RIGHT)
        
        # 添加簽到狀態切換
        self.sign_in_status_var = tk.IntVar(value=1 if self.task.sign_in_done else 0)
        sign_in_cb = ttk.Checkbutton(status_toggle_frame, text="已簽到", 
                                   variable=self.sign_in_status_var,
                                   command=lambda: self.update_task_status("sign_in", self.sign_in_status_var.get()))
        sign_in_cb.pack(side=tk.LEFT, padx=(0, 10))
        
        # 添加簽退狀態切換
        self.sign_out_status_var = tk.IntVar(value=1 if self.task.sign_out_done else 0)
        sign_out_cb = ttk.Checkbutton(status_toggle_frame, text="已簽退", 
                                    variable=self.sign_out_status_var,
                                    command=lambda: self.update_task_status("sign_out", self.sign_out_status_var.get()))
        sign_out_cb.pack(side=tk.LEFT)
        
        # 任務受限警告顯示
        if hasattr(self.task, 'campus_restricted') and self.task.campus_restricted:
            warning_frame = tk.Frame(self, bg=COLORS["card"])
            warning_frame.pack(fill=tk.X, pady=(5, 10))
            
            restricted_label = tk.Label(warning_frame, text="⚠️ 環境受限", 
                                      font=("Arial", 9), bg=COLORS["status_warning"], fg=COLORS["status_warning_text"],
                                      padx=8, pady=3)
            restricted_label.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # 按鈕區域
        button_frame = tk.Frame(self, bg=COLORS["card"])
        button_frame.pack(fill=tk.X, pady=(10, 0))
        
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
    
    def _calculate_progress(self):
        """計算任務完成進度"""
        progress = 0.0
        
        # 如果已經簽到，進度至少50%
        if getattr(self.task, 'sign_in_done', False):
            progress += 0.5
        
        # 如果已經簽退，再加50%
        if getattr(self.task, 'sign_out_done', False):
            progress += 0.5
            
        return progress
    
    def _get_progress_color(self, progress):
        """根據進度值獲取顏色"""
        if progress >= 1.0:
            return COLORS["progress_done"]  # 綠色，完成
        elif progress >= 0.5:
            return COLORS["progress_pending"]  # 橙色，進行中
        else:
            return COLORS["progress_waiting"]  # 藍色，待處理
    
    def _redraw_progress(self, event):
        """重繪進度條"""
        progress = self._calculate_progress()
        width = self.progress_bg.winfo_width()
        progress_width = int(width * progress)
        
        # 清除現有進度條
        self.progress_bg.delete(self.progress_fill)
        
        # 重繪進度條
        progress_color = self._get_progress_color(progress)
        self.progress_fill = self.progress_bg.create_rectangle(
            0, 0, progress_width, 6, 
            fill=progress_color, outline=""
        )
    
    def update_task_status(self, status_type, value):
        """更新任務狀態並刷新界面
        
        Args:
            status_type: 'sign_in' 或 'sign_out'
            value: True/False 或 1/0
        """
        # 轉換value為布爾值
        value = bool(value)
        
        # 更新任務狀態
        if status_type == "sign_in":
            self.task.sign_in_done = value
            self.sign_in_status_var.set(1 if value else 0)
        elif status_type == "sign_out":
            self.task.sign_out_done = value
            self.sign_out_status_var.set(1 if value else 0)
        
        # 更新UI狀態
        status_text, status_color = self.get_status_info()
        self.status_label.config(text=status_text, bg=status_color)
        
        # 重繪進度條
        self._redraw_progress(None)
        
        # 通知應用程序更新任務狀態
        if self.on_update_status:
            self.on_update_status(self.task)
        
        # 視覺反饋
        self.flash_status()
    
    def flash_status(self):
        """狀態更新時的視覺反饋"""
        orig_bg = self.cget("bg")
        self.config(bg=COLORS["status_info"])  # 使用信息狀態背景色閃爍
        
        # 恢復原背景色
        self.after(200, lambda: self.config(bg=orig_bg))
    
    def reset_status(self):
        """重置所有狀態"""
        # 重置任務狀態
        self.task.sign_in_done = False
        self.task.sign_out_done = False
        
        # 如果有校內網絡限制，也重置它
        if hasattr(self.task, 'campus_restricted'):
            self.task.campus_restricted = False
        
        # 更新複選框狀態
        self.sign_in_status_var.set(0)
        self.sign_out_status_var.set(0)
        
        # 更新UI狀態
        status_text, status_color = self.get_status_info()
        self.status_label.config(text=status_text, bg=status_color)
        
        # 重繪進度條
        self._redraw_progress(None)
        
        # 通知應用程序更新任務狀態
        if self.on_update_status:
            self.on_update_status(self.task)
        
        # 提供強烈的視覺反饋
        self.flash_reset()
    
    def flash_reset(self):
        """重置時的視覺反饋"""
        orig_bg = self.cget("bg")
        self.config(bg=COLORS["status_danger"])  # 使用危險狀態背景色閃爍
        
        # 恢復原背景色
        self.after(300, lambda: self.config(bg=orig_bg))
    
    def set_all_complete(self):
        """設置所有狀態為完成"""
        # 設置任務狀態
        self.task.sign_in_done = True
        self.task.sign_out_done = True
        
        # 更新複選框狀態
        self.sign_in_status_var.set(1)
        self.sign_out_status_var.set(1)
        
        # 更新UI狀態
        status_text, status_color = self.get_status_info()
        self.status_label.config(text=status_text, bg=status_color)
        
        # 重繪進度條
        self._redraw_progress(None)
        
        # 通知應用程序更新任務狀態
        if self.on_update_status:
            self.on_update_status(self.task)
        
        # 提供強烈的視覺反饋
        self.flash_complete()
    
    def flash_complete(self):
        """完成時的視覺反饋"""
        orig_bg = self.cget("bg")
        self.config(bg=COLORS["status_success"])  # 使用成功狀態背景色閃爍
        
        # 恢復原背景色
        self.after(300, lambda: self.config(bg=orig_bg))
    
    def reset_restriction(self):
        """重置環境限制狀態"""
        if hasattr(self.task, 'campus_restricted'):
            # 重置環境限制
            self.task.campus_restricted = False
            
            # 移除警告標籤
            for widget in self.winfo_children():
                if isinstance(widget, tk.Frame):
                    for child in widget.winfo_children():
                        if isinstance(child, tk.Label) and "環境受限" in child.cget("text"):
                            widget.destroy()
                            break
            
            # 通知應用程序更新任務狀態
            if self.on_update_status:
                self.on_update_status(self.task)
            
            # 刷新卡片畫面
            self.update_idletasks()
    
    def get_status_info(self):
        """根據任務狀態獲取狀態文本和顏色
        
        Returns:
            tuple: (狀態文本, 狀態顏色)
        """
        today = datetime.datetime.now().strftime("%Y-%m-%d")
        current_time = datetime.datetime.now().strftime("%H:%M")
        
        # 如果不是今天的任務
        if self.task.date != today:
            if self.task.date < today:
                # 過期任務狀態顯示處理
                if self.task.sign_in_done and self.task.sign_out_done:
                    return "已完成", COLORS["progress_done"]  # 綠色
                elif not self.task.sign_in_done and not self.task.sign_out_done:
                    return "已過期", COLORS["warning"]  # 紅色
                else:
                    return "部分完成", COLORS["progress_pending"]  # 橙色
            else:
                # 未來任務
                return "未開始", COLORS["progress_waiting"]  # 藍色
        
        # 今天的任務
        if self.task.sign_in_done and self.task.sign_out_done:
            return "已完成", COLORS["progress_done"]  # 綠色
        
        if not self.task.sign_in_done:
            if current_time < self.task.sign_in_time:
                return "待簽到", COLORS["progress_waiting"]  # 藍色
            else:
                # 已過簽到時間但未簽到
                return "待簽到(已遲到)", COLORS["warning"]  # 紅色
        
        # 已簽到但未簽退
        if current_time < self.task.sign_out_time:
            return "進行中", COLORS["progress_pending"]  # 橙色
        else:
            # 已過簽退時間但未簽退
            return "待簽退(已遲到)", COLORS["warning"]  # 紅色
    
    def edit(self):
        """編輯任務"""
        if self.on_edit:
            self.on_edit(self.task)
    
    def delete(self):
        """刪除任務"""
        if self.on_delete:
            self.on_delete(self.task)
    
    def sign_in(self):
        """執行簽到操作"""
        if self.on_sign_in:
            self.on_sign_in(self.task)
    
    def sign_out(self):
        """執行簽退操作"""
        if self.on_sign_out:
            self.on_sign_out(self.task)
