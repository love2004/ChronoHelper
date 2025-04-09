# -*- coding: utf-8 -*-
"""
任務管理服務
"""

import datetime
import requests
from requests.exceptions import RequestException

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
    
    def perform_sign_in(self, task, settings):
        """執行簽到操作
        
        Args:
            task: 任務對象
            settings: 設定字典
            
        Returns:
            bool: 簽到是否成功
        """
        try:
            self.logger.log(f"執行簽到: {task.name}, 時間: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            
            # 確保已登入
            if not self.auth_service.ensure_login(settings):
                self.logger.log("簽到前檢測到未登入，嘗試重新登入")
                if not self.auth_service.login(settings, force=True):
                    self.logger.log("重新登入失敗，無法執行簽到")
                    return False
            
            # 獲取會話
            session = self.auth_service.get_session()
            
            # 簽到URL
            sign_in_url = settings.get("sign_in_url", "https://adm_acc.dyu.edu.tw/budget/prj_epfee/kernel/kernel_prj_carddata_edit.php?page=NDgy")
            
            # 構建簽到請求數據
            sign_data = {
                "type": 1  # 簽到使用type=1
            }
            
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
                "Content-Type": "application/json",
                "Accept": "application/json, text/plain, */*",
                "X-Requested-With": "XMLHttpRequest"
            }
            
            # 發送簽到請求
            response = session.post(sign_in_url, json=sign_data, headers=headers, timeout=30)
            
            # 記錄原始響應以便調試
            self.logger.log(f"簽到API原始響應: {response.text}")
            
            # 檢查簽到結果
            if response.status_code == 200:
                try:
                    result = response.json()
                    result_code = result.get("result")
                    result_msg = result.get("msg", "未知響應")
                    
                    # 處理不同的響應結果
                    if result_code == 1:  # 成功簽到
                        self.logger.log(f"簽到成功: {result_msg}")
                        
                        # 更新任務狀態
                        task.sign_in_done = True
                        
                        return True
                    
                    elif result_code == 0 and "已簽到" in result_msg:  # 已簽到
                        self.logger.log(f"簽到提示: {result_msg}，您已經完成簽到")
                        
                        # 更新任務狀態，因為已經簽到了
                        task.sign_in_done = True
                        
                        return True  # 返回成功，因為已經簽到了
                    
                    elif result_code == 0 and "請先簽退" in result_msg:  # 需要先簽退
                        self.logger.log(f"簽到提示: {result_msg}，系統中已有簽到記錄")
                        
                        # 更新任務狀態為已簽到，因為"請先簽退"表示系統中已有記錄
                        task.sign_in_done = True
                        
                        return True  # 返回成功，因為實際上任務已標記為已完成
                    
                    elif result_code == -1 and ("無使用權限" in result_msg or "-101" in result_msg):  # 權限錯誤
                        self.logger.log(f"簽到權限錯誤: {result_msg}")
                        
                        # 處理校外環境情況
                        self.logger.log("檢測到校外環境或登入失效")
                        
                        # 標記任務為環境受限
                        task.campus_restricted = True
                        task.last_attempt_time = datetime.datetime.now().isoformat()
                        
                        # 嘗試重新登入
                        self.logger.log("嘗試重新登入...")
                        if self.auth_service.login(settings, force=True):
                            self.logger.log("重新登入成功，但仍需在校內網絡環境操作")
                        
                        return False
                    
                    else:  # 其他錯誤情況
                        self.logger.log(f"簽到失敗: 未知結果碼 {result_code}, 消息: {result_msg}")
                        return False
                    
                except ValueError as e:
                    # JSON解析失敗
                    self.logger.log(f"簽到響應解析失敗: {str(e)}\n響應內容: {response.text[:200]}")
                    return False
                    
                except Exception as e:
                    # 其他解析錯誤
                    self.logger.log(f"簽到響應處理錯誤: {str(e)}")
                    return False
            else:
                self.logger.log(f"簽到請求失敗，狀態碼: {response.status_code}")
                return False
                
        except RequestException as e:
            error_msg = f"簽到過程中發生網絡錯誤: {str(e)}"
            self.logger.log(error_msg)
            return False
        except Exception as e:
            error_msg = f"簽到過程中發生未知錯誤: {str(e)}"
            self.logger.log(error_msg)
            return False
    
    def perform_sign_out(self, task, settings):
        """執行簽退操作
        
        Args:
            task: 任務對象
            settings: 設定字典
            
        Returns:
            bool: 簽退是否成功
        """
        try:
            self.logger.log(f"執行簽退: {task.name}, 時間: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            
            # 確保已登入
            if not self.auth_service.ensure_login(settings):
                self.logger.log("簽退前檢測到未登入，嘗試重新登入")
                if not self.auth_service.login(settings, force=True):
                    self.logger.log("重新登入失敗，無法執行簽退")
                    return False
            
            # 獲取會話
            session = self.auth_service.get_session()
            
            # 簽退URL
            sign_out_url = settings.get("sign_out_url", "https://adm_acc.dyu.edu.tw/budget/prj_epfee/kernel/kernel_prj_carddata_edit.php?page=NDgy")
            
            # 構建簽退請求數據
            sign_data = {
                "type": 2  # 簽退使用type=2
            }
            
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
                "Content-Type": "application/json",
                "Accept": "application/json, text/plain, */*",
                "X-Requested-With": "XMLHttpRequest"
            }
            
            # 發送簽退請求
            response = session.post(sign_out_url, json=sign_data, headers=headers, timeout=30)
            
            # 記錄原始響應以便調試
            self.logger.log(f"簽退API原始響應: {response.text}")
            
            # 檢查簽退結果
            if response.status_code == 200:
                try:
                    result = response.json()
                    result_code = result.get("result")
                    result_msg = result.get("msg", "未知響應")
                    
                    # 處理不同的響應結果
                    if result_code == 1:  # 成功簽退
                        self.logger.log(f"簽退成功: {result_msg}")
                        
                        # 更新任務狀態
                        task.sign_out_done = True
                        
                        # 檢查特殊訊息
                        if "工讀時數" in result_msg and "不足30分鐘" in result_msg:
                            self.logger.log("系統提示工讀時數不足30分鐘部分不計算")
                        
                        return True
                        
                    elif result_code == 0 and ("請先簽到" in result_msg or "尚未簽到" in result_msg):  # 未簽到就嘗試簽退
                        self.logger.log(f"簽退提示: {result_msg}，需要先完成簽到")
                        
                        # 確保狀態是未簽退
                        task.sign_out_done = False
                        
                        return False
                        
                    elif result_code == 0 and "已簽退" in result_msg:  # 已經簽退
                        self.logger.log(f"簽退提示: {result_msg}，您已經完成簽退")
                        
                        # 更新任務狀態，因為已經簽退了
                        task.sign_out_done = True
                        
                        # 返回True因為實際上簽退狀態已完成
                        return True
                        
                    elif result_code == -1 and ("無使用權限" in result_msg or "-101" in result_msg):  # 權限錯誤
                        self.logger.log(f"簽退權限錯誤: {result_msg}")
                        
                        # 處理校外環境情況
                        self.logger.log("檢測到校外環境或登入失效")
                        
                        # 標記任務為環境受限
                        task.campus_restricted = True
                        task.last_attempt_time = datetime.datetime.now().isoformat()
                        
                        # 嘗試重新登入
                        self.logger.log("嘗試重新登入...")
                        if self.auth_service.login(settings, force=True):
                            self.logger.log("重新登入成功，但仍需在校內網絡環境操作")
                        
                        return False
                        
                    else:  # 其他錯誤情況
                        self.logger.log(f"簽退失敗: 未知結果碼 {result_code}, 消息: {result_msg}")
                        return False
                        
                except ValueError as e:
                    # JSON解析失敗
                    self.logger.log(f"簽退響應解析失敗: {str(e)}\n響應內容: {response.text[:200]}")
                    return False
                    
                except Exception as e:
                    # 其他解析錯誤
                    self.logger.log(f"簽退響應處理錯誤: {str(e)}")
                    return False
            else:
                self.logger.log(f"簽退請求失敗，狀態碼: {response.status_code}")
                return False
                
        except RequestException as e:
            error_msg = f"簽退過程中發生網絡錯誤: {str(e)}"
            self.logger.log(error_msg)
            return False
        except Exception as e:
            error_msg = f"簽退過程中發生未知錯誤: {str(e)}"
            self.logger.log(error_msg)
            return False
