# -*- coding: utf-8 -*-
"""
VPN設定選項卡
"""

import tkinter as tk
from tkinter import ttk, messagebox
import os
import subprocess
import webbrowser
from chronohelper.config.colors import COLORS
from chronohelper.ui.base import ModernButton
from chronohelper.ui.components.dialogs.settings.base_settings_tab import BaseSettingsTab

class VPNTab(BaseSettingsTab):
    """VPN設定選項卡"""
    def create_widgets(self):
        """創建UI元素"""
        # 添加開發中提示
        dev_frame = tk.Frame(self, bg=COLORS["warning_light"], padx=10, pady=10)
        dev_frame.pack(fill=tk.X, padx=5, pady=5)
        
        dev_label = tk.Label(
            dev_frame,
            text="⚠️ VPN 功能開發中 ⚠️\n此功能尚未完全實現，可能無法正常運作",
            bg=COLORS["warning_light"],
            fg=COLORS["warning_text"],
            font=("Arial", 11, "bold"),
            padx=10,
            pady=10,
            wraplength=350,
            justify=tk.CENTER
        )
        dev_label.pack(fill=tk.X)
        
        # VPN 設置內容
        vpn_label = ttk.LabelFrame(self, text="VPN 設置")
        vpn_label.pack(fill=tk.X, padx=10, pady=5)
        
        self.vpn_var = tk.BooleanVar(value=self.settings.get("use_vpn", False))
        self.vpn_checkbox = ttk.Checkbutton(
            vpn_label,
            text="啟用 VPN",
            variable=self.vpn_var,
            command=self._on_vpn_toggle
        )
        self.vpn_checkbox.pack(anchor=tk.W, padx=5, pady=5)
        
        # Docker 狀態框架
        docker_frame = ttk.LabelFrame(self, text="Docker 狀態")
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
        
        # 在初始化時檢查Docker狀態
        if self.vpn_var.get():
            self._check_docker_status_and_update_ui()
    
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
    
    def _check_docker_status_and_update_ui(self):
        """檢查 Docker 狀態並更新 UI"""
        is_installed, is_running, message = self._check_docker_status()
        self._update_docker_ui(is_installed, is_running, message)
        return is_installed, is_running
    
    def _on_vpn_toggle(self):
        """處理 VPN 開關切換事件"""
        if self.vpn_var.get():  # 當 VPN 被啟用時
            self.log("VPN 已啟用，檢查 Docker 安裝狀態")
            is_installed, is_running = self._check_docker_status_and_update_ui()
            
            if not is_installed:
                messagebox.showwarning(
                    "需要 Docker",
                    "使用 VPN 功能需要安裝 Docker Desktop。\n請點擊下方的安裝按鈕進行安裝。",
                    parent=self.winfo_toplevel()
                )
                self.vpn_var.set(False)
            elif not is_running:
                messagebox.showwarning(
                    "Docker 未運行",
                    "Docker Desktop 已安裝但未運行。\n請先啟動 Docker Desktop 再啟用 VPN。",
                    parent=self.winfo_toplevel()
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
                parent=self.winfo_toplevel()
            )
        except Exception as e:
            self.log(f"打開 Docker 下載頁面時發生錯誤: {str(e)}")
            messagebox.showerror(
                "打開失敗",
                f"無法打開 Docker 下載頁面：{str(e)}",
                parent=self.winfo_toplevel()
            )
    
    def log(self, message):
        """記錄日誌"""
        print(f"[VPN設定] {message}")  # 簡單輸出到控制台
    
    def validate(self):
        """驗證輸入
        
        Returns:
            bool: 輸入是否有效
        """
        if self.vpn_var.get():
            # 如果啟用VPN，檢查Docker是否已安裝並運行
            is_installed, is_running = self._check_docker_status_and_update_ui()
            if not (is_installed and is_running):
                messagebox.showwarning(
                    "VPN 設置無效",
                    "無法啟用 VPN，因為 Docker 未安裝或未運行。",
                    parent=self.winfo_toplevel()
                )
                self.vpn_var.set(False)
                return False
        return True
    
    def get_settings(self):
        """獲取設定
        
        Returns:
            dict: 選項卡的設定
        """
        return {
            "use_vpn": self.vpn_var.get()
        } 