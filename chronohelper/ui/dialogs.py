# -*- coding: utf-8 -*-
"""
對話框UI元件
"""

import tkinter as tk
from tkinter import ttk, messagebox
import datetime
import re
import requests
from requests.exceptions import RequestException
from bs4 import BeautifulSoup

from chronohelper.config.colors import COLORS
from chronohelper.ui.base import ModernButton

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
    
    def log(self, message):
        """在測試登入時記錄日誌"""
        print(f"[設定] {message}")  # 簡單輸出到控制台
    
    def on_save(self):
        # 更新設定
        self.settings["global_notify"] = self.notify_var.get()
        self.settings["auto_start"] = self.autostart_var.get()
        self.settings["check_interval"] = self.interval_var.get()
        
        # 新增：保存會話維持設定
        self.settings["session_refresh_interval"] = self.session_refresh_var.get()
        self.settings["session_valid_time"] = self.session_valid_var.get()
        
        self.settings["api_url"] = self.api_url_var.get().strip() or "https://adm_acc.dyu.edu.tw/entrance/index.php"
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
