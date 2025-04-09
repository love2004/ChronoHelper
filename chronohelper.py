import tkinter as tk
from tkinter import ttk, messagebox, simpledialog, filedialog
import schedule
import time
import json
import os
import threading
import datetime
import requests
from requests.exceptions import RequestException
from tkinter import scrolledtext
import uuid
import webbrowser
from PIL import Image, ImageTk  # 需要安裝: pip install pillow
import re
from bs4 import BeautifulSoup  # 需要安裝: pip install beautifulsoup4
import socket
import pickle
import urllib3
import base64
import hashlib
from cryptography.fernet import Fernet

# 定義顏色方案
COLORS = {
    "primary": "#3498db",     # 主色調
    "primary_dark": "#2980b9", # 深主色調
    "secondary": "#2ecc71",   # 次色調
    "warning": "#e74c3c",     # 警告色
    "warning_dark": "#c0392b", # 深警告色
    "background": "#f5f6fa",  # 背景色
    "text": "#2d3436",        # 文字色
    "light_text": "#7f8c8d",  # 淺色文字
    "card": "#ffffff",        # 卡片背景
    "border": "#dfe6e9"       # 邊框色
}

# 全局設定
APP_SETTINGS = {
    "global_notify": True,    # 全局通知開關
    "check_interval": 30,     # 任務檢查間隔（秒）
    "api_url": "",            # API URL
    "login_url": "https://adm_acc.dyu.edu.tw/entrance/save_id.php", # 登入URL
    "sign_in_url": "https://adm_acc.dyu.edu.tw/budget/prj_epfee/kernel/kernel_prj_carddata_edit.php?page=NDgy", # 簽到URL
    "sign_out_url": "https://adm_acc.dyu.edu.tw/budget/prj_epfee/kernel/kernel_prj_carddata_edit.php?page=NDgy", # 簽退URL
    "username": "",           # 用戶名
    "password": "",           # 密碼
    "name": "",               # 用戶姓名
    "auto_start": True,       # 自動啟動調度器
    "default_sign_in": "09:00", # 默認簽到時間
    "default_sign_out": "18:00" # 默認簽退時間
}

class SettingsEncryption:
    """設定檔加密管理"""
    
    @staticmethod
    def get_encryption_key(salt=None):
        """生成或獲取加密密鑰"""
        key_file = "chronohelper.key"
        
        if os.path.exists(key_file):
            # 讀取現有密鑰
            with open(key_file, 'rb') as f:
                key = f.read()
        else:
            # 創建新密鑰
            if salt is None:
                salt = os.urandom(16)
            
            # 使用機器特有的識別信息生成密鑰
            machine_info = f"{os.getlogin()}_{os.name}"
            key_base = hashlib.pbkdf2_hmac(
                'sha256', 
                machine_info.encode(), 
                salt, 
                100000
            )
            
            # 轉換為Fernet可用的格式
            key = base64.urlsafe_b64encode(key_base)
            
            # 保存密鑰
            with open(key_file, 'wb') as f:
                f.write(key)
        
        return key
    
    @staticmethod
    def encrypt_data(data):
        """加密數據"""
        if not isinstance(data, str):
            return data
        
        key = SettingsEncryption.get_encryption_key()
        cipher = Fernet(key)
        return cipher.encrypt(data.encode()).decode()
    
    @staticmethod
    def decrypt_data(encrypted_data):
        """解密數據"""
        if not isinstance(encrypted_data, str):
            return encrypted_data
        
        try:
            key = SettingsEncryption.get_encryption_key()
            cipher = Fernet(key)
            return cipher.decrypt(encrypted_data.encode()).decode()
        except Exception:
            return encrypted_data  # 如果解密失敗，返回原數據

class Task:
    def __init__(self, name, date, sign_in_time, sign_out_time, notify=True, task_id=None):
        self.id = task_id if task_id else str(uuid.uuid4())
        self.name = name
        self.date = date  # 格式: YYYY-MM-DD
        self.sign_in_time = sign_in_time  # 格式: HH:MM
        self.sign_out_time = sign_out_time  # 格式: HH:MM
        self.notify = notify
        self.sign_in_done = False
        self.sign_out_done = False
        # 新增屬性用於記錄環境限制狀態
        self.campus_restricted = False
        self.last_attempt_time = None  # 上次嘗試的時間
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'date': self.date,
            'sign_in_time': self.sign_in_time,
            'sign_out_time': self.sign_out_time,
            'notify': self.notify,
            'sign_in_done': self.sign_in_done,
            'sign_out_done': self.sign_out_done,
            'campus_restricted': getattr(self, 'campus_restricted', False),
            'last_attempt_time': getattr(self, 'last_attempt_time', None)
        }
    
    @classmethod
    def from_dict(cls, data):
        task = cls(
            name=data['name'],
            date=data['date'],
            sign_in_time=data['sign_in_time'],
            sign_out_time=data['sign_out_time'],
            notify=data.get('notify', True),
            task_id=data['id']
        )
        task.sign_in_done = data.get('sign_in_done', False)
        task.sign_out_done = data.get('sign_out_done', False)
        task.campus_restricted = data.get('campus_restricted', False)
        task.last_attempt_time = data.get('last_attempt_time', None)
        return task


class ModernButton(tk.Button):
    """現代化按鈕，帶有懸停效果"""
    def __init__(self, master=None, **kwargs):
        bg = kwargs.pop('bg', COLORS["primary"])
        fg = kwargs.pop('fg', 'white')
        activebackground = kwargs.pop('activebackground', COLORS["primary_dark"])
        
        # 保存原始顏色用於恢復
        self.orig_bg = bg
        self.orig_active_bg = activebackground
        
        # 額外的屬性用於控制懸停行為
        self.keep_color = kwargs.pop('keep_color', False)
        
        activeforeground = kwargs.pop('activeforeground', 'white')
        bd = kwargs.pop('bd', 0)
        relief = kwargs.pop('relief', tk.FLAT)
        padx = kwargs.pop('padx', 15)
        pady = kwargs.pop('pady', 8)
        
        super().__init__(master, bg=bg, fg=fg, activebackground=activebackground,
                         activeforeground=activeforeground, bd=bd, relief=relief,
                         padx=padx, pady=pady, **kwargs)
        
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)
    
    def _on_enter(self, e):
        if not self.keep_color:
            if self.orig_bg == COLORS["warning"]:
                self.config(bg=COLORS["warning_dark"])
            else:
                self.config(bg=COLORS["primary_dark"])
    
    def _on_leave(self, e):
        if not self.keep_color:
            self.config(bg=self.orig_bg)


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
        
        if task_date < today:
            return "已過期", "#95a5a6"
        elif task_date > today:
            return "等待中", "#3498db"
        else:
            if self.task.sign_in_done and self.task.sign_out_done:
                return "已完成", "#2ecc71"
            elif self.task.sign_in_done:
                return "已簽到", "#f39c12"
            else:
                now = datetime.datetime.now().strftime("%H:%M")
                if now < self.task.sign_in_time:
                    return "今日待執行", "#3498db"
                else:
                    return "待處理", "#e74c3c"
    
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


class NotificationWindow(tk.Toplevel):
    """自定義通知窗口"""
    def __init__(self, title, message, duration=5000):
        super().__init__()
        self.title("")
        self.overrideredirect(True)  # 無邊框窗口
        self.geometry("300x120")  # 增加高度以容納更多文本
        self.configure(bg=COLORS["card"], bd=1, relief=tk.SOLID)
        self.attributes("-topmost", True)  # 置頂顯示
        
        # 創建主框架以確保正確排列
        main_frame = tk.Frame(self, bg=COLORS["card"])
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 頭部區域
        header_frame = tk.Frame(main_frame, bg=COLORS["primary"], height=25)
        header_frame.pack(fill=tk.X)
        
        tk.Label(header_frame, text=title, fg="white", bg=COLORS["primary"], 
                 font=("Arial", 10, "bold")).pack(side=tk.LEFT, padx=10, pady=3)
        
        close_btn = tk.Label(header_frame, text="×", fg="white", bg=COLORS["primary"], 
                           font=("Arial", 12, "bold"))
        close_btn.pack(side=tk.RIGHT, padx=10, pady=2)
        close_btn.bind("<Button-1>", lambda e: self.destroy())
        
        # 內容區域
        content_frame = tk.Frame(main_frame, bg=COLORS["card"], padx=10, pady=15)
        content_frame.pack(fill=tk.BOTH, expand=True)
        
        message_label = tk.Label(content_frame, text=message, bg=COLORS["card"], fg=COLORS["text"], 
                 wraplength=280, justify=tk.LEFT)
        message_label.pack(fill=tk.BOTH, expand=True)
        
        # 放在螢幕右下角
        self.update_idletasks()
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        x = screen_width - 320
        y = screen_height - 140  # 調整位置以適應更高的窗口
        self.geometry(f"+{x}+{y}")
        
        # 設置自動關閉
        self.after(duration, self.destroy)


