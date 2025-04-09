# -*- coding: utf-8 -*-
"""
日誌功能
"""

import datetime
import os
import tkinter as tk

class Logger:
    """日誌管理器"""
    
    def __init__(self, log_file="chronohelper_log.txt", max_size=1024*1024, max_lines=500):
        """初始化日誌管理器
        
        Args:
            log_file: 日誌文件路徑
            max_size: 日誌文件最大大小(bytes)
            max_lines: 清理時保留的最大行數
        """
        self.log_file = log_file
        self.max_size = max_size
        self.max_lines = max_lines
        self.log_text = None  # UI文本組件，由外部設置
    
    def set_text_widget(self, log_text):
        """設置日誌顯示的文本組件
        
        Args:
            log_text: tkinter的ScrolledText組件
        """
        self.log_text = log_text
    
    def log(self, message):
        """記錄日誌信息
        
        Args:
            message: 日誌消息內容
        """
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_msg = f"[{timestamp}] {message}\n"
        
        # 添加到UI日誌
        if self.log_text:
            self.log_text.insert(tk.END, log_msg)
            self.log_text.see(tk.END)  # 自動滾動到底部
        
        # 保存到文件
        try:
            with open(self.log_file, 'a', encoding='utf-8') as f:
                f.write(log_msg)
            
            # 自動檢查日誌文件大小
            self.check_and_clean_log()
        except Exception as e:
            print(f"保存日誌失敗: {str(e)}")
    
    def load_recent_logs(self, lines=100):
        """載入最近的日誌內容
        
        Args:
            lines: 載入的行數
            
        Returns:
            list: 日誌行列表
        """
        if not os.path.exists(self.log_file):
            return []
        
        try:
            with open(self.log_file, 'r', encoding='utf-8') as f:
                # 只讀取最後指定行數
                all_lines = f.readlines()
                return all_lines[-lines:] if len(all_lines) > lines else all_lines
        except Exception as e:
            print(f"載入日誌失敗: {str(e)}")
            return []
    
    def check_and_clean_log(self):
        """檢查並清理過大的日誌文件"""
        try:
            if os.path.exists(self.log_file) and os.path.getsize(self.log_file) > self.max_size:
                # 保留最後指定行數
                with open(self.log_file, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                
                with open(self.log_file, 'w', encoding='utf-8') as f:
                    f.writelines(lines[-self.max_lines:])
                
                self.log("日誌文件已自動清理")
        except Exception as e:
            print(f"清理日誌時出錯: {str(e)}")
