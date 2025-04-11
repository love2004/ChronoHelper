#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
ChronoHelper - 自動化簽到/簽退工具
主程序入口點
"""

import tkinter as tk
import urllib3
import requests
import sys
import os
import logging
import traceback
from typing import Callable, Any

# 將當前目錄添加到系統路徑，以便導入本地模塊
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from chronohelper.app import ChronoHelper

# 配置基本日誌系統
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('ChronoHelper')

def setup_ssl_handling() -> None:
    """
    配置SSL處理和請求設定
    
    永久禁用SSL證書驗證，適用於本系統訪問的自簽證書網站
    
    警告：
        禁用SSL證書驗證可能導致安全風險，僅應在受控內部網絡環境中使用。
    """
    # 禁用SSL證書驗證
    logger.warning("安全警告：SSL證書驗證已被禁用。")
    
    # 禁用SSL證書驗證警告
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    
    # 保存原始請求方法
    old_request = requests.Session.request
    
    # 修改requests庫的默認行為，禁用SSL驗證
    def new_request(self: requests.Session, method: str, url: str, **kwargs: Any) -> requests.Response:
        # 禁用證書驗證
        if 'verify' not in kwargs:
            kwargs['verify'] = False
        return old_request(self, method, url, **kwargs)
    
    # 覆蓋原始請求方法
    requests.Session.request = new_request  # type: ignore
    
    logger.info("已配置忽略SSL證書驗證的網絡請求")

def setup_resources() -> None:
    """
    確保必要的資源目錄存在
    """
    # 設置資源目錄路徑
    base_dir = os.path.dirname(os.path.abspath(__file__))
    resources_dir = os.path.join(base_dir, "resources")
    
    # 創建資源目錄（如果不存在）
    if not os.path.exists(resources_dir):
        os.makedirs(resources_dir, exist_ok=True)
        
        # 創建圖標目錄
        icons_dir = os.path.join(resources_dir, "icons")
        if not os.path.exists(icons_dir):
            os.makedirs(icons_dir, exist_ok=True)

def main() -> None:
    """
    程序主入口
    """
    try:
        # 配置SSL處理 - 直接禁用SSL證書驗證
        setup_ssl_handling()
        
        # 設置資源目錄
        setup_resources()
        
        # 創建並啟動應用
        root = tk.Tk()
        root.title("ChronoHelper")
        
        # 設置最小視窗大小
        root.minsize(400, 300)
        
        # 在異常時優雅地終止
        def on_error(exc_type: Any, exc_value: Any, exc_tb: Any) -> bool:
            error_msg = "".join(traceback.format_exception(exc_type, exc_value, exc_tb))
            logging.error(f"未處理的異常: {error_msg}")
            
            # 如果應用已初始化，嘗試正確關閉
            try:
                if 'app' in locals() and hasattr(app, 'on_exit'):
                    app.on_exit()
            except Exception:
                pass
                
            # 顯示錯誤並終止程序
            try:
                from tkinter import messagebox
                messagebox.showerror("錯誤", f"應用程式發生未預期的錯誤，必須關閉。\n\n{exc_value}")
            except Exception:
                pass
                
            return False  # 讓系統處理異常
            
        # 設置異常處理
        sys.excepthook = on_error
        
        # 啟動應用
        app = ChronoHelper(root)
        root.mainloop()
        
    except Exception as e:
        logging.error(f"啟動應用失敗: {str(e)}")
        
        # 嘗試使用tkinter顯示錯誤
        try:
            import tkinter.messagebox as messagebox
            messagebox.showerror("啟動錯誤", f"無法啟動應用程式: {str(e)}")
        except Exception:
            # 如果無法使用tkinter，則輸出到控制台
            print(f"致命錯誤: {str(e)}")
        
        sys.exit(1)

if __name__ == "__main__":
    main()
