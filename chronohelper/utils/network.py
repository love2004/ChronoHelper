# -*- coding: utf-8 -*-
"""
網絡檢測功能
"""

import socket
import subprocess
import platform
import re
import time
import threading
import contextlib

class NetworkUtils:
    """網絡工具類"""
    
    def __init__(self, logger, settings=None):
        """初始化網絡工具
        
        Args:
            logger: 日誌記錄器實例
            settings: 設定字典，若提供則使用設定中的配置
        """
        self.logger = logger
        self.settings = settings or {}
        self.cache = {
            'is_campus': None,
            'ip_address': None,
            'hop_info': None,
            'last_check_time': 0,
            'check_in_progress': False
        }
        self.cache_timeout = 60  # 緩存有效期（秒）
        self.lock = threading.RLock()  # 使用可重入鎖，更安全
        self.shutdown_flag = False  # 關閉標記，用於中止進行中的操作
        self.active_processes = []  # 跟踪活動的子進程
        self.active_threads = []    # 跟踪活動的線程
    
    def update_settings(self, settings):
        """更新設定，無需重啟應用程式
        
        Args:
            settings: 新的設定字典
        """
        # 保存新設定
        self.settings = settings or {}
        
        # 讀取最新的超時設定
        self.hop_check_timeout = self.settings.get("hop_check_timeout", 3)
        
        # 清除緩存，強制下次檢測使用新設定
        self.clear_cache()
        self.logger.log("網絡檢測設定已更新")
    
    def clear_cache(self):
        """清除檢測結果緩存"""
        with self.lock:
            self.cache['last_check_time'] = 0
    
    def shutdown(self):
        """關閉和清理所有網絡操作
        
        在應用程式關閉前調用，確保所有資源被釋放
        """
        self.logger.log("正在停止所有網絡檢測操作...")
        self.shutdown_flag = True
        
        # 中止所有活動子進程
        for proc in self.active_processes:
            try:
                if proc.poll() is None:  # 如果進程仍在運行
                    proc.terminate()
                    self.logger.log("已終止進程")
            except Exception as e:
                self.logger.log(f"終止進程時發生錯誤: {str(e)}")
        
        # 清空進程列表
        self.active_processes = []
        
        # 等待所有線程完成（最多等待3秒）
        for thread in self.active_threads:
            if thread.is_alive():
                thread.join(3.0)
        
        # 清空線程列表
        self.active_threads = []
        
        # 確保鎖被釋放
        with contextlib.suppress(Exception):
            if self.lock._is_owned():
                self.lock.release()
        
        self.logger.log("網絡檢測操作已全部停止")
    
    def check_campus_network(self, verbose=True, check_second_hop=None):
        """檢測是否在校內網絡環境（163.23.x.x）
        
        Args:
            verbose: 是否輸出檢測過程的日誌，默認為True
            check_second_hop: 是否檢查第二躍點，如果為None則使用設定中的值
            
        Returns:
            tuple: (is_campus, ip_address, hop_info) 是否在校內網絡、當前IP地址和躍點信息
        """
        # 檢查是否已關閉
        if self.shutdown_flag:
            return False, "已關閉", {}
            
        # 如果未提供check_second_hop參數，使用設定中的值
        if check_second_hop is None:
            check_second_hop = self.settings.get("enable_second_hop", False)
        
        # 檢查緩存是否有效
        current_time = time.time()
        if (current_time - self.cache['last_check_time'] < self.cache_timeout and 
            self.cache['ip_address'] is not None):
            if verbose:
                self.logger.log("使用緩存的網絡檢測結果")
            return (self.cache['is_campus'] or False, 
                    self.cache['ip_address'] or "未知", 
                    self.cache['hop_info'] or {})
        
        # 檢測處理中標記
        if self.cache['check_in_progress']:
            if verbose:
                self.logger.log("另一個網絡檢測正在進行，使用緩存結果")
            return (self.cache['is_campus'] or False, 
                    self.cache['ip_address'] or "未知", 
                    self.cache['hop_info'] or {})
        
        # 嘗試獲取線程鎖，最多等待100毫秒
        if not self.lock.acquire(blocking=True, timeout=0.1):
            if verbose:
                self.logger.log("無法獲取鎖，使用緩存結果")
            return (self.cache['is_campus'] or False, 
                    self.cache['ip_address'] or "未知", 
                    self.cache['hop_info'] or {})
        
        try:
            self.cache['check_in_progress'] = True
            
            # 輕量級檢測：獲取本機IP地址
            try:
                # 獲取本機名稱和IP地址
                hostname = socket.gethostname()
                ip_address = socket.gethostbyname(hostname)
                
                # 更新緩存
                self.cache['ip_address'] = ip_address
                self.cache['last_check_time'] = current_time
                
                # 檢查IP地址是否符合校內網絡特徵
                is_campus = ip_address.startswith('163.23.')
                self.cache['is_campus'] = is_campus
                
                if verbose:
                    self.logger.log(f"檢測到本地IP地址: {ip_address}")
                    if is_campus:
                        self.logger.log("網絡檢測結果: 校內網絡 ✓")
                    else:
                        self.logger.log("本機IP不是校內網絡")
                
                # 如果是校內網絡，或者不需要檢查第二躍點，直接返回結果
                if is_campus or not check_second_hop:
                    # 如果不檢查第二躍點但又不是校內網絡，輸出提示
                    if not is_campus and not check_second_hop and verbose:
                        self.logger.log("註: 第二躍點檢測已禁用，不進行進一步檢查")
                    
                    hop_info = self.cache['hop_info'] or {}  # 使用之前的躍點信息或空字典
                    
                    # 釋放鎖並返回結果
                    self.cache['check_in_progress'] = False
                    self.lock.release()
                    return is_campus, ip_address, hop_info
                
                # 啟動一個線程進行第二躍點檢測，不阻塞主線程
                if verbose:
                    self.logger.log("本機IP不是校內網絡，在背景檢查第二躍點...")
                
                # 創建檢測線程函數
                def check_hop_thread():
                    try:
                        # 使用設定中的超時值
                        timeout = self.settings.get("hop_check_timeout", 3)
                        
                        # 檢測第二躍點
                        second_hop_info = self.check_second_hop(verbose, timeout)
                        
                        # 檢查是否已關閉
                        if self.shutdown_flag:
                            return
                            
                        # 更新緩存中的躍點信息和校內網絡狀態
                        with contextlib.suppress(Exception):
                            with self.lock:
                                # 更新緩存
                                self.cache['hop_info'] = second_hop_info
                                
                                # 如果第二躍點是校內網絡，更新is_campus標記
                                if second_hop_info.get('is_campus', False):
                                    self.cache['is_campus'] = True
                                    if verbose:
                                        self.logger.log(f"網絡檢測結果: 通過第二躍點識別為校內網絡 ✓")
                                else:
                                    if verbose:
                                        self.logger.log(f"網絡檢測結果: 非校內網絡 ✗")
                    except Exception as e:
                        if verbose:
                            self.logger.log(f"第二躍點檢測異常: {type(e).__name__} - {str(e)}")
                    finally:
                        # 確保標記被正確設置
                        with contextlib.suppress(Exception):
                            self.cache['check_in_progress'] = False
                        
                        # 從活動線程列表中移除自己
                        with contextlib.suppress(Exception):
                            if thread in self.active_threads:
                                self.active_threads.remove(thread)
                
                # 創建線程
                thread = threading.Thread(target=check_hop_thread, daemon=True)
                
                # 添加到活動線程列表
                self.active_threads.append(thread)
                
                # 啟動線程
                thread.start()
                
                # 釋放鎖，讓方法可以立即返回結果
                self.lock.release()
                
                # 返回目前已知的結果
                return is_campus, ip_address, self.cache['hop_info'] or {}
                
            except Exception as e:
                if verbose:
                    self.logger.log(f"IP地址檢測失敗: {str(e)}")
                return False, "未知", {}
        finally:
            # 確保在出現異常時也釋放鎖
            with contextlib.suppress(Exception):
                if self.lock._is_owned():
                    self.lock.release()
    
    def check_second_hop(self, verbose=True, timeout=None):
        """檢測第二躍點是否在校內網絡環境
        
        Args:
            verbose: 是否輸出檢測過程的日誌，默認為True
            timeout: 檢測命令超時時間（秒），默認使用設定中的值或3秒
            
        Returns:
            dict: 包含第二躍點信息的字典
        """
        # 檢查是否已關閉
        if self.shutdown_flag:
            return {'is_campus': False, 'ip': '已關閉', 'method': 'shutdown'}
            
        # 使用參數或實例屬性中的超時值
        if timeout is None:
            timeout = getattr(self, 'hop_check_timeout', self.settings.get("hop_check_timeout", 3))
            
        hop_info = {
            'is_campus': False,
            'ip': '未知',
            'hop_number': 2,
            'method': 'unknown'
        }
        
        try:
            # 使用比較輕量級的方法來確定路由器/閘道器IP
            gateway_ip = self.get_gateway_ip(timeout)
            if gateway_ip:
                hop_info['ip'] = gateway_ip
                hop_info['is_campus'] = gateway_ip.startswith('163.23.')
                hop_info['method'] = 'gateway'
                
                if verbose:
                    self.logger.log(f"檢測到閘道器IP: {gateway_ip}")
                
                # 如果閘道器已經是校內網絡，直接返回結果
                if hop_info['is_campus']:
                    if verbose:
                        self.logger.log("閘道器IP識別為校內網絡")
                    return hop_info
                elif verbose:
                    self.logger.log("閘道器IP不是校內網絡，繼續檢測")
            
            # 檢查是否已關閉
            if self.shutdown_flag:
                return {'is_campus': False, 'ip': '已關閉', 'method': 'shutdown'}
                
            # 如果輕量級方法失敗或閘道器不是校內網絡，使用tracert/traceroute
            # 根據操作系統選擇不同的追蹤路由命令
            system = platform.system().lower()
            
            if system == 'windows':
                # Windows使用tracert命令
                target = '8.8.8.8'  # Google DNS服務器作為目標
                cmd = f'tracert -h 2 -w 500 {target}'
                
                if verbose:
                    self.logger.log(f"執行命令: {cmd}")
                
                # 執行命令並獲取輸出
                process = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, 
                                           stderr=subprocess.PIPE, text=True)
                # 跟踪進程
                self.active_processes.append(process)
                
                try:
                    # 等待進程完成，設置超時
                    stdout, stderr = process.communicate(timeout=timeout)
                    
                    # 從活動進程列表中刪除
                    if process in self.active_processes:
                        self.active_processes.remove(process)
                    
                    # 解析tracert輸出以獲取第二躍點信息
                    lines = stdout.split('\n')
                    for line in lines:
                        # 第二躍點通常在第4行（索引3，因為有標題行）
                        if '  2 ' in line:
                            # 使用正則表達式提取IP地址
                            ip_match = re.search(r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b', line)
                            if ip_match:
                                hop_ip = ip_match.group(0)
                                hop_info['ip'] = hop_ip
                                hop_info['is_campus'] = hop_ip.startswith('163.23.')
                                hop_info['method'] = 'tracert'
                                
                                if verbose:
                                    self.logger.log(f"第二躍點IP: {hop_ip}")
                                    if hop_info['is_campus']:
                                        self.logger.log(f"第二躍點IP識別為校內網絡")
                                    else:
                                        self.logger.log(f"第二躍點IP不是校內網絡")
                                break
                except subprocess.TimeoutExpired:
                    # 超時時中止進程
                    if process.poll() is None:
                        process.terminate()
                    # 從活動進程列表中刪除
                    if process in self.active_processes:
                        self.active_processes.remove(process)
                    if verbose:
                        self.logger.log(f"tracert命令超時（{timeout}秒）")
                    hop_info['method'] = 'timeout'
            else:
                # Linux/Mac使用traceroute命令
                target = '8.8.8.8'  # Google DNS服務器作為目標
                cmd = f'traceroute -m 2 -w 1 {target}'
                
                if verbose:
                    self.logger.log(f"執行命令: {cmd}")
                
                # 執行命令並獲取輸出
                process = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, 
                                           stderr=subprocess.PIPE, text=True)
                # 跟踪進程
                self.active_processes.append(process)
                
                try:
                    # 等待進程完成，設置超時
                    stdout, stderr = process.communicate(timeout=timeout)
                    
                    # 從活動進程列表中刪除
                    if process in self.active_processes:
                        self.active_processes.remove(process)
                    
                    # 解析traceroute輸出以獲取第二躍點信息
                    lines = stdout.split('\n')
                    if len(lines) >= 3:  # 確保至少有3行（標題行+兩個躍點）
                        # 第二躍點在第3行（索引2）
                        second_hop_line = lines[2]
                        # 使用正則表達式提取IP地址
                        ip_match = re.search(r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b', second_hop_line)
                        if ip_match:
                            hop_ip = ip_match.group(0)
                            hop_info['ip'] = hop_ip
                            hop_info['is_campus'] = hop_ip.startswith('163.23.')
                            hop_info['method'] = 'traceroute'
                            
                            if verbose:
                                self.logger.log(f"第二躍點IP: {hop_ip}")
                                if hop_info['is_campus']:
                                    self.logger.log(f"第二躍點IP識別為校內網絡")
                                else:
                                    self.logger.log(f"第二躍點IP不是校內網絡")
                except subprocess.TimeoutExpired:
                    # 超時時中止進程
                    if process.poll() is None:
                        process.terminate()
                    # 從活動進程列表中刪除
                    if process in self.active_processes:
                        self.active_processes.remove(process)
                    if verbose:
                        self.logger.log(f"traceroute命令超時（{timeout}秒）")
                    hop_info['method'] = 'timeout'
            
            return hop_info
            
        except subprocess.TimeoutExpired:
            if verbose:
                self.logger.log(f"第二躍點檢測超時（{timeout}秒限制）")
            hop_info['method'] = 'timeout'
            return hop_info
        except Exception as e:
            if verbose:
                self.logger.log(f"第二躍點檢測失敗: {str(e)}")
            hop_info['method'] = 'error'
            return hop_info
    
    def get_gateway_ip(self, timeout=2):
        """獲取默認閘道器IP（更輕量級的方法）
        
        Args:
            timeout: 命令執行超時時間（秒）
            
        Returns:
            str: 閘道器IP地址或None
        """
        try:
            system = platform.system().lower()
            
            if system == 'windows':
                # Windows使用ipconfig
                result = subprocess.run('ipconfig', shell=True, capture_output=True, text=True, timeout=timeout)
                output = result.stdout
                
                # 嘗試查找默認閘道器
                lines = output.split('\n')
                for i, line in enumerate(lines):
                    if '默認閘道' in line or 'Default Gateway' in line:
                        # 提取IP地址
                        ip_match = re.search(r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b', line)
                        if ip_match:
                            return ip_match.group(0)
            else:
                # Linux/Mac使用route -n或netstat -nr
                try:
                    # 首先嘗試route -n
                    result = subprocess.run('route -n', shell=True, capture_output=True, text=True, timeout=timeout)
                    output = result.stdout
                    
                    lines = output.split('\n')
                    for line in lines:
                        if '0.0.0.0' in line or 'default' in line:
                            parts = line.split()
                            for part in parts:
                                if re.match(r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b', part):
                                    return part
                except:
                    # 如果route -n失敗，嘗試netstat -nr
                    result = subprocess.run('netstat -nr', shell=True, capture_output=True, text=True, timeout=timeout)
                    output = result.stdout
                    
                    lines = output.split('\n')
                    for line in lines:
                        if '0.0.0.0' in line or 'default' in line:
                            parts = line.split()
                            for part in parts:
                                if re.match(r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b', part):
                                    return part
            
            return None
        except Exception:
            return None
