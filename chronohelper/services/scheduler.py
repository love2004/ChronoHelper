# -*- coding: utf-8 -*-
"""
任務調度服務
"""

import time
import datetime
import threading

class SchedulerService:
    """任務調度服務，負責自動執行到期任務"""
    
    def __init__(self, app):
        """初始化調度服務
        
        Args:
            app: 應用主類實例的引用
        """
        self.app = app
        self.running = True
        self.thread = None
        
        # 如果設置了自動啟動，則啟動調度線程
        if self.app.settings.get("auto_start", True):
            self.start()
    
    def start(self):
        """啟動調度線程"""
        if self.thread is None or not self.thread.is_alive():
            self.running = True
            self.thread = threading.Thread(target=self.scheduler_loop)
            self.thread.daemon = True
            self.thread.start()
            self.app.logger.log("調度器已啟動")
    
    def stop(self):
        """停止調度線程"""
        self.running = False
        if self.thread and self.thread.is_alive():
            self.thread.join(1)  # 等待線程結束，最多1秒
            self.app.logger.log("調度器已停止")
    
    def scheduler_loop(self):
        """調度器主循環"""
        # 首次啟動立即檢查一次
        self.check_tasks()
        
        while self.running:
            try:
                # 使用設定中的檢查間隔
                check_interval = self.app.settings.get("check_interval", 30)
                time.sleep(check_interval)
                
                if self.running:
                    self.check_tasks()
            except Exception as e:
                self.app.logger.log(f"調度器錯誤: {str(e)}")
                time.sleep(5)  # 出錯後稍等一下再繼續
    
    def check_tasks(self):
        """檢查並執行到期的任務"""
        # 首先刷新會話
        self.app.auth_service.keep_session_alive(self.app.settings)
        
        # 檢查網絡環境
        if not self.app.is_campus_network:
            now = datetime.datetime.now()
            
            # 檢查上次輸出日誌的時間和網絡狀態
            should_log = False
            
            if not hasattr(self.app, 'last_network_log_time') or self.app.last_network_log_time is None:
                # 首次檢測
                should_log = True
            elif (now - self.app.last_network_log_time).total_seconds() >= 300:
                # 至少間隔5分鐘
                should_log = True
            elif not hasattr(self.app, 'last_network_log_status') or self.app.last_network_log_status != self.app.is_campus_network:
                # 網絡狀態發生變化
                should_log = True
                
            if should_log:
                self.app.logger.log("檢測到校外網絡環境，跳過任務執行")
                self.app.last_network_log_time = now
                self.app.last_network_log_status = self.app.is_campus_network
                
            # 更新狀態欄但不記錄日誌
            self.app.status_var.set("校外網絡環境，任務已暫停")
            return  # 如果在校外網絡，直接跳過所有任務
        else:
            # 在校內網絡環境，更新記錄狀態
            self.app.last_network_log_status = self.app.is_campus_network
        
        # 檢查任務
        now = datetime.datetime.now()
        today = now.strftime("%Y-%m-%d")
        current_time = now.strftime("%H:%M")
        
        for task in self.app.tasks:
            if task.date == today:
                # 檢查任務是否被標記為環境受限
                if hasattr(task, 'campus_restricted') and task.campus_restricted:
                    # 如果上次嘗試時間在30分鐘內，則跳過
                    if task.last_attempt_time:
                        last_attempt = datetime.datetime.fromisoformat(task.last_attempt_time)
                        elapsed_minutes = (now - last_attempt).total_seconds() / 60
                        if elapsed_minutes < 30:  # 30分鐘內不重複嘗試
                            self.app.logger.log(f"任務 '{task.name}' 因校外環境限制暫停嘗試 (冷卻中: {int(30-elapsed_minutes)}分鐘)")
                            continue
                
                # 檢查簽到 - 只對未手動標記為已完成的任務執行
                if current_time >= task.sign_in_time and not task.sign_in_done:
                    result = self.app.perform_sign_in(task)
                    
                    # 檢查是否因為校外環境而失敗
                    if not result and self.app.status_var.get() == "簽到需要校內網絡環境":
                        task.campus_restricted = True
                        task.last_attempt_time = now.isoformat()
                        self.app.logger.log(f"任務 '{task.name}' 因校外環境限制暫時跳過，將在30分鐘後重試")
                        self.app.save_tasks()  # 儲存狀態
                    elif result:
                        # 成功簽到，清除環境限制標記
                        task.campus_restricted = False
                        task.sign_in_done = True
                        self.app.save_tasks()
                
                # 檢查簽退 - 只對已簽到但未簽退的任務執行
                if current_time >= task.sign_out_time and not task.sign_out_done and task.sign_in_done:
                    result = self.app.perform_sign_out(task)
                    
                    # 檢查是否因為校外環境而失敗
                    if not result and self.app.status_var.get() == "簽退需要校內網絡環境":
                        task.campus_restricted = True
                        task.last_attempt_time = now.isoformat()
                        self.app.logger.log(f"任務 '{task.name}' 因校外環境限制暫時跳過，將在30分鐘後重試")
                        self.app.save_tasks()  # 儲存狀態
                    elif result:
                        # 成功簽退，清除環境限制標記
                        task.campus_restricted = False
                        task.sign_out_done = True
                        self.app.save_tasks()