class SettingsDialog:
    """設定對話框"""
    def __init__(self, parent, settings):
        self.result = None
        self.settings = settings.copy()
        
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("ChronoHelper - 設定")
        self.dialog.geometry("500x520")  # 增加初始高度
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
        
        # 設定內容（使用Notebook選項卡）
        notebook_frame = tk.Frame(main_frame, bg=COLORS["card"], padx=15, pady=15)
        notebook_frame.pack(fill=tk.BOTH, expand=True)
        
        notebook = ttk.Notebook(notebook_frame)
        notebook.pack(fill=tk.BOTH, expand=True)
        
        # 基本設定選項卡
        general_frame = tk.Frame(notebook, bg=COLORS["card"], padx=15, pady=15)
        notebook.add(general_frame, text="基本設定")
        
        # API設定選項卡
        api_frame = tk.Frame(notebook, bg=COLORS["card"], padx=15, pady=15)
        notebook.add(api_frame, text="API設定")
        
        # 用戶資訊選項卡
        user_frame = tk.Frame(notebook, bg=COLORS["card"], padx=15, pady=15)
        notebook.add(user_frame, text="用戶資訊")
        
        # 預設時間選項卡
        time_frame = tk.Frame(notebook, bg=COLORS["card"], padx=15, pady=15)
        notebook.add(time_frame, text="預設時間")
        
        # 基本設定內容
        self.notify_var = tk.BooleanVar(value=settings.get("global_notify", True))
        tk.Label(general_frame, text="通知設定", font=("Arial", 11, "bold"), 
                 bg=COLORS["card"], fg=COLORS["text"]).grid(row=0, column=0, sticky=tk.W, pady=(0,10))
        ttk.Checkbutton(general_frame, text="啟用全局通知（影響所有任務）", 
                       variable=self.notify_var).grid(row=1, column=0, sticky=tk.W, padx=15)
        
        self.autostart_var = tk.BooleanVar(value=settings.get("auto_start", True))
        ttk.Checkbutton(general_frame, text="啟動程式時自動開始檢查任務", 
                       variable=self.autostart_var).grid(row=2, column=0, sticky=tk.W, padx=15, pady=10)
        
        tk.Label(general_frame, text="任務檢查間隔", font=("Arial", 11, "bold"), 
                 bg=COLORS["card"], fg=COLORS["text"]).grid(row=3, column=0, sticky=tk.W, pady=(10,5))
        
        interval_frame = tk.Frame(general_frame, bg=COLORS["card"])
        interval_frame.grid(row=4, column=0, sticky=tk.W, padx=15)
        
        self.interval_var = tk.IntVar(value=settings.get("check_interval", 30))
        ttk.Spinbox(interval_frame, from_=10, to=300, increment=10, 
                   textvariable=self.interval_var, width=5).pack(side=tk.LEFT)
        tk.Label(interval_frame, text="秒", bg=COLORS["card"]).pack(side=tk.LEFT, padx=5)
        
        # API設定內容
        tk.Label(api_frame, text="API連接設定", font=("Arial", 11, "bold"), 
                 bg=COLORS["card"], fg=COLORS["text"]).grid(row=0, column=0, columnspan=2, sticky=tk.W, pady=(0,15))
        
        tk.Label(api_frame, text="登入URL:", bg=COLORS["card"]).grid(row=1, column=0, sticky=tk.W, padx=(15,5), pady=5)
        self.login_url_var = tk.StringVar(value=settings.get("login_url", ""))
        ttk.Entry(api_frame, textvariable=self.login_url_var, width=40).grid(row=1, column=1, sticky=tk.W, pady=5)
        
        tk.Label(api_frame, text="API基礎URL:", bg=COLORS["card"]).grid(row=2, column=0, sticky=tk.W, padx=(15,5), pady=5)
        self.api_url_var = tk.StringVar(value=settings.get("api_url", ""))
        ttk.Entry(api_frame, textvariable=self.api_url_var, width=40).grid(row=2, column=1, sticky=tk.W, pady=5)
        
        tk.Label(api_frame, text="簽到URL:", bg=COLORS["card"]).grid(row=3, column=0, sticky=tk.W, padx=(15,5), pady=5)
        self.sign_in_url_var = tk.StringVar(value=settings.get("sign_in_url", ""))
        ttk.Entry(api_frame, textvariable=self.sign_in_url_var, width=40).grid(row=3, column=1, sticky=tk.W, pady=5)
        
        tk.Label(api_frame, text="簽退URL:", bg=COLORS["card"]).grid(row=4, column=0, sticky=tk.W, padx=(15,5), pady=5)
        self.sign_out_url_var = tk.StringVar(value=settings.get("sign_out_url", ""))
        ttk.Entry(api_frame, textvariable=self.sign_out_url_var, width=40).grid(row=4, column=1, sticky=tk.W, pady=5)
        
        tk.Label(api_frame, text="用戶名:", bg=COLORS["card"]).grid(row=5, column=0, sticky=tk.W, padx=(15,5), pady=5)
        self.username_var = tk.StringVar(value=settings.get("username", ""))
        ttk.Entry(api_frame, textvariable=self.username_var, width=30).grid(row=5, column=1, sticky=tk.W, pady=5)
        
        tk.Label(api_frame, text="密碼:", bg=COLORS["card"]).grid(row=6, column=0, sticky=tk.W, padx=(15,5), pady=5)
        self.password_var = tk.StringVar(value=settings.get("password", ""))
        ttk.Entry(api_frame, textvariable=self.password_var, show="*", width=30).grid(row=6, column=1, sticky=tk.W, pady=5)
        
        # 測試連接按鈕和測試登入按鈕
        button_frame = tk.Frame(api_frame, bg=COLORS["card"])
        button_frame.grid(row=7, column=1, sticky=tk.W, pady=15)
        
        test_connection_button = ModernButton(button_frame, text="測試連接", 
                                            command=self.test_connection, padx=10, pady=5)
        test_connection_button.pack(side=tk.LEFT, padx=(0,10))
        
        test_login_button = ModernButton(button_frame, text="測試登入", 
                                       command=self.test_login, padx=10, pady=5)
        test_login_button.pack(side=tk.LEFT)
        
        # 用戶資訊內容
        tk.Label(user_frame, text="個人資料", font=("Arial", 11, "bold"), 
                 bg=COLORS["card"], fg=COLORS["text"]).grid(row=0, column=0, columnspan=3, sticky=tk.W, pady=(0,15))
        
        tk.Label(user_frame, text="姓名:", bg=COLORS["card"]).grid(row=1, column=0, sticky=tk.W, padx=(15,5), pady=5)
        self.name_var = tk.StringVar(value=settings.get("name", ""))
        ttk.Entry(user_frame, textvariable=self.name_var, width=15).grid(row=1, column=1, sticky=tk.W, pady=5)
        
        tk.Label(user_frame, text="(用於確認登入狀態)", bg=COLORS["card"], fg=COLORS["light_text"]).grid(
            row=1, column=2, sticky=tk.W, padx=5, pady=5)
        
        # 預設時間設定
        tk.Label(time_frame, text="預設簽到簽退時間", font=("Arial", 11, "bold"), 
                 bg=COLORS["card"], fg=COLORS["text"]).grid(row=0, column=0, columnspan=2, sticky=tk.W, pady=(0,15))
        
        tk.Label(time_frame, text="預設簽到時間:", bg=COLORS["card"]).grid(row=1, column=0, sticky=tk.W, padx=(15,5), pady=5)
        
        # 簽到時間選擇器
        sign_in_frame = tk.Frame(time_frame, bg=COLORS["card"])
        sign_in_frame.grid(row=1, column=1, sticky=tk.W, pady=5)
        
        self.default_sign_in_hour = tk.StringVar(value=settings.get("default_sign_in", "09:00").split(":")[0])
        self.default_sign_in_minute = tk.StringVar(value=settings.get("default_sign_in", "09:00").split(":")[1])
        
        hours = [f"{h:02d}" for h in range(24)]
        minutes = [f"{m:02d}" for m in range(60)]
        
        ttk.Combobox(sign_in_frame, textvariable=self.default_sign_in_hour, 
                    values=hours, width=3).pack(side=tk.LEFT)
        tk.Label(sign_in_frame, text=":", bg=COLORS["card"]).pack(side=tk.LEFT)
        ttk.Combobox(sign_in_frame, textvariable=self.default_sign_in_minute, 
                    values=minutes, width=3).pack(side=tk.LEFT)
        
        # 簽退時間選擇器
        tk.Label(time_frame, text="預設簽退時間:", bg=COLORS["card"]).grid(row=2, column=0, sticky=tk.W, padx=(15,5), pady=5)
        
        sign_out_frame = tk.Frame(time_frame, bg=COLORS["card"])
        sign_out_frame.grid(row=2, column=1, sticky=tk.W, pady=5)
        
        self.default_sign_out_hour = tk.StringVar(value=settings.get("default_sign_out", "18:00").split(":")[0])
        self.default_sign_out_minute = tk.StringVar(value=settings.get("default_sign_out", "18:00").split(":")[1])
        
        ttk.Combobox(sign_out_frame, textvariable=self.default_sign_out_hour, 
                    values=hours, width=3).pack(side=tk.LEFT)
        tk.Label(sign_out_frame, text=":", bg=COLORS["card"]).pack(side=tk.LEFT)
        ttk.Combobox(sign_out_frame, textvariable=self.default_sign_out_minute, 
                    values=minutes, width=3).pack(side=tk.LEFT)
        
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
        
        # 設置最小窗口大小，確保按鈕始終可見
        self.dialog.update_idletasks()
        self.dialog.minsize(500, 400)
        
        self.dialog.protocol("WM_DELETE_WINDOW", self.on_cancel)
        self.dialog.wait_visibility()
        self.dialog.focus_set()
        self.dialog.wait_window()
    
    def test_connection(self):
        api_url = self.api_url_var.get().strip()
        
        if not api_url:
            messagebox.showwarning("警告", "請輸入API URL", parent=self.dialog)
            return
        
        try:
            self.dialog.config(cursor="wait")
            self.dialog.update()
            
            response = requests.get(api_url, timeout=10)
            
            if response.status_code == 200:
                messagebox.showinfo("連接成功", f"成功連接到API服務器", parent=self.dialog)
            else:
                messagebox.showwarning("連接警告", f"連接返回非200狀態碼: {response.status_code}", parent=self.dialog)
        except Exception as e:
            messagebox.showerror("連接失敗", f"無法連接到API服務器: {str(e)}", parent=self.dialog)
        finally:
            self.dialog.config(cursor="")
            self.dialog.update()
    
    def test_login(self):
        """測試大葉大學系統登入"""
        username = self.username_var.get().strip()
        password = self.password_var.get().strip()
        
        if not username or not password:
            messagebox.showwarning("警告", "請輸入用戶名和密碼", parent=self.dialog)
            return
        
        # 創建臨時測試對象
        try:
            self.dialog.config(cursor="wait")
            self.dialog.update()
            
            session = requests.Session()
            login_url = self.login_url_var.get().strip() or "https://adm_acc.dyu.edu.tw/entrance/save_id.php"
            
            login_data = {
                "login_id": username,
                "login_pwd": password,
                "login_agent": "0",
                "login_ent": "15",
                "login_page": ""
            }
            
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
                "Content-Type": "application/x-www-form-urlencoded"
            }
            
            response = session.post(login_url, data=login_data, headers=headers, timeout=30)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                status_span = soup.select_one('span.status')
                
                if status_span:
                    # 提取姓名 (從 "楊智景 您好" 格式中提取姓名)
                    status_text = status_span.get_text().strip()
                    name_match = re.match(r'([^\s]+)\s*您好', status_text)
                    
                    if name_match:
                        actual_name = name_match.group(1).strip()
                        result = messagebox.askquestion(
                            "登入成功", 
                            f"成功登入系統！\n\n檢測到用戶姓名: {actual_name}\n\n是否將此姓名更新到設定中？",
                            parent=self.dialog
                        )
                        
                        if result == "yes":
                            self.name_var.set(actual_name)
                    else:
                        messagebox.showinfo(
                            "登入結果", 
                            "已連接系統，但無法自動檢測用戶姓名。\n請手動確認登入狀態。",
                            parent=self.dialog
                        )
                else:
                    # 檢查特定錯誤
                    if "密碼錯誤" in response.text or "帳號不存在" in response.text:
                        messagebox.showerror("登入失敗", "帳號或密碼錯誤", parent=self.dialog)
                    elif "登出" in response.text:
                        messagebox.showinfo(
                            "登入結果", 
                            "登入似乎成功，但無法檢測用戶信息。\n頁面結構可能已變更。",
                            parent=self.dialog
                        )
                    else:
                        messagebox.showwarning(
                            "未知結果", 
                            "無法確定登入結果。請手動檢查帳號信息。",
                            parent=self.dialog
                        )
            else:
                messagebox.showerror(
                    "連接錯誤", 
                    f"連接服務器失敗，狀態碼: {response.status_code}",
                    parent=self.dialog
                )
        
        except RequestException as e:
            self.log(f"登入過程中發生網絡錯誤: {str(e)}")
            messagebox.showerror("網絡錯誤", f"連接服務器失敗: {str(e)}", parent=self.dialog)
        except Exception as e:
            self.log(f"登入過程中發生未知錯誤: {str(e)}")
            import traceback
            self.log(traceback.format_exc())
            messagebox.showerror("未知錯誤", f"測試過程中發生錯誤: {str(e)}", parent=self.dialog)
        finally:
            # 確保無論何種情況都會重置游標狀態
            self.dialog.config(cursor="")
            self.dialog.update()
    
    def on_save(self):
        # 更新設定
        self.settings["global_notify"] = self.notify_var.get()
        self.settings["auto_start"] = self.autostart_var.get()
        self.settings["check_interval"] = self.interval_var.get()
        self.settings["api_url"] = self.api_url_var.get().strip()
        self.settings["login_url"] = self.login_url_var.get().strip() or "https://adm_acc.dyu.edu.tw/entrance/save_id.php"
        self.settings["sign_in_url"] = self.sign_in_url_var.get().strip() or "https://adm_acc.dyu.edu.tw/budget/prj_epfee/kernel/kernel_prj_carddata_edit.php?page=NDgy"
        self.settings["sign_out_url"] = self.sign_out_url_var.get().strip() or "https://adm_acc.dyu.edu.tw/budget/prj_epfee/kernel/kernel_prj_carddata_edit.php?page=NDgy"
        self.settings["username"] = self.username_var.get().strip()
        self.settings["password"] = self.password_var.get().strip()
        self.settings["name"] = self.name_var.get().strip()
        
        # 更新預設時間
        self.settings["default_sign_in"] = f"{self.default_sign_in_hour.get()}:{self.default_sign_in_minute.get()}"
        self.settings["default_sign_out"] = f"{self.default_sign_out_hour.get()}:{self.default_sign_out_minute.get()}"
        
        self.result = self.settings
        self.dialog.destroy()
    
    def on_cancel(self):
        self.dialog.destroy()
    
    def log(self, message):
        """在測試登入時記錄日誌"""
        print(f"[設定] {message}")  # 簡單輸出到控制台


