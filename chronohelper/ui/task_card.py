# -*- coding: utf-8 -*-
"""
任務卡片UI元件
"""

import os
import tkinter as tk
import datetime

from tkinter import ttk
from chronohelper.config.colors import COLORS
from chronohelper.ui.base import ModernButton
from chronohelper.ui.helpers import SettingTooltip, add_tooltip

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
        
        # 綁定所有事件
        self.setup_event_bindings()
    
    def setup_event_bindings(self):
        """設置卡片的所有事件綁定"""
        # 綁定右鍵事件到卡片和子元件
        self.bind("<Button-3>", self.show_context_menu)
        self.bind_right_click_to_children(self)
        
        # 綁定滾輪事件
        self.bind_wheel_events()
        
        # 綁定任務卡片懸停效果
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)
    
    def _on_enter(self, event):
        """鼠標進入卡片時的效果 - 已禁用懸停效果"""
        # 懸停效果已禁用
        return None
    
    def _on_leave(self, event):
        """鼠標離開卡片時的效果 - 已禁用懸停效果"""
        # 懸停效果已禁用
        return None
    
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
        """為所有子元件添加右鍵點擊處理
        
        Args:
            widget: 要綁定的父元件
        """
        # 只為非按鈕的元件添加右鍵事件，避免和按鈕自身的事件衝突
        if not isinstance(widget, ModernButton):
            widget.bind("<Button-3>", self.show_context_menu, add="+")  # 使用add="+"確保不覆蓋其他綁定
        
        # 遞歸處理所有子元件
        for child in widget.winfo_children():
            # 跳過按鈕元件，避免干擾其正常使用
            if not isinstance(child, ModernButton):
                self.bind_right_click_to_children(child)
    
    def show_context_menu(self, event):
        """
        顯示任務卡片的右鍵選單
        
        Args:
            event: 觸發的事件對象
            
        Returns:
            str: "break" 以阻止事件進一步傳播
        """
        # 保存原來的邊框顏色，但不改變背景色
        original_highlight = self.cget("highlightbackground")
        # 視覺反饋只改變邊框顏色
        self.config(highlightbackground=COLORS["primary_dark"], 
                    highlightthickness=2)  # 增加邊框厚度提高視覺反饋效果
        
        # 建立右鍵選單
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
        
        # 在菜單關閉時恢復原來的樣式
        def restore_style():
            # 檢查滑鼠是否仍在卡片上，如果是則保持懸停樣式
            x, y = self.winfo_pointerxy()
            widget_under_mouse = self.winfo_containing(x, y)
            
            # 檢查滑鼠是否在這個卡片或其子元件上
            is_on_this_card = widget_under_mouse and (widget_under_mouse == self or 
                            self.winfo_id() in [w.winfo_id() for w in widget_under_mouse.winfo_toplevel().winfo_children()])
            
            # 如果滑鼠仍在卡片上，保持高亮效果
            if is_on_this_card:
                self.config(highlightbackground=COLORS["primary"], 
                          highlightthickness=1)
            else:
                # 否則恢復原來的邊框樣式
                self.config(highlightbackground=original_highlight, 
                          highlightthickness=1)
        
        # 顯示選單並在關閉時恢復樣式
        try:
            context_menu.tk_popup(event.x_root, event.y_root)
        finally:
            # 確保無論如何都會恢復樣式
            self.after(100, restore_style)
            context_menu.bind("<Unmap>", lambda e: restore_style())
        
        # 阻止事件繼續傳播，避免觸發其他綁定
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
        
        # 為狀態標籤添加工具提示
        status_tooltip_text = self.get_status_tooltip_text()
        self.status_tooltip = SettingTooltip(self.status_label, status_tooltip_text)
        
        # 日期和時間信息
        info_frame = tk.Frame(self, bg=COLORS["card"])
        info_frame.pack(fill=tk.X, pady=5)
        
        date_label = tk.Label(info_frame, text=f"日期: {self.task.date}", font=("Arial", 10),
                             bg=COLORS["card"], fg=COLORS["text"])
        date_label.pack(side=tk.LEFT)
        
        time_label = tk.Label(info_frame, text=f"時間: {self.task.sign_in_time} - {self.task.sign_out_time}", 
                             font=("Arial", 10), bg=COLORS["card"], fg=COLORS["text"])
        time_label.pack(side=tk.RIGHT)
        
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
        
        # 簽到按鈕
        sign_in_button = ModernButton(button_frame, text="簽到", command=self.sign_in,
                                   bg=COLORS["primary"], width=8, padx=5, pady=3, height=1)
        sign_in_button.pack(side=tk.LEFT, padx=(0, 10))
        
        # 為簽到按鈕添加工具提示 - 使用較短延遲以提高響應速度
        tooltip_sign_in = add_tooltip(sign_in_button, 
                                     "執行簽到操作\n系統會自動檢查校內網絡環境",
                                     delay=300, button_safe=True)
        
        # 簽退按鈕
        sign_out_button = ModernButton(button_frame, text="簽退", command=self.sign_out,
                                    bg=COLORS["secondary"], width=8, padx=5, pady=3, height=1)
        sign_out_button.pack(side=tk.LEFT, padx=(0, 10))
        
        # 為簽退按鈕添加工具提示 - 使用較短延遲以提高響應速度
        tooltip_sign_out = add_tooltip(sign_out_button, 
                                      "執行簽退操作\n需要先完成簽到才能簽退",
                                      delay=300, button_safe=True)
        
        # 編輯按鈕
        edit_button = ModernButton(button_frame, text="編輯", command=self.edit)
        edit_button.pack(side=tk.RIGHT, padx=(5, 0))
        # 為編輯按鈕添加工具提示
        add_tooltip(edit_button, "編輯此任務的詳細信息", delay=300)
        
        # 刪除按鈕保持紅色
        delete_button = ModernButton(button_frame, text="刪除", command=self.delete,
                                   bg=COLORS["warning"], activebackground=COLORS["warning_dark"],
                                   keep_color=True)
        delete_button.pack(side=tk.RIGHT, padx=5)
        # 為刪除按鈕添加工具提示
        add_tooltip(delete_button, "刪除此任務\n此操作無法撤銷", delay=300)
        
        # 將右鍵菜單綁定到所有子元素
        self.bind_right_click_to_children(self)
    
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
        
        # 通知應用程序更新任務狀態
        if self.on_update_status:
            self.on_update_status(self.task)
        
        # 視覺反饋
        self.flash_status()
    
    def flash_status(self):
        """狀態更新時的視覺反饋 - 只改變邊框顏色"""
        try:
            # 確保組件未被銷毀
            if self.winfo_exists():
                # 記錄原邊框設定
                orig_highlight = self.cget("highlightbackground")
                orig_thickness = self.cget("highlightthickness")
                
                # 改變邊框顏色和厚度
                self.config(highlightbackground=COLORS["status_info"],
                          highlightthickness=2)  # 使用較粗的邊框提高視覺效果
                
                # 使用try-except確保恢復操作不會失敗
                def restore_border():
                    try:
                        if self.winfo_exists():
                            self.config(highlightbackground=orig_highlight,
                                      highlightthickness=orig_thickness)
                    except Exception:
                        pass  # 忽略可能的錯誤
                
                # 恢復原邊框設定
                self.after(200, restore_border)
        except Exception:
            pass  # 如果元素已被銷毀，則忽略錯誤
    
    def flash_reset(self):
        """重置時的視覺反饋 - 只改變邊框顏色"""
        try:
            # 確保組件未被銷毀
            if self.winfo_exists():
                # 記錄原邊框設定
                orig_highlight = self.cget("highlightbackground")
                orig_thickness = self.cget("highlightthickness")
                
                # 改變邊框顏色和厚度
                self.config(highlightbackground=COLORS["status_danger"],
                          highlightthickness=2)  # 使用較粗的邊框提高視覺效果
                
                # 使用try-except確保恢復操作不會失敗
                def restore_border():
                    try:
                        if self.winfo_exists():
                            self.config(highlightbackground=orig_highlight,
                                      highlightthickness=orig_thickness)
                    except Exception:
                        pass  # 忽略可能的錯誤
                
                # 恢復原邊框設定
                self.after(300, restore_border)
        except Exception:
            pass  # 如果元素已被銷毀，則忽略錯誤
    
    def flash_complete(self):
        """完成時的視覺反饋 - 只改變邊框顏色"""
        try:
            # 確保組件未被銷毀
            if self.winfo_exists():
                # 記錄原邊框設定
                orig_highlight = self.cget("highlightbackground")
                orig_thickness = self.cget("highlightthickness")
                
                # 改變邊框顏色和厚度
                self.config(highlightbackground=COLORS["status_success"],
                          highlightthickness=2)  # 使用較粗的邊框提高視覺效果
                
                # 使用try-except確保恢復操作不會失敗
                def restore_border():
                    try:
                        if self.winfo_exists():
                            self.config(highlightbackground=orig_highlight,
                                      highlightthickness=orig_thickness)
                    except Exception:
                        pass  # 忽略可能的錯誤
                
                # 恢復原邊框設定
                self.after(300, restore_border)
        except Exception:
            pass  # 如果元素已被銷毀，則忽略錯誤
    
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
        
        # 通知應用程序更新任務狀態
        if self.on_update_status:
            self.on_update_status(self.task)
        
        # 提供強烈的視覺反饋
        self.flash_reset()
    
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
        
        # 通知應用程序更新任務狀態
        if self.on_update_status:
            self.on_update_status(self.task)
        
        # 提供強烈的視覺反饋
        self.flash_complete()
    
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
    
    def get_status_tooltip_text(self):
        """獲取狀態提示文本"""
        if hasattr(self.task, 'campus_restricted') and self.task.campus_restricted:
            return "此任務由於網絡環境限制暫時無法執行\n請確保連接到校內網絡後再試"
            
        if getattr(self.task, 'sign_in_done', False) and getattr(self.task, 'sign_out_done', False):
            return "任務已完成，已成功執行簽到和簽退"
        elif getattr(self.task, 'sign_in_done', False):
            return "已完成簽到，等待簽退"
        elif self._is_due_today():
            # 判斷是否已過簽到時間
            now = datetime.datetime.now().strftime("%H:%M")
            
            if now >= self.task.sign_in_time:
                return "簽到時間已到，但尚未簽到"
            else:
                return "等待任務開始時間"
        elif self._is_past_date():
            return "任務日期已過，未能完成"
        else:
            return "未來任務，等待任務日期到來"
    
    def _is_due_today(self):
        """檢查是否為今天的任務"""
        today = datetime.datetime.now().strftime("%Y-%m-%d")
        return self.task.date == today
        
    def _is_past_date(self):
        """檢查是否為過去的任務"""
        today = datetime.datetime.now().strftime("%Y-%m-%d")
        return self.task.date < today
