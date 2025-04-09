# -*- coding: utf-8 -*-
"""
文件操作工具
"""

import json
import os
from chronohelper.models.task import Task
from chronohelper.utils.encryption import SettingsEncryption

class FileHandler:
    """文件讀寫處理器"""
    
    def __init__(self, logger):
        """初始化文件處理器
        
        Args:
            logger: 日誌記錄器實例
        """
        self.logger = logger
        self.config_file = "chronohelper_tasks.json"
        self.settings_file = "chronohelper_settings.json"
        self.cookie_file = "chronohelper_cookies.json"
    
    def load_tasks(self):
        """從配置文件讀取任務列表
        
        Returns:
            list: 任務對象列表
        """
        tasks = []
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    tasks_data = json.load(f)
                    tasks = [Task.from_dict(task_data) for task_data in tasks_data]
                self.logger.log(f"成功載入 {len(tasks)} 個任務")
            except Exception as e:
                self.logger.log(f"載入任務失敗: {str(e)}")
        return tasks
    
    def save_tasks(self, tasks):
        """保存任務列表到配置文件
        
        Args:
            tasks: 任務對象列表
            
        Returns:
            bool: 保存是否成功
        """
        try:
            tasks_data = [task.to_dict() for task in tasks]
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(tasks_data, f, indent=2)
            return True
        except Exception as e:
            self.logger.log(f"保存任務失敗: {str(e)}")
            return False
    
    def load_settings(self, default_settings):
        """載入應用設定
        
        Args:
            default_settings: 默認設定字典
            
        Returns:
            dict: 設定字典
        """
        if os.path.exists(self.settings_file):
            try:
                with open(self.settings_file, 'r', encoding='utf-8') as f:
                    settings = json.load(f)
                    
                    # 解密敏感數據
                    try:
                        if 'username' in settings and settings['username']:
                            settings['username'] = SettingsEncryption.decrypt_data(settings['username'])
                        if 'password' in settings and settings['password']:
                            settings['password'] = SettingsEncryption.decrypt_data(settings['password'])
                    except Exception as e:
                        self.logger.log(f"解密設定失敗: {str(e)}")
                    
                    return settings
            except Exception as e:
                self.logger.log(f"載入設定失敗: {str(e)}")
        return default_settings.copy()
    
    def save_settings(self, settings):
        """保存應用設定
        
        Args:
            settings: 設定字典
            
        Returns:
            bool: 保存是否成功
        """
        try:
            # 創建設定的副本
            settings_to_save = settings.copy()
            
            # 加密敏感數據
            if 'username' in settings_to_save and settings_to_save['username']:
                settings_to_save['username'] = SettingsEncryption.encrypt_data(settings_to_save['username'])
            if 'password' in settings_to_save and settings_to_save['password']:
                settings_to_save['password'] = SettingsEncryption.encrypt_data(settings_to_save['password'])
            
            with open(self.settings_file, 'w', encoding='utf-8') as f:
                json.dump(settings_to_save, f, indent=2)
            return True
        except Exception as e:
            self.logger.log(f"保存設定失敗: {str(e)}")
            return False
    
    def load_cookies(self):
        """載入保存的Cookie
        
        Returns:
            list: Cookie字典列表
        """
        if os.path.exists(self.cookie_file):
            try:
                with open(self.cookie_file, 'r', encoding='utf-8') as f:
                    cookies = json.load(f)
                    self.logger.log("成功載入已保存的Cookie")
                    return cookies
            except Exception as e:
                self.logger.log(f"載入Cookie失敗: {str(e)}")
        return []
    
    def save_cookies(self, cookies_list):
        """保存Cookie
        
        Args:
            cookies_list: Cookie字典列表
            
        Returns:
            bool: 保存是否成功
        """
        try:
            with open(self.cookie_file, 'w', encoding='utf-8') as f:
                json.dump(cookies_list, f)
            self.logger.log("已保存Cookie")
            return True
        except Exception as e:
            self.logger.log(f"保存Cookie失敗: {str(e)}")
            return False
