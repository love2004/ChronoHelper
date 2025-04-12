# -*- coding: utf-8 -*-
"""
任務調度服務
"""

import time
import datetime
import threading
import random

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
        self.last_check_time = None
        # 從應用設定中讀取網絡檢測間隔
        self.network_check_interval = self.app.settings.get("network_check_interval", 300)
        self.last_network_check = None
        self.execution_stats = {
            "total_executions": 0,
            "successful_sign_ins": 0,
            "successful_sign_outs": 0,
            "failed_sign_ins": 0,
            "failed_sign_outs": 0,
            "last_success_time": None
        }
        
        # 如果設置了自動啟動，則啟動調度線程
        if self.app.settings.get("auto_start", True):
            self.start()
    
    def start(self):
        """啟動調度線程"""
        if self.thread is None or not self.thread.is_alive():
            self.running = True
            self.thread = threading.Thread(target=self.scheduler_loop, daemon=True)
            self.thread.daemon = True
            self.thread.start()
            self.app.logger.log("調度器已啟動")
    
    def stop(self):
        """停止調度線程"""
        self.running = False
        if self.thread and self.thread.is_alive():
            try:
                self.thread.join(2)  # 等待線程結束，最多2秒
                if self.thread.is_alive():
                    self.app.logger.log("調度器無法正常停止，強制中止")
                else:
                    self.app.logger.log("調度器已停止")
            except Exception as e:
                self.app.logger.log(f"停止調度器時發生錯誤: {str(e)}")
        else:
            self.app.logger.log("調度器已停止")
    
    def scheduler_loop(self):
        """調度器主循環，智能調整檢查頻率"""
        # 首次啟動時，先等待較長時間（確保應用程式和網絡檢測完全初始化完成）
        time.sleep(3)
        
        # 首次啟動立即檢查一次，但不重複進行網絡檢測
        self.check_tasks(is_initial_check=True, skip_network_check=True)
        
        # 延遲更長時間再啟動正常的循環，避免干擾初始UI更新和網絡檢測
        time.sleep(10)
        
        while self.running:
            try:
                now = datetime.datetime.now()
                
                # 智能調整檢查間隔
                check_interval = self._calculate_check_interval()
                
                # 執行任務檢查
                if self.running:
                    self.check_tasks()
                    self.last_check_time = now
                
                # 動態休眠時間，根據與下一個任務的接近程度調整
                sleep_time = max(5, min(check_interval, self._get_sleep_time_to_next_task()))
                
                # 添加少量隨機抖動，避免固定間隔
                sleep_time += random.uniform(-2, 2) if sleep_time > 10 else 0
                sleep_time = max(5, sleep_time)  # 確保最小間隔為5秒
                
                # 分段休眠，允許更快地響應停止命令
                segments = max(1, int(sleep_time / 5))
                for _ in range(segments):
                    if not self.running:
                        break
                    time.sleep(min(5, sleep_time / segments))
                
            except Exception as e:
                self.app.logger.log(f"調度器循環錯誤: {str(e)}")
                # 發生錯誤時，短暫休眠後繼續
                time.sleep(5)
    
    def _calculate_check_interval(self):
        """智能計算檢查間隔
        
        Returns:
            int: 建議的檢查間隔（秒）
        """
        # 從設定中讀取基礎檢查間隔
        base_interval = max(30, self.app.settings.get("check_interval", 30))
        
        # 獲取當前時間和今天的任務
        now = datetime.datetime.now()
        today = now.strftime("%Y-%m-%d")
        today_tasks = [task for task in self.app.tasks if task.date == today]
        
        # 如果今天沒有任務，使用較長間隔
        if not today_tasks:
            return max(base_interval, 300)  # 至少5分鐘
        
        # 計算距離最近任務的時間
        current_time = now.strftime("%H:%M")
        pending_sign_ins = []
        pending_sign_outs = []
        
        for task in today_tasks:
            # 檢查待執行的簽到
            if task.sign_in_time > current_time and not getattr(task, 'sign_in_done', False):
                pending_sign_ins.append(task.sign_in_time)
            
            # 檢查待執行的簽退
            if task.sign_out_time > current_time and getattr(task, 'sign_in_done', False) and not getattr(task, 'sign_out_done', False):
                pending_sign_outs.append(task.sign_out_time)
        
        # 找出最近的待執行任務時間
        next_times = pending_sign_ins + pending_sign_outs
        if not next_times:
            return base_interval  # 使用預設間隔
        
        next_time = min(next_times)
        next_dt = datetime.datetime.strptime(f"{today} {next_time}", "%Y-%m-%d %H:%M")
        minutes_to_next = max(0, (next_dt - now).total_seconds() / 60)
        
        # 根據距下一任務的時間動態調整檢查間隔
        if minutes_to_next < 5:  # 5分鐘內
            return max(15, int(base_interval / 2))  # 加快檢查頻率
        elif minutes_to_next < 30:  # 30分鐘內
            return base_interval  # 使用預設間隔
        else:
            return min(300, int(base_interval * 1.5))  # 增加間隔但不超過5分鐘
    
    def _get_sleep_time_to_next_task(self):
        """計算距離下一個任務的休眠時間
        
        Returns:
            float: 建議休眠時間（秒）
        """
        now = datetime.datetime.now()
        today = now.strftime("%Y-%m-%d")
        today_tasks = [task for task in self.app.tasks if task.date == today]
        
        if not today_tasks:
            return 300  # 今天沒有任務，休眠5分鐘
        
        # 找出所有待執行的任務時間
        pending_times = []
        for task in today_tasks:
            if task.sign_in_time > now.strftime("%H:%M") and not getattr(task, 'sign_in_done', False):
                pending_times.append(datetime.datetime.strptime(f"{today} {task.sign_in_time}", "%Y-%m-%d %H:%M"))
            
            if task.sign_out_time > now.strftime("%H:%M") and getattr(task, 'sign_in_done', False) and not getattr(task, 'sign_out_done', False):
                pending_times.append(datetime.datetime.strptime(f"{today} {task.sign_out_time}", "%Y-%m-%d %H:%M"))
        
        if not pending_times:
            return 300  # 今天沒有待執行任務，休眠5分鐘
        
        # 計算距離最近任務的時間差
        next_task_time = min(pending_times)
        seconds_to_next = max(0, (next_task_time - now).total_seconds())
        
        # 如果距離下個任務小於60秒，設置為30秒以確保不會錯過
        if seconds_to_next < 60:
            return 30
        
        # 如果距離下個任務小於5分鐘，設置為1分鐘
        if seconds_to_next < 300:
            return 60
            
        # 距離下個任務超過5分鐘但小於30分鐘，設置為任務前5分鐘或2分鐘的較大值
        if seconds_to_next < 1800:
            return min(seconds_to_next - 300, 120)  # 任務前5分鐘或2分鐘
            
        # 距離下個任務超過30分鐘，最多休眠5分鐘
        return min(300, seconds_to_next / 4)
    
    def check_tasks(self, is_initial_check=False, skip_network_check=False):
        """檢查並執行到期的任務
        
        Args:
            is_initial_check: 是否是系統啟動後的首次檢查
            skip_network_check: 是否跳過網絡環境檢測（使用應用程式當前狀態）
        """
        try:
            # 記錄開始時間，用於性能監控
            check_start_time = datetime.datetime.now()
            
            # 記錄舊的網絡狀態（用於判斷狀態是否變更）
            old_is_campus = getattr(self.app, 'is_campus_network', False)
            
            # 檢查網絡環境（根據間隔控制檢查頻率）
            if skip_network_check:
                # 使用應用程式已設置的網絡狀態
                current_is_campus = getattr(self.app, 'is_campus_network', False)
                # 跳過保持會話，避免警告信息
                session_valid = True
            else:
                # 正常執行網絡環境檢測
                current_is_campus = self._check_network_environment()
                
                # 只有在實際狀態變化時才嘗試維持會話並顯示警告
                if current_is_campus != old_is_campus:
                    # 確保會話有效
                    session_valid = self._ensure_valid_session()
                    if not session_valid and current_is_campus:
                        self.app.logger.log("警告: 在校內網絡環境下無法維持有效會話")
                else:
                    # 狀態無變化時，除非在校內網絡且上次檢測已超過10分鐘，否則跳過會話維持
                    if current_is_campus and self.last_check_time and (datetime.datetime.now() - self.last_check_time).total_seconds() > 600:
                        session_valid = self._ensure_valid_session()
                        # 靜默處理會話問題，只在明確的錯誤時記錄
                    else:
                        session_valid = True
            
            # 獲取當前時間信息
            now = datetime.datetime.now()
            today = now.strftime("%Y-%m-%d")
            current_time = now.strftime("%H:%M")
            
            # 檢查是否有今天的任務
            today_tasks = [task for task in self.app.tasks if task.date == today]
            if not today_tasks:
                if is_initial_check:
                    self.app.logger.log(f"今天({today})沒有安排的任務")
                return
            
            # 處理潛在異常情況的任務
            self._handle_abnormal_tasks(today)
            
            # 計算待執行的任務數量
            pending_sign_ins = [t for t in today_tasks if current_time >= t.sign_in_time and not getattr(t, 'sign_in_done', False)]
            pending_sign_outs = [t for t in today_tasks if current_time >= t.sign_out_time and getattr(t, 'sign_in_done', False) and not getattr(t, 'sign_out_done', False)]
            
            if is_initial_check and (pending_sign_ins or pending_sign_outs):
                self.app.logger.log(f"啟動時檢測到 {len(pending_sign_ins)} 個待簽到和 {len(pending_sign_outs)} 個待簽退的任務")
            
            # 按時間順序排序今天的任務
            today_tasks.sort(key=lambda t: t.sign_in_time)
            
            # 處理今天的任務
            for task in today_tasks:
                # 檢查任務是否被標記為異常
                if self._should_skip_task(task):
                    continue
                
                # 使用智能執行策略
                self._execute_task_if_needed(task, current_time, current_is_campus)
            
            # 任務檢查完成後，計算執行時間
            check_duration = (datetime.datetime.now() - check_start_time).total_seconds()
            if check_duration > 10:  # 如果執行時間過長，記錄警告
                self.app.logger.log(f"警告: 任務檢查耗時 {check_duration:.2f} 秒，可能影響系統性能")
            
        except Exception as e:
            self.app.logger.log(f"任務調度檢查過程中發生錯誤: {str(e)}")
            import traceback
            self.app.logger.log(traceback.format_exc())
    
    def _check_network_environment(self):
        """檢查當前網絡環境，判斷是否在校內網絡
        
        Returns:
            bool: 是否在校內網絡環境
        """
        now = datetime.datetime.now()
        
        # 確保使用最新的網絡檢測間隔設定
        self.network_check_interval = self.app.settings.get("network_check_interval", 300)
        
        # 如果上次檢查時間在有效期內，直接返回之前的結果
        if self.last_network_check and (now - self.last_network_check).total_seconds() < self.network_check_interval:
            return getattr(self.app, 'is_campus_network', False)
        
        # 更新檢查時間
        self.last_network_check = now
        
        # 記錄舊的網絡狀態（用於後續判斷是否發生變化）
        old_is_campus = getattr(self.app, 'is_campus_network', False)
        
        try:
            # 直接調用 NetworkUtils 的檢測方法進行網絡環境檢測
            # 設置 verbose=False 避免重複的日誌輸出
            is_campus, ip, hop_info = self.app.network_utils.check_campus_network(verbose=False, wait_for_hop_check=True)
            
            # 更新網絡狀態
            current_is_campus = is_campus
            self.app.is_campus_network = current_is_campus
            
            # 只在網絡狀態變更時記錄日誌
            if old_is_campus != current_is_campus:
                if current_is_campus:
                    self.app.logger.log("網絡環境已變更: 校外 -> 校內")
                    # 從校外變為校內，重置環境限制
                    reset_count = self.app.reset_campus_restrictions()
                else:
                    self.app.logger.log("網絡環境已變更: 校內 -> 校外")
                    self.app.show_notification("網絡環境變更", "檢測到您已離開校內網絡\n簽到/簽退操作將暫停執行")
                
                # 更新日誌記錄時間和狀態
                self.app.last_network_log_time = now
                self.app.last_network_log_status = current_is_campus
                
            # 更新狀態欄
            if current_is_campus:
                self.app.status_var.set("校內網絡環境，任務執行中")
            else:
                self.app.status_var.set("校外網絡環境，任務已暫停")
            
            return current_is_campus
            
        except Exception as e:
            self.app.logger.log(f"網絡環境檢測錯誤: {str(e)}")
            # 發生錯誤時，保守地返回False
            self.app.is_campus_network = False
            self.app.status_var.set("網絡檢測錯誤，任務已暫停")
            return False
    
    def _ensure_valid_session(self):
        """確保會話有效
        
        Returns:
            bool: 會話是否有效
        """
        try:
            # 嘗試刷新會話
            return self.app.auth_service.keep_session_alive(self.app.settings)
        except Exception as e:
            self.app.logger.log(f"刷新會話時發生錯誤: {str(e)}")
            return False
    
    def _should_skip_task(self, task):
        """判斷是否應該跳過該任務
        
        Args:
            task: 要檢查的任務
            
        Returns:
            bool: 是否應該跳過該任務
        """
        # 檢查任務是否已標記為異常
        if getattr(task, 'marked_abnormal', False):
            return True
        
        # 檢查任務是否因為校外網絡環境而被限制
        if hasattr(task, 'campus_restricted') and task.campus_restricted:
            # 如果上次嘗試時間在冷卻期內，則跳過
            if hasattr(task, 'last_attempt_time') and task.last_attempt_time:
                try:
                    now = datetime.datetime.now()
                    last_attempt = datetime.datetime.fromisoformat(task.last_attempt_time)
                    elapsed_minutes = (now - last_attempt).total_seconds() / 60
                    
                    # 檢查失敗次數
                    if not hasattr(task, 'failure_count'):
                        task.failure_count = 0
                    
                    # 根據失敗次數動態調整冷卻時間
                    cooldown_minutes = min(30 * (task.failure_count + 1), 120)  # 最大冷卻時間2小時
                    
                    # 如果在冷卻期內，跳過
                    if elapsed_minutes < cooldown_minutes:
                        return True
                    
                except Exception:
                    # 如果時間解析出錯，重置嘗試時間
                    task.last_attempt_time = None
        
        return False
    
    def _execute_task_if_needed(self, task, current_time, is_campus_network):
        """根據需要執行任務
        
        Args:
            task: 要執行的任務
            current_time: 當前時間
            is_campus_network: 是否在校內網絡
        """
        # 如果不在校內網絡，跳過執行
        if not is_campus_network:
            return
        
        try:
            # 檢查簽到 - 只對未標記為已完成的任務執行
            self._execute_sign_in_if_needed(task, current_time)
            
            # 檢查簽退 - 只對已簽到但未簽退的任務執行
            self._execute_sign_out_if_needed(task, current_time)
                
        except Exception as e:
            self.app.logger.log(f"執行任務 '{task.name}' 時發生錯誤: {str(e)}")
            
            # 記錄錯誤為一次失敗
            if not hasattr(task, 'failure_count'):
                task.failure_count = 0
            task.failure_count += 1
            task.last_attempt_time = datetime.datetime.now().isoformat()
            
            # 保存任務狀態
            self.app.save_tasks()
    
    def _execute_sign_in_if_needed(self, task, current_time):
        """根據需要執行簽到操作
        
        Args:
            task: 要執行的任務
            current_time: 當前時間
        """
        if current_time >= task.sign_in_time and not getattr(task, 'sign_in_done', False):
            # 記錄執行統計
            self.execution_stats["total_executions"] += 1
            
            try:
                self.app.logger.log(f"執行簽到任務: {task.name}")
                result = self.app.perform_sign_in(task)
                
                if result:
                    # 簽到成功
                    self.execution_stats["successful_sign_ins"] += 1
                    self.execution_stats["last_success_time"] = datetime.datetime.now()
                    
                    # 清除環境限制標記和失敗計數
                    task.campus_restricted = False
                    task.failure_count = 0
                    task.sign_in_done = True
                    
                    # 移除警告標記
                    if hasattr(task, '_sign_in_warning_shown'):
                        delattr(task, '_sign_in_warning_shown')
                        
                else:
                    # 簽到失敗
                    self.execution_stats["failed_sign_ins"] += 1
                    
                    # 檢查是否由於環境限制而失敗
                    if self.app.status_var.get() == "簽到需要校內網絡環境":
                        task.campus_restricted = True
                    
                # 保存任務狀態
                self.app.save_tasks()
                
            except Exception as e:
                self.app.logger.log(f"執行簽到 '{task.name}' 時發生錯誤: {str(e)}")
                self.execution_stats["failed_sign_ins"] += 1
                
                # 記錄為一次失敗
                if not hasattr(task, 'failure_count'):
                    task.failure_count = 0
                task.failure_count += 1
                task.last_attempt_time = datetime.datetime.now().isoformat()
                
                # 保存任務狀態
                self.app.save_tasks()
    
    def _execute_sign_out_if_needed(self, task, current_time):
        """根據需要執行簽退操作
        
        Args:
            task: 要執行的任務
            current_time: 當前時間
        """
        if current_time >= task.sign_out_time and getattr(task, 'sign_in_done', False) and not getattr(task, 'sign_out_done', False):
            # 記錄執行統計
            self.execution_stats["total_executions"] += 1
            
            try:
                self.app.logger.log(f"執行簽退任務: {task.name}")
                result = self.app.perform_sign_out(task)
                
                if result:
                    # 簽退成功
                    self.execution_stats["successful_sign_outs"] += 1
                    self.execution_stats["last_success_time"] = datetime.datetime.now()
                    
                    # 清除環境限制標記和失敗計數
                    task.campus_restricted = False
                    task.failure_count = 0
                    task.sign_out_done = True
                    
                    # 移除警告標記
                    if hasattr(task, '_sign_out_warning_shown'):
                        delattr(task, '_sign_out_warning_shown')
                        
                else:
                    # 簽退失敗
                    self.execution_stats["failed_sign_outs"] += 1
                    
                    # 檢查是否由於環境限制而失敗
                    if self.app.status_var.get() == "簽退需要校內網絡環境":
                        task.campus_restricted = True
                    
                # 保存任務狀態
                self.app.save_tasks()
                
            except Exception as e:
                self.app.logger.log(f"執行簽退 '{task.name}' 時發生錯誤: {str(e)}")
                self.execution_stats["failed_sign_outs"] += 1
                
                # 記錄為一次失敗
                if not hasattr(task, 'failure_count'):
                    task.failure_count = 0
                task.failure_count += 1
                task.last_attempt_time = datetime.datetime.now().isoformat()
                
                # 保存任務狀態
                self.app.save_tasks()

    def _handle_abnormal_tasks(self, today):
        """處理異常情況的任務，例如前一任務簽退失敗但需要進行下一個任務簽到的情況
        
        Args:
            today: 今天的日期字符串 (YYYY-MM-DD)
        """
        try:
            # 獲取當前時間
            now = datetime.datetime.now()
            current_time = now.strftime("%H:%M")
            
            # 檢查是否有今天的任務
            if not hasattr(self.app, 'tasks') or not self.app.tasks:
                return
                
            # 按時間順序排序今天的任務
            today_tasks = [task for task in self.app.tasks if task.date == today]
            if not today_tasks:
                return
                
            today_tasks.sort(key=lambda t: t.sign_in_time)
            
            if len(today_tasks) < 2:
                # 如果只有一個任務，檢查是否出現卡住的情況
                if len(today_tasks) == 1:
                    self._check_single_task_stuck(today_tasks[0])
                return
            
            # 嘗試智能修復任務序列中的異常情況
            self._repair_task_sequence(today_tasks, current_time)
            
            # 檢查最後一個任務是否卡住
            if today_tasks:
                self._check_single_task_stuck(today_tasks[-1])
                
        except Exception as e:
            self.app.logger.log(f"處理異常任務時發生錯誤: {str(e)}")
            import traceback
            self.app.logger.log(traceback.format_exc())
    
    def _repair_task_sequence(self, tasks, current_time):
        """智能修復任務序列中的異常情況
        
        Args:
            tasks: 按時間排序的任務列表
            current_time: 當前時間
        """
        now = datetime.datetime.now()
        today = now.strftime("%Y-%m-%d")
        
        # 系統啟動時不主動修復，只在長時間運行後修復
        if not self.last_check_time:
            return
        
        # 檢查任務之間的狀態連續性
        for i in range(len(tasks) - 1):
            prev_task = tasks[i]
            next_task = tasks[i + 1]
            
            # 如果還沒到下一個任務的時間，不進行修復
            if current_time < next_task.sign_in_time:
                continue
            
            # 情況1: 前一個任務簽到成功但簽退失敗，阻塞下一個任務
            if self._is_blocking_next_task(prev_task, next_task):
                self._repair_blocking_task(prev_task, next_task)
            
            # 情況2: 前一個任務完全未執行但已經超時很久
            elif self._is_missed_task(prev_task, next_task):
                self._mark_missed_task(prev_task, next_task)
            
            # 情況3: 任務順序異常（後面的任務已完成但前面的未完成）
            elif self._is_task_sequence_abnormal(prev_task, next_task):
                self._fix_abnormal_sequence(prev_task, next_task)
    
    def _is_blocking_next_task(self, prev_task, next_task):
        """檢查前一個任務是否阻塞了下一個任務
        
        Args:
            prev_task: 前一個任務
            next_task: 下一個任務
            
        Returns:
            bool: 是否存在阻塞情況
        """
        # 前一個任務簽到成功但簽退失敗，而下一個任務需要開始
        return (getattr(prev_task, 'sign_in_done', False) and 
                not getattr(prev_task, 'sign_out_done', False) and 
                not getattr(next_task, 'sign_in_done', False))
    
    def _repair_blocking_task(self, prev_task, next_task):
        """修復阻塞的任務
        
        Args:
            prev_task: 正在阻塞的任務
            next_task: 被阻塞的任務
        """
        now = datetime.datetime.now()
        today = now.strftime("%Y-%m-%d")
        
        self.app.logger.log(f"檢測到前一任務 '{prev_task.name}' 簽到已完成但簽退未完成，可能阻塞下一任務 '{next_task.name}'")
        
        # 檢查是否已經超過簽退時間過長
        sign_out_time = datetime.datetime.strptime(f"{today} {prev_task.sign_out_time}", "%Y-%m-%d %H:%M")
        time_diff = (now - sign_out_time).total_seconds() / 60
        
        # 嘗試自動強制簽退前一個任務
        try:
            # 如果超過特定時間（30分鐘），不再嘗試正常簽退，直接標記
            if time_diff > 30:
                self.app.logger.log(f"前一任務簽退已超時 {int(time_diff)} 分鐘，將直接標記為完成")
                prev_task.sign_out_done = True
                
                # 添加警告信息
                self.app.logger.log(f"⚠️ 已強制標記任務 '{prev_task.name}' 為已簽退，但實際簽退可能未成功")
                self.app.logger.log(f"⚠️ 請在下一任務簽到後，聯繫管理員處理前一任務的簽退問題")
                
                # 設置標記以防止重複警告
                prev_task._force_completed = True
                
                # 保存任務變更
                self.app.save_tasks()
                return
            
            # 嘗試正常簽退
            self.app.logger.log(f"嘗試自動補簽退任務 '{prev_task.name}'")
            result = self.app.perform_sign_out(prev_task)
            
            if result:
                self.app.logger.log(f"✅ 已成功補簽退任務 '{prev_task.name}'")
            else:
                # 如果無法正常簽退且已超過15分鐘，標記為強制完成
                if time_diff > 15:
                    self.app.logger.log(f"無法自動補簽退且已超時15分鐘，將標記為已完成以允許下一任務運行")
                    prev_task.sign_out_done = True
                    self.app.save_tasks()
                    
                    # 添加警告說明需要手動處理
                    self.app.logger.log(f"⚠️ 警告: 任務 '{prev_task.name}' 的簽退已被標記為完成，但實際可能未簽退成功")
                    self.app.logger.log(f"⚠️ 請在下一任務簽到後，聯繫管理員處理")
                else:
                    self.app.logger.log(f"自動補簽退失敗，但尚未超過15分鐘，將繼續嘗試")
                
        except Exception as e:
            self.app.logger.log(f"嘗試補簽退時發生錯誤: {str(e)}")
            
            # 如果簽退時間已超過一定時間(30分鐘)，標記為強制完成
            if time_diff > 30:
                self.app.logger.log(f"由於錯誤且已超時30分鐘，強制標記任務 '{prev_task.name}' 為已完成")
                prev_task.sign_out_done = True
                self.app.save_tasks()
                self.app.logger.log(f"⚠️ 請稍後手動檢查此任務的實際狀態")
    
    def _is_missed_task(self, prev_task, next_task):
        """檢查是否存在已錯過的任務
        
        Args:
            prev_task: 前一個任務
            next_task: 下一個任務
            
        Returns:
            bool: 是否已錯過任務
        """
        now = datetime.datetime.now()
        today = now.strftime("%Y-%m-%d")
        
        # 前一個任務未簽到，但當前時間已經過了下一個任務的簽到時間
        if not getattr(prev_task, 'sign_in_done', False):
            # 檢查是否已經超過前一任務的簽到時間很久
            prev_sign_in_time = datetime.datetime.strptime(f"{today} {prev_task.sign_in_time}", "%Y-%m-%d %H:%M")
            time_diff = (now - prev_sign_in_time).total_seconds() / 3600
            
            # 如果已超過3小時，認為已錯過
            return time_diff >= 3
        
        return False
    
    def _mark_missed_task(self, prev_task, next_task):
        """標記已錯過的任務
        
        Args:
            prev_task: 已錯過的任務
            next_task: 下一個任務
        """
        now = datetime.datetime.now()
        today = now.strftime("%Y-%m-%d")
        
        # 檢查時間差
        prev_sign_in_time = datetime.datetime.strptime(f"{today} {prev_task.sign_in_time}", "%Y-%m-%d %H:%M")
        time_diff = (now - prev_sign_in_time).total_seconds() / 3600
        
        # 避免重複警告
        if not hasattr(prev_task, '_missed_warning_shown'):
            self.app.logger.log(f"檢測到可能已錯過的任務: '{prev_task.name}' (已超過簽到時間 {int(time_diff)} 小時)")
            prev_task._missed_warning_shown = True
        
        # 如果下一個任務還未簽到且超過特定時間，標記前一個為已完成
        if not getattr(next_task, 'sign_in_done', False) and time_diff >= 3:
            self.app.logger.log(f"將標記錯過的任務 '{prev_task.name}' 為已完成，以允許執行下一任務 '{next_task.name}'")
            
            # 標記為已完成
            prev_task.sign_in_done = True
            prev_task.sign_out_done = True
            prev_task.marked_abnormal = True
            prev_task.abnormal_reason = f"任務已錯過 {int(time_diff)} 小時，系統自動標記"
            
            # 保存狀態
            self.app.save_tasks()
    
    def _is_task_sequence_abnormal(self, prev_task, next_task):
        """檢查任務順序是否異常
        
        Args:
            prev_task: 前一個任務
            next_task: 下一個任務
            
        Returns:
            bool: 順序是否異常
        """
        # 如果後面的任務已經簽到，但前一個任務未完成
        return (getattr(next_task, 'sign_in_done', False) and 
                (not getattr(prev_task, 'sign_in_done', False) or 
                 not getattr(prev_task, 'sign_out_done', False)))
    
    def _fix_abnormal_sequence(self, prev_task, next_task):
        """修復異常的任務順序
        
        Args:
            prev_task: 前一個任務
            next_task: 下一個任務
        """
        # 避免重複警告
        if not hasattr(prev_task, '_sequence_warning_shown'):
            self.app.logger.log(f"檢測到順序異常: 任務 '{next_task.name}' 已開始，但前一任務 '{prev_task.name}' 未完成")
            prev_task._sequence_warning_shown = True
        
        # 標記前一個任務為已完成以保持一致性
        if not getattr(prev_task, '_auto_completed', False):
            self.app.logger.log(f"自動標記前一任務 '{prev_task.name}' 為已完成以維持系統一致性")
            prev_task.sign_in_done = True
            prev_task.sign_out_done = True
            prev_task._auto_completed = True
            
            # 添加警告標記，但不完全標記為異常
            prev_task._sequence_abnormal = True
            
            # 保存狀態
            self.app.save_tasks()
    
    def _check_single_task_stuck(self, task):
        """檢查單個任務是否卡在某個狀態
        
        Args:
            task: 要檢查的任務對象
        """
        try:
            now = datetime.datetime.now()
            today = now.strftime("%Y-%m-%d")
            current_time = now.strftime("%H:%M")
            
            # 如果任務已標記為異常，跳過檢查
            if getattr(task, 'marked_abnormal', False):
                return
                
            # 檢查任務是否屬於今天
            if task.date != today:
                return
                
            # 情況1: 簽到時間已過很久但未簽到
            if not getattr(task, 'sign_in_done', False) and current_time > task.sign_in_time:
                sign_in_time = datetime.datetime.strptime(f"{today} {task.sign_in_time}", "%Y-%m-%d %H:%M")
                time_diff = (now - sign_in_time).total_seconds() / 60
                
                # 根據時間差設置不同級別的警告
                if time_diff > 180:  # 超過3小時
                    # 標記為異常
                    if not getattr(task, 'marked_abnormal', False):
                        self.app.logger.log(f"⚠️ 嚴重警告: 任務 '{task.name}' 已超過簽到時間 {int(time_diff)} 分鐘(超過3小時)")
                        task.marked_abnormal = True
                        task.abnormal_reason = f"簽到超時 {int(time_diff)} 分鐘"
                        self.app.save_tasks()
                elif time_diff > 60:  # 超過1小時
                    # 記錄警告
                    if not hasattr(task, '_sign_in_warning_shown'):
                        self.app.logger.log(f"⚠️ 警告: 任務 '{task.name}' 已超過簽到時間 {int(time_diff)} 分鐘但尚未簽到")
                        task._sign_in_warning_shown = True
                        
                        # 如果超過90分鐘且近期網絡環境正常，嘗試自動簽到
                        if time_diff > 90 and getattr(self.app, 'is_campus_network', False):
                            self.app.logger.log(f"任務 '{task.name}' 已超時90分鐘，嘗試自動簽到...")
                            try:
                                result = self.app.perform_sign_in(task)
                                if result:
                                    self.app.logger.log(f"✅ 自動簽到成功")
                                else:
                                    self.app.logger.log(f"❌ 自動簽到失敗")
                            except Exception as e:
                                self.app.logger.log(f"嘗試自動簽到時發生錯誤: {str(e)}")
            
            # 情況2: 簽到已完成，簽退時間已過很久但未簽退
            elif getattr(task, 'sign_in_done', False) and not getattr(task, 'sign_out_done', False) and current_time > task.sign_out_time:
                sign_out_time = datetime.datetime.strptime(f"{today} {task.sign_out_time}", "%Y-%m-%d %H:%M")
                time_diff = (now - sign_out_time).total_seconds() / 60
                
                # 根據時間差設置不同級別的警告
                if time_diff > 300:  # 超過5小時
                    # 標記為異常
                    if not getattr(task, 'marked_abnormal', False):
                        self.app.logger.log(f"⚠️ 嚴重警告: 任務 '{task.name}' 已超過簽退時間 {int(time_diff)} 分鐘(超過5小時)")
                        task.marked_abnormal = True
                        task.abnormal_reason = f"簽退超時 {int(time_diff)} 分鐘"
                        self.app.save_tasks()
                elif time_diff > 60:  # 超過1小時
                    # 記錄警告
                    if not hasattr(task, '_sign_out_warning_shown'):
                        self.app.logger.log(f"⚠️ 警告: 任務 '{task.name}' 已超過簽退時間 {int(time_diff)} 分鐘但尚未簽退")
                        task._sign_out_warning_shown = True
                        
                        # 如果超過3小時且近期網絡環境正常，嘗試自動簽退
                        if time_diff > 180 and getattr(self.app, 'is_campus_network', False):
                            self.app.logger.log(f"任務 '{task.name}' 已超時3小時，嘗試自動簽退...")
                            try:
                                result = self.app.perform_sign_out(task)
                                if result:
                                    self.app.logger.log(f"✅ 自動簽退成功")
                                else:
                                    self.app.logger.log(f"❌ 自動簽退失敗")
                            except Exception as e:
                                self.app.logger.log(f"嘗試自動簽退時發生錯誤: {str(e)}")
        
        except Exception as e:
            self.app.logger.log(f"檢查任務卡住狀態時發生錯誤: {str(e)}")
            # 不影響主流程
    
    def get_statistics(self):
        """獲取調度器的統計信息
        
        Returns:
            dict: 包含統計信息的字典
        """
        stats = self.execution_stats.copy()
        
        # 添加成功率
        total_tasks = stats["successful_sign_ins"] + stats["successful_sign_outs"] + stats["failed_sign_ins"] + stats["failed_sign_outs"]
        if total_tasks > 0:
            success_rate = (stats["successful_sign_ins"] + stats["successful_sign_outs"]) / total_tasks * 100
            stats["success_rate"] = f"{success_rate:.1f}%"
        else:
            stats["success_rate"] = "N/A"
        
        # 添加上次成功執行時間的友好顯示
        if stats["last_success_time"]:
            time_diff = (datetime.datetime.now() - stats["last_success_time"]).total_seconds()
            if time_diff < 60:
                stats["last_success_ago"] = f"{int(time_diff)}秒前"
            elif time_diff < 3600:
                stats["last_success_ago"] = f"{int(time_diff/60)}分鐘前"
            else:
                stats["last_success_ago"] = f"{int(time_diff/3600)}小時前"
        else:
            stats["last_success_ago"] = "從未成功"
            
        return stats
