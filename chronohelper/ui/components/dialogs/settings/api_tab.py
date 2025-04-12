# -*- coding: utf-8 -*-
"""
API設定選項卡
"""

import tkinter as tk
from tkinter import ttk, messagebox
import requests
from requests.exceptions import RequestException
from bs4 import BeautifulSoup
import re
from chronohelper.config.colors import COLORS
from chronohelper.ui.base import ModernButton
from chronohelper.ui.components.dialogs.settings.base_settings_tab import BaseSettingsTab

class APITab(BaseSettingsTab):
    """API設定選項卡"""
    def create_widgets(self):
        """創建UI元素"""
        tk.Label(self, text="API連接設定", font=("Arial", 11, "bold"), 
                 bg=COLORS["card"], fg=COLORS["text"]).grid(row=0, column=0, columnspan=2, sticky=tk.W, pady=(0,15))
        
        tk.Label(self, text="登入URL:", bg=COLORS["card"]).grid(row=1, column=0, sticky=tk.W, padx=(15,5), pady=5)
        self.login_url_var = tk.StringVar(value=self.settings.get("login_url", ""))
        ttk.Entry(self, textvariable=self.login_url_var, width=40).grid(row=1, column=1, sticky=tk.W, pady=5)
        
        tk.Label(self, text="API基礎URL:", bg=COLORS["card"]).grid(row=2, column=0, sticky=tk.W, padx=(15,5), pady=5)
        self.api_url_var = tk.StringVar(value=self.settings.get("api_url", ""))
        ttk.Entry(self, textvariable=self.api_url_var, width=40).grid(row=2, column=1, sticky=tk.W, pady=5)
        
        tk.Label(self, text="簽到URL:", bg=COLORS["card"]).grid(row=3, column=0, sticky=tk.W, padx=(15,5), pady=5)
        self.sign_in_url_var = tk.StringVar(value=self.settings.get("sign_in_url", ""))
        ttk.Entry(self, textvariable=self.sign_in_url_var, width=40).grid(row=3, column=1, sticky=tk.W, pady=5)
        
        tk.Label(self, text="簽退URL:", bg=COLORS["card"]).grid(row=4, column=0, sticky=tk.W, padx=(15,5), pady=5)
        self.sign_out_url_var = tk.StringVar(value=self.settings.get("sign_out_url", ""))
        ttk.Entry(self, textvariable=self.sign_out_url_var, width=40).grid(row=4, column=1, sticky=tk.W, pady=5)
        
        tk.Label(self, text="用戶名:", bg=COLORS["card"]).grid(row=5, column=0, sticky=tk.W, padx=(15,5), pady=5)
        self.username_var = tk.StringVar(value=self.settings.get("username", ""))
        ttk.Entry(self, textvariable=self.username_var, width=30).grid(row=5, column=1, sticky=tk.W, pady=5)
        
        tk.Label(self, text="密碼:", bg=COLORS["card"]).grid(row=6, column=0, sticky=tk.W, padx=(15,5), pady=5)
        self.password_var = tk.StringVar(value=self.settings.get("password", ""))
        ttk.Entry(self, textvariable=self.password_var, show="*", width=30).grid(row=6, column=1, sticky=tk.W, pady=5)
        
        # 測試連接按鈕和測試登入按鈕
        button_frame = tk.Frame(self, bg=COLORS["card"])
        button_frame.grid(row=7, column=1, sticky=tk.W, pady=15)
        
        test_connection_button = ModernButton(button_frame, text="測試連接", 
                                            command=self.test_connection, padx=10, pady=5)
        test_connection_button.pack(side=tk.LEFT, padx=(0,10))
        
        test_login_button = ModernButton(button_frame, text="測試登入", 
                                       command=self.test_login, padx=10, pady=5)
        test_login_button.pack(side=tk.LEFT)
    
    def test_connection(self):
        """測試API連接"""
        api_url = self.api_url_var.get().strip()
        
        if not api_url:
            messagebox.showwarning("警告", "請輸入API URL", parent=self.winfo_toplevel())
            return
        
        try:
            self.winfo_toplevel().config(cursor="wait")
            self.winfo_toplevel().update()
            
            response = requests.get(api_url, timeout=10)
            
            if response.status_code == 200:
                messagebox.showinfo("連接成功", f"成功連接到API服務器", parent=self.winfo_toplevel())
            else:
                messagebox.showwarning("連接警告", f"連接返回非200狀態碼: {response.status_code}", parent=self.winfo_toplevel())
        except Exception as e:
            messagebox.showerror("連接失敗", f"無法連接到API服務器: {str(e)}", parent=self.winfo_toplevel())
        finally:
            self.winfo_toplevel().config(cursor="")
            self.winfo_toplevel().update()
    
    def test_login(self):
        """測試大葉大學系統登入"""
        username = self.username_var.get().strip()
        password = self.password_var.get().strip()
        
        if not username or not password:
            messagebox.showwarning("警告", "請輸入用戶名和密碼", parent=self.winfo_toplevel())
            return
        
        # 創建臨時測試對象
        try:
            self.winfo_toplevel().config(cursor="wait")
            self.winfo_toplevel().update()
            
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
                            parent=self.winfo_toplevel()
                        )
                        
                        if result == "yes":
                            # 獲取UserTab並更新姓名
                            for tab in self.winfo_toplevel().children.values():
                                if hasattr(tab, 'name_var'):  # 假設UserTab有name_var
                                    tab.name_var.set(actual_name)
                                    break
                    else:
                        messagebox.showinfo(
                            "登入結果", 
                            "已連接系統，但無法自動檢測用戶姓名。\n請手動確認登入狀態。",
                            parent=self.winfo_toplevel()
                        )
                else:
                    # 檢查特定錯誤
                    if "密碼錯誤" in response.text or "帳號不存在" in response.text:
                        messagebox.showerror("登入失敗", "帳號或密碼錯誤", parent=self.winfo_toplevel())
                    elif "登出" in response.text:
                        messagebox.showinfo(
                            "登入結果", 
                            "登入似乎成功，但無法檢測用戶信息。\n頁面結構可能已變更。",
                            parent=self.winfo_toplevel()
                        )
                    else:
                        messagebox.showwarning(
                            "未知結果", 
                            "無法確定登入結果。請手動檢查帳號信息。",
                            parent=self.winfo_toplevel()
                        )
            else:
                messagebox.showerror(
                    "連接錯誤", 
                    f"連接服務器失敗，狀態碼: {response.status_code}",
                    parent=self.winfo_toplevel()
                )
        
        except RequestException as e:
            self.log(f"登入過程中發生網絡錯誤: {str(e)}")
            messagebox.showerror("網絡錯誤", f"連接服務器失敗: {str(e)}", parent=self.winfo_toplevel())
        except Exception as e:
            self.log(f"登入過程中發生未知錯誤: {str(e)}")
            import traceback
            self.log(traceback.format_exc())
            messagebox.showerror("未知錯誤", f"測試過程中發生錯誤: {str(e)}", parent=self.winfo_toplevel())
        finally:
            # 確保無論何種情況都會重置游標狀態
            self.winfo_toplevel().config(cursor="")
            self.winfo_toplevel().update()
    
    def log(self, message):
        """在測試登入時記錄日誌"""
        print(f"[API設定] {message}")  # 簡單輸出到控制台
    
    def validate(self):
        """驗證輸入
        
        Returns:
            bool: 輸入是否有效
        """
        return True
    
    def get_settings(self):
        """獲取設定
        
        Returns:
            dict: 選項卡的設定
        """
        return {
            "login_url": self.login_url_var.get().strip(),
            "api_url": self.api_url_var.get().strip(),
            "sign_in_url": self.sign_in_url_var.get().strip(),
            "sign_out_url": self.sign_out_url_var.get().strip(),
            "username": self.username_var.get().strip(),
            "password": self.password_var.get()
        } 