class ChronoHelper:
    def __init__(self, root):
        self.root = root
        self.root.title("ChronoHelper - 時間助手")
        self.root.geometry("950x650")
        self.root.configure(bg=COLORS["background"])
        
        # 設置應用圖標的自定義文字版本
        self.root.iconphoto(False, tk.PhotoImage(width=1, height=1))
        
        self.tasks = []
        self.config_file = "chronohelper_tasks.json"
        self.settings_file = "chronohelper_settings.json"
        self.log_file = "chronohelper_log.txt"
        self.cookie_file = "chronohelper_cookies.json"
        
        # 會話管理
        self.session = requests.Session()
        # 禁用SSL證書驗證
        self.session.verify = False
        
        self.login_status = False
        self.last_login_time = None
        self.login_valid_time = 270  # Cookie有效時間(秒)，設為4.5分鐘（5分鐘會話 - 30秒緩衝）
        
        # 網絡狀態屬性
        self.is_campus_network = False
        self.current_ip = "未知"
        
        # 新增：上次記錄的網絡環境日誌時間和狀態
        self.last_network_log_time = None
        self.last_network_log_status = None
        
        # 載入設定
        self.settings = self.load_settings()
        
        # 先創建界面元素
        self.create_widgets()
        
        # 載入任務和日誌
        self.load_tasks()
        self.refresh_task_list()
        self.load_log()
        
        # 載入已保存的Cookie
        self.load_cookies()
        
        # 啟動調度線程
        self.scheduler_running = True
        self.scheduler_thread = threading.Thread(target=self.scheduler_loop)
        self.scheduler_thread.daemon = True
        self.scheduler_thread.start()
    
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
        settings_button = ModernButton(header_frame, text="設定", 
                                    command=self.open_settings, bg=COLORS["primary"],
                                    activebackground=COLORS["primary_dark"])
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
        
        # 日誌區域
        log_label = tk.Label(right_frame, text="執行日誌", font=("Arial", 14, "bold"), 
                           bg=COLORS["background"], fg=COLORS["text"])
        log_label.pack(anchor=tk.W, pady=(0, 10))
        
        log_frame = tk.Frame(right_frame, bg=COLORS["card"], bd=1, relief=tk.SOLID)
        log_frame.pack(fill=tk.BOTH, expand=True)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, wrap=tk.WORD, font=("Arial", 9))
        self.log_text.pack(fill=tk.BOTH, expand=True, padx=1, pady=1)
        self.log_text.config(bg=COLORS["card"], fg=COLORS["text"])
        
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
        
        # 右下角信息
        info_label = tk.Label(status_frame, text="ChronoHelper v1.0", 
                            fg="white", bg=COLORS["primary_dark"], font=("Arial", 10))
        info_label.pack(side=tk.RIGHT)
        
        # 設置任務畫布的捲動功能
        self.tasks_frame.bind("<Configure>", self.on_frame_configure)
        self.tasks_canvas.bind("<Configure>", self.on_canvas_configure)
        
        # 在初始化完成後加載設定並檢測網絡
        self.root.after(1000, self.initial_network_check)
    
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
    
    def load_settings(self):
        if os.path.exists(self.settings_file):
            try:
                with open(self.settings_file, 'r', encoding='utf-8') as f:
                    settings = json.load(f)
                    
                    # 解密敏感數據
                    try:
                        if 'username' in settings and settings['username']:
                            settings['username'] = SettingsEncryption.decrypt_data(settings['username'])
                        if 'password' in settings and settings['password']:
                            settings['password'] = SettingsEncryption.decrypt_data(settings['password'])
                    except Exception as e:
                        self.log(f"解密設定失敗: {str(e)}")
                    
                    return settings
            except Exception as e:
                print(f"載入設定失敗: {str(e)}")
        return APP_SETTINGS.copy()

    def save_settings(self):
        try:
            # 創建設定的副本
            settings_to_save = self.settings.copy()
            
            # 加密敏感數據
            if 'username' in settings_to_save and settings_to_save['username']:
                settings_to_save['username'] = SettingsEncryption.encrypt_data(settings_to_save['username'])
            if 'password' in settings_to_save and settings_to_save['password']:
                settings_to_save['password'] = SettingsEncryption.encrypt_data(settings_to_save['password'])
            
            with open(self.settings_file, 'w', encoding='utf-8') as f:
                json.dump(settings_to_save, f, indent=2)
        except Exception as e:
            print(f"保存設定失敗: {str(e)}")
    
    def open_settings(self):
        dialog = SettingsDialog(self.root, self.settings)
        if dialog.result:
            # 更新設定
            old_interval = self.settings.get("check_interval", 30)
            self.settings = dialog.result
            self.save_settings()
            
            # 如果檢查間隔有變更，重啟調度線程
            if old_interval != self.settings.get("check_interval", 30):
                self.scheduler_running = False
                if self.scheduler_thread.is_alive():
                    self.scheduler_thread.join(1)
                
                self.scheduler_running = True
                self.scheduler_thread = threading.Thread(target=self.scheduler_loop)
                self.scheduler_thread.daemon = True
                self.scheduler_thread.start()
            
            self.log("已更新應用程式設定")
            self.show_notification("設定已更新", "已成功更新ChronoHelper設定")
    
    def load_tasks(self):
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    tasks_data = json.load(f)
                    self.tasks = [Task.from_dict(task_data) for task_data in tasks_data]
            except Exception as e:
                self.log(f"載入任務失敗: {str(e)}")
    
    def save_tasks(self):
        try:
            tasks_data = [task.to_dict() for task in self.tasks]
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(tasks_data, f, indent=2)
            self.refresh_task_list()
        except Exception as e:
            self.log(f"保存任務失敗: {str(e)}")
    
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
            self.tasks.append(new_task)
            self.save_tasks()
            self.log(f"新增任務: {name}, 日期: {date}, 時間: {sign_in}-{sign_out}")
            self.show_notification("任務已建立", f"已成功新增「{name}」任務")
    
    def edit_task(self, task):
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
            self.log(f"編輯任務: {name}, 日期: {date}, 時間: {sign_in}-{sign_out}")
            self.show_notification("任務已更新", f"已成功更新「{name}」任務")
    
    def delete_task(self, task):
        if messagebox.askyesno("確認刪除", f"確定要刪除「{task.name}」任務嗎？", parent=self.root):
            self.tasks.remove(task)
            self.save_tasks()
            self.log(f"刪除任務: {task.name}")
            self.show_notification("任務已刪除", f"已成功刪除「{task.name}」任務")
    
    def load_cookies(self):
        """載入保存的Cookies"""
        if os.path.exists(self.cookie_file):
            try:
                with open(self.cookie_file, 'r', encoding='utf-8') as f:
                    cookies = json.load(f)
                    for cookie_dict in cookies:
                        self.session.cookies.set(**cookie_dict)
                    self.log("成功載入已保存的Cookie")
                    # 設置登入狀態，但需要驗證
                    self.login_status = True
                    self.last_login_time = datetime.datetime.now()
            except Exception as e:
                self.log(f"載入Cookie失敗: {str(e)}")
                self.login_status = False
    
    def save_cookies(self):
        """保存當前會話的Cookies"""
        try:
            cookies_list = []
            for cookie in self.session.cookies:
                cookie_dict = {
                    'name': cookie.name,
                    'value': cookie.value,
                    'domain': cookie.domain,
                    'path': cookie.path
                }
                cookies_list.append(cookie_dict)
                
            with open(self.cookie_file, 'w', encoding='utf-8') as f:
                json.dump(cookies_list, f)
            self.log("已保存Cookie")
        except Exception as e:
            self.log(f"保存Cookie失敗: {str(e)}")
    
    def login(self, force=False):
        """登入大葉大學系統並獲取Cookie
        
        Args:
            force: 是否強制重新登入，即使Cookie可能還有效
            
        Returns:
            bool: 登入是否成功
        """
        # 添加視覺反饋，使用狀態欄
        old_status = self.status_var.get()
        self.status_var.set("正在登入系統...")
        self.root.update_idletasks()  # 立即更新UI
        
        # 檢查登入狀態，如果已登入且Cookie未過期，則不需要再次登入
        if self.login_status and not force:
            if self.last_login_time:
                elapsed = (datetime.datetime.now() - self.last_login_time).total_seconds()
                if elapsed < self.login_valid_time:
                    self.log("使用現有會話，無需重新登入")
                    self.status_var.set(old_status)  # 還原狀態
                    return True
        
        # 從設定中獲取登入信息
        login_url = self.settings.get("login_url", "https://adm_acc.dyu.edu.tw/entrance/save_id.php")
        username = self.settings.get("username", "")
        password = self.settings.get("password", "")
        expected_name = self.settings.get("name", "")  # 從設定中獲取姓名
        
        if not username or not password:
            self.log("登入信息不完整，請在設定中配置用戶名和密碼")
            self.status_var.set("登入失敗，請在設定中配置用戶名和密碼")
            return False
        
        try:
            self.log(f"嘗試登入大葉大學系統")
            
            # 清除現有會話
            self.session = requests.Session()
            
            # 登入請求 - 使用x-www-form-urlencoded格式
            login_data = {
                "login_id": username,
                "login_pwd": password,
                "login_agent": "0",
                "login_ent": "15",
                "login_page": ""
            }
            
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
                "Content-Type": "application/x-www-form-urlencoded",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8"
            }
            
            # 發送登入請求
            response = self.session.post(login_url, data=login_data, headers=headers, timeout=30)
            
            # 檢查登入結果
            if response.status_code == 200:
                # 使用BeautifulSoup解析HTML
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # 尋找狀態元素
                status_span = soup.select_one('span.status')
                
                if status_span:
                    # 提取姓名 (從 "楊智景 您好" 格式中提取姓名)
                    status_text = status_span.get_text().strip()
                    name_match = re.match(r'([^\s]+)\s*您好', status_text)
                    
                    if name_match:
                        actual_name = name_match.group(1).strip()
                        self.log(f"檢測到登入用戶: {actual_name}")
                        
                        # 如果設定了預期姓名，則進行比對
                        if expected_name and expected_name.strip() != actual_name:
                            self.log(f"警告: 登入用戶名 '{actual_name}' 與設定的姓名 '{expected_name}' 不符")
                        
                        # 無論是否比對一致，都認為登入成功
                        self.login_status = True
                        self.last_login_time = datetime.datetime.now()
                        self.save_cookies()
                        
                        # 更新設定中的姓名，如果未設定
                        if not expected_name:
                            self.settings["name"] = actual_name
                            self.save_settings()
                            self.log(f"已自動更新設定中的姓名為: {actual_name}")
                        
                        self.status_var.set(old_status)  # 還原狀態
                        return True
                    else:
                        # 如果找不到姓名格式，但有status元素，可能頁面格式已變更
                        self.log(f"警告: 找到狀態元素但無法提取姓名, 內容: {status_text}")
                        
                        # 檢查是否有錯誤信息
                        if "密碼錯誤" in response.text or "帳號不存在" in response.text:
                            self.log("登入失敗: 帳號或密碼錯誤")
                            self.status_var.set("登入失敗，帳號或密碼錯誤")
                            return False
                        
                        # 假設登入成功，但格式已變更
                        self.login_status = True
                        self.last_login_time = datetime.datetime.now()
                        self.save_cookies()
                        self.status_var.set(old_status)  # 還原狀態
                        return True
                else:
                    # 檢查是否有錯誤信息
                    if "密碼錯誤" in response.text or "帳號不存在" in response.text:
                        self.log("登入失敗: 帳號或密碼錯誤")
                        self.status_var.set("登入失敗，帳號或密碼錯誤")
                        return False
                    
                    # 如果沒有找到status元素，檢查其他可能的登入成功標記
                    if "登出" in response.text and "changeEntrance.php" in response.text:
                        self.log("檢測到登入成功標記，但無法找到用戶姓名")
                        self.login_status = True
                        self.last_login_time = datetime.datetime.now()
                        self.save_cookies()
                        self.status_var.set(old_status)  # 還原狀態
                        return True
                    
                    self.log("無法確認登入狀態，請檢查網頁結構是否已變更")
                    self.status_var.set("登入失敗，無法確認登入狀態")
                    return False
            else:
                self.log(f"登入請求失敗，狀態碼: {response.status_code}")
                self.status_var.set(f"登入失敗，狀態碼: {response.status_code}")
                return False
        
        except RequestException as e:
            self.log(f"登入過程中發生網絡錯誤: {str(e)}")
            self.status_var.set("登入失敗，網絡錯誤")
            return False
        except Exception as e:
            self.log(f"登入過程中發生未知錯誤: {str(e)}")
            import traceback
            self.log(traceback.format_exc())
            self.status_var.set("登入失敗，未知錯誤")
            return False
    
    def ensure_login(self):
        """確保用戶已登入，必要時重新登入
        
        Returns:
            bool: 是否已成功登入
        """
        # 如果未登入或登入已過期，則執行登入
        if not self.login_status:
            return self.login()
        
        # 檢查登入狀態是否過期
        if self.last_login_time:
            elapsed = (datetime.datetime.now() - self.last_login_time).total_seconds()
            if elapsed >= self.login_valid_time:
                self.log("會話可能已過期，重新登入")
                return self.login(force=True)
        
        return True
    
    def keep_session_alive(self):
        """定期刷新會話以保持登入狀態"""
        try:
            # 如果已登入且距離上次登入不超過4分鐘
            if self.login_status and self.last_login_time:
                elapsed = (datetime.datetime.now() - self.last_login_time).total_seconds()
                
                # 在4分鐘後刷新會話
                if 240 <= elapsed < 270:  # 4-4.5分鐘之間
                    self.log("會話即將過期，正在刷新...")
                    
                    # 訪問一個簡單頁面來刷新會話
                    refresh_url = "https://adm_acc.dyu.edu.tw/continue_to_use.php"
                    headers = {
                        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
                    }
                    
                    data = {
                        "action": "set_last_active"
                    }
                    
                    response = self.session.post(refresh_url, data=data, headers=headers, timeout=10)
                    
                    if response.status_code == 200:
                        self.last_login_time = datetime.datetime.now()
                        self.log("會話已成功刷新")
                    else:
                        self.log(f"刷新會話失敗，將在下次檢查時重新登入")
                        self.login_status = False
        except Exception as e:
            self.log(f"刷新會話時出錯: {str(e)}")
            self.login_status = False
    
    def perform_sign_in(self, task):
        """執行簽到操作
        
        Args:
            task: 任務對象
            
        Returns:
            bool: 簽到是否成功
        """
        try:
            # 檢查網絡環境
            if hasattr(self, 'is_campus_network') and not self.is_campus_network:
                self.log(f"簽到失敗: 當前處於校外網絡環境，IP: {getattr(self, 'current_ip', '未知')}")
                if self.settings.get("global_notify", True) and task.notify:
                    self.show_notification(f"{task.name} 簽到失敗", 
                                         "您當前處於校外網絡環境，無法執行簽到操作\n請連接校內網絡後再試")
                self.status_var.set("簽到需要校內網絡環境")
                return False
                
            self.log(f"執行簽到: {task.name}, 時間: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            
            # 確保已登入
            if not self.ensure_login():
                self.log("簽到前檢測到未登入，嘗試重新登入")
                if not self.login(force=True):
                    self.log("重新登入失敗，無法執行簽到")
                    if self.settings.get("global_notify", True) and task.notify:
                        self.show_notification(f"{task.name} 簽到失敗", "無法登入系統，請檢查網絡和帳號設定")
                    return False
            
            # 簽到URL
            sign_in_url = self.settings.get("sign_in_url", "https://adm_acc.dyu.edu.tw/budget/prj_epfee/kernel/kernel_prj_carddata_edit.php?page=NDgy")
            
            # 構建簽到請求數據
            sign_data = {
                "type": 1  # 簽到使用type=1
            }
            
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
                "Content-Type": "application/json",
                "Accept": "application/json, text/plain, */*",
                "X-Requested-With": "XMLHttpRequest"
            }
            
            # 發送簽到請求
            response = self.session.post(sign_in_url, json=sign_data, headers=headers, timeout=30)
            
            # 記錄原始響應以便調試
            self.log(f"簽到API原始響應: {response.text}")
            
            # 檢查簽到結果
            if response.status_code == 200:
                try:
                    result = response.json()
                    result_code = result.get("result")
                    result_msg = result.get("msg", "未知響應")
                    
                    # 處理不同的響應結果
                    if result_code == 1:  # 成功簽到
                        self.log(f"簽到成功: {result_msg}")
                        
                        # 更新任務狀態
                        task.sign_in_done = True
                        self.save_tasks()
                        
                        # 顯示通知 - 處理可能的Unicode消息
                        success_msg = result_msg
                        
                        if self.settings.get("global_notify", True) and task.notify:
                            self.show_notification(f"{task.name} 簽到成功", 
                                                   f"已在 {datetime.datetime.now().strftime('%H:%M:%S')} 完成簽到\n\n{success_msg}")
                        
                        self.status_var.set(f"已完成 '{task.name}' 的簽到")
                        return True
                    
                    elif result_code == 0 and "已簽到" in result_msg:  # 已簽到
                        self.log(f"簽到提示: {result_msg}，您已經完成簽到")
                        
                        # 如果任務狀態不一致，更新為已簽到
                        if not task.sign_in_done:
                            task.sign_in_done = True
                            self.save_tasks()
                        
                        if self.settings.get("global_notify", True) and task.notify:
                            self.show_notification(f"{task.name} 簽到狀態", 
                                                 f"您今天已經完成簽到\n{result_msg}")
                        
                        self.status_var.set(f"'{task.name}': {result_msg}")
                        return True  # 返回成功，因為已經簽到了
                    
                    elif result_code == 0 and "請先簽退" in result_msg:  # 需要先簽退
                        self.log(f"簽到提示: {result_msg}，系統中已有簽到記錄")
                        
                        # 顯示建議手動設置狀態的通知
                        if self.settings.get("global_notify", True) and task.notify:
                            self.show_notification(f"{task.name} 簽到提示", 
                                                 f"系統提示您需要先完成簽退才能簽到\n\n這表示系統中已存在簽到記錄，任務狀態已更新為已簽到")
                        
                        # 更新任務狀態為已簽到，因為"請先簽退"表示系統中已有記錄
                        task.sign_in_done = True
                        self.save_tasks()
                        
                        self.status_var.set(f"'{task.name}': 系統中已有簽到記錄")
                        return True  # 返回成功，因為實際上任務已標記為已完成
                    
                    elif result_code == -1 and ("無使用權限" in result_msg or "-101" in result_msg):  # 權限錯誤
                        self.log(f"簽到權限錯誤: {result_msg}")
                        
                        # 處理校外環境情況
                        self.log("檢測到校外環境或登入失效")
                        self.show_campus_restriction_warning()
                        
                        # 嘗試重新登入
                        self.log("嘗試重新登入...")
                        if self.login(force=True):
                            self.log("重新登入成功，但仍需在校內網絡環境操作")
                        
                        if self.settings.get("global_notify", True) and task.notify:
                            self.show_notification(f"{task.name} 簽到失敗", 
                                                 f"請確保您在校內網絡環境\n{result_msg}")
                        
                        self.status_var.set("簽到需要校內網絡環境")
                        return False
                    
                    else:  # 其他錯誤情況
                        self.log(f"簽到失敗: 未知結果碼 {result_code}, 消息: {result_msg}")
                        
                        if self.settings.get("global_notify", True) and task.notify:
                            self.show_notification(f"{task.name} 簽到失敗", 
                                                 f"原因: {result_msg}\n請嘗試手動簽到或聯繫管理員")
                        
                        self.status_var.set(f"'{task.name}' 簽到失敗: {result_msg}")
                        return False
                    
                except ValueError as e:
                    # JSON解析失敗
                    self.log(f"簽到響應解析失敗: {str(e)}\n響應內容: {response.text[:200]}")
                    if self.settings.get("global_notify", True) and task.notify:
                        self.show_notification(f"{task.name} 簽到失敗", "響應格式錯誤，無法解析")
                    self.status_var.set("簽到失敗: 響應格式錯誤")
                    return False
                    
                except Exception as e:
                    # 其他解析錯誤
                    self.log(f"簽到響應處理錯誤: {str(e)}")
                    if self.settings.get("global_notify", True) and task.notify:
                        self.show_notification(f"{task.name} 簽到失敗", f"響應處理錯誤: {str(e)}")
                    self.status_var.set("簽到失敗: 響應處理錯誤")
                    return False
            else:
                self.log(f"簽到請求失敗，狀態碼: {response.status_code}")
                
                if self.settings.get("global_notify", True) and task.notify:
                    self.show_notification(f"{task.name} 簽到失敗", f"請求失敗，狀態碼: {response.status_code}")
                
                self.status_var.set(f"簽到請求失敗: {response.status_code}")
                return False
                
        except RequestException as e:
            error_msg = f"簽到過程中發生網絡錯誤: {str(e)}"
            self.log(error_msg)
            if self.settings.get("global_notify", True) and task.notify:
                self.show_notification(f"{task.name} 簽到失敗", error_msg)
            self.status_var.set("簽到失敗: 網絡錯誤")
            return False
        except Exception as e:
            error_msg = f"簽到過程中發生未知錯誤: {str(e)}"
            self.log(error_msg)
            if self.settings.get("global_notify", True) and task.notify:
                self.show_notification(f"{task.name} 簽到失敗", error_msg)
            self.status_var.set("簽到失敗: 程式錯誤")
            return False
    
    def perform_sign_out(self, task):
        """執行簽退操作
        
        Args:
            task: 任務對象
            
        Returns:
            bool: 簽退是否成功
        """
        try:
            # 檢查網絡環境
            if hasattr(self, 'is_campus_network') and not self.is_campus_network:
                self.log(f"簽退失敗: 當前處於校外網絡環境，IP: {getattr(self, 'current_ip', '未知')}")
                if self.settings.get("global_notify", True) and task.notify:
                    self.show_notification(f"{task.name} 簽退失敗", 
                                         "您當前處於校外網絡環境，無法執行簽退操作\n請連接校內網絡後再試")
                self.status_var.set("簽退需要校內網絡環境")
                return False
                
            self.log(f"執行簽退: {task.name}, 時間: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            
            # 確保已登入
            if not self.ensure_login():
                self.log("簽退前檢測到未登入，嘗試重新登入")
                if not self.login(force=True):
                    self.log("重新登入失敗，無法執行簽退")
                    if self.settings.get("global_notify", True) and task.notify:
                        self.show_notification(f"{task.name} 簽退失敗", "無法登入系統，請檢查網絡和帳號設定")
                    return False
            
            # 簽退URL
            sign_out_url = self.settings.get("sign_out_url", "https://adm_acc.dyu.edu.tw/budget/prj_epfee/kernel/kernel_prj_carddata_edit.php?page=NDgy")
            
            # 構建簽退請求數據
            sign_data = {
                "type": 2  # 簽退使用type=2
            }
            
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
                "Content-Type": "application/json",
                "Accept": "application/json, text/plain, */*",
                "X-Requested-With": "XMLHttpRequest"
            }
            
            # 發送簽退請求
            response = self.session.post(sign_out_url, json=sign_data, headers=headers, timeout=30)
            
            # 記錄原始響應以便調試
            self.log(f"簽退API原始響應: {response.text}")
            
            # 檢查簽退結果
            if response.status_code == 200:
                try:
                    result = response.json()
                    result_code = result.get("result")
                    result_msg = result.get("msg", "未知響應")
                    
                    # 處理不同的響應結果
                    if result_code == 1:  # 成功簽退
                        self.log(f"簽退成功: {result_msg}")
                        
                        # 更新任務狀態
                        task.sign_out_done = True
                        self.save_tasks()
                        
                        # 顯示通知 - 處理可能的Unicode消息
                        success_msg = result_msg
                        
                        if self.settings.get("global_notify", True) and task.notify:
                            self.show_notification(f"{task.name} 簽退成功", 
                                                 f"已在 {datetime.datetime.now().strftime('%H:%M:%S')} 完成簽退\n\n{success_msg}")
                        
                        # 特殊處理：如果消息包含"工讀時數"提示，添加額外提示
                        if "工讀時數" in success_msg and "不足30分鐘" in success_msg:
                            self.log("系統提示工讀時數不足30分鐘部分不計算")
                            # 執行工作時間警告處理
                            self.handle_work_time_warning(task, success_msg)
                        
                        self.status_var.set(f"已完成 '{task.name}' 的簽退")
                        return True
                        
                    elif result_code == 0 and ("請先簽到" in result_msg or "尚未簽到" in result_msg):  # 未簽到就嘗試簽退
                        self.log(f"簽退提示: {result_msg}，需要先完成簽到")
                        
                        if self.settings.get("global_notify", True) and task.notify:
                            self.show_notification(f"{task.name} 簽退提示", 
                                                 f"您今天尚未簽到，無法簽退\n{result_msg}")
                        
                        task.sign_out_done = False  # 確保狀態是未簽退
                        self.save_tasks()
                        
                        self.status_var.set(f"'{task.name}' 尚未簽到，無法簽退")
                        return False
                        
                    elif result_code == 0 and "已簽退" in result_msg:  # 已經簽退
                        self.log(f"簽退提示: {result_msg}，您已經完成簽退")
                        
                        # 更新任務狀態，因為已經簽退了
                        if not task.sign_out_done:
                            task.sign_out_done = True
                            self.save_tasks()
                        
                        if self.settings.get("global_notify", True) and task.notify:
                            self.show_notification(f"{task.name} 簽退提示", 
                                                 f"您今天已經完成簽退\n{result_msg}")
                        
                        self.status_var.set(f"'{task.name}' 已完成簽退")
                        # 返回True因為實際上簽退狀態已完成
                        return True
                        
                    elif result_code == -1 and ("無使用權限" in result_msg or "-101" in result_msg):  # 權限錯誤
                        self.log(f"簽退權限錯誤: {result_msg}")
                        
                        # 處理校外環境情況
                        self.log("檢測到校外環境或登入失效")
                        self.show_campus_restriction_warning()
                        
                        # 嘗試重新登入
                        self.log("嘗試重新登入...")
                        if self.login(force=True):
                            self.log("重新登入成功，但仍需在校內網絡環境操作")
                        
                        if self.settings.get("global_notify", True) and task.notify:
                            self.show_notification(f"{task.name} 簽退失敗", 
                                                 f"請確保您在校內網絡環境\n{result_msg}")
                        
                        self.status_var.set("簽退需要校內網絡環境")
                        return False
                        
                    else:  # 其他錯誤情況
                        self.log(f"簽退失敗: 未知結果碼 {result_code}, 消息: {result_msg}")
                        
                        if self.settings.get("global_notify", True) and task.notify:
                            self.show_notification(f"{task.name} 簽退失敗", 
                                                 f"原因: {result_msg}\n請嘗試手動簽退或聯繫管理員")
                        
                        self.status_var.set(f"'{task.name}' 簽退失敗: {result_msg}")
                        return False
                        
                except ValueError as e:
                    # JSON解析失敗
                    self.log(f"簽退響應解析失敗: {str(e)}\n響應內容: {response.text[:200]}")
                    if self.settings.get("global_notify", True) and task.notify:
                        self.show_notification(f"{task.name} 簽退失敗", "響應格式錯誤，無法解析")
                    self.status_var.set("簽退失敗: 響應格式錯誤")
                    return False
                    
                except Exception as e:
                    # 其他解析錯誤
                    self.log(f"簽退響應處理錯誤: {str(e)}")
                    if self.settings.get("global_notify", True) and task.notify:
                        self.show_notification(f"{task.name} 簽退失敗", f"響應處理錯誤: {str(e)}")
                    self.status_var.set("簽退失敗: 響應處理錯誤")
                    return False
            else:
                self.log(f"簽退請求失敗，狀態碼: {response.status_code}")
                
                if self.settings.get("global_notify", True) and task.notify:
                    self.show_notification(f"{task.name} 簽退失敗", f"請求失敗，狀態碼: {response.status_code}")
                
                self.status_var.set(f"簽退請求失敗: {response.status_code}")
                return False
                
        except RequestException as e:
            error_msg = f"簽退過程中發生網絡錯誤: {str(e)}"
            self.log(error_msg)
            if self.settings.get("global_notify", True) and task.notify:
                self.show_notification(f"{task.name} 簽退失敗", error_msg)
            self.status_var.set("簽退失敗: 網絡錯誤")
            return False
        except Exception as e:
            error_msg = f"簽退過程中發生未知錯誤: {str(e)}"
            self.log(error_msg)
            if self.settings.get("global_notify", True) and task.notify:
                self.show_notification(f"{task.name} 簽退失敗", error_msg)
            self.status_var.set("簽退失敗: 程式錯誤")
            return False
    
    def show_campus_restriction_warning(self):
        """顯示校內限制警告"""
        warning_msg = """
⚠️ 校內網絡限制

系統要求必須在校內網絡環境進行簽到/簽退操作。

解決方法:
1. 確保您已連接到學校WiFi或有線網絡
2. 如果您在校外，可以嘗試使用學校提供的VPN服務
3. 向學校IT部門諮詢遠程簽到/退選項
"""
        
        self.log(warning_msg)
        
        # 顯示一個通知而不是對話框，避免阻塞程序
        self.show_notification("校內網絡限制", 
                             "系統要求必須在校內網絡環境進行簽到/簽退。\n請確保您已連接到學校網絡。")
        
        # 將警告狀態記錄到設定中，避免短時間內重複顯示
        self.settings["last_campus_warning"] = datetime.datetime.now().timestamp()
        self.save_settings()
    
    def check_tasks(self):
        """檢查並執行到期的任務"""
        # 首先刷新會話
        self.keep_session_alive()
        
        # 檢查網絡環境
        if hasattr(self, 'is_campus_network') and not self.is_campus_network:
            now = datetime.datetime.now()
            
            # 新增：日誌頻率和狀態檢查
            should_log = False
            
            # 檢查上次輸出日誌的時間和網絡狀態
            if self.last_network_log_time is None:  # 首次檢測
                should_log = True
            elif (now - self.last_network_log_time).total_seconds() >= 300:  # 至少間隔5分鐘
                should_log = True
            elif self.last_network_log_status != self.is_campus_network:  # 網絡狀態發生變化
                should_log = True
                
            if should_log:
                self.log("檢測到校外網絡環境，跳過任務執行")
                self.last_network_log_time = now
                self.last_network_log_status = self.is_campus_network
                
            # 更新狀態欄但不記錄日誌
            self.status_var.set("校外網絡環境，任務已暫停")
            return  # 如果在校外網絡，直接跳過所有任務
        else:
            # 在校內網絡環境，更新記錄狀態
            self.last_network_log_status = self.is_campus_network
        
        # 檢查任務
        now = datetime.datetime.now()
        today = now.strftime("%Y-%m-%d")
        current_time = now.strftime("%H:%M")
        
        for task in self.tasks:
            if task.date == today:
                # 檢查任務是否被標記為環境受限
                if hasattr(task, 'campus_restricted') and task.campus_restricted:
                    # 如果上次嘗試時間在30分鐘內，則跳過
                    if task.last_attempt_time:
                        last_attempt = datetime.datetime.fromisoformat(task.last_attempt_time)
                        elapsed_minutes = (now - last_attempt).total_seconds() / 60
                        if elapsed_minutes < 30:  # 30分鐘內不重複嘗試
                            self.log(f"任務 '{task.name}' 因校外環境限制暫停嘗試 (冷卻中: {int(30-elapsed_minutes)}分鐘)")
                            continue
                
                # 檢查簽到 - 只對未手動標記為已完成的任務執行
                if current_time >= task.sign_in_time and not task.sign_in_done:
                    result = self.perform_sign_in(task)
                    
                    # 檢查是否因為校外環境而失敗
                    if not result and self.status_var.get() == "簽到需要校內網絡環境":
                        task.campus_restricted = True
                        task.last_attempt_time = now.isoformat()
                        self.log(f"任務 '{task.name}' 因校外環境限制暫時跳過，將在30分鐘後重試")
                        self.save_tasks()  # 儲存狀態
                    elif result:
                        # 成功簽到，清除環境限制標記
                        task.campus_restricted = False
                        task.sign_in_done = True
                        self.save_tasks()
                
                # 檢查簽退 - 只對已簽到但未簽退的任務執行
                if current_time >= task.sign_out_time and not task.sign_out_done and task.sign_in_done:
                    result = self.perform_sign_out(task)
                    
                    # 檢查是否因為校外環境而失敗
                    if not result and self.status_var.get() == "簽退需要校內網絡環境":
                        task.campus_restricted = True
                        task.last_attempt_time = now.isoformat()
                        self.log(f"任務 '{task.name}' 因校外環境限制暫時跳過，將在30分鐘後重試")
                        self.save_tasks()  # 儲存狀態
                    elif result:
                        # 成功簽退，清除環境限制標記
                        task.campus_restricted = False
                        task.sign_out_done = True
                        self.save_tasks()
    
    def scheduler_loop(self):
        """調度器主循環"""
        self.log("調度器已啟動")
        
        # 如果設置了自動啟動，則直接開始檢查
        if self.settings.get("auto_start", True):
            self.check_tasks()
        
        while self.scheduler_running:
            try:
                # 使用設定中的檢查間隔
                check_interval = self.settings.get("check_interval", 30)
                time.sleep(check_interval)
                
                if self.scheduler_running:
                    self.check_tasks()
            except Exception as e:
                self.log(f"調度器錯誤: {str(e)}")
                time.sleep(5)  # 出錯後稍等一下再繼續
    
    def show_notification(self, title, message):
        """顯示桌面通知"""
        # 使用自定義通知窗口
        NotificationWindow(title, message)
        self.log(f"通知: {title} - {message}")
    
    def log(self, message):
        """記錄日誌信息"""
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_msg = f"[{timestamp}] {message}\n"
        
        # 添加到UI日誌
        self.log_text.insert(tk.END, log_msg)
        self.log_text.see(tk.END)  # 自動滾動到底部
        
        # 保存到文件
        try:
            with open(self.log_file, 'a', encoding='utf-8') as f:
                f.write(log_msg)
        except Exception as e:
            print(f"保存日誌失敗: {str(e)}")
    
    def load_log(self):
        """載入最近的日誌內容"""
        if not os.path.exists(self.log_file):
            self.log("ChronoHelper 已啟動")
            return
        
        try:
            with open(self.log_file, 'r', encoding='utf-8') as f:
                # 只讀取最後100行
                lines = f.readlines()
                lines = lines[-100:] if len(lines) > 100 else lines
                
                # 顯示最近日誌
                for line in lines:
                    self.log_text.insert(tk.END, line)
                self.log_text.see(tk.END)
            
            self.log("ChronoHelper 已啟動")
            
            # 啟動時檢查並清理過大的日誌文件
            self.clean_logs()
            
        except Exception as e:
            print(f"載入日誌失敗: {str(e)}")
            self.log("ChronoHelper 已啟動")
    
    def clean_logs(self):
        """清理過大的日誌文件"""
        try:
            if os.path.exists(self.log_file) and os.path.getsize(self.log_file) > 1024 * 1024:  # 大於1MB
                # 保留最後500行
                with open(self.log_file, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                
                with open(self.log_file, 'w', encoding='utf-8') as f:
                    f.writelines(lines[-500:])
                
                self.log("日誌文件已自動清理")
        except Exception as e:
            print(f"清理日誌時出錯: {str(e)}")
    
    def check_campus_network(self, verbose=True):
        """檢測是否在校內網絡環境（163.23.x.x）
        
        Args:
            verbose: 是否輸出檢測過程的日誌，默認為True
            
        Returns:
            bool: 是否在校內網絡
            str: 當前IP地址
        """
        try:

            hostname = socket.gethostname()
            ip_address = socket.gethostbyname(hostname)
            is_campus = ip_address.startswith('163.23.')
            if verbose:
                self.log(f"檢測到本地IP地址: {ip_address}")
            return is_campus, ip_address
            
        except Exception as e:
            if verbose:
                self.log(f"IP地址檢測失敗: {str(e)}")
            return False, "未知"
    
    def handle_work_time_warning(self, task, message):
        """處理工作時間計算相關的警告"""
        if "工讀時數" in message and "不足30分鐘" in message:
            # 計算實際工作時間
            if task.sign_in_done and hasattr(task, 'sign_in_time') and task.sign_in_time:
                try:
                    # 解析簽到時間
                    sign_in_time = datetime.datetime.strptime(task.sign_in_time, "%H:%M")
                    
                    # 當前時間作為簽退時間
                    now = datetime.datetime.now()
                    sign_out_time = datetime.datetime(
                        now.year, now.month, now.day, 
                        now.hour, now.minute
                    )
                    
                    # 將簽到時間設置為今天
                    sign_in_time = sign_in_time.replace(
                        year=now.year, month=now.month, day=now.day
                    )
                    
                    # 計算時間差
                    time_diff = sign_out_time - sign_in_time
                    minutes = time_diff.total_seconds() / 60
                    
                    if minutes < 30:
                        # 顯示特殊警告
                        warning_msg = (
                            f"注意：您的工作時間僅為 {int(minutes)} 分鐘，不足30分鐘。\n\n"
                            "根據系統規則，不足30分鐘的工讀時數將不列入計算。\n"
                            "請確保您的工作時間達到學校規定的最低要求。"
                        )
                        messagebox.showwarning("工作時間不足", warning_msg, parent=self.root)
                        self.log(f"警告: 工作時間不足30分鐘 ({int(minutes)}分鐘)")
                except Exception as e:
                    self.log(f"計算工作時間時出錯: {str(e)}")
    
    def ensure_unicode(self, text):
        """確保文本是Unicode格式"""
        if isinstance(text, bytes):
            return text.decode('utf-8')
        return text
    
    def initial_network_check(self):
        """初始化時檢測網絡環境"""
        self.log("正在進行初始網絡環境檢測...")
        is_campus, ip = self.check_campus_network(verbose=True)  # 明確指定顯示詳細信息
        self.update_network_status(is_campus, ip)
        
        # 設置定期檢測
        self.root.after(60000, self.periodic_network_check)  # 每分鐘檢測一次
    
    def periodic_network_check(self):
        """定期檢測網絡環境"""
        if not self.scheduler_running:
            return  # 如果調度器已停止，不再檢測
            
        # 正常執行網絡檢測，但避免在日誌中重複記錄過程
        try:
            is_campus, ip = self.check_campus_network(verbose=False)  # 添加verbose參數
            self.update_network_status(is_campus, ip)
        except Exception as e:
            # 只記錄檢測失敗的情況
            self.log(f"定期網絡檢測失敗: {str(e)}")
        
        # 繼續定期檢測
        self.root.after(60000, self.periodic_network_check)  # 每分鐘檢測一次
    
    def update_network_status(self, is_campus, ip):
        """更新網絡狀態顯示
        
        Args:
            is_campus: 是否在校內網絡
            ip: 當前IP地址
        """
        # 檢查是否有前一個狀態
        had_previous_state = hasattr(self, 'is_campus_network')
        status_changed = had_previous_state and self.is_campus_network != is_campus
        
        # 如果有前一個狀態且狀態發生變化，則發送通知
        if status_changed:
            if is_campus:
                self.log("網絡環境已變更: 校外 -> 校內")
                self.show_notification("網絡環境變更", "檢測到您已連接到校內網絡\n現在可以正常執行簽到/簽退操作")
                # 重置校內網絡限制狀態
                self.reset_campus_restrictions()
            else:
                self.log("網絡環境已變更: 校內 -> 校外")
                self.show_notification("網絡環境變更", "檢測到您已離開校內網絡\n簽到/簽退操作將暫停執行")
        elif not had_previous_state:
            # 首次檢測，記錄初始狀態
            network_type = "校內" if is_campus else "校外"
            self.log(f"初始網絡環境檢測: {network_type} 網絡 (IP: {ip})")
        
        # 只在首次檢測或IP變更時記錄IP
        if not had_previous_state or self.current_ip != ip:
            self.log(f"IP地址: {ip}")
        
        # 更新UI顯示
        if is_campus:
            self.network_status_var.set(f"校內網絡 ✓ ({ip})")
            self.network_status_label.config(fg="#2ecc71")  # 綠色
        else:
            self.network_status_var.set(f"校外網絡 ⚠️ ({ip})")
            self.network_status_label.config(fg="#e74c3c")  # 紅色
        
        # 記錄網絡狀態以供任務檢查使用
        self.is_campus_network = is_campus
        self.current_ip = ip
        
        # 記錄上次網絡環境日誌時間和狀態
        self.last_network_log_time = datetime.datetime.now()
        self.last_network_log_status = is_campus
    
    def refresh_network_status(self):
        """手動刷新網絡狀態"""
        self.network_status_var.set("檢測網絡中...")
        self.network_status_label.config(fg="white")
        
        # 使用after確保UI先更新
        self.root.after(100, self._refresh_network_status_task)
    
    def _refresh_network_status_task(self):
        """刷新網絡狀態實際任務"""
        try:
            self.log("正在刷新網絡狀態...")
            is_campus, ip = self.check_campus_network(verbose=True)  # 手動刷新時顯示詳細信息
            
            # 保存當前狀態以檢測變化
            old_status = getattr(self, 'is_campus_network', None)
            
            # 更新網絡狀態
            self.update_network_status(is_campus, ip)
            
            # 如果是校內網絡或網絡狀態從校外變為校內，強制重置所有任務的環境限制
            if is_campus or (old_status is False and is_campus is True):
                reset_count = self.reset_campus_restrictions()
                if reset_count > 0:
                    self.show_notification("環境限制已重置", 
                                         f"已重置 {reset_count} 個受環境限制的任務\n現在可以正常執行了")
            
            # 強制刷新任務列表顯示
            self.refresh_task_list()
        except Exception as e:
            self.log(f"網絡狀態刷新失敗: {str(e)}")
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
            self.log(f"已重置 {reset_count} 個任務的環境限制狀態")
            self.save_tasks()
        
        return reset_count
    
    def update_task_status(self, task):
        """更新任務狀態
        
        Args:
            task: 要更新的任務
        """
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
        
        self.log(f"已手動更新任務 '{task.name}' 狀態: {status_str}")


class ModernTaskDialog:
    """現代風格的任務編輯對話框"""
    def __init__(self, parent, title, name="", date="", sign_in="", sign_out="", notify=True):
        self.result = None
        
        # 如果日期為空，設置為今天
        if not date:
            date = datetime.date.today().strftime("%Y-%m-%d")
        
        self.dialog = tk.Toplevel(parent)
        self.dialog.title(title)
        self.dialog.geometry("450x450")  # 增加初始高度
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
        
        tk.Label(header, text=title, font=("Arial", 14, "bold"), 
                 bg=COLORS["primary"], fg="white").pack(anchor=tk.W)
        
        # 表單內容
        form_frame = tk.Frame(main_frame, bg=COLORS["card"], padx=20, pady=20)
        form_frame.pack(fill=tk.BOTH, expand=True)
        
        # 任務名稱
        tk.Label(form_frame, text="任務名稱:", bg=COLORS["card"], fg=COLORS["text"]).pack(anchor=tk.W, pady=(0, 5))
        self.name_var = tk.StringVar(value=name)
        name_entry = ttk.Entry(form_frame, textvariable=self.name_var, width=30)
        name_entry.pack(fill=tk.X, pady=(0, 15))
        
        # 日期
        tk.Label(form_frame, text="日期:", bg=COLORS["card"], fg=COLORS["text"]).pack(anchor=tk.W, pady=(0, 5))
        
        date_frame = tk.Frame(form_frame, bg=COLORS["card"])
        date_frame.pack(fill=tk.X, pady=(0, 15))
        
        self.year_var = tk.StringVar(value=date.split("-")[0] if date else "")
        self.month_var = tk.StringVar(value=date.split("-")[1] if date else "")
        self.day_var = tk.StringVar(value=date.split("-")[2] if date else "")
        
        years = [str(datetime.date.today().year + i) for i in range(-1, 3)]
        months = [f"{m:02d}" for m in range(1, 13)]
        days = [f"{d:02d}" for d in range(1, 32)]
        
        ttk.Combobox(date_frame, textvariable=self.year_var, values=years, width=5).pack(side=tk.LEFT)
        tk.Label(date_frame, text="-", bg=COLORS["card"]).pack(side=tk.LEFT)
        ttk.Combobox(date_frame, textvariable=self.month_var, values=months, width=3).pack(side=tk.LEFT)
        tk.Label(date_frame, text="-", bg=COLORS["card"]).pack(side=tk.LEFT)
        ttk.Combobox(date_frame, textvariable=self.day_var, values=days, width=3).pack(side=tk.LEFT)
        
        # 簽到時間
        tk.Label(form_frame, text="簽到時間:", bg=COLORS["card"], fg=COLORS["text"]).pack(anchor=tk.W, pady=(0, 5))
        
        sign_in_frame = tk.Frame(form_frame, bg=COLORS["card"])
        sign_in_frame.pack(fill=tk.X, pady=(0, 15))
        
        self.sign_in_hour = tk.StringVar(value=sign_in.split(":")[0] if sign_in else "")
        self.sign_in_minute = tk.StringVar(value=sign_in.split(":")[1] if sign_in else "")
        
        hours = [f"{h:02d}" for h in range(24)]
        minutes = [f"{m:02d}" for m in range(60)]
        
        ttk.Combobox(sign_in_frame, textvariable=self.sign_in_hour, values=hours, width=3).pack(side=tk.LEFT)
        tk.Label(sign_in_frame, text=":", bg=COLORS["card"]).pack(side=tk.LEFT)
        ttk.Combobox(sign_in_frame, textvariable=self.sign_in_minute, values=minutes, width=3).pack(side=tk.LEFT)
        
        # 簽退時間
        tk.Label(form_frame, text="簽退時間:", bg=COLORS["card"], fg=COLORS["text"]).pack(anchor=tk.W, pady=(0, 5))
        
        sign_out_frame = tk.Frame(form_frame, bg=COLORS["card"])
        sign_out_frame.pack(fill=tk.X, pady=(0, 15))
        
        self.sign_out_hour = tk.StringVar(value=sign_out.split(":")[0] if sign_out else "")
        self.sign_out_minute = tk.StringVar(value=sign_out.split(":")[1] if sign_out else "")
        
        ttk.Combobox(sign_out_frame, textvariable=self.sign_out_hour, values=hours, width=3).pack(side=tk.LEFT)
        tk.Label(sign_out_frame, text=":", bg=COLORS["card"]).pack(side=tk.LEFT)
        ttk.Combobox(sign_out_frame, textvariable=self.sign_out_minute, values=minutes, width=3).pack(side=tk.LEFT)
        
        # 通知選項
        self.notify_var = tk.BooleanVar(value=notify)
        ttk.Checkbutton(form_frame, text="啟用通知", variable=self.notify_var).pack(anchor=tk.W, pady=(0, 15))
        
        # 底部按鈕 - 使用獨立框架並固定在底部
        button_frame = tk.Frame(self.dialog, bg=COLORS["card"], padx=20, pady=20)
        button_frame.pack(side=tk.BOTTOM, fill=tk.X)  # 固定在底部
        
        cancel_btn = tk.Button(button_frame, text="取消", bg="#f1f2f6", fg=COLORS["text"],
                             relief=tk.FLAT, padx=15, pady=8, bd=0,
                             command=self.on_cancel)
        cancel_btn.pack(side=tk.RIGHT, padx=5)
        
        save_btn = ModernButton(button_frame, text="儲存", 
                              command=self.on_save)
        save_btn.pack(side=tk.RIGHT)
        
        # 設置最小窗口大小
        self.dialog.update_idletasks()
        self.dialog.minsize(450, 350)
        
        # 設置焦點
        name_entry.focus_set()
        
        self.dialog.protocol("WM_DELETE_WINDOW", self.on_cancel)
        self.dialog.wait_visibility()
        self.dialog.focus_set()
        self.dialog.wait_window()
    
    def on_save(self):
        # 獲取並驗證輸入值
        name = self.name_var.get().strip()
        if not name:
            messagebox.showwarning("輸入錯誤", "請輸入任務名稱", parent=self.dialog)
            return
        
        try:
            # 檢查日期格式
            year = self.year_var.get().strip()
            month = self.month_var.get().strip()
            day = self.day_var.get().strip()
            
            # 確保年月日都有填寫
            if not (year and month and day):
                messagebox.showwarning("輸入錯誤", "請輸入完整日期", parent=self.dialog)
                return
                
            # 驗證日期有效性
            date_str = f"{year}-{month}-{day}"
            datetime.datetime.strptime(date_str, "%Y-%m-%d")
            
            # 檢查時間格式
            sign_in_hour = self.sign_in_hour.get().strip()
            sign_in_minute = self.sign_in_minute.get().strip()
            sign_out_hour = self.sign_out_hour.get().strip()
            sign_out_minute = self.sign_out_minute.get().strip()
            
            # 確保時間都有填寫
            if not (sign_in_hour and sign_in_minute and sign_out_hour and sign_out_minute):
                messagebox.showwarning("輸入錯誤", "請輸入完整的簽到簽退時間", parent=self.dialog)
                return
            
            # 格式化時間
            sign_in_time = f"{sign_in_hour}:{sign_in_minute}"
            sign_out_time = f"{sign_out_hour}:{sign_out_minute}"
            
            # 驗證時間格式
            datetime.datetime.strptime(sign_in_time, "%H:%M")
            datetime.datetime.strptime(sign_out_time, "%H:%M")
            
            # 確保簽退時間晚於簽到時間
            if sign_in_time >= sign_out_time:
                messagebox.showwarning("輸入錯誤", "簽退時間必須晚於簽到時間", parent=self.dialog)
                return
            
            # 所有驗證通過，設置結果
            self.result = (name, date_str, sign_in_time, sign_out_time, self.notify_var.get())
            self.dialog.destroy()
            
        except ValueError as e:
            messagebox.showwarning("輸入錯誤", f"日期或時間格式無效: {str(e)}", parent=self.dialog)
    
    def on_cancel(self):
        self.dialog.destroy()


def main():
    # 禁用SSL證書驗證
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    
    # 修改requests庫的默認行為
    import requests
    old_request = requests.Session.request
    def new_request(self, method, url, **kwargs):
        kwargs.setdefault('verify', False)
        return old_request(self, method, url, **kwargs)
    requests.Session.request = new_request
    
    root = tk.Tk()
    app = ChronoHelper(root)
    root.mainloop()

if __name__ == "__main__":
    main()