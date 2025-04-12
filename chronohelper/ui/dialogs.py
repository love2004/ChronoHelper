# -*- coding: utf-8 -*-
"""
對話框UI元件
"""

import tkinter as tk
import datetime
import re
import requests
import subprocess
import webbrowser
import os

from requests.exceptions import RequestException
from bs4 import BeautifulSoup
from tkinter import ttk, messagebox
from chronohelper.config.colors import COLORS
from chronohelper.ui.base import ModernButton
from chronohelper.ui.helpers import add_tooltip

class SettingsDialog:
    """設定對話框"""
    def __init__(self, parent, settings):
        self.result = None
        self.settings = settings.copy()
        
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("ChronoHelper - 設定")
        self.dialog.geometry("500x580") 
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
        
        # 網絡設定選項卡
        network_frame = tk.Frame(notebook, bg=COLORS["card"], padx=15, pady=15)
        notebook.add(network_frame, text="網絡設定")
        
        # 用戶資訊選項卡
        user_frame = tk.Frame(notebook, bg=COLORS["card"], padx=15, pady=15)
        notebook.add(user_frame, text="用戶資訊")
        
        # 預設時間選項卡
        time_frame = tk.Frame(notebook, bg=COLORS["card"], padx=15, pady=15)
        notebook.add(time_frame, text="預設時間")
        
        # VPN 設置選項卡
        vpn_frame = tk.Frame(notebook, bg=COLORS["card"], padx=15, pady=15)
        notebook.add(vpn_frame, text="VPN")
        
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
        
        # 新增：會話維持設定
        tk.Label(general_frame, text="會話維持設定", font=("Arial", 11, "bold"), 
                 bg=COLORS["card"], fg=COLORS["text"]).grid(row=5, column=0, sticky=tk.W, pady=(20,5))
        # 會話刷新間隔
        session_frame = tk.Frame(general_frame, bg=COLORS["card"])
        session_frame.grid(row=6, column=0, sticky=tk.W, padx=15)
        tk.Label(session_frame, text="會話刷新間隔:", bg=COLORS["card"]).pack(side=tk.LEFT, padx=(0,5))
        self.session_refresh_var = tk.IntVar(value=settings.get("session_refresh_interval", 240))
        ttk.Spinbox(session_frame, from_=60, to=600, increment=30, 
                   textvariable=self.session_refresh_var, width=5).pack(side=tk.LEFT)
        tk.Label(session_frame, text="秒 (建議240秒)", bg=COLORS["card"], fg=COLORS["light_text"]).pack(side=tk.LEFT, padx=5)
        # 會話有效時間
        valid_frame = tk.Frame(general_frame, bg=COLORS["card"])
        valid_frame.grid(row=7, column=0, sticky=tk.W, padx=15, pady=(5,0))
        tk.Label(valid_frame, text="會話有效時間:", bg=COLORS["card"]).pack(side=tk.LEFT, padx=(0,5))
        self.session_valid_var = tk.IntVar(value=settings.get("session_valid_time", 270))
        ttk.Spinbox(valid_frame, from_=120, to=600, increment=30, 
                   textvariable=self.session_valid_var, width=5).pack(side=tk.LEFT)
        tk.Label(valid_frame, text="秒 (建議270秒)", bg=COLORS["card"], fg=COLORS["light_text"]).pack(side=tk.LEFT, padx=5)
        # 會話設定說明
        session_info = tk.Label(general_frame, 
            text="注意: 會話刷新間隔應小於會話有效時間，建議差值約30秒",
            bg=COLORS["card"], fg=COLORS["light_text"], wraplength=350, justify=tk.LEFT)
        session_info.grid(row=8, column=0, sticky=tk.W, padx=15, pady=(5, 0))
        
        # 為會話設定添加詳細工具提示
        session_tooltip_text = (
            "會話維持設定說明：\n\n"
            "會話刷新間隔：系統會每隔此設定的時間自動訪問一次系統以保持會話活躍。\n"
            "會話有效時間：系統假設會話在此時間內有效，超過此時間將重新登入。\n\n"
            "建議設定：\n"
            "- 會話刷新間隔：240秒（4分鐘）\n"
            "- 會話有效時間：270秒（4.5分鐘）\n\n"
            "這樣可以確保系統在會話過期前進行刷新，避免需要重新登入。"
        )
        add_tooltip(session_info, session_tooltip_text)
        
        # 通知設定
        notification_frame = tk.Frame(general_frame, bg=COLORS["card"])
        notification_frame.grid(row=9, column=0, sticky=tk.W, padx=15, pady=(20,5))
        
        tk.Label(notification_frame, text="通知顯示時間:", bg=COLORS["card"]).pack(side=tk.LEFT)
        
        self.notification_duration_var = tk.IntVar(value=settings.get("notification_duration", 5))
        duration_spinbox = ttk.Spinbox(notification_frame, from_=1, to=10, increment=1, 
                   textvariable=self.notification_duration_var, width=3)
        duration_spinbox.pack(side=tk.LEFT, padx=5)
        
        tk.Label(notification_frame, text="秒", bg=COLORS["card"]).pack(side=tk.LEFT)
        
        # 為通知設定添加工具提示
        notify_tooltip_text = (
            "通知設定說明：\n\n"
            "通知顯示時間：控制桌面通知在螢幕上顯示的時間長度。\n"
            "較長的顯示時間使您有更多時間閱讀通知內容，\n"
            "但可能會占用螢幕空間更久。\n\n"
            "建議時間：3-5秒"
        )
        add_tooltip(duration_spinbox, notify_tooltip_text)
        
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
        
        # 網絡設定選項卡內容
        # 第二躍點檢測設定
        tk.Label(network_frame, text="校內網絡檢測設定", font=("Arial", 11, "bold"), 
                 bg=COLORS["card"], fg=COLORS["text"]).grid(row=0, column=0, columnspan=3, sticky=tk.W, pady=(0,15))
        
        # 啟用第二躍點檢測
        self.enable_second_hop_var = tk.BooleanVar(value=settings.get("enable_second_hop", False))
        ttk.Checkbutton(network_frame, text="啟用第二躍點檢測", 
                      variable=self.enable_second_hop_var).grid(row=1, column=0, sticky=tk.W, padx=15)
        
        tk.Label(network_frame, text="當本機IP非163.23開頭時，檢測路由第二躍點是否為校內網絡", 
                 bg=COLORS["card"], fg=COLORS["light_text"], wraplength=350, justify=tk.LEFT).grid(
                 row=2, column=0, columnspan=3, sticky=tk.W, padx=25, pady=(0, 10))
        
        # 第二躍點檢測超時設定
        timeout_frame = tk.Frame(network_frame, bg=COLORS["card"])
        timeout_frame.grid(row=3, column=0, sticky=tk.W, padx=15, pady=5)
        
        tk.Label(timeout_frame, text="第二躍點檢測超時時間:", bg=COLORS["card"]).pack(side=tk.LEFT, padx=(0,5))
        self.hop_timeout_var = tk.IntVar(value=settings.get("hop_check_timeout", 10))
        ttk.Spinbox(timeout_frame, from_=1, to=10, increment=1, 
                   textvariable=self.hop_timeout_var, width=3).pack(side=tk.LEFT)
        tk.Label(timeout_frame, text="秒", bg=COLORS["card"]).pack(side=tk.LEFT, padx=5)
        
        # 檢測說明
        tk.Label(network_frame, text="檢測方式說明:", font=("Arial", 10, "bold"), 
                 bg=COLORS["card"], fg=COLORS["text"]).grid(row=4, column=0, sticky=tk.W, padx=15, pady=(20, 5))
        
        detection_info = (
            "1. 首先檢查本機IP是否為163.23開頭\n"
            "2. 如果不是，檢查默認閘道器IP（快速檢測）\n"
            "3. 如果閘道器IP也不是校內網絡，使用tracert命令檢測第二躍點\n"
            "4. 如果檢測超時，將使用緩存的上次結果"
        )
        
        tk.Label(network_frame, text=detection_info, 
                 bg=COLORS["card"], fg=COLORS["light_text"], wraplength=350, justify=tk.LEFT).grid(
                 row=5, column=0, columnspan=3, sticky=tk.W, padx=25, pady=(0, 10))
        
        # 超時機制說明
        tk.Label(network_frame, text="超時與性能說明:", font=("Arial", 10, "bold"), 
                 bg=COLORS["card"], fg=COLORS["text"]).grid(row=6, column=0, sticky=tk.W, padx=15, pady=(10, 5))
        
        timeout_info = (
            "• 設定較短的超時時間可減少應用程式卡頓，但可能降低檢測準確性\n"
            "• 檢測會在背景線程中執行，不會阻塞主界面\n"
            "• 檢測結果會自動緩存60秒，以減少系統資源使用\n"
            "• 如果檢測中斷或超時，將使用前次有效結果"
        )
        
        tk.Label(network_frame, text=timeout_info, 
                 bg=COLORS["card"], fg=COLORS["light_text"], wraplength=350, justify=tk.LEFT).grid(
                 row=7, column=0, columnspan=3, sticky=tk.W, padx=25, pady=(0, 10))
        
        # VPN 設置內容
        vpn_label = ttk.LabelFrame(vpn_frame, text="VPN 設置")
        vpn_label.pack(fill=tk.X, padx=10, pady=5)
        
        self.vpn_var = tk.BooleanVar(value=settings.get("use_vpn", False))
        self.vpn_checkbox = ttk.Checkbutton(
            vpn_label,
            text="啟用 VPN",
            variable=self.vpn_var,
            command=self._on_vpn_toggle
        )
        self.vpn_checkbox.pack(anchor=tk.W, padx=5, pady=5)
        
        # Docker 狀態框架
        docker_frame = ttk.LabelFrame(vpn_frame, text="Docker 狀態")
        docker_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # Docker 狀態標籤
        self.docker_status_label = ttk.Label(
            docker_frame,
            text="等待檢查...",
            foreground="gray"
        )
        self.docker_status_label.pack(anchor=tk.W, padx=5, pady=5)
        
        # 安裝按鈕（初始隱藏）
        self.install_button = ModernButton(
            docker_frame,
            text="安裝 Docker",
            command=self._on_docker_install_click
        )
        self.install_button.pack(anchor=tk.W, padx=5, pady=5)
        self.install_button.pack_forget()  # 初始時隱藏按鈕
        
        # 設置最小窗口大小，確保按鈕始終可見
        self.dialog.update_idletasks()
        self.dialog.minsize(500, 450)  # 增加最小高度
        
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
    
    def log(self, message):
        """在測試登入時記錄日誌"""
        print(f"[設定] {message}")  # 簡單輸出到控制台
    
    def on_save(self):
        # 更新設定
        try:
            # 驗證設定值
            try:
                check_interval = int(self.interval_var.get())
                session_refresh = int(self.session_refresh_var.get())
                session_valid = int(self.session_valid_var.get())
                notification_duration = int(self.notification_duration_var.get())
                hop_timeout = int(self.hop_timeout_var.get())
            except ValueError:
                messagebox.showerror("格式錯誤", "請確保所有數值設定為有效數字")
                return
            
            # 驗證會話維持時間邏輯
            if session_refresh >= session_valid:
                messagebox.showwarning("設定警告", "會話刷新間隔應小於會話有效時間。已自動調整為有效值。")
                # 自動調整，刷新間隔設為有效時間的90%
                session_refresh = int(session_valid * 0.9)
                self.session_refresh_var.set(session_refresh)
            
            # 獲取基本設定
            self.settings["global_notify"] = self.notify_var.get()
            self.settings["auto_start"] = self.autostart_var.get()
            self.settings["check_interval"] = check_interval
            self.settings["session_refresh_interval"] = session_refresh
            self.settings["session_valid_time"] = session_valid
            self.settings["notification_duration"] = notification_duration
            
            # 獲取網絡設定
            self.settings["enable_second_hop"] = self.enable_second_hop_var.get()
            self.settings["hop_check_timeout"] = hop_timeout
            
            # 獲取API設定
            self.settings["login_url"] = self.login_url_var.get().strip()
            self.settings["api_url"] = self.api_url_var.get().strip()
            self.settings["sign_in_url"] = self.sign_in_url_var.get().strip()
            self.settings["sign_out_url"] = self.sign_out_url_var.get().strip()
            
            # 獲取登入設定
            self.settings["username"] = self.username_var.get().strip()
            self.settings["password"] = self.password_var.get()
            
            # 獲取用戶資訊
            self.settings["name"] = self.name_var.get().strip()
            
            # 獲取默認時間設定
            try:
                # 格式化為HH:MM格式
                sign_in_hour = int(self.default_sign_in_hour.get())
                sign_in_minute = int(self.default_sign_in_minute.get())
                sign_out_hour = int(self.default_sign_out_hour.get())
                sign_out_minute = int(self.default_sign_out_minute.get())
                
                # 驗證時間格式
                if not (0 <= sign_in_hour <= 23 and 0 <= sign_in_minute <= 59 and
                        0 <= sign_out_hour <= 23 and 0 <= sign_out_minute <= 59):
                    raise ValueError("無效的時間格式")
                
                self.settings["default_sign_in"] = f"{sign_in_hour:02d}:{sign_in_minute:02d}"
                self.settings["default_sign_out"] = f"{sign_out_hour:02d}:{sign_out_minute:02d}"
            except ValueError:
                messagebox.showerror("時間格式錯誤", "請確保時間格式為有效的小時(0-23)和分鐘(0-59)")
                return
            
            # 保存 VPN 設置
            self.settings["use_vpn"] = self.vpn_var.get()
            
            self.result = self.settings
            self.dialog.destroy()
            
        except Exception as e:
            messagebox.showerror("保存設定失敗", f"發生錯誤: {str(e)}")
            self.log(f"保存設定時發生錯誤: {str(e)}")
            return
    
    def on_cancel(self):
        self.dialog.destroy()

    def _check_docker_status(self):
        """檢查 Docker 安裝和運行狀態
        
        Returns:
            tuple: (is_installed, is_running, error_message)
        """
        try:
            # 在 Windows 上檢查 Docker Desktop 的安裝路徑
            docker_paths = [
                r"C:\Program Files\Docker\Docker\Docker Desktop.exe",
                r"C:\Program Files\Docker\Docker\resources\bin\docker.exe"
            ]
            docker_installed = any(os.path.exists(path) for path in docker_paths)
            
            if not docker_installed:
                self.log("未在標準路徑找到 Docker Desktop")
                # 嘗試通過命令檢查
                try:
                    result = subprocess.run(
                        ["where", "docker"],
                        capture_output=True,
                        text=True,
                        check=True
                    )
                    docker_installed = bool(result.stdout.strip())
                    self.log(f"通過 where 命令找到 docker: {result.stdout.strip()}")
                except subprocess.CalledProcessError:
                    self.log("where docker 命令失敗")
                    return False, False, "Docker 未安裝"
            
            if docker_installed:
                # Docker 已安裝，檢查服務狀態
                try:
                    subprocess.run(
                        ["docker", "info"],
                        capture_output=True,
                        text=True,
                        check=True
                    )
                    return True, True, "Docker 已安裝且運行中"
                except subprocess.CalledProcessError:
                    return True, False, "Docker 已安裝但未運行"
            
            return False, False, "Docker 未安裝"
            
        except Exception as e:
            self.log(f"檢查 Docker 時發生錯誤: {str(e)}")
            return False, False, f"檢查 Docker 狀態時發生錯誤：{str(e)}"

    def _update_docker_ui(self, is_installed, is_running, message):
        """更新 Docker 相關的 UI 狀態
        
        Args:
            is_installed (bool): Docker 是否已安裝
            is_running (bool): Docker 是否正在運行
            message (str): 狀態訊息
        """
        if is_installed and is_running:
            self.docker_status_label.config(
                text=message,
                foreground="green"
            )
            self.install_button.pack_forget()
        elif is_installed and not is_running:
            self.docker_status_label.config(
                text=message,
                foreground="orange"
            )
            self.install_button.pack_forget()
        else:
            self.docker_status_label.config(
                text=message,
                foreground="red"
            )
            self.install_button.pack(anchor=tk.W, padx=5, pady=5)

    def _on_vpn_toggle(self):
        """處理 VPN 開關切換事件"""
        if self.vpn_var.get():  # 當 VPN 被啟用時
            self.log("VPN 已啟用，檢查 Docker 安裝狀態")
            is_installed, is_running, message = self._check_docker_status()
            
            self._update_docker_ui(is_installed, is_running, message)
            
            if not is_installed:
                messagebox.showwarning(
                    "需要 Docker",
                    "使用 VPN 功能需要安裝 Docker Desktop。\n請點擊下方的安裝按鈕進行安裝。",
                    parent=self.dialog
                )
                self.vpn_var.set(False)
            elif not is_running:
                messagebox.showwarning(
                    "Docker 未運行",
                    "Docker Desktop 已安裝但未運行。\n請先啟動 Docker Desktop 再啟用 VPN。",
                    parent=self.dialog
                )
                self.vpn_var.set(False)
        else:
            # VPN 被禁用時，隱藏安裝按鈕並重置狀態
            self.log("VPN 已禁用")
            self.docker_status_label.config(
                text="等待檢查...",
                foreground="gray"
            )
            self.install_button.pack_forget()

    def _on_docker_install_click(self):
        """處理 Docker 安裝按鈕點擊事件"""
        self.log("用戶點擊安裝 Docker 按鈕")
        try:
            # 打開 Docker Desktop 下載頁面
            webbrowser.open("https://www.docker.com/products/docker-desktop")
            messagebox.showinfo(
                "安裝 Docker",
                "請下載並安裝 Docker Desktop。\n安裝完成後，請重新啟動應用程式並再次啟用 VPN。",
                parent=self.dialog
            )
        except Exception as e:
            self.log(f"打開 Docker 下載頁面時發生錯誤: {str(e)}")
            messagebox.showerror(
                "打開失敗",
                f"無法打開 Docker 下載頁面：{str(e)}",
                parent=self.dialog
            )

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
