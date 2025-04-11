# -*- coding: utf-8 -*-
"""
認證服務
"""

import datetime
import re
import requests
from bs4 import BeautifulSoup
from requests.exceptions import RequestException

class AuthService:
    """認證服務，處理系統登入和會話維護"""
    
    def __init__(self, logger):
        """初始化認證服務
        
        Args:
            logger: 日誌記錄器
        """
        self.logger = logger
        self.session = requests.Session()
        self.session.verify = False  
        self.login_status = False
        self.last_login_time = None
        self.consecutive_failures = 0  # 追蹤連續登入失敗次數
        self.login_lock_until = None  # 登入鎖定直到某時間點
        self.important_cookies = []  # 儲存重要的cookie名稱
        
        # 設置標準請求頭部
        self.standard_headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Gecko/20100101 Firefox/137.0",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Encoding": "gzip, deflate, br, zstd",
            "Accept-Language": "zh-TW,zh;q=0.8,en-US;q=0.5,en;q=0.3",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1"
        }
    
    def login(self, settings, force=False):
        """登入大葉大學系統並獲取Cookie
        
        Args:
            settings: 包含登入信息的設定字典
            force: 是否強制重新登入，即使Cookie可能還有效
            
        Returns:
            bool: 登入是否成功
        """
        # 檢查是否處於登入鎖定狀態
        if self.login_lock_until and datetime.datetime.now() < self.login_lock_until:
            lock_remaining = (self.login_lock_until - datetime.datetime.now()).total_seconds()
            self.logger.log(f"登入暫時鎖定中，請等待 {int(lock_remaining)} 秒後再試")
            return False
            
        # 檢查登入狀態，如果已登入且Cookie未過期，則不需要再次登入
        if self.login_status and not force:
            if self.last_login_time:
                login_valid_time = settings.get("session_valid_time", 270)
                elapsed = (datetime.datetime.now() - self.last_login_time).total_seconds()
                if elapsed < login_valid_time:
                    self.logger.log("使用現有會話，無需重新登入")
                    return self.verify_session(settings)  # 快速驗證會話是否真的有效
        
        # 從設定中獲取登入信息
        login_url = settings.get("login_url", "https://adm_acc.dyu.edu.tw/entrance/save_id.php")
        username = settings.get("username", "")
        password = settings.get("password", "")
        expected_name = settings.get("name", "")  # 從設定中獲取姓名
        
        if not username or not password:
            self.logger.log("登入信息不完整，請在設定中配置用戶名和密碼")
            return False
        
        try:
            self.logger.log(f"嘗試登入大葉大學系統")
            
            # 清除現有會話
            self.session = requests.Session()
            self.session.verify = False
            
            # 設置標準請求頭
            for key, value in self.standard_headers.items():
                self.session.headers[key] = value
            
            # 先獲取登入頁面，獲取必要的cookies
            try:
                pre_login_url = settings.get("api_url", "https://adm_acc.dyu.edu.tw/entrance/index.php")
                pre_login_headers = self.standard_headers.copy()
                
                self.logger.log(f"正在獲取登入頁面以初始化cookies...")
                pre_login_response = self.session.get(pre_login_url, headers=pre_login_headers, timeout=30)
                self.logger.log(f"獲取登入頁面: 狀態碼 {pre_login_response.status_code}")
                
                # 記錄獲取到的初始cookies
                initial_cookies = dict(self.session.cookies)
                if initial_cookies:
                    self.logger.log(f"已獲取初始cookies: {', '.join(initial_cookies.keys())}")
                    # 記錄重要的cookie (如PHPSESSID)
                    for cookie_name in initial_cookies.keys():
                        if cookie_name.upper() in ['PHPSESSID', 'SESSION', 'JSESSIONID']:
                            self.important_cookies.append(cookie_name)
                            self.logger.log(f"識別到重要cookie: {cookie_name}")
                
            except Exception as e:
                self.logger.log(f"獲取登入頁面時出錯 (非致命): {str(e)}")
                # 繼續執行，這不是致命錯誤
            
            # 登入請求 - 使用x-www-form-urlencoded格式
            login_data = {
                "login_id": username,
                "login_pwd": password,
                "login_agent": "0",
                "login_ent": "15",
                "login_page": ""
            }
            
            headers = self.standard_headers.copy()
            headers.update({
                "Content-Type": "application/x-www-form-urlencoded",
                "Origin": "https://adm_acc.dyu.edu.tw",
                "Referer": "https://adm_acc.dyu.edu.tw/entrance/index.php"
            })
            
            # 發送登入請求
            response = self.session.post(login_url, data=login_data, headers=headers, timeout=30)
            
            # 記錄響應狀態和cookies（用於調試）
            self.logger.log(f"登入響應: 狀態碼 {response.status_code}")
            login_cookies = dict(self.session.cookies)
            self.logger.log(f"登入後cookies: {', '.join(login_cookies.keys())}")
            
            # 檢查重要cookie是否存在
            critical_cookie_missing = False
            for cookie_name in self.important_cookies:
                if cookie_name not in login_cookies:
                    self.logger.log(f"警告: 重要cookie {cookie_name} 在登入後丟失")
                    critical_cookie_missing = True
            
            if critical_cookie_missing:
                self.logger.log("重要cookie丟失，登入可能失敗")
            
            # 檢查登入結果
            if response.status_code == 200:
                # 使用BeautifulSoup解析HTML
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # 尋找狀態元素
                status_span = soup.select_one('span.status')
                
                if status_span:
                    # 提取姓名 (從 "楊智景 您好" 格式中提取姓名)
                    status_text = status_span.get_text().strip()
                    name_match = re.match(r'([^\s]+)\s*您好', status_text)
                    
                    if name_match:
                        actual_name = name_match.group(1).strip()
                        self.logger.log(f"檢測到登入用戶: {actual_name}")
                        
                        # 如果設定了預期姓名，則進行比對
                        if expected_name and expected_name.strip() != actual_name:
                            self.logger.log(f"警告: 登入用戶名 '{actual_name}' 與設定的姓名 '{expected_name}' 不符")
                        
                        # 無論是否比對一致，都認為登入成功
                        self.login_status = True
                        self.last_login_time = datetime.datetime.now()
                        self.consecutive_failures = 0  # 重置失敗計數
                        
                        # 確認登入後訪問主頁面，驗證會話有效性並獲取額外cookies
                        self._confirm_login(settings)
                        
                        return True
                    else:
                        # 如果找不到姓名格式，但有status元素，可能頁面格式已變更
                        self.logger.log(f"警告: 找到狀態元素但無法提取姓名, 內容: {status_text}")
                        
                        # 檢查系統錯誤訊息
                        if "<meta http-equiv='refresh' content='0; url=error.php?error=" in response.text:
                            # 帳號錯誤或密碼錯誤的情況
                            if "error=2" in response.text or "error=3" in response.text:
                                self.logger.log("登入失敗: 帳號或密碼錯誤")
                                self._handle_login_failure()
                                return False
                            # 其他系統錯誤
                            self.logger.log(f"登入失敗: 系統錯誤，請稍後再試")
                            self._handle_login_failure()
                            return False
                        
                        # 假設登入成功，但格式已變更
                        self.login_status = True
                        self.last_login_time = datetime.datetime.now()
                        self.consecutive_failures = 0  # 重置失敗計數
                        
                        # 確認登入
                        self._confirm_login(settings)
                        
                        return True
                else:
                    # 檢查系統錯誤訊息
                    if "<meta http-equiv='refresh' content='0; url=error.php?error=" in response.text:
                        # 帳號錯誤或密碼錯誤的情況
                        if "error=2" in response.text or "error=3" in response.text:
                            self.logger.log("登入失敗: 帳號或密碼錯誤")
                            self._handle_login_failure()
                            return False
                        # 其他系統錯誤
                        self.logger.log(f"登入失敗: 系統錯誤，請稍後再試")
                        self._handle_login_failure()
                        return False
                    
                    # 檢查是否仍在登入頁面
                    if "<form name=\"dyulogin\"" in response.text:
                        self.logger.log("登入失敗: 仍在登入頁面")
                        self._handle_login_failure()
                        return False
                    
                    # 如果找不到明確的登入失敗標誌，檢查cookies是否增加
                    if len(login_cookies) > len(initial_cookies) if 'initial_cookies' in locals() else 0:
                        self.logger.log("登入可能成功 (cookies增加)，但無法確認用戶名")
                        self.login_status = True
                        self.last_login_time = datetime.datetime.now()
                        self.consecutive_failures = 0
                        self._confirm_login(settings)
                        return True
                    
                    self.logger.log("無法確認登入狀態，請檢查網頁結構是否已變更")
                    self._handle_login_failure()
                    return False
            else:
                self.logger.log(f"登入請求失敗，狀態碼: {response.status_code}")
                self._handle_login_failure()
                return False
        
        except RequestException as e:
            self.logger.log(f"登入過程中發生網絡錯誤: {str(e)}")
            self._handle_login_failure()
            return False
        except Exception as e:
            self.logger.log(f"登入過程中發生未知錯誤: {str(e)}")
            import traceback
            self.logger.log(traceback.format_exc())
            self._handle_login_failure()
            return False
    
    def _handle_login_failure(self):
        """處理登入失敗的情況，實現指數退避策略"""
        self.consecutive_failures += 1
        self.login_status = False
        
        if self.consecutive_failures >= 3:
            # 按失敗次數計算鎖定時間，指數增長
            lockout_seconds = min(60 * (2 ** (self.consecutive_failures - 3)), 1800)  # 最長30分鐘
            self.login_lock_until = datetime.datetime.now() + datetime.timedelta(seconds=lockout_seconds)
            self.logger.log(f"因連續 {self.consecutive_failures} 次登入失敗，已暫時鎖定登入功能 {lockout_seconds} 秒")
    
    def _confirm_login(self, settings):
        """確認登入成功並獲取額外必要的cookies"""
        try:
            # 訪問首頁或儀表板以確認登入狀態
            dashboard_url = settings.get("api_url", "https://adm_acc.dyu.edu.tw/entrance/index.php")
            
            # 使用標準頭部並添加Referer
            headers = self.standard_headers.copy()
            headers["Referer"] = settings.get("login_url", "https://adm_acc.dyu.edu.tw/entrance/save_id.php")
            
            response = self.session.get(dashboard_url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                self.logger.log("成功訪問首頁，確認登入狀態")
                
                # 檢查是否有登出連結，這通常表示已登入
                if "登出</a>" in response.text:
                    self.logger.log("確認已登入: 找到登出連結")
                
                # 記錄cookies情況
                confirm_cookies = dict(self.session.cookies)
                self.logger.log(f"確認後的cookies: {', '.join(confirm_cookies.keys())}")
                
                # 檢查是否獲得了新的cookies
                initial_cookies = set(self.session.cookies.keys())
                if len(initial_cookies) > len(self.important_cookies):
                    self.logger.log(f"確認登入後獲得額外cookies")
            else:
                self.logger.log(f"訪問首頁失敗，狀態碼: {response.status_code}")
        
        except Exception as e:
            self.logger.log(f"確認登入時出錯 (非致命): {str(e)}")
    
    def verify_session(self, settings):
        """快速驗證當前會話是否有效
        
        Args:
            settings: 設定字典
        
        Returns:
            bool: 會話是否有效
        """
        try:
            # 檢查重要cookie是否存在
            current_cookies = {cookie.name: cookie.value for cookie in self.session.cookies}
            for cookie_name in self.important_cookies:
                if cookie_name not in current_cookies:
                    self.logger.log(f"會話已失效: 缺少重要cookie {cookie_name}")
                    self.login_status = False
                    return False
            
            # 訪問一個需要登入才能查看的頁面
            verify_url = settings.get("api_url", "https://adm_acc.dyu.edu.tw/entrance/index.php")
            
            # 使用標準頭部
            headers = self.standard_headers.copy()
            
            response = self.session.get(verify_url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                # 檢查頁面內容，確認是否需要登入
                if "<form name=\"dyulogin\"" in response.text or "login_id" in response.text and "login_pwd" in response.text:
                    self.logger.log("會話已失效: 發現登入表單")
                    self.login_status = False
                    return False
                elif "登出</a>" in response.text and "您好" in response.text:
                    return True
                elif "ispass = \"t\"" in response.text:  # 已登入狀態特徵
                    return True
                else:
                    # 嘗試查找用戶名或歡迎訊息
                    soup = BeautifulSoup(response.text, 'html.parser')
                    status = soup.select_one('span.status')
                    if status and "您好" in status.text:
                        return True
                    
                    # 檢查是否有明確的登出連結
                    logout_links = soup.find_all('a', href=re.compile(r'logout|signout|exit|登出'))
                    if logout_links:
                        return True
                    
                    # 最後的保險措施，可能需要根據實際情況調整
                    self.logger.log("無法確定會話狀態，將重新登入以確保")
                    return False
            else:
                self.logger.log(f"驗證會話失敗，狀態碼: {response.status_code}")
                return False
        except Exception as e:
            self.logger.log(f"驗證會話時出錯: {str(e)}")
            return False
    
    def keep_session_alive(self, settings):
        """定期刷新會話以保持登入狀態
        
        Args:
            settings: 包含會話設定的字典
            
        Returns:
            bool: 會話是否仍然有效
        """
        try:
            # 如果已登入且距離上次登入不超過設定的刷新間隔
            if self.login_status and self.last_login_time:
                # 從設定中獲取刷新間隔
                refresh_interval = settings.get("session_refresh_interval", 240)
                valid_time = settings.get("session_valid_time", 270)
                
                elapsed = (datetime.datetime.now() - self.last_login_time).total_seconds()
                
                # 在刷新間隔後刷新會話
                if refresh_interval <= elapsed < valid_time:
                    self.logger.log("會話即將過期，正在刷新...")
                    
                    # 快速驗證會話
                    if not self.verify_session(settings):
                        self.logger.log("會話驗證失敗，需要重新登入")
                        return self.login(settings, force=True)
                    
                    # 使用API基礎URL刷新會話
                    refresh_url = settings.get("api_url", "https://adm_acc.dyu.edu.tw/entrance/index.php")
                    
                    # 使用標準頭部
                    headers = self.standard_headers.copy()
                    
                    # 嘗試訪問API基礎URL刷新會話
                    response = self.session.get(refresh_url, headers=headers, timeout=10)
                    
                    if response.status_code == 200:
                        # 檢查頁面內容確認登入狀態維持
                        # 檢查是否有登出連結和用戶歡迎訊息，這表示會話仍然有效
                        if "登出</a>" in response.text and "<span class=\"status\">" in response.text and "您好" in response.text:
                            self.last_login_time = datetime.datetime.now()
                            self.logger.log("會話已成功刷新")
                            return True
                        # 檢查是否有登入表單，表示會話已失效
                        elif "<form name=\"dyulogin\"" in response.text or "login_id" in response.text and "login_pwd" in response.text:
                            self.logger.log("會話已過期，需要重新登入")
                            self.login_status = False
                            return self.login(settings, force=True)
                        # 檢查是否有密碼錯誤信息，表示會話已失效
                        elif "密碼不得為空" in response.text or "帳號不得為空" in response.text:
                            self.logger.log("會話已過期，需要重新登入")
                            self.login_status = False
                            return self.login(settings, force=True)
                        else:
                            # 如果無法確定，嘗試檢查其他特徵
                            if "ispass = \"\"" in response.text:  # 未登入狀態特徵
                                self.logger.log("檢測到未登入狀態特徵，需要重新登入")
                                self.login_status = False
                                return self.login(settings, force=True)
                            elif "ispass = \"t\"" in response.text:  # 已登入狀態特徵
                                self.last_login_time = datetime.datetime.now()
                                self.logger.log("檢測到已登入狀態特徵，會話已成功刷新")
                                return True
                            else:
                                # 嘗試使用BeautifulSoup檢查
                                soup = BeautifulSoup(response.text, 'html.parser')
                                status = soup.select_one('span.status')
                                if status and "您好" in status.text:
                                    self.last_login_time = datetime.datetime.now()
                                    self.logger.log("檢測到歡迎訊息，會話已成功刷新")
                                    return True

                                # 檢查cookies是否仍然有效
                                current_cookies = {cookie.name: cookie.value for cookie in self.session.cookies}
                                all_important_cookies_present = True
                                for cookie_name in self.important_cookies:
                                    if cookie_name not in current_cookies:
                                        all_important_cookies_present = False
                                        self.logger.log(f"重要cookie {cookie_name} 已丟失")
                                
                                if all_important_cookies_present:
                                    # 最後的保險措施，假設會話可能仍然有效
                                    self.last_login_time = datetime.datetime.now()
                                    self.logger.log("會話狀態不明確，但重要cookie仍存在，假設有效並已刷新")
                                    return True
                                else:
                                    self.logger.log("重要cookie已丟失，需要重新登入")
                                    self.login_status = False
                                    return self.login(settings, force=True)

                    else:
                        self.logger.log(f"刷新會話失敗，狀態碼: {response.status_code}，將在下次檢查時重新登入")
                        self.login_status = False
                        return self.login(settings, force=True)
                
                # 如果超過有效期，標記為失效
                if elapsed >= valid_time:
                    self.logger.log("會話已超過有效期，標記為失效")
                    self.login_status = False
                    return self.login(settings, force=True)
                    
                # 如果在正常的刷新間隔內，會話還有效
                return True
            
            # 未登入，嘗試登入
            self.logger.log("未檢測到活動會話，嘗試登入")
            return self.login(settings)
            
        except Exception as e:
            self.logger.log(f"刷新會話時出錯: {str(e)}")
            self.login_status = False
            return self.login(settings, force=True)
    
    def ensure_login(self, settings):
        """確保用戶已登入，必要時重新登入
        
        Args:
            settings: 包含登入信息的設定字典
            
        Returns:
            bool: 是否成功確保登入狀態
        """
        # 如果未登入或登入已過期，則執行登入
        if not self.login_status:
            return self.login(settings)
        
        # 檢查登入狀態是否過期
        if self.last_login_time:
            # 使用最新的設定值
            valid_time = settings.get("session_valid_time", 270)
            elapsed = (datetime.datetime.now() - self.last_login_time).total_seconds()
            
            if elapsed >= valid_time * 0.8:  # 如果已過80%的有效期，提前刷新
                self.logger.log("會話接近過期，主動刷新")
                return self.keep_session_alive(settings)
            
            # 如果真的過期了
            if elapsed >= valid_time:
                self.logger.log("會話可能已過期，重新登入")
                return self.login(settings, force=True)
            
            # 還在有效期內，進行快速驗證
            if elapsed >= valid_time * 0.5:  # 超過一半的有效期，進行驗證
                # 檢查重要cookie是否存在
                current_cookies = {cookie.name: cookie.value for cookie in self.session.cookies}
                for cookie_name in self.important_cookies:
                    if cookie_name not in current_cookies:
                        self.logger.log(f"會話驗證失敗: 缺少重要cookie {cookie_name}")
                        return self.login(settings, force=True)
                
                # 只有在cookie檢查不夠時才進行完整驗證
                if not self.important_cookies or elapsed >= valid_time * 0.7:
                    if not self.verify_session(settings):
                        self.logger.log("會話驗證失敗，重新登入")
                        return self.login(settings, force=True)
        
        return True
    
    def get_session(self):
        """獲取當前會話
        
        Returns:
            Session: 當前的requests.Session實例
        """
        # 更新會話的標準頭部
        for key, value in self.standard_headers.items():
            self.session.headers[key] = value
            
        return self.session
        
    def get_cookies_list(self):
        """獲取當前會話的Cookies列表，用於保存
        
        Returns:
            list: Cookie字典列表
        """
        cookies_list = []
        for cookie in self.session.cookies:
            cookie_dict = {
                'name': cookie.name,
                'value': cookie.value,
                'domain': cookie.domain,
                'path': cookie.path
            }
            cookies_list.append(cookie_dict)
            
            # 記錄重要cookie
            if cookie.name.upper() in ['PHPSESSID', 'SESSION', 'JSESSIONID'] and cookie.name not in self.important_cookies:
                self.important_cookies.append(cookie.name)
                
        return cookies_list
    
    def set_cookies(self, cookies):
        """從保存的列表設置會話的Cookies
        
        Args:
            cookies: Cookie字典列表
        """
        # 重置重要cookie列表
        self.important_cookies = []
        
        for cookie_dict in cookies:
            self.session.cookies.set(**cookie_dict)
            
            # 檢測重要cookie
            if cookie_dict['name'].upper() in ['PHPSESSID', 'SESSION', 'JSESSIONID']:
                self.important_cookies.append(cookie_dict['name'])
                self.logger.log(f"從保存的cookie中識別到重要cookie: {cookie_dict['name']}")
        
        # 不要立即假設Cookies有效
        self.login_status = False
        self.last_login_time = None
        
        # 更新標準頭部
        for key, value in self.standard_headers.items():
            self.session.headers[key] = value

    def verify_cookie_auth(self, settings):
        """驗證網站是否使用cookies進行權限控制
        
        Args:
            settings: 設定字典
        
        Returns:
            dict: 包含測試結果的字典
        """
        results = {
            "uses_cookie_auth": False,
            "critical_cookies": [],
            "details": "",
            "tests_performed": []
        }
        
        try:
            # 首先確保已經登入
            if not self.login_status:
                login_success = self.login(settings)
                if not login_success:
                    results["details"] = "無法登入以執行測試"
                    return results
            
            # 記錄當前所有cookies
            original_cookies = {cookie.name: cookie.value for cookie in self.session.cookies}
            results["tests_performed"].append("記錄原始cookies")
            
            # 1. 測試: 拷貝會話並嘗試訪問，作為基準
            test_session = requests.Session()
            test_session.headers.update(self.session.headers)
            # 複製所有cookies
            for name, value in original_cookies.items():
                test_session.cookies.set(name, value)
            
            # 訪問需要授權的頁面
            auth_url = settings.get("api_url", "https://adm_acc.dyu.edu.tw/entrance/index.php")
            response = test_session.get(auth_url, timeout=10)
            
            # 檢查基準結果 - 是否訪問成功
            has_login_form = "<form name=\"dyulogin\"" in response.text
            has_welcome = "您好" in response.text and "登出" in response.text
            base_authorized = has_welcome and not has_login_form
            
            results["tests_performed"].append("完成基準測試")
            
            if not base_authorized:
                results["details"] = "基準測試失敗，即使有完整cookies也無法訪問受保護頁面"
                return results
            
            # 2. 測試: 移除所有cookies並嘗試訪問
            test_session = requests.Session()
            test_session.headers.update(self.session.headers)
            # 不添加任何cookies
            
            response = test_session.get(auth_url, timeout=10)
            no_cookies_has_login = "<form name=\"dyulogin\"" in response.text
            
            results["tests_performed"].append("完成無cookies測試")
            
            # 3. 測試: 有選擇地移除cookies並測試
            for cookie_name in original_cookies.keys():
                test_session = requests.Session()
                test_session.headers.update(self.session.headers)
                
                # 複製除了當前測試cookie外的所有cookies
                for name, value in original_cookies.items():
                    if name != cookie_name:
                        test_session.cookies.set(name, value)
                
                # 訪問授權頁面
                response = test_session.get(auth_url, timeout=10)
                
                # 檢查是否包含登入表單或歡迎訊息
                has_login_form = "<form name=\"dyulogin\"" in response.text
                has_welcome = "您好" in response.text and "登出" in response.text
                
                # 如果缺少這個cookie導致需要重新登入，則這個cookie對授權很重要
                if has_login_form and not has_welcome:
                    results["critical_cookies"].append(cookie_name)
                
                results["tests_performed"].append(f"測試移除 {cookie_name}")
            
            # 分析結果
            if no_cookies_has_login and results["critical_cookies"]:
                results["uses_cookie_auth"] = True
                results["details"] = f"確認網站使用cookies進行權限控制。關鍵cookies: {', '.join(results['critical_cookies'])}"
            
            # 4. 測試: 修改PHPSESSID並嘗試訪問
            if "PHPSESSID" in original_cookies:
                test_session = requests.Session()
                test_session.headers.update(self.session.headers)
                
                # 複製所有cookies，但修改PHPSESSID
                for name, value in original_cookies.items():
                    if name == "PHPSESSID":
                        # 將PHPSESSID修改為隨機值
                        import random
                        import string
                        random_value = ''.join(random.choices(string.ascii_lowercase + string.digits, k=26))
                        test_session.cookies.set(name, random_value)
                    else:
                        test_session.cookies.set(name, value)
                
                # 訪問授權頁面
                response = test_session.get(auth_url, timeout=10)
                
                # 檢查是否包含登入表單
                has_login_form = "<form name=\"dyulogin\"" in response.text
                
                if has_login_form:
                    results["uses_cookie_auth"] = True
                    if "PHPSESSID" not in results["critical_cookies"]:
                        results["critical_cookies"].append("PHPSESSID")
                    results["details"] += " 修改PHPSESSID導致需要重新登入，確認其為關鍵會話標識。"
                
                results["tests_performed"].append("完成PHPSESSID修改測試")
            
            # 更新重要cookies列表
            self.important_cookies = list(set(self.important_cookies + results["critical_cookies"]))
            
            return results
        
        except Exception as e:
            import traceback
            results["details"] = f"測試過程中發生錯誤: {str(e)}\n{traceback.format_exc()}"
            return results

