# -*- coding: utf-8 -*-
"""
網絡檢測功能
"""

import socket

class NetworkUtils:
    """網絡工具類"""
    
    def __init__(self, logger):
        """初始化網絡工具
        
        Args:
            logger: 日誌記錄器實例
        """
        self.logger = logger
    
    def check_campus_network(self, verbose=True):
        """檢測是否在校內網絡環境（163.23.x.x）
        
        Args:
            verbose: 是否輸出檢測過程的日誌，默認為True
            
        Returns:
            tuple: (is_campus, ip_address) 是否在校內網絡和當前IP地址
        """
        try:
            # 獲取本機名稱和IP地址
            hostname = socket.gethostname()
            ip_address = socket.gethostbyname(hostname)
            
            # 檢查IP地址是否符合校內網絡特徵
            is_campus = ip_address.startswith('163.23.')
            
            if verbose:
                self.logger.log(f"檢測到本地IP地址: {ip_address}")
                
            return is_campus, ip_address
            
        except Exception as e:
            if verbose:
                self.logger.log(f"IP地址檢測失敗: {str(e)}")
            return False, "未知"
