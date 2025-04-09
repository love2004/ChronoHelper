# -*- coding: utf-8 -*-
"""
通知窗口
"""

import tkinter as tk
from chronohelper.config.colors import COLORS

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
