# -*- coding: utf-8 -*-
"""
ChronoHelper主應用類
"""

import tkinter as tk
from tkinter import scrolledtext, ttk, messagebox
import datetime
import os
import sys
import time
import random

from chronohelper.config.colors import COLORS
from chronohelper.config.settings import APP_SETTINGS
from chronohelper.ui.notification import NotificationWindow
from chronohelper.ui.dialogs import SettingsDialog, ModernTaskDialog
from chronohelper.ui.task_card import TaskCard
from chronohelper.utils.logger import Logger
from chronohelper.utils.network import NetworkUtils
from chronohelper.utils.file_handler import FileHandler
from chronohelper.services.auth_service import AuthService
from chronohelper.services.task_service import TaskService
from chronohelper.services.scheduler import SchedulerService
from chronohelper.models.task import Task

class ChronoHelper:
    def __init__(self, root):
        self.root = root
        self.root.title("ChronoHelper - 時間助手")
        self.root.geometry("950x650")
        self.root.configure(bg=COLORS["background"])
        
        # 先初始化核心組件
        self.logger = Logger() 
        
        # 設置應用圖標
        self.set_icon_for_all_windows()
        
        # 初始化 file_handler
        self.file_handler = FileHandler(self.logger)
        
        # 載入設定
        self.settings = self.file_handler.load_settings(APP_SETTINGS)
        
        # 初始化其他核心組件
        self.network_utils = NetworkUtils(self.logger, self.settings)
        self.auth_service = AuthService(self.logger)
        self.task_service = TaskService(self.logger, self.auth_service)
        
        # 初始化狀態變量
        self.tasks = []
        self.is_campus_network = False
        self.current_ip = "未知"
        self.last_network_log_time = None
        self.last_network_log_status = None
        self.system_stats = {
            "total_tasks": 0,
            "active_tasks": 0,
            "completed_tasks": 0,
            "pending_tasks": 0,
            "last_update": "從未",
            "scheduler_status": "停止",
            "sign_in_success": 0,
            "sign_out_success": 0,
            "failures": 0
        }
        
        # 預先初始化執行統計結構
        self.execution_stats = {
            "total_executions": 0,
            "successful_sign_ins": 0,
            "successful_sign_outs": 0,
            "failed_sign_ins": 0,
            "failed_sign_outs": 0,
            "last_success_time": None
        }
        
        # 創建界面
        self.create_widgets()
        
        # 載入任務和Cookie
        self.load_tasks()
        self.refresh_task_list()
        self.log_text.see(tk.END) 
        
        self.load_cookies()
        
        # 先進行網絡環境初始檢測，不使用緩存結果
        self.logger.log("進行初始網絡環境檢測...")
        self.network_utils.clear_cache()  # 清除緩存，確保獲得新的檢測結果
        is_campus, ip, hop_info = self.network_utils.check_campus_network(verbose=True)
        self.update_network_status(is_campus, ip, hop_info, force_update=True)
        
        # 確保將結果設為應用程式的狀態
        self.is_campus_network = is_campus
        
        # 記錄初始檢測時間
        self.last_periodic_check_time = time.time()
        
        # 啟動調度器（在網絡檢測完成後）
        self.scheduler = SchedulerService(self)
        
        # 將我們的統計數據賦值給調度器
        if hasattr(self.scheduler, 'execution_stats'):
            self.scheduler.execution_stats = self.execution_stats
        
        # 啟動定期網絡檢測（增加隨機延遲，避免所有實例同時檢測）
        initial_delay = 10000 + random.randint(0, 5000)  # 10-15秒的初始延遲
        self.root.after(initial_delay, self.periodic_network_check)
        
        # 啟動狀態統計更新
        self.update_system_stats()  # 立即更新一次
        self.root.after(5000, self.update_system_stats)
        
        # 註冊關閉窗口事件處理器
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
    
    def create_widgets(self):
        # 頂部標題欄
        header_frame = tk.Frame(self.root, bg=COLORS["primary"], padx=20, pady=15)
        header_frame.pack(fill=tk.X)
        
        title_label = tk.Label(header_frame, text="ChronoHelper", 
                              font=("Arial", 18, "bold"), bg=COLORS["primary"], fg="white")
        title_label.pack(side=tk.LEFT)
        
        subtitle_label = tk.Label(header_frame, text="多任務自動簽到簽退工具", 
                                font=("Arial", 12), bg=COLORS["primary"], fg="white")
        subtitle_label.pack(side=tk.LEFT, padx=10)
        
        # 添加設定按鈕
        settings_button = tk.Button(header_frame, text="設定", 
                                    command=self.open_settings, bg=COLORS["primary"],
                                    activebackground=COLORS["primary_dark"],
                                    fg="white", activeforeground="white",
                                    bd=0, padx=15, pady=8)
        settings_button.pack(side=tk.RIGHT)
        
        # 主內容區
        content_frame = tk.Frame(self.root, bg=COLORS["background"])
        content_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # 左側任務面板
        left_frame = tk.Frame(content_frame, bg=COLORS["background"])
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        tasks_header = tk.Frame(left_frame, bg=COLORS["background"])
        tasks_header.pack(fill=tk.X, pady=(0, 10))
        
        tk.Label(tasks_header, text="任務列表", font=("Arial", 14, "bold"), 
                 bg=COLORS["background"], fg=COLORS["text"]).pack(side=tk.LEFT)
        
        from chronohelper.ui.base import ModernButton
        add_button = ModernButton(tasks_header, text="+ 新增任務", command=self.add_task)
        add_button.pack(side=tk.RIGHT)
        
        # 任務捲動區域
        self.tasks_canvas = tk.Canvas(left_frame, bg=COLORS["background"], 
                                     highlightthickness=0)
        self.tasks_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # 捲動條
        tasks_scrollbar = ttk.Scrollbar(left_frame, orient=tk.VERTICAL, 
                                       command=self.tasks_canvas.yview)
        tasks_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.tasks_canvas.configure(yscrollcommand=tasks_scrollbar.set)
        
        # 任務列表框架
        self.tasks_frame = tk.Frame(self.tasks_canvas, bg=COLORS["background"])
        self.tasks_canvas_window = self.tasks_canvas.create_window((0, 0), window=self.tasks_frame, 
                                       anchor=tk.NW, tags="self.tasks_frame")
        
        # 設置滾輪事件綁定
        self.tasks_canvas.bind("<Enter>", self._bind_mousewheel)
        self.tasks_canvas.bind("<Leave>", self._unbind_mousewheel)
        
        # 右側日誌和狀態面板
        right_frame = tk.Frame(content_frame, bg=COLORS["background"], width=300)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, padx=(20, 0))
        right_frame.pack_propagate(False)  # 防止框架縮小
        
        # 系統狀態卡片
        status_label = tk.Label(right_frame, text="系統狀態", font=("Arial", 14, "bold"), 
                             bg=COLORS["background"], fg=COLORS["text"])
        status_label.pack(anchor=tk.W, pady=(0, 10))
        
        # 系統狀態卡片框架
        self.status_card = tk.Frame(right_frame, bg=COLORS["card"], bd=1, relief=tk.SOLID, padx=10, pady=10)
        self.status_card.pack(fill=tk.X, pady=(0, 15))
        
        # 標題和刷新按鈕
        status_header = tk.Frame(self.status_card, bg=COLORS["card"])
        status_header.pack(fill=tk.X, pady=(0, 5))
        
        tk.Label(status_header, text="系統運行狀態", font=("Arial", 10, "bold"),
               bg=COLORS["card"], fg=COLORS["text"]).pack(side=tk.LEFT)
        
        # 按鈕框架
        button_frame = tk.Frame(status_header, bg=COLORS["card"])
        button_frame.pack(side=tk.RIGHT)
        
        # 添加重置按鈕
        reset_button = tk.Button(button_frame, text="重置", bg=COLORS["card"],
                               fg=COLORS["warning"], relief=tk.FLAT, bd=0, padx=5,
                               command=self.reset_statistics,
                               activebackground=COLORS["card_hover"],
                               activeforeground=COLORS["warning_dark"])
        reset_button.pack(side=tk.RIGHT, padx=(0, 5))
        
        # 添加刷新按鈕
        refresh_button = tk.Button(button_frame, text="⟳", bg=COLORS["card"],
                                  fg=COLORS["primary"], relief=tk.FLAT, bd=0, padx=5,
                                  command=self.update_system_stats,
                                  activebackground=COLORS["card_hover"],
                                  activeforeground=COLORS["primary_dark"])
        refresh_button.pack(side=tk.RIGHT)
        
        # 調度器狀態
        self.scheduler_status_frame = tk.Frame(self.status_card, bg=COLORS["card"])
        self.scheduler_status_frame.pack(fill=tk.X, pady=3)
        
        tk.Label(self.scheduler_status_frame, text="調度器:", bg=COLORS["card"], 
               fg=COLORS["text"], font=("Arial", 9, "bold")).pack(side=tk.LEFT)
        
        self.scheduler_status_var = tk.StringVar(value="初始化中")
        self.scheduler_indicator = tk.Label(self.scheduler_status_frame, textvariable=self.scheduler_status_var,
                                        bg=COLORS["card"], fg="#e74c3c", font=("Arial", 9))
        self.scheduler_indicator.pack(side=tk.RIGHT)
        
        # 任務統計
        self.task_stats_frame = tk.Frame(self.status_card, bg=COLORS["card"])
        self.task_stats_frame.pack(fill=tk.X, pady=3)
        
        tk.Label(self.task_stats_frame, text="任務統計:", bg=COLORS["card"], 
               fg=COLORS["text"], font=("Arial", 9, "bold")).pack(side=tk.LEFT)
        
        self.task_stats_var = tk.StringVar(value="總共 0 | 待執行 0 | 已完成 0")
        self.task_stats_label = tk.Label(self.task_stats_frame, textvariable=self.task_stats_var,
                                      bg=COLORS["card"], fg=COLORS["text"], font=("Arial", 9))
        self.task_stats_label.pack(side=tk.RIGHT)
        
        # 簽到簽退統計
        self.sign_stats_frame = tk.Frame(self.status_card, bg=COLORS["card"])
        self.sign_stats_frame.pack(fill=tk.X, pady=3)
        
        tk.Label(self.sign_stats_frame, text="簽到/簽退:", bg=COLORS["card"], 
               fg=COLORS["text"], font=("Arial", 9, "bold")).pack(side=tk.LEFT)
        
        self.sign_stats_var = tk.StringVar(value="成功 0 / 0 | 失敗 0")
        self.sign_stats_label = tk.Label(self.sign_stats_frame, textvariable=self.sign_stats_var,
                                      bg=COLORS["card"], fg=COLORS["text"], font=("Arial", 9))
        self.sign_stats_label.pack(side=tk.RIGHT)
        
        # 最後更新時間
        self.last_update_frame = tk.Frame(self.status_card, bg=COLORS["card"])
        self.last_update_frame.pack(fill=tk.X, pady=3)
        
        tk.Label(self.last_update_frame, text="最後更新:", bg=COLORS["card"], 
               fg=COLORS["text"], font=("Arial", 9, "bold")).pack(side=tk.LEFT)
        
        self.last_update_var = tk.StringVar(value="從未")
        self.last_update_label = tk.Label(self.last_update_frame, textvariable=self.last_update_var,
                                       bg=COLORS["card"], fg=COLORS["text"], font=("Arial", 9))
        self.last_update_label.pack(side=tk.RIGHT)
        
        # 日誌區域
        log_label = tk.Label(right_frame, text="執行日誌", font=("Arial", 14, "bold"), 
                           bg=COLORS["background"], fg=COLORS["text"])
        log_label.pack(anchor=tk.W, pady=(0, 10))
        
        log_frame = tk.Frame(right_frame, bg=COLORS["card"], bd=1, relief=tk.SOLID)
        log_frame.pack(fill=tk.BOTH, expand=True)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, wrap=tk.WORD, font=("Arial", 9))
        self.log_text.pack(fill=tk.BOTH, expand=True, padx=1, pady=1)
        self.log_text.config(bg=COLORS["card"], fg=COLORS["text"])
        
        # 設置日誌組件
        self.logger.set_text_widget(self.log_text)
        
        # 狀態區域
        status_frame = tk.Frame(self.root, bg=COLORS["primary_dark"], padx=10, pady=8)
        status_frame.pack(fill=tk.X, side=tk.BOTTOM)
        
        self.status_var = tk.StringVar(value="就緒，等待任務...")
        status_label = tk.Label(status_frame, textvariable=self.status_var, 
                              fg="white", bg=COLORS["primary_dark"], font=("Arial", 10))
        status_label.pack(side=tk.LEFT)
        
        # 網絡狀態顯示
        self.network_status_var = tk.StringVar(value="檢測網絡中...")
        self.network_status_label = tk.Label(status_frame, textvariable=self.network_status_var, 
                                       fg="white", bg=COLORS["primary_dark"], font=("Arial", 10))
        self.network_status_label.pack(side=tk.RIGHT, padx=(0, 20))
        
        # 在狀態欄中添加刷新網絡狀態按鈕
        refresh_network_button = tk.Button(status_frame, text="⟳", bg=COLORS["primary_dark"],
                                         fg="white", relief=tk.FLAT, bd=0, padx=5,
                                         command=self.refresh_network_status,
                                         activebackground=COLORS["primary"],
                                         activeforeground="white")
        refresh_network_button.pack(side=tk.RIGHT)
        
        # 添加powered by zhijing標籤
        powered_label = tk.Label(status_frame, text="Powered by zhijing", 
                               fg="white", bg=COLORS["primary_dark"], font=("Arial", 10))
        powered_label.pack(side=tk.RIGHT, padx=(0, 10))
        
        # 右下角信息
        info_label = tk.Label(status_frame, text="ChronoHelper v1.0", 
                            fg="white", bg=COLORS["primary_dark"], font=("Arial", 10))
        info_label.pack(side=tk.RIGHT)
        
        # 設置任務畫布的捲動功能
        self.tasks_frame.bind("<Configure>", self.on_frame_configure)
        self.tasks_canvas.bind("<Configure>", self.on_canvas_configure)
        
        # 記錄啟動信息
        self.logger.log("ChronoHelper 已啟動")
    
    def _on_mousewheel(self, event):
        # 滾輪捲動任務列表
        self.tasks_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
    
    def _bind_mousewheel(self, event):
        """綁定滾輪事件 - 修改為只綁定到Canvas的空白區域"""
        if os.name == 'nt':  # Windows
            self.tasks_canvas.bind("<MouseWheel>", self._on_mousewheel)
        else:  # Linux, macOS
            self.tasks_canvas.bind("<Button-4>", lambda e: self.tasks_canvas.yview_scroll(-1, "units"))
            self.tasks_canvas.bind("<Button-5>", lambda e: self.tasks_canvas.yview_scroll(1, "units"))
    
    def _unbind_mousewheel(self, event):
        """解除滾輪事件綁定 - 修改為只解綁Canvas的事件"""
        if os.name == 'nt':
            self.tasks_canvas.unbind("<MouseWheel>")
        else:
            self.tasks_canvas.unbind("<Button-4>")
            self.tasks_canvas.unbind("<Button-5>")
    
    def on_frame_configure(self, event):
        # 更新捲動區域
        self.tasks_canvas.configure(scrollregion=self.tasks_canvas.bbox("all"))
    
    def on_canvas_configure(self, event):
        # 調整任務列表框架的寬度
        self.tasks_canvas.itemconfig("self.tasks_frame", width=event.width)
    
    def load_tasks(self):
        """載入任務列表"""
        self.tasks = self.file_handler.load_tasks()
        
        # 初始化任務的前一狀態，用於追蹤狀態變更
        for task in self.tasks:
            task._prev_sign_in_done = getattr(task, 'sign_in_done', False)
            task._prev_sign_out_done = getattr(task, 'sign_out_done', False)
            
        self.logger.log(f"已載入 {len(self.tasks)} 個任務")
    
    def save_tasks(self):
        """保存任務列表"""
        if self.file_handler.save_tasks(self.tasks):
            self.refresh_task_list()
            self.logger.log("任務已保存")
    
    def refresh_task_list(self):
        """刷新任務列表顯示"""
        # 清空任務列表
        for widget in self.tasks_frame.winfo_children():
            widget.destroy()
        
        if not self.tasks:
            # 顯示空任務提示
            empty_label = tk.Label(self.tasks_frame, text="目前沒有任務，請點擊「新增任務」來開始", 
                                 font=("Arial", 11), bg=COLORS["background"], fg=COLORS["light_text"],
                                 padx=20, pady=40)
            empty_label.pack(fill=tk.X)
            return
        
        # 排序任務：先按日期，再按簽到時間
        sorted_tasks = sorted(self.tasks, key=lambda x: (x.date, x.sign_in_time))
        
        # 創建任務卡片，傳遞Canvas引用
        for task in sorted_tasks:
            task_card = TaskCard(
                self.tasks_frame, 
                task, 
                on_edit=self.edit_task,
                on_delete=self.delete_task,
                on_sign_in=self.perform_sign_in,
                on_sign_out=self.perform_sign_out,
                on_update_status=self.update_task_status,
                main_canvas=self.tasks_canvas  # 傳遞Canvas引用
            )
            task_card.pack(fill=tk.X, pady=5, padx=5)
    
    def add_task(self):
        """添加新任務"""
        # 使用預設時間
        default_sign_in = self.settings.get("default_sign_in", "09:00")
        default_sign_out = self.settings.get("default_sign_out", "18:00")
        
        # 創建新增任務對話框
        dialog = ModernTaskDialog(self.root, "新增簽到簽退任務", 
                                 sign_in=default_sign_in, 
                                 sign_out=default_sign_out)
        if dialog.result:
            name, date, sign_in, sign_out, notify = dialog.result
            new_task = Task(name, date, sign_in, sign_out, notify)
            
            # 初始化任務的前一狀態
            new_task._prev_sign_in_done = False
            new_task._prev_sign_out_done = False
            
            self.tasks.append(new_task)
            self.save_tasks()
            self.logger.log(f"新增任務: {name}, 日期: {date}, 時間: {sign_in}-{sign_out}")
            self.show_notification("任務已建立", f"已成功新增「{name}」任務")
    
    def edit_task(self, task):
        """編輯任務"""
        # 顯示編輯對話框
        dialog = ModernTaskDialog(
            self.root, 
            "編輯簽到簽退任務",
            name=task.name,
            date=task.date,
            sign_in=task.sign_in_time,
            sign_out=task.sign_out_time,
            notify=task.notify
        )
        
        if dialog.result:
            name, date, sign_in, sign_out, notify = dialog.result
            task.name = name
            task.date = date
            task.sign_in_time = sign_in
            task.sign_out_time = sign_out
            task.notify = notify
            self.save_tasks()
            self.logger.log(f"編輯任務: {name}, 日期: {date}, 時間: {sign_in}-{sign_out}")
            self.show_notification("任務已更新", f"已成功更新「{name}」任務")
    
    def delete_task(self, task):
        """刪除任務"""
        if messagebox.askyesno("確認刪除", f"確定要刪除「{task.name}」任務嗎？", parent=self.root):
            self.tasks.remove(task)
            self.save_tasks()
            self.logger.log(f"刪除任務: {task.name}")
            self.show_notification("任務已刪除", f"已成功刪除「{task.name}」任務")
    
    def update_task_status(self, task):
        """更新任務狀態"""
        # 獲取任務變更前的狀態，如果不存在則設為False
        old_sign_in_done = getattr(task, '_prev_sign_in_done', False)
        old_sign_out_done = getattr(task, '_prev_sign_out_done', False)
        
        # 保存任務當前狀態作為下次比較的基準
        task._prev_sign_in_done = task.sign_in_done
        task._prev_sign_out_done = task.sign_out_done
        
        # 保存更新後的任務
        self.save_tasks()
        
        # 更新日誌
        status_text = []
        if task.sign_in_done:
            status_text.append("已簽到")
        if task.sign_out_done:
            status_text.append("已簽退")
        
        status_str = " 和 ".join(status_text) if status_text else "未完成"
        
        # 環境限制狀態
        if hasattr(task, 'campus_restricted') and task.campus_restricted:
            status_str += "（環境受限已清除）"
        
        self.logger.log(f"已手動更新任務 '{task.name}' 狀態: {status_str}")
        
        # 更新統計信息
        if hasattr(self, 'scheduler') and hasattr(self.scheduler, 'execution_stats'):
            stats = self.scheduler.execution_stats
            
            # 確保統計數據結構完整
            if stats is None:
                stats = {
                    "total_executions": 0,
                    "successful_sign_ins": 0,
                    "successful_sign_outs": 0,
                    "failed_sign_ins": 0,
                    "failed_sign_outs": 0,
                    "last_success_time": None
                }
                self.scheduler.execution_stats = stats
            
            # 檢查簽到狀態變化
            if task.sign_in_done and not old_sign_in_done:
                stats["successful_sign_ins"] = stats.get("successful_sign_ins", 0) + 1
                stats["last_success_time"] = datetime.datetime.now()
            elif not task.sign_in_done and old_sign_in_done:
                stats["successful_sign_ins"] = max(0, stats.get("successful_sign_ins", 0) - 1)
            
            # 檢查簽退狀態變化
            if task.sign_out_done and not old_sign_out_done:
                stats["successful_sign_outs"] = stats.get("successful_sign_outs", 0) + 1
                stats["last_success_time"] = datetime.datetime.now()
            elif not task.sign_out_done and old_sign_out_done:
                stats["successful_sign_outs"] = max(0, stats.get("successful_sign_outs", 0) - 1)
            
            # 更新總執行次數
            if (task.sign_in_done != old_sign_in_done) or (task.sign_out_done != old_sign_out_done):
                stats["total_executions"] = stats.get("total_executions", 0) + 1
            
            # 使用after延遲更新系統狀態面板，避免與界面更新衝突
            self.root.after(100, self.update_system_stats)
    
    def load_cookies(self):
        """載入保存的Cookies"""
        cookies = self.file_handler.load_cookies()
        if cookies:
            self.auth_service.set_cookies(cookies)
            self.logger.log("已載入保存的Cookie，將在首次操作時驗證")
    
    def save_cookies(self):
        """保存當前會話的Cookies"""
        cookies_list = self.auth_service.get_cookies_list()
        if self.file_handler.save_cookies(cookies_list):
            self.logger.log("已保存Cookie")
    
    def open_settings(self):
        """打開設置對話框"""
        dialog = SettingsDialog(self.root, self.settings)
        if dialog.result:
            # 保存舊設定的某些值用於比較
            old_interval = self.settings.get("check_interval", 30)
            old_hop_timeout = self.settings.get("hop_check_timeout", 3)
            old_enable_second_hop = self.settings.get("enable_second_hop", False)
            
            # 更新設定
            self.settings = dialog.result
            
            # 立即保存到文件
            self.file_handler.save_settings(self.settings)
            self.logger.log("已更新應用程式設定")
            
            # 將新設定應用到網絡工具
            self.network_utils.update_settings(self.settings)
            
            # 如果檢查間隔有變更，重啟調度器
            if old_interval != self.settings.get("check_interval", 30):
                self.scheduler.stop()
                self.scheduler = SchedulerService(self)
            
            # 通知用戶設定已更新
            update_message = "已成功更新ChronoHelper設定"
            
            # 如果網絡檢測相關設定有變更，顯示特定消息
            if (old_hop_timeout != self.settings.get("hop_check_timeout", 3) or
                old_enable_second_hop != self.settings.get("enable_second_hop", False)):
                update_message += "\n網絡檢測設定已更新，點擊狀態欄的刷新圖標測試"
            
            self.show_notification("設定已更新", update_message)
            
            # 清除緩存，但不立即執行檢測
            self.network_utils.clear_cache()
    
    def perform_sign_in(self, task):
        """執行簽到操作"""
        # 檢查網絡環境
        if not self.is_campus_network:
            self.logger.log(f"簽到失敗: 當前處於校外網絡環境，IP: {self.current_ip}")
            if self.settings.get("global_notify", True) and task.notify:
                self.show_notification(f"{task.name} 簽到失敗", 
                                     "您當前處於校外網絡環境，無法執行簽到操作\n請連接校內網絡後再試")
            self.status_var.set("簽到需要校內網絡環境")
            return False
        
        # 調用任務服務執行簽到
        result = self.task_service.perform_sign_in(task, self.settings)
        
        # 處理結果
        if result:
            # 更新任務狀態
            task.sign_in_done = True
            self.save_tasks()
            
            # 更新統計信息
            if hasattr(self, 'scheduler') and hasattr(self.scheduler, 'execution_stats'):
                stats = self.scheduler.execution_stats
                stats["successful_sign_ins"] = stats.get("successful_sign_ins", 0) + 1
                stats["total_executions"] = stats.get("total_executions", 0) + 1
                stats["last_success_time"] = datetime.datetime.now()
                
                # 立即更新系統狀態面板
                self.update_system_stats()
            
            # 顯示通知
            if self.settings.get("global_notify", True) and task.notify:
                self.show_notification(f"{task.name} 簽到成功", 
                                      f"已在 {datetime.datetime.now().strftime('%H:%M:%S')} 完成簽到")
            
            self.status_var.set(f"已完成 '{task.name}' 的簽到")
            return True
        else:
            # 更新統計信息
            if hasattr(self, 'scheduler') and hasattr(self.scheduler, 'execution_stats'):
                stats = self.scheduler.execution_stats
                stats["failed_sign_ins"] = stats.get("failed_sign_ins", 0) + 1
                stats["total_executions"] = stats.get("total_executions", 0) + 1
                
                # 立即更新系統狀態面板
                self.update_system_stats()
                
            # 如果任務有環境限制標記，更新UI
            if hasattr(task, 'campus_restricted') and task.campus_restricted:
                self.save_tasks()
            
            self.status_var.set(f"'{task.name}' 簽到失敗")
            return False
    
    def perform_sign_out(self, task):
        """執行簽退操作"""
        # 檢查網絡環境
        if not self.is_campus_network:
            self.logger.log(f"簽退失敗: 當前處於校外網絡環境，IP: {self.current_ip}")
            if self.settings.get("global_notify", True) and task.notify:
                self.show_notification(f"{task.name} 簽退失敗", 
                                     "您當前處於校外網絡環境，無法執行簽退操作\n請連接校內網絡後再試")
            self.status_var.set("簽退需要校內網絡環境")
            return False
        
        # 調用任務服務執行簽退
        result = self.task_service.perform_sign_out(task, self.settings)
        
        # 處理結果
        if result:
            # 更新任務狀態
            task.sign_out_done = True
            self.save_tasks()
            
            # 更新統計信息
            if hasattr(self, 'scheduler') and hasattr(self.scheduler, 'execution_stats'):
                stats = self.scheduler.execution_stats
                stats["successful_sign_outs"] = stats.get("successful_sign_outs", 0) + 1
                stats["total_executions"] = stats.get("total_executions", 0) + 1
                stats["last_success_time"] = datetime.datetime.now()
                
                # 立即更新系統狀態面板
                self.update_system_stats()
            
            # 顯示通知
            if self.settings.get("global_notify", True) and task.notify:
                self.show_notification(f"{task.name} 簽退成功", 
                                      f"已在 {datetime.datetime.now().strftime('%H:%M:%S')} 完成簽退")
            
            # 特殊處理：檢查工作時間不足的情況
            self.check_work_time(task)
            
            self.status_var.set(f"已完成 '{task.name}' 的簽退")
            return True
        else:
            # 更新統計信息
            if hasattr(self, 'scheduler') and hasattr(self.scheduler, 'execution_stats'):
                stats = self.scheduler.execution_stats
                stats["failed_sign_outs"] = stats.get("failed_sign_outs", 0) + 1
                stats["total_executions"] = stats.get("total_executions", 0) + 1
                
                # 立即更新系統狀態面板
                self.update_system_stats()
                
            # 如果任務有環境限制標記，更新UI
            if hasattr(task, 'campus_restricted') and task.campus_restricted:
                self.save_tasks()
            
            self.status_var.set(f"'{task.name}' 簽退失敗")
            return False
    
    def check_work_time(self, task):
        """檢查工作時間是否足夠"""
        if task.sign_in_done and task.sign_in_time:
            try:
                # 解析簽到時間
                sign_in_parts = task.sign_in_time.split(":")
                now = datetime.datetime.now()
                
                # 構建今天的簽到時間和當前時間對象
                sign_in_time = datetime.datetime(
                    now.year, now.month, now.day,
                    int(sign_in_parts[0]), int(sign_in_parts[1])
                )
                
                # 計算時間差
                time_diff = now - sign_in_time
                minutes = time_diff.total_seconds() / 60
                
                if minutes < 30:
                    warning_msg = (
                        f"注意：您的工作時間僅為 {int(minutes)} 分鐘，不足30分鐘。\n\n"
                        "根據系統規則，不足30分鐘的工讀時數將不列入計算。\n"
                        "請確保您的工作時間達到學校規定的最低要求。"
                    )
                    messagebox.showwarning("工作時間不足", warning_msg, parent=self.root)
                    self.logger.log(f"警告: 工作時間不足30分鐘 ({int(minutes)}分鐘)")
            except Exception as e:
                self.logger.log(f"計算工作時間時出錯: {str(e)}")
    
    def show_notification(self, title, message):
        """顯示桌面通知"""
        NotificationWindow(title, message)
        self.logger.log(f"通知: {title} - {message}")
    
    def periodic_network_check(self):
        """定期檢測網絡環境"""
        if not self.scheduler.running:
            return  # 如果調度器已停止，不再檢測
        
        # 檢查上次檢測時間，避免頻繁檢測
        now = time.time()
        last_check = getattr(self, 'last_periodic_check_time', 0)
        min_interval = self.settings.get("network_check_interval", 30)  # 最小間隔（秒）
        
        # 如果距離上次檢測時間不夠長，延遲檢測
        if now - last_check < min_interval:
            # 繼續排程定期檢測，但避免頻繁執行
            self.root.after(max(1000, int((min_interval - (now - last_check)) * 1000)), 
                           self.periodic_network_check)
            return
            
        # 更新最後檢測時間
        self.last_periodic_check_time = now
            
        # 執行網絡檢測，但避免重複記錄
        is_campus, ip, hop_info = self.network_utils.check_campus_network(verbose=False)
        
        # 強制更新UI，確保界面狀態和後端檢測結果同步
        self.root.after(0, lambda: self.update_network_status(is_campus, ip, hop_info, force_update=True))
        
        # 繼續定期檢測（使用動態間隔，根據設定決定頻率）
        check_interval = max(10000, self.settings.get("network_check_interval", 30) * 1000)
        self.root.after(check_interval, self.periodic_network_check)
    
    def update_network_status(self, is_campus, ip, hop_info=None, force_update=False):
        """更新網絡狀態顯示
        
        Args:
            is_campus: 是否為校內網絡
            ip: IP地址
            hop_info: 躍點信息
            force_update: 是否強制更新UI，不考慮狀態是否變化
        """
        # 檢查是否有前一個狀態
        had_previous_state = hasattr(self, 'is_campus_network')
        status_changed = had_previous_state and self.is_campus_network != is_campus
        
        # 如果狀態變化或需要強制更新
        if status_changed or force_update:
            # 只在狀態變化且不是首次檢測時發出更改通知
            if status_changed and had_previous_state:
                if is_campus:
                    self.logger.log("網絡環境已變更: 校外 -> 校內")
                    
                    # 如果是通過第二躍點檢測到的，則顯示相關信息
                    if hop_info and hop_info.get('is_campus', False) and not ip.startswith('163.23.'):
                        hop_ip = hop_info.get('ip', '未知')
                        self.logger.log(f"通過第二躍點識別為校內網絡 (第二躍點IP: {hop_ip})")
                        self.show_notification("網絡環境變更", f"檢測到第二躍點 {hop_ip} 為校內網絡\n現在可以正常執行簽到/簽退操作")
                    else:
                        self.show_notification("網絡環境變更", "檢測到您已連接到校內網絡\n現在可以正常執行簽到/簽退操作")
                    
                    # 重置校內網絡限制狀態
                    reset_count = self.reset_campus_restrictions()
                    
                    # 立即觸發一次任務調度檢查
                    if hasattr(self, 'scheduler') and self.scheduler.running:
                        self.root.after(1000, self.scheduler.check_tasks)
                else:
                    self.logger.log("網絡環境已變更: 校內 -> 校外")
                    self.show_notification("網絡環境變更", "檢測到您已離開校內網絡\n簽到/簽退操作將暫停執行")
            elif not had_previous_state:
                # 首次檢測，記錄初始狀態
                network_type = "校內" if is_campus else "校外"
                
                # 如果是通過第二躍點檢測到的，則顯示相關信息
                if is_campus and hop_info and hop_info.get('is_campus', False) and not ip.startswith('163.23.'):
                    hop_ip = hop_info.get('ip', '未知')
                    self.logger.log(f"初始網絡環境檢測: 校內網絡 (通過第二躍點 {hop_ip})")
                else:
                    self.logger.log(f"初始網絡環境檢測: {network_type}網絡")
        
            # 只在首次檢測或IP變更時記錄IP
            if not had_previous_state or self.current_ip != ip:
                self.logger.log(f"IP地址: {ip}")
            
            # 更新UI顯示
            if is_campus:
                # 如果是通過第二躍點檢測到的，則在UI中顯示相關信息
                if hop_info and hop_info.get('is_campus', False) and not ip.startswith('163.23.'):
                    hop_ip = hop_info.get('ip', '未知')
                    self.network_status_var.set(f"校內網絡(通過躍點) ✓ ({hop_ip})")
                else:
                    self.network_status_var.set(f"校內網絡 ✓ ({ip})")
                self.network_status_label.config(fg=COLORS["progress_done"])  # 綠色
            else:
                self.network_status_var.set(f"校外網絡 ⚠️ ({ip})")
                self.network_status_label.config(fg=COLORS["warning"])  # 紅色
            
            # 記錄網絡狀態以供任務檢查使用
            self.is_campus_network = is_campus
            self.current_ip = ip
            
            # 記錄上次網絡環境日誌時間和狀態
            self.last_network_log_time = datetime.datetime.now()
            self.last_network_log_status = is_campus
            
            # 添加網絡質量指示器
            self._update_network_quality_indicator(hop_info)
            
            # 強制更新UI
            self.root.update_idletasks()
            
            # 如果狀態發生變化，刷新任務列表顯示
            if status_changed:
                self.refresh_task_list()
    
    def _update_network_quality_indicator(self, hop_info):
        """更新網絡質量指示器"""
        # 如果狀態欄中不存在網絡質量指示器，則創建一個
        if not hasattr(self, 'network_quality_indicator'):
            # 查找狀態欄
            for widget in self.root.winfo_children():
                if isinstance(widget, tk.Frame) and widget.winfo_y() > self.root.winfo_height() - 50:
                    # 創建網絡質量指示器框架
                    quality_frame = tk.Frame(widget, bg=COLORS["primary_dark"])
                    quality_frame.pack(side=tk.RIGHT, padx=(0, 5))
                    
                    # 創建指示器
                    self.network_quality_indicator = tk.Canvas(quality_frame, width=12, height=12, 
                                                         bg=COLORS["primary_dark"], highlightthickness=0)
                    self.network_quality_indicator.pack(side=tk.RIGHT)
                    
                    # 初始化指示器圓形
                    self.network_quality_circle = self.network_quality_indicator.create_oval(
                        2, 2, 10, 10, fill="#e74c3c", outline="")
                    break
        
        # 根據躍點信息更新網絡質量指示器顏色
        if hasattr(self, 'network_quality_indicator'):
            if not self.is_campus_network:
                # 校外網絡:紅色
                quality_color = "#e74c3c"
            elif hop_info and "latency" in hop_info:
                # 根據延遲設置顏色
                latency = hop_info["latency"]
                if latency < 50:
                    quality_color = "#2ecc71"  # 綠色:良好
                elif latency < 100:
                    quality_color = "#f39c12"  # 橙色:一般
                else:
                    quality_color = "#e74c3c"  # 紅色:較差
            else:
                # 默認為綠色
                quality_color = "#2ecc71"
            
            # 更新指示器顏色
            self.network_quality_indicator.itemconfig(self.network_quality_circle, fill=quality_color)
            
            # 添加提示文字
            quality_text = "校外網絡"
            if self.is_campus_network:
                if hop_info and "latency" in hop_info:
                    quality_text = f"網絡延遲: {hop_info['latency']}ms"
                else:
                    quality_text = "校內網絡"
            
            # 使用工具提示顯示網絡質量信息
            ToolTip(self.network_quality_indicator, quality_text)

    def refresh_network_status(self):
        """手動刷新網絡狀態"""
        self.network_status_var.set("檢測網絡中...")
        self.network_status_label.config(fg="white")
        
        # 使用after確保UI先更新
        self.root.after(100, self._refresh_network_status_task)
    
    def _refresh_network_status_task(self):
        """刷新網絡狀態實際任務"""
        try:
            self.logger.log("正在刷新網絡狀態...")
            is_campus, ip, hop_info = self.network_utils.check_campus_network(verbose=True)
            
            # 保存當前狀態以檢測變化
            old_status = getattr(self, 'is_campus_network', None)
            
            # 更新網絡狀態（強制更新界面）
            self.update_network_status(is_campus, ip, hop_info, force_update=True)
            
            # 如果網絡狀態發生變化，進行額外處理
            if old_status != is_campus:
                if is_campus:
                    # 從校外變為校內：重置環境限制並觸發任務檢查
                    reset_count = self.reset_campus_restrictions()
                    if reset_count > 0:
                        self.show_notification("環境限制已重置", 
                                             f"已重置 {reset_count} 個受環境限制的任務\n現在可以正常執行了")
                    
                    # 立即觸發一次任務調度檢查，不需要等待下一個調度周期
                    if hasattr(self, 'scheduler') and self.scheduler.running:
                        self.logger.log("網絡環境變更，立即檢查待執行任務...")
                        self.root.after(1000, self.scheduler.check_tasks)
                else:
                    # 從校內變為校外：更新任務列表顯示
                    self.logger.log("網絡環境變更為校外，暫停所有需要校內網絡的任務")
            
            # 強制刷新任務列表顯示
            self.refresh_task_list()
        except Exception as e:
            self.logger.log(f"網絡狀態刷新失敗: {str(e)}")
            self.network_status_var.set("網絡檢測失敗")
            self.network_status_label.config(fg="#e74c3c")  # 紅色
    
    def reset_campus_restrictions(self):
        """重置所有任務的環境限制狀態，返回重置的任務數量"""
        reset_count = 0
        for task in self.tasks:
            if hasattr(task, 'campus_restricted') and task.campus_restricted:
                task.campus_restricted = False
                task.last_attempt_time = None
                reset_count += 1
        
        if reset_count > 0:
            self.logger.log(f"已重置 {reset_count} 個任務的環境限制狀態")
            self.save_tasks()
        
        return reset_count

    def set_icon_for_all_windows(self):
        """使用更可靠的方法設置所有視窗的圖標"""
        try:
            self.logger.log("設置應用圖標...")
            
            # 獲取圖標數據
            icon_data = self.get_icon_data()
            
            if icon_data:
                # 為Tkinter根窗口設置圖標
                if hasattr(self.root, "_iconphoto"):
                    self.root.iconphoto(True, icon_data)
                elif os.name == 'nt':  # Windows
                    # 設置Windows特有的圖標
                    if hasattr(self.root, "iconbitmap"):
                        # 使用臨時文件來設置圖標
                        import tempfile
                        with tempfile.NamedTemporaryFile(suffix='.ico', delete=False) as temp_icon:
                            temp_icon.write(self.get_raw_icon_data())
                            temp_icon_path = temp_icon.name
                        
                        try:
                            self.root.iconbitmap(default=temp_icon_path)
                            # 保存路徑供其他窗口使用
                            self.root.iconpath = temp_icon_path
                        except:
                            pass
                
                self.logger.log("圖標設置成功")
            else:
                self.logger.log("無法獲取圖標數據，使用默認圖標")
        except Exception as e:
            self.logger.log(f"設置圖標時發生錯誤: {str(e)}")
            
        # 無論成功與否，確保應用不會因圖標問題而崩潰
        try:
            if not hasattr(self.root, "iconphoto") and not hasattr(self.root, "iconbitmap"):
                # 設置一個空白圖標
                self.root.iconphoto(False, tk.PhotoImage(width=1, height=1))
        except:
            pass
            
    def get_raw_icon_data(self):
        """獲取原始圖標二進制數據"""
        try:
            # 嘗試多種可能的路徑
            possible_paths = [
                os.path.join("resources", "chronohelper.ico"),
                os.path.join(os.path.dirname(sys.executable), "resources", "chronohelper.ico"),
                os.path.join(os.path.dirname(__file__), "..", "resources", "chronohelper.ico"),
                # 對於PyInstaller打包環境
                os.path.join(sys._MEIPASS, "resources", "chronohelper.ico") if hasattr(sys, "_MEIPASS") else None
            ]
            
            # 過濾掉None值
            possible_paths = [p for p in possible_paths if p]
            
            # 嘗試所有可能的路徑
            for path in possible_paths:
                if os.path.exists(path):
                    with open(path, 'rb') as f:
                        return f.read()
                    
            # 如果找不到圖標，返回None
            return None
        except Exception as e:
            self.logger.log(f"讀取圖標數據失敗: {str(e)}")
            return None
            
    def get_icon_data(self):
        """獲取圖標PhotoImage對象"""
        try:
            # 嘗試讀取PNG圖標 (對Tkinter PhotoImage更友好)
            possible_paths = [
                os.path.join("resources", "chronohelper.png"),
                os.path.join(os.path.dirname(sys.executable), "resources", "chronohelper.png"),
                os.path.join(os.path.dirname(__file__), "..", "resources", "chronohelper.png"),
                # 對於PyInstaller打包環境
                os.path.join(sys._MEIPASS, "resources", "chronohelper.png") if hasattr(sys, "_MEIPASS") else None
            ]
            
            # 過濾掉None值
            possible_paths = [p for p in possible_paths if p]
            
            # 嘗試所有可能的路徑
            for path in possible_paths:
                if os.path.exists(path):
                    self.logger.log(f"使用PNG圖標: {path}")
                    return tk.PhotoImage(file=path)
                    
            # 如果找不到PNG圖標，嘗試在內存中創建一個圖標
            self.logger.log("創建默認圖標")
            return self.create_default_icon()
        except Exception as e:
            self.logger.log(f"載入圖標失敗: {str(e)}")
            return None
            
    def create_default_icon(self):
        """創建一個簡單的默認圖標"""
        try:
            # 創建一個32x32的圖標
            icon = tk.PhotoImage(width=32, height=32)
            
            # 藍色背景
            for y in range(32):
                for x in range(32):
                    # 創建圓形
                    dist = ((x-16)**2 + (y-16)**2)**0.5
                    if dist <= 16:  # 在圓內
                        icon.put("#3498db", (x, y))  # 藍色
                    
            # 返回創建的圖標
            return icon
        except:
            # 如果圖標創建失敗，返回None
            return None

    def on_close(self):
        """處理應用程式關閉"""
        try:
            self.logger.log("正在關閉應用程式...")
            
            # 停止調度器
            if hasattr(self, 'scheduler'):
                self.scheduler.stop()
                self.logger.log("調度器已停止")
            
            # 停止所有網絡檢測操作
            if hasattr(self, 'network_utils'):
                self.network_utils.shutdown()
                
            # 保存所有設定和任務
            if hasattr(self, 'file_handler'):
                self.save_cookies()
                self.file_handler.save_settings(self.settings)
                self.file_handler.save_tasks(self.tasks)
                self.logger.log("設定和任務已保存")
            
            # 清理其他資源
            self.logger.log("ChronoHelper 已關閉")
        except Exception as e:
            # 發生錯誤時也確保應用關閉
            print(f"關閉時出錯: {str(e)}")
        finally:
            # 銷毀窗口並退出
            self.root.destroy()

    def update_system_stats(self):
        """更新系統狀態統計信息"""
        if not hasattr(self, 'scheduler') or not self.root:
            return

        # 獲取調度器狀態
        scheduler_status = "運行中" if self.scheduler.running else "停止"
        self.scheduler_status_var.set(scheduler_status)
        
        # 更新調度器狀態指示器顏色
        if scheduler_status == "運行中":
            self.scheduler_indicator.config(fg=COLORS["progress_done"])  # 綠色
        else:
            self.scheduler_indicator.config(fg=COLORS["warning"])  # 紅色
        
        # 對任務進行統計
        total_tasks = len(self.tasks)
        
        if total_tasks > 0:
            today = datetime.datetime.now().strftime("%Y-%m-%d")
            today_tasks = [t for t in self.tasks if t.date == today]
            active_tasks = len(today_tasks)
            
            # 計算今日已完成和待執行任務
            completed_tasks = len([t for t in today_tasks if getattr(t, 'sign_in_done', False) and getattr(t, 'sign_out_done', False)])
            pending_tasks = active_tasks - completed_tasks
            
            # 更新任務統計信息
            self.task_stats_var.set(f"總共 {total_tasks} | 今日 {active_tasks} | 已完成 {completed_tasks}")
        else:
            # 沒有任務
            self.task_stats_var.set("總共 0 | 今日 0 | 已完成 0")
        
        # 確保調度器的執行統計數據可用
        stats = getattr(self.scheduler, 'execution_stats', {})
        if not stats:
            stats = {
                "total_executions": 0,
                "successful_sign_ins": 0,
                "successful_sign_outs": 0,
                "failed_sign_ins": 0,
                "failed_sign_outs": 0,
                "last_success_time": None
            }
            # 如果調度器沒有統計數據，賦值一個
            if hasattr(self.scheduler, 'execution_stats'):
                self.scheduler.execution_stats = stats
        
        # 獲取統計數據
        sign_in_success = stats.get("successful_sign_ins", 0)
        sign_out_success = stats.get("successful_sign_outs", 0)
        failed = stats.get("failed_sign_ins", 0) + stats.get("failed_sign_outs", 0)
        
        # 更新顯示格式
        self.sign_stats_var.set(f"簽到 {sign_in_success} | 簽退 {sign_out_success} | 失敗 {failed}")
        
        # 更新最後成功時間
        last_success = stats.get("last_success_time")
        if last_success:
            last_time_str = last_success.strftime("%H:%M:%S")
            self.last_update_var.set(last_time_str)
        else:
            self.last_update_var.set("從未")
        
        # 定期更新狀態統計
        self.root.after(5000, self.update_system_stats)

    def reset_statistics(self):
        """重置統計數據"""
        if hasattr(self, 'scheduler') and hasattr(self.scheduler, 'execution_stats'):
            # 詢問用戶是否確定重置
            if messagebox.askyesno("確認操作", "確定要重置所有統計數據嗎？", parent=self.root):
                # 保存最後操作時間和總執行次數
                last_time = datetime.datetime.now()
                old_stats = self.scheduler.execution_stats or {}
                
                # 重置統計數據
                self.scheduler.execution_stats = {
                    "total_executions": 0,
                    "successful_sign_ins": 0,
                    "successful_sign_outs": 0,
                    "failed_sign_ins": 0,
                    "failed_sign_outs": 0,
                    "last_success_time": last_time  # 使用當前時間作為最後更新時間
                }
                
                # 立即更新統計面板
                self.update_system_stats()
                
                # 記錄操作
                self.logger.log("已重置所有統計數據")
                
                # 顯示通知
                self.status_var.set("統計數據已重置")
        else:
            messagebox.showwarning("操作失敗", "無法重置統計數據，請確保系統正常運行", parent=self.root)

class ToolTip:
    """工具提示類，顯示懸停提示"""
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tip_window = None
        self.widget.bind("<Enter>", self.show_tip)
        self.widget.bind("<Leave>", self.hide_tip)
    
    def show_tip(self, event=None):
        """顯示提示窗口"""
        if self.tip_window or not self.text:
            return
        
        x, y, _, _ = self.widget.bbox("insert")
        x += self.widget.winfo_rootx() + 25
        y += self.widget.winfo_rooty() + 25
        
        # 創建工具提示窗口
        self.tip_window = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.wm_geometry(f"+{x}+{y}")
        
        label = tk.Label(tw, text=self.text, justify=tk.LEFT,
                      background="#ffffe0", relief=tk.SOLID, borderwidth=1,
                      font=("Arial", "9", "normal"))
        label.pack(padx=3, pady=3)
    
    def hide_tip(self, event=None):
        """隱藏提示窗口"""
        tw = self.tip_window
        self.tip_window = None
        if tw:
            tw.destroy()

