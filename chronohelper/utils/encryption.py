# -*- coding: utf-8 -*-
"""
敏感數據加密解密功能
"""

import os
import hashlib
import base64
from cryptography.fernet import Fernet

class SettingsEncryption:
    """設定檔加密管理"""
    
    @staticmethod
    def get_encryption_key(salt=None):
        """生成或獲取加密密鑰"""
        key_file = "chronohelper.key"
        
        if os.path.exists(key_file):
            # 讀取現有密鑰
            with open(key_file, 'rb') as f:
                key = f.read()
        else:
            # 創建新密鑰
            if salt is None:
                salt = os.urandom(16)
            
            # 使用機器特有的識別信息生成密鑰
            machine_info = f"{os.getlogin()}_{os.name}"
            key_base = hashlib.pbkdf2_hmac(
                'sha256', 
                machine_info.encode(), 
                salt, 
                100000
            )
            
            # 轉換為Fernet可用的格式
            key = base64.urlsafe_b64encode(key_base)
            
            # 保存密鑰
            with open(key_file, 'wb') as f:
                f.write(key)
        
        return key
    
    @staticmethod
    def encrypt_data(data):
        """加密數據"""
        if not isinstance(data, str):
            return data
        
        key = SettingsEncryption.get_encryption_key()
        cipher = Fernet(key)
        return cipher.encrypt(data.encode()).decode()
    
    @staticmethod
    def decrypt_data(encrypted_data):
        """解密數據"""
        if not isinstance(encrypted_data, str):
            return encrypted_data
        
        try:
            key = SettingsEncryption.get_encryption_key()
            cipher = Fernet(key)
            return cipher.decrypt(encrypted_data.encode()).decode()
        except Exception:
            return encrypted_data  # 如果解密失敗，返回原數據
