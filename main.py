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

# 將當前目錄添加到系統路徑，以便導入本地模塊
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from chronohelper.app import ChronoHelper

def main():
    # 禁用SSL證書驗證
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    
    # 修改requests庫的默認行為
    old_request = requests.Session.request
    def new_request(self, method, url, **kwargs):
        kwargs.setdefault('verify', False)
        return old_request(self, method, url, **kwargs)
    requests.Session.request = new_request

    # 設置資源目錄路徑
    base_dir = os.path.dirname(os.path.abspath(__file__))
    resources_dir = os.path.join(base_dir, "resources")
    if not os.path.exists(resources_dir):
        os.makedirs(resources_dir, exist_ok=True)
        icons_dir = os.path.join(resources_dir, "icons")
        if not os.path.exists(icons_dir):
            os.makedirs(icons_dir, exist_ok=True)
    
    # 創建並啟動應用
    root = tk.Tk()
    app = ChronoHelper(root)
    root.mainloop()

if __name__ == "__main__":
    main()
