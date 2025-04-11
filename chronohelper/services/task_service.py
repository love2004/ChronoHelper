# -*- coding: utf-8 -*-
"""
任務管理服務
"""

import datetime
import time
import random
from requests.exceptions import RequestException, ConnectionError, Timeout, TooManyRedirects
from urllib3.exceptions import ProtocolError

class TaskService:
    """任務管理服務，處理簽到/簽退操作"""
    
    def __init__(self, logger, auth_service):
        """初始化任務服務
        
        Args:
            logger: 日誌記錄器
            auth_service: 認證服務實例
        """
        self.logger = logger
        self.auth_service = auth_service
        self.max_retry_attempts = 3  # 最大重試次數
        self.retry_base_delay = 2    # 基本重試延遲（秒）
        self.last_request_time = None  # 上次請求時間
        self.min_request_interval = 1.5  # 最小請求間隔（秒）
    
    def perform_sign_in(self, task, settings):
        """執行簽到操作
        
        Args:
            task: 任務對象
            settings: 設定字典
            
        Returns:
            bool: 簽到是否成功
        """
        self.logger.log(f"執行簽到: {task.name}, 時間: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # 確保已登入
        if not self.auth_service.ensure_login(settings):
            self.logger.log("簽到前檢測到未登入，嘗試重新登入")
            if not self.auth_service.login(settings, force=True):
                self.logger.log("重新登入失敗，無法執行簽到")
                self._handle_task_failure(task, "登入失敗")
                return False
        
        # 簽到URL
        sign_in_url = settings.get("sign_in_url", "https://adm_acc.dyu.edu.tw/budget/prj_epfee/kernel/kernel_prj_carddata_edit.php?page=NDgy")
        
        # 構建簽到請求數據
        sign_data = {
            "type": 1  # 簽到使用type=1
        }
        
        # 使用與認證服務相同的標準頭部，並添加必要的API請求頭
        headers = self.auth_service.standard_headers.copy()
        headers.update({
            "Content-Type": "application/json",
            "Accept": "application/json, text/plain, */*",
            "X-Requested-With": "XMLHttpRequest",
            "Referer": settings.get("api_url", "https://adm_acc.dyu.edu.tw/entrance/index.php")
        })
        
        # 使用智能重試機制執行請求
        return self._execute_request_with_retry(
            task=task,
            url=sign_in_url,
            method="POST",
            data=sign_data,
            headers=headers,
            settings=settings,
            operation_type="簽到",
            success_handler=self._handle_sign_in_success,
            failure_handler=self._handle_sign_in_failure
        )
    
    def perform_sign_out(self, task, settings):
        """執行簽退操作
        
        Args:
            task: 任務對象
            settings: 設定字典
            
        Returns:
            bool: 簽退是否成功
        """
        self.logger.log(f"執行簽退: {task.name}, 時間: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # 確保已登入
        if not self.auth_service.ensure_login(settings):
            self.logger.log("簽退前檢測到未登入，嘗試重新登入")
            if not self.auth_service.login(settings, force=True):
                self.logger.log("重新登入失敗，無法執行簽退")
                self._handle_task_failure(task, "登入失敗") 
                return False
        
        # 簽退URL
        sign_out_url = settings.get("sign_out_url", "https://adm_acc.dyu.edu.tw/budget/prj_epfee/kernel/kernel_prj_carddata_edit.php?page=NDgy")
        
        # 構建簽退請求數據
        sign_data = {
            "type": 2  # 簽退使用type=2
        }
        
        # 使用與認證服務相同的標準頭部，並添加必要的API請求頭
        headers = self.auth_service.standard_headers.copy()
        headers.update({
            "Content-Type": "application/json",
            "Accept": "application/json, text/plain, */*",
            "X-Requested-With": "XMLHttpRequest",
            "Referer": settings.get("api_url", "https://adm_acc.dyu.edu.tw/entrance/index.php")
        })
        
        # 使用智能重試機制執行請求
        return self._execute_request_with_retry(
            task=task,
            url=sign_out_url,
            method="POST",
            data=sign_data,
            headers=headers,
            settings=settings,
            operation_type="簽退",
            success_handler=self._handle_sign_out_success,
            failure_handler=self._handle_sign_out_failure
        )
    
    def _execute_request_with_retry(self, task, url, method, data, headers, settings, operation_type, success_handler, failure_handler):
        """執行帶重試機制的HTTP請求
        
        Args:
            task: 任務對象
            url: 請求URL
            method: 請求方法 (GET, POST等)
            data: 請求數據
            headers: 請求頭
            settings: 設定字典
            operation_type: 操作類型 (簽到/簽退)
            success_handler: 成功處理函數
            failure_handler: 失敗處理函數
            
        Returns:
            bool: 請求是否成功
        """
        attempt = 0
        last_error = None
        
        # 控制請求頻率
        self._apply_request_throttling()
        
        # 獲取會話
        session = self.auth_service.get_session()
        
        while attempt < self.max_retry_attempts:
            attempt += 1
            
            try:
                if attempt > 1:
                    delay = self.retry_base_delay * (1.5 ** (attempt - 1)) * (0.8 + 0.4 * random.random())  # 指數退避+隨機抖動
                    self.logger.log(f"{operation_type}操作第{attempt}次重試，延遲{delay:.1f}秒...")
                    time.sleep(delay)
                    
                    # 重試前重新檢查登入狀態
                    if not self.auth_service.verify_session(settings):
                        self.logger.log(f"重試前發現會話已失效，重新登入...")
                        if not self.auth_service.login(settings, force=True):
                            self.logger.log(f"重新登入失敗，無法繼續{operation_type}操作")
                            break
                        # 獲取新的會話
                        session = self.auth_service.get_session()
                
                # 紀錄本次請求時間
                self.last_request_time = datetime.datetime.now()
                
                # 發送請求
                if method.upper() == "POST":
                    response = session.post(url, json=data, headers=headers, timeout=30)
                else:  # GET
                    response = session.get(url, headers=headers, timeout=30)
                
                # 檢查PHPSESSID是否仍然存在
                if not self._check_session_cookie(session):
                    self.logger.log(f"{operation_type}操作後發現PHPSESSID丟失，將重新登入")
                    if self.auth_service.login(settings, force=True):
                        continue  # 重新登入成功，重試請求
                    else:
                        self.logger.log(f"重新登入失敗，無法繼續{operation_type}操作")
                        break
                
                # 記錄簡潔的響應信息
                if len(response.text) > 500:
                    preview = response.text[:500] + "... (截斷)"
                else:
                    preview = response.text
                self.logger.log(f"{operation_type}API響應: 狀態碼={response.status_code}, 內容長度={len(response.text)}, 預覽={preview}")
                
                # 檢查是否重定向到登入頁面（會話失效）
                if "login_id" in response.text and "login_pwd" in response.text and "<form" in response.text.lower():
                    self.logger.log(f"{operation_type}操作返回登入頁面，會話可能已失效，嘗試重新登入")
                    if self.auth_service.login(settings, force=True):
                        continue  # 重新登入成功，重試請求
                    else:
                        self.logger.log(f"重新登入失敗，無法繼續{operation_type}操作")
                        break
                
                # 檢查響應狀態碼
                if response.status_code != 200:
                    self.logger.log(f"{operation_type}請求失敗，狀態碼: {response.status_code}")
                    # 只有在狀態碼為5xx或4xx(除了401/403)時才重試
                    if (500 <= response.status_code < 600) or (400 <= response.status_code < 500 and response.status_code not in [401, 403]):
                        continue  # 重試請求
                    else:
                        return failure_handler(task, response, f"狀態碼錯誤: {response.status_code}")
                
                # 嘗試解析JSON
                try:
                    result = response.json()
                    return success_handler(task, result)
                except ValueError as e:
                    # JSON解析失敗但狀態碼是200，可能是API格式變更或登入過期
                    self.logger.log(f"{operation_type}響應解析失敗: {str(e)}")
                    if "login_id" in response.text or "login_pwd" in response.text:
                        self.logger.log(f"檢測到重定向到登入頁面，嘗試重新登入")
                        if self.auth_service.login(settings, force=True):
                            continue  # 重新登入成功，重試請求
                
                # 所有處理方式都失敗，使用failure_handler
                return failure_handler(task, response, f"響應無法解析")
                
            except (ConnectionError, Timeout, TooManyRedirects, ProtocolError) as e:
                # 網絡相關錯誤，可以重試
                self.logger.log(f"{operation_type}過程中發生網絡錯誤: {str(e)}")
                last_error = e
                continue
            except Exception as e:
                # 其他錯誤，記錄下來
                self.logger.log(f"{operation_type}過程中發生未預期錯誤: {str(e)}")
                import traceback
                self.logger.log(traceback.format_exc())
                last_error = e
                # 對於未知錯誤，可能需要重新登入
                if attempt == 1:  # 只在第一次嘗試後重新登入
                    self.logger.log(f"嘗試重新登入以恢復...")
                    if self.auth_service.login(settings, force=True):
                        continue  # 重新嘗試
                break
        
        # 所有重試都失敗了
        error_msg = f"{operation_type}操作失敗，已重試{attempt}次"
        if last_error:
            error_msg += f"，最後錯誤: {str(last_error)}"
        self.logger.log(error_msg)
        
        # 處理最終失敗
        self._handle_task_failure(task, error_msg)
        return False
    
    def _apply_request_throttling(self):
        """控制請求頻率，避免發送過於頻繁的請求"""
        if self.last_request_time:
            elapsed = (datetime.datetime.now() - self.last_request_time).total_seconds()
            if elapsed < self.min_request_interval:
                sleep_time = self.min_request_interval - elapsed + (random.random() * 0.5)  # 添加一些隨機抖動
                self.logger.log(f"控制請求頻率，等待 {sleep_time:.2f} 秒...")
                time.sleep(sleep_time)
    
    def _check_session_cookie(self, session):
        """檢查會話是否包含必要的cookie（特別是PHPSESSID）"""
        for cookie_name in self.auth_service.important_cookies:
            if cookie_name not in session.cookies.keys():
                return False
        return True
    
    def _handle_task_failure(self, task, reason):
        """處理任務失敗"""
        task.last_attempt_time = datetime.datetime.now().isoformat()
        
        # 初始化失敗計數
        if not hasattr(task, 'failure_count'):
            task.failure_count = 0
        
        task.failure_count += 1
        
        # 添加失敗原因
        task.last_failure_reason = reason
        
        # 超過一定失敗次數，標記為異常
        if task.failure_count >= 3:
            if not getattr(task, 'marked_abnormal', False):
                self.logger.log(f"⚠️ 任務 '{task.name}' 已連續失敗 {task.failure_count} 次，標記為異常")
                task.marked_abnormal = True
                task.abnormal_reason = f"連續失敗 {task.failure_count} 次，最後原因: {reason}"
    
    def _handle_sign_in_success(self, task, result):
        """處理簽到成功的情況"""
        result_code = result.get("result")
        result_msg = result.get("msg", "未知響應")
        
        # 處理不同的響應結果
        if result_code == 1:  # 成功簽到
            self.logger.log(f"簽到成功: {result_msg}")
            
            # 更新任務狀態
            task.sign_in_done = True
            task.failure_count = 0  # 重置失敗計數
            
            return True
        
        elif result_code == 0 and "已簽到" in result_msg:  # 已簽到
            self.logger.log(f"簽到提示: {result_msg}，您已經完成簽到")
            
            # 更新任務狀態，因為已經簽到了
            task.sign_in_done = True
            task.failure_count = 0  # 重置失敗計數
            
            return True  # 返回成功，因為已經簽到了
        
        elif result_code == 0 and "請先簽退" in result_msg:  # 需要先簽退
            self.logger.log(f"簽到提示: {result_msg}，系統中已有簽到記錄")
            
            # 更新任務狀態為已簽到，因為"請先簽退"表示系統中已有記錄
            task.sign_in_done = True
            task.failure_count = 0  # 重置失敗計數
            
            return True  # 返回成功，因為實際上任務已標記為已完成
        
        elif result_code == -1 and ("無使用權限" in result_msg or "-101" in result_msg):  # 權限錯誤
            self.logger.log(f"簽到權限錯誤: {result_msg}")
            
            # 處理校外環境情況
            self.logger.log("檢測到校外環境或登入失效")
            
            # 標記任務為環境受限
            task.campus_restricted = True
            task.last_attempt_time = datetime.datetime.now().isoformat()
            
            # 不立即增加失敗計數，因為這是環境限制而非系統錯誤
            
            return False
        
        else:  # 其他錯誤情況
            self.logger.log(f"簽到失敗: 未知結果碼 {result_code}, 消息: {result_msg}")
            self._handle_task_failure(task, f"未知結果: {result_code} - {result_msg}")
            return False
    
    def _handle_sign_in_failure(self, task, response, reason):
        """處理簽到失敗的情況"""
        self.logger.log(f"簽到失敗: {reason}")
        self._handle_task_failure(task, reason)
        return False
    
    def _handle_sign_out_success(self, task, result):
        """處理簽退成功的情況"""
        result_code = result.get("result")
        result_msg = result.get("msg", "未知響應")
        
        # 處理不同的響應結果
        if result_code == 1:  # 成功簽退
            self.logger.log(f"簽退成功: {result_msg}")
            
            # 更新任務狀態
            task.sign_out_done = True
            task.failure_count = 0  # 重置失敗計數
            
            # 檢查特殊訊息
            if "工讀時數" in result_msg and "不足30分鐘" in result_msg:
                self.logger.log("系統提示工讀時數不足30分鐘部分不計算")
            
            return True
            
        elif result_code == 0 and ("請先簽到" in result_msg or "尚未簽到" in result_msg):  # 未簽到就嘗試簽退
            self.logger.log(f"簽退提示: {result_msg}，需要先完成簽到")
            
            # 確保狀態是未簽退
            task.sign_out_done = False
            
            # 如果是合理的未簽到情況，不增加失敗計數
            
            return False
            
        elif result_code == 0 and "已簽退" in result_msg:  # 已經簽退
            self.logger.log(f"簽退提示: {result_msg}，您已經完成簽退")
            
            # 更新任務狀態，因為已經簽退了
            task.sign_out_done = True
            task.failure_count = 0  # 重置失敗計數
            
            # 返回True因為實際上簽退狀態已完成
            return True
            
        elif result_code == -1 and ("無使用權限" in result_msg or "-101" in result_msg):  # 權限錯誤
            self.logger.log(f"簽退權限錯誤: {result_msg}")
            
            # 處理校外環境情況
            self.logger.log("檢測到校外環境或登入失效")
            
            # 標記任務為環境受限
            task.campus_restricted = True
            task.last_attempt_time = datetime.datetime.now().isoformat()
            
            return False
            
        else:  # 其他錯誤情況
            self.logger.log(f"簽退失敗: 未知結果碼 {result_code}, 消息: {result_msg}")
            self._handle_task_failure(task, f"未知結果: {result_code} - {result_msg}")
            return False
    
    def _handle_sign_out_failure(self, task, response, reason):
        """處理簽退失敗的情況"""
        self.logger.log(f"簽退失敗: {reason}")
        self._handle_task_failure(task, reason)
        return False
