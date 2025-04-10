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
    
    def login(self, settings, force=False):
        """登入大葉大學系統並獲取Cookie
        
        Args:
            settings: 包含登入信息的設定字典
            force: 是否強制重新登入，即使Cookie可能還有效
            
        Returns:
            bool: 登入是否成功
        """
        # 檢查登入狀態，如果已登入且Cookie未過期，則不需要再次登入
        if self.login_status and not force:
            if self.last_login_time:
                login_valid_time = settings.get("session_valid_time", 270)
                elapsed = (datetime.datetime.now() - self.last_login_time).total_seconds()
                if elapsed < login_valid_time:
                    self.logger.log("使用現有會話，無需重新登入")
                    return True
        
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
            
            # 登入請求 - 使用x-www-form-urlencoded格式
            login_data = {
                "login_id": username,
                "login_pwd": password,
                "login_agent": "0",
                "login_ent": "15",
                "login_page": ""
            }
            
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
                "Content-Type": "application/x-www-form-urlencoded",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8"
            }
            
            # 發送登入請求
            response = self.session.post(login_url, data=login_data, headers=headers, timeout=30)
            
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
                        
                        return True
                    else:
                        # 如果找不到姓名格式，但有status元素，可能頁面格式已變更
                        self.logger.log(f"警告: 找到狀態元素但無法提取姓名, 內容: {status_text}")
                        
                        # 檢查是否有錯誤信息
                        # if "密碼有誤" in response.text or "帳號不存在" in response.text or "密碼錯誤" in response.text:
                        #     self.logger.log("登入失敗: 帳號或密碼錯誤")
                        #     return False
                        
                        # 檢查系統錯誤訊息
                        if "<meta http-equiv='refresh' content='0; url=error.php?error=" in response.text:
                            # 帳號錯誤或密碼錯誤的情況
                            if "error=2" in response.text or "error=3" in response.text:
                                self.logger.log("登入失敗: 帳號或密碼錯誤")
                                return False
                            # 其他系統錯誤
                            self.logger.log(f"登入失敗: 系統錯誤，請稍後再試")
                            return False
                        
                        # 假設登入成功，但格式已變更
                        self.login_status = True
                        self.last_login_time = datetime.datetime.now()
                        return True
                else:
                    # 檢查是否有錯誤信息 
                    # if "密碼有誤" in response.text or "帳號不存在" in response.text or "密碼錯誤" in response.text:
                    #     self.logger.log("登入失敗: 帳號或密碼錯誤")
                    #     return False
                    
                    # 檢查系統錯誤訊息
                    if "<meta http-equiv='refresh' content='0; url=error.php?error=" in response.text:
                        # 帳號錯誤或密碼錯誤的情況
                        if "error=2" in response.text or "error=3" in response.text:
                            self.logger.log("登入失敗: 帳號或密碼錯誤")
                            return False
                        # 其他系統錯誤
                        self.logger.log(f"登入失敗: 系統錯誤，請稍後再試")
                        return False
                    
                    self.logger.log("無法確認登入狀態，請檢查網頁結構是否已變更")
                    return False
            else:
                self.logger.log(f"登入請求失敗，狀態碼: {response.status_code}")
                return False
        
        except RequestException as e:
            self.logger.log(f"登入過程中發生網絡錯誤: {str(e)}")
            return False
        except Exception as e:
            self.logger.log(f"登入過程中發生未知錯誤: {str(e)}")
            import traceback
            self.logger.log(traceback.format_exc())
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
                    
                    # 使用API基礎URL刷新會話
                    refresh_url = settings.get("api_url", "https://adm_acc.dyu.edu.tw/entrance/index.php")
                    
                    headers = {
                        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
                    }
                    
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
                            return False
                        # 檢查是否有密碼錯誤信息，表示會話已失效
                        elif "密碼不得為空" in response.text or "帳號不得為空" in response.text:
                            self.logger.log("會話已過期，需要重新登入")
                            self.login_status = False
                            return False
                        else:
                            # 如果無法確定，嘗試檢查其他特徵
                            if "ispass = \"\"" in response.text:  # 未登入狀態特徵
                                self.logger.log("檢測到未登入狀態特徵，需要重新登入")
                                self.login_status = False
                                return False
                            elif "ispass = \"t\"" in response.text:  # 已登入狀態特徵
                                self.last_login_time = datetime.datetime.now()
                                self.logger.log("檢測到已登入狀態特徵，會話已成功刷新")
                                return True
                            else:
                                # 最後的保險措施，假設會話可能仍然有效
                                self.last_login_time = datetime.datetime.now()
                                self.logger.log("會話狀態不明確，假設有效並已刷新")
                                return True

                    else:
                        self.logger.log(f"刷新會話失敗，狀態碼: {response.status_code}，將在下次檢查時重新登入")
                        self.login_status = False
                        return False
                
                # 如果超過有效期，標記為失效
                if elapsed >= valid_time:
                    self.logger.log("會話已超過有效期，標記為失效")
                    self.login_status = False
                    return False
                    
                # 如果在正常的刷新間隔內，會話還有效
                return True
                
            return False  # 未登入或無上次登入時間記錄
        except Exception as e:
            self.logger.log(f"刷新會話時出錯: {str(e)}")
            self.login_status = False
            return False
    
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
            
            if elapsed >= valid_time:
                self.logger.log("會話可能已過期，重新登入")
                return self.login(settings, force=True)
        
        return True
    
    def get_session(self):
        """獲取當前會話
        
        Returns:
            Session: 當前的requests.Session實例
        """
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
        return cookies_list
    
    def set_cookies(self, cookies):
        """從保存的列表設置會話的Cookies
        
        Args:
            cookies: Cookie字典列表
        """
        for cookie_dict in cookies:
            self.session.cookies.set(**cookie_dict)
        
        # 初始認為Cookies有效，但會在首次操作時驗證
        self.login_status = True
        self.last_login_time = datetime.datetime.now()

