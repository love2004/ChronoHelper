# -*- coding: utf-8 -*-

"""
網絡服務 - 處理網絡狀態檢測
"""

import re
import socket
import threading
import time
import requests
from requests.exceptions import RequestException

class NetworkService:
    """網絡服務類，處理網絡狀態檢測"""
    
    def __init__(self, settings, logger=None):
        """初始化網絡服務
        
        Args:
            settings: 應用設置字典
            logger: 可選的日誌記錄器
        """
        self.settings = settings
        self.logger = logger
        self.network_status = {
            "is_campus": None,
            "ip_address": None,
            "last_check_time": 0,
            "status_message": "未檢查網絡"
        }
        self.check_thread = None
    
    def log(self, message):
        """記錄日誌消息
        
        Args:
            message: 要記錄的消息
        """
        if self.logger:
            self.logger.log(message)
    
    def get_ip_address(self):
        """獲取當前IP地址
        
        Returns:
            str: IP地址或None（如果無法獲取）
        """
        try:
            # 創建一個到外部服務器的UDP連接以獲取本地IP
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except Exception as e:
            self.log(f"獲取IP地址時出錯: {str(e)}")
            return None
    
    def check_campus_network(self, verbose=True):
        """檢查是否在校園網絡環境
        
        Args:
            verbose: 是否記錄詳細日誌
            
        Returns:
            dict: 網絡狀態信息
        """
        # 如果上次檢查後不久，直接返回緩存的結果
        current_time = time.time()
        if current_time - self.network_status["last_check_time"] < 60 and self.network_status["is_campus"] is not None:
            return self.network_status
            
        # 獲取IP地址
        ip_address = self.get_ip_address()
        
        if ip_address:
            # 檢查是否是校園網IP
            is_campus = False
            campus_ip_pattern = r'^10\.|^172\.16\.|^192\.168\.'  # 常見的私有IP範圍
            
            if re.match(campus_ip_pattern, ip_address):
                is_campus = True
            
            # 更新狀態
            self.network_status = {
                "is_campus": is_campus,
                "ip_address": ip_address,
                "last_check_time": current_time,
                "status_message": f"{'校園網絡' if is_campus else '外部網絡'} ({ip_address})"
            }
            
            if verbose:
                self.log(f"網絡檢測: {self.network_status['status_message']}")
        else:
            # 無法獲取IP
            self.network_status = {
                "is_campus": None,
                "ip_address": None,
                "last_check_time": current_time,
                "status_message": "無法檢測網絡環境"
            }
            
            if verbose:
                self.log("網絡檢測失敗: 無法獲取IP地址")
        
        return self.network_status
    
    def test_connection(self, url=None):
        """測試網絡連接
        
        Args:
            url: 要測試的URL，默認使用API設置中的URL
            
        Returns:
            dict: 連接測試結果
        """
        if url is None:
            url = self.settings.get("api_url", "https://www.google.com")
            
        try:
            self.log(f"測試網絡連接: {url}")
            start_time = time.time()
            response = requests.get(url, timeout=10, verify=False)
            response_time = time.time() - start_time
            
            return {
                "success": True,
                "status_code": response.status_code,
                "response_time": round(response_time * 1000),  # 轉換為毫秒
                "message": f"連接成功: HTTP {response.status_code} ({round(response_time * 1000)}ms)"
            }
        except RequestException as e:
            self.log(f"網絡連接測試失敗: {str(e)}")
            return {
                "success": False,
                "status_code": None,
                "response_time": None,
                "message": f"連接失敗: {str(e)}"
            }
    
    def start_periodic_check(self, interval=300):
        """啟動定期網絡檢查
        
        Args:
            interval: 檢查間隔（秒）
            
        Returns:
            bool: 是否成功啟動
        """
        if self.check_thread and self.check_thread.is_alive():
            return False
            
        def check_loop():
            while True:
                try:
                    self.check_campus_network(verbose=False)
                except Exception as e:
                    self.log(f"定期網絡檢查錯誤: {str(e)}")
                time.sleep(interval)
        
        self.check_thread = threading.Thread(target=check_loop, daemon=True)
        self.check_thread.start()
        self.log(f"已啟動定期網絡檢查，間隔 {interval} 秒")
        return True